#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import sqlite3
import numpy as np
import tables
import re
from itertools import chain
from types import StringType, IntType, FloatType, ListType

databases = {}
class Database(object):
    def __new__(cls, filename):
        if filename in databases:
            return databases[filename]
        databases[filename] = db = object.__new__(cls)
        db.filename = filename
        db.init_once(filename)
        return db
    def __init__(self, filename):
        pass # do not use
    def init_once(self, filename):
        self.filename = filename

class Column(object):
    def __init__(self, description):
        if '=' not in description:
            description += '=float'
        self.name, datatype = description.split('=',1)
        assert(re.match('[a-z][a-z0-9_]*$', self.name, re.I))
        typematch = re.match(r'(\w+)(?:\((\d+)\))?$', datatype)
        if (typematch):
            size = typematch.group(2)
            size = 0 if size is None else int(size)
            typename = typematch.group(1).lower()
            if typename in ('int', 'integer', 'number', 'long'):
                self.datatype = IntType
                self.size = 4
            elif typename in ('text', 'string', 'char', 'varchar'):
                self.datatype = StringType
                self.size = max(8,size)
            elif typename in ('real', 'double', 'dbl', 'float'):
                self.datatype = FloatType
                self.size = 8
            else:
                raise Exception("unknown type name %s." % typename)
        else:
            raise Exception("unable to parse type %s" % typename)
    def __repr__(self):
        dtype = "Int"
        if self.datatype == StringType: dtype = "String"
        if self.datatype == FloatType: dtype = "Float"
        return "<%s %s>" % (self.name, dtype)

def parse_columns(string):
    """
    Get a list of column types

    This method interprets the requested section property as a list
    of key=value items where value denotes a data type. It returns a
    list of dict items with the properties 'name', 'type' and 'size'.

    var=REAL  -- denotes a column of floating point values (double)
    var=INT   -- denotes a column of integer numbers (4 bytes)
    var=TEXT  -- denotes a column containing text (8 chars)

    Alternatives include (REAL|DBL|DOUBLE|FLOAT), (INT|INTEGER|NUMBER)
    and (TEXT|STR|STRING|VARCHAR). Each type may be followed by
    parentheses denoting the number of bytes to use (currently only
    does something for TEXT, REAL(8) and INT(4) are fixed).
    """
    assert(type(string) is StringType)
    return [Column(desc) for desc in string.split()]

class Table(object):
    def __init__(self, database, name, columns=[], unique=[]):
        self.database = database
        self.name = name
        self.columns = self._make_column_list(columns)
        self.unique = self._make_column_list(unique)
        self.database.create_table(self)
    def get_groups(self, grouping):
        return self.database.get_groups(self.name, grouping)
    def get_group_data(self, columns, grouping, values, ordering=None, where=None):
        return self.database.get_group_data(self.name, columns=columns,
                                            grouping=grouping,
                                            values=values, ordering=ordering,
                                            where=where)
    def insert(self, datadict):
        return self.database.insert(self.name, datadict)
    def _entry_from_dict(self, datadict):
        return [datadict[col.name] for col in self.columns]
    @classmethod
    def _make_column_list(cls, columns):
        if type(columns) is StringType:
            return parse_columns(columns)
        assert(type(columns) is ListType)
        for i, desc in enumerate(columns):
            if type(desc) is not Column:
                columns[i] = Column(desc)
        return columns


class SqliteDB(Database):
    def __init__(self, filename):
        super(SqliteDB, self).__init__(filename)
    def init_once(self, filename):
        self.filename = filename
        self.connection = sqlite3.connect('analysis/'+filename+'.db')
        self.cursor = self.connection.cursor()
    def __del__(self):
        self.connection.commit()
        self.connection.close()
    def create_table(self, table):
        """ Create table for column description """
        # TODO drop and redo if does not match
        if (table.name not in ('bootstrap','extract')):
            #print('(not) Dropping table %s' % table.name)
            #self.cursor.execute('DROP TABLE %s' % table.name)
            pass
        #print(table.name, self._describe(table))
        self.cursor.execute('CREATE TABLE IF NOT EXISTS %s(%s)' % (
            table.name, ','.join(self._describe(table))))
    def _columntypes(self, table, columns):
        if columns is None:
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' and name='"+table+"';")
            tabledesc = self.cursor.fetchone()[0]
            tabledesc = re.sub(r'\s+','=',tabledesc)
            tabledesc = re.sub(r',',' ',tabledesc)
            tabledesc = re.sub(r'.*\((.*)\)','\\1',tabledesc)
            columns = parse_columns(str(tabledesc))
        colnames = [(c if type(c) is StringType else c.name) for c in columns]
        query = 'SELECT '+(','.join(colnames))+' FROM '+table+' LIMIT 1'

        self.cursor.execute(query)
        types = []
        for column in self.cursor.fetchone():
            if type(column) is IntType:
                types.append('i4')
            elif type(column) is FloatType:
                types.append('f8')
            elif type(column) is StringType:
                types.append('a16') # todo should not be hardcoded ...
            else:
                types.append('a16') # todo should not be hardcoded ...
                #print "unknown type %s" % (str(type(column)))
        return [(col,typ) for col,typ in zip(columns,types)]

    def _select(self, tablename, columns=None, where=None, ordering=None, distinct=False):
        # TODO refactor this to own function!
        if columns is None:
            self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' and name='"+tablename+"';")
            tabledesc = self.cursor.fetchone()[0]
            tabledesc = re.sub(r'\s+','=',tabledesc)
            tabledesc = re.sub(r',',' ',tabledesc)
            tabledesc = re.sub(r'.*\((.*)\)','\\1',tabledesc)
            columns = parse_columns(str(tabledesc))

        colnames = [(c if type(c) is StringType else c.name) for c in columns]
        query = 'SELECT DISTINCT ' if distinct else 'SELECT '
        query += ','.join(colnames)
        types = self._columntypes(tablename, colnames)

        query += ' FROM '+tablename
        if where is not None:
            query += ' WHERE '+where
        if ordering is not None and len(ordering)>0:
            ordnames = [(c if type(c) is StringType else c.name) for c in ordering]
            query += ' ORDER BY '+(','.join(ordnames))
        try:
            self.cursor.execute(query)
            data = np.fromiter(self.cursor, dtype=types)
        except Exception as e:
            print(query)
            raise e
        return data

    def get_groups(self, tablename, grouping):
        if len(grouping)==0: return [[]]
        colnames = [(c if type(c) is StringType else c.name) for c in grouping]
        query = 'SELECT DISTINCT ' + (','.join(colnames))
        query += ' FROM %s ORDER BY %s' % (tablename,','.join(colnames))
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_group_data(self, tablename, columns=None, grouping=[], values=[],
                       ordering=None, where=None):
        assert(len(grouping)==len(values))
        if len(grouping)>0:
            paramvalues = zip(grouping,values)
            groupwhere = [self._where(var,val) for var,val in paramvalues]
            groupwhere = ' AND '.join(groupwhere)
            if where is None:
                where = groupwhere
            else:
                where = "(%s) AND (%s)" % (where, groupwhere)
        return self._select(tablename, columns, ordering=ordering, where=where)
    def insert(self, tablename, entry):
        # TODO: datadict might not be necessary?
        """ Insert data dictionary into the table """
        query = 'INSERT INTO %s VALUES (%s)' % (
            tablename, ','.join(['?']*len(entry)))
        self.cursor.executemany(query, [entry])
    @classmethod
    def _describe(cls, table):
        """
        Tranform types into column description for sqlite

        This takes a list of types and converts them to a list of
        variable + type-string ('REAL', 'INT' or 'TEXT') for sqlite.
        """
        desc = []
        for column in table.columns:
            if column.datatype is FloatType:
                desc.append(column.name+' REAL')
            elif column.datatype is StringType:
                desc.append(column.name+' TEXT')
            elif column.datatype is IntType:
                desc.append(column.name+' INT')
        return desc
    @classmethod
    def _where(cls, x,y):
        if type(x) is Column:
            x = x.name
        if type(y) is IntType or type(y) is FloatType:
            return x+'='+str(y)
        else:
            return x+'=\''+y+'\''
    pass

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
