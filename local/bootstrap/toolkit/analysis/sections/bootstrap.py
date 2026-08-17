#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

from database import SqliteDB
from sections.section import TabledSection
from evaluator import Evaluator
import numpy as np
from numpy import random as npr
from config import parse_columns

class Bootstrap(TabledSection):
    """
    Bootstrap section to resample grouped data from a
    previous database table.

    source:    table to read the data for resampling from
               (defaults to 'extract')

    grouping:  list of columns to use for grouping
               (defaults to empty list: no grouping)

    resample:  list of columns to use for resampling
               (defaults to all but the grouping columns)

    calculate: eval_list of new columns to calculate
               (defaults to empty list)

    samples:   number of resamplings to generate
               (defaults to 500)

    store:     list of columns to store in the resulting table
               (defaults to grouping and calculate items)
    """
    def __init__(self, name, config):
        super(Bootstrap, self).__init__(name, config)
        self.select_max = self.config.get_list('select_max', default=[])
        self.select_min = self.config.get_list('select_min', default=[])
        self.grouping = self.config.get_list('grouping', default=[])
        self.calculate = self.config.get_evals('calculate', default=[])
        self.resample = self.config.get_list('resample', default=[]) #TODO

    def get_dbcolumns(self):
        columns = super(Bootstrap, self).get_dbcolumns()
        return parse_columns('sample=INT')+columns

    def update(self, analysis):
        """
        Do extraction from dependent data sections

        Parse the settings file config.txt, read in all the data files
        described by data sections and extract the requested columns.
        """
        #print(self.do_update(analysis))
        if not (analysis.args.force or analysis.args.bootstrap):
            return
        assert(len(self.source)==1)
        #print(self.source)
        section = analysis.get_section(self.source[0])
        groups = section.get_groups(self.grouping)
        for group_values in groups:
            columns = self.resample+self.select_min+self.select_max
            data = section.get_group_data(columns=columns, grouping=self.grouping,
                                                values=group_values, ordering=self.grouping)
            for col in self.select_min:
                rows = np.where(min(data[col])==data[col])
                data = data[rows]
            for col in self.select_max:
                rows = np.where(max(data[col])==data[col])
                data = data[rows]

            # TODO make sure there is a reasonable number
            # of data values selected (i.e. more than 10?)
            # note this only works for int and float
            data = np.array(data.tolist())
            # TODO allow for user seed
            np.random.seed(seed=[42,len(data)])
            idx = np.random.randint(0, len(data), (500, len(data)))
            samples = np.average(data[idx], axis=1)
            entry_dict = dict(zip(self.grouping, group_values))
            sampleno = 0
            for sample in samples:
                sampleno += 1
                entry_dict.update(dict(zip(self.resample, sample)))
                for key, value in self.calculate:
                    entry_dict[key] = self.eval(value, entry_dict)
                entry_dict['sample'] = sampleno
                entry = [entry_dict[column.name] for column in self.store]
                self.insert(entry)
            #print(group_values)

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
