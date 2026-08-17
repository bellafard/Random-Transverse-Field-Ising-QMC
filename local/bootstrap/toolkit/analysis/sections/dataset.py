#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import os, re
from sections.section import Section
from database import Column
from config import parse_columns

class Dataset(Section):

    def __init__(self, name, config):
        super(Dataset, self).__init__(name, config)
        self.filepattern = self.config.get('filename')
        self.files = []
        for root, dirs, files in os.walk('.'):
            files = [root+os.sep+filename for filename in files]
            self.files += [f for f in files if re.search(self.filepattern, f)]
        if len(self.files) == 0:
            raise Exception('No Files match section %s.' % self.name)
        self.time = max([os.path.getmtime(f) for f in self.files])
        self.calculate = self.config.get_evals('calculate', default=[])
        if self.config.has_option('columns'):
            self.columns = self.config.get_columns('columns')
            self.colnames = [x.name for x in self.columns]
        self.settings = dict(self.config.items(self.name))
        self.res = {
            'head': re.compile(self.settings['head']),
            'param': re.compile(self.settings['param']),
            'ignore': re.compile(self.settings['ignore']),
            'data': re.compile(self.settings['data']),
            'dbl': re.compile(self.settings['dbl']),
            'var': re.compile(self.settings['var']),
        }
        self.params = {} # todo

    def update(self, analysis):
        # nothing to do for updating
        pass

    def _match_head(self, line):
        """Match and interpret line as column header"""
        match = self.res['head'].search(line)
        if not match:
            return False
        self.columns = parse_columns(match.group('vars'))
        self.colnames = [column.name for column in self.columns]
        return True

    def _match_param(self, line, params):
        """Match and interpret line as parameter setter"""
        match = self.res['param'].search(line)
        if not match:
            return False
        groupdict = match.groupdict()
        try:
            float_val = float(groupdict['value'])
            params.update({groupdict['key']:float_val})
        except ValueError:
            params.update({groupdict['key']:groupdict['value']})
        return True

    def _match_data(self, line, store, params, calculate, table):
        """
        Match and interpret line as data row

        For each row, the columns are interpreted as variables according
        to the last header statement setting "colnames". Then, the following
        operations are performed (in order):

        1.) Current parameters are added as extra columns

        2.) The line is selected/ignored according to the truth
            value "select" evaluates to (default: True) (TODO)

        TODO: defaults are evaluated?

        3.) Statements in "calculate" are evaluated and added as
            additional columns for storage

        4.) Columns listed in the extract section are retained for storage

        Note: All parameters and variables (and already calculated values)
        are available for the evaluations in steps 2, 3 and 4.
        """
        match = self.res['data'].search(line)
        if not match:
            return False
        # TODO don't assume dbl
        data = [float(x) for x in self.res['dbl'].findall(match.group('dbls'))]
        if self.columns is None:
            raise Exception("columns not set in section %s" % self.name)
        if len(data)!=len(self.columns):
            raise Exception("Wrong number of columns in file %s on line %d")
        datadict = dict(params.items()+zip(self.colnames, data))
        for key, value in calculate:
            datadict[key] = self.eval(value, datadict)
        datadict.update({'file':self.fileno, 'line':self.lineno})
        entry = tuple([datadict[column.name] for column in store])
        table.insert(entry)
        return True

    def parse_file(self, filepath, store, table, params, calculate):
        """
        Read filepath and parse according to settings
        """
        print("parsing file",filepath)
        self.lineno = 0
        for line in open(filepath):
            self.lineno += 1
            line = re.sub(r"\s*\n$", '', line)
            if self._match_head(line):
                continue
            elif self._match_param(line, params):
                continue
            elif self.res['ignore'].search(line):
                continue
            elif self._match_data(line, store, params, calculate, table):
                continue
            raise Exception("Parse error on %s" % line)

    def do_update(self, analysis, callers=[]):
        return False

    def timestamp(self):
        mtime = 0
        for filepath in self.files:
            mtime = max(mtime, os.path.getmtime(filepath))
        return mtime if mtime != 0 else None

    def extract(self, store, table, calculate=[]):
        if table is None:
            print("None argument passed as table")
        self.fileno = 0
        for filepath in self.files:
            self.fileno += 1
            match = re.search(self.filepattern, filepath)
            file_params = match.groupdict()
            for key, value in file_params.items():
                try:
                    file_params[key] = float(value)
                except ValueError:
                    pass
            self.parse_file(
                filepath = filepath, store = store, table = table,
                params = dict(self.params.items() + file_params.items(),),
                calculate = self.calculate + calculate,
            )


# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
