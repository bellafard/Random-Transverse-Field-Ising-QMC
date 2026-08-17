#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import re, os, time
from evaluator import Evaluator
from database import SqliteDB, Table
from copy import copy

#sections = {}
class Section(object):
    def __new__(cls, name, config):
        #if name in sections:
        #    return sections[name]
        if cls == Section:
            for newcls in Section.get_subclasses():
                if re.match(newcls.__name__+'_', name+'_', re.I):
                    cls = newcls
                    break
            else:
                raise Exception("unknown type for section %s" % name)
        return object.__new__(cls)
    def __init__(self, name, config):
        self.name = name
        self.config = copy(config)
        self.config.set_section(name)
        self.eval = Evaluator()
    def timestamp(self):
        return time.time()
    def update(self, analysis):
        pass
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.name)

    @classmethod
    def get_subclasses(cls):
        subclasses = cls.__subclasses__()
        for cls in subclasses:
            subclasses += cls.get_subclasses()
        return list(set(subclasses))

class TabledSection(Section):
    def get_dbname(self):
        return self.name
    def get_dbcolumns(self):
        return self.config.get_columns('store')
    def get_dbunique(self):
        return []
    def __init__(self, *args, **kwargs):
        super(TabledSection, self).__init__(*args, **kwargs)
        self.source = self.config.get_list('source')
        self.store = self.get_dbcolumns()
        #self.database = SqliteDB(self.get_dbname())
        #self.table = Table(self.database, self.name, self.store)
        self._table = None
        self._database = None
    def _get_db(self):
        if self._database is None:
            self._database = SqliteDB(self.get_dbname())
        return self._database
    def _get_table(self):
        if self._table is None:
            self._table = Table(self._get_db(), self.name, self.store)
        return self._table
    def timestamp(self):
        if not os.path.exists('analysis/%s.db' % self.get_dbname()):
            return None
        else:
            return os.path.getmtime('analysis/%s.db' % self.get_dbname())
    def do_update(self, analysis, callers=[]):
        if self.name in callers:
            return True
        callers += [self.name]
        stamp, max_mtime = self.timestamp(), 0
        if stamp is None:
            return True
        for source in self.source:
            section = analysis.get_section(source)
            mtime = section.timestamp()
            if mtime is None or section.do_update(analysis, callers):
                return True
            max_mtime = max(max_mtime, mtime)
        return max_mtime > stamp
    def get_groups(self, grouping):
        table = self._get_table()
        return table.get_groups(grouping)
    def get_group_data(self, columns=None, grouping=[], values=[], ordering=None, where=None):
        table = self._get_table()
        return table.get_group_data(columns=columns, grouping=grouping,
                                    values=values, ordering=ordering,
                                         where=where)
    def insert(self, data):
        table = self._get_table()
        table.insert(data)

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
