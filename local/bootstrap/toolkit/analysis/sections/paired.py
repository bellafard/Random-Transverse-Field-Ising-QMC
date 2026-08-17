#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import numpy as np
import sys
from numpy import random as npr

from database import SqliteDB
from sections.section import Section
from sections.section import TabledSection
from config import parse_columns
from types import StringType

class Paired(TabledSection):
    """
    TODO
    """
    def __init__(self, name, config):
        super(Paired, self).__init__(name, config)
        self.source = self.config.get_list('source')
        self.calculate = self.config.get_evals('calculate')
        self.columns = self.config.get_columns('store')
        self.grouping = self.config.get_columns('grouping')
        self.where = self.config.get('where', default=None)

    def update(self, analysis):
        #if not (analysis.args.force or analysis.args.paired):
        #    return
        assert(len(self.source)==2)
        print "PAIRED"

        section1 = analysis.get_section(self.source[0])
        section2 = analysis.get_section(self.source[1])

        groups1 = section1.get_groups(self.grouping)
        groups2 = section2.get_groups(self.grouping)

        for group1 in groups1:
            # TODO just load all data here
            data1 = section1.get_group_data(grouping=self.grouping,
                                            values=group1, where=self.where,
                                            ordering=["sample"])
            for group2 in groups2:
                # TODO make this generic
                if group2 != (8,): continue
                print
                # TODO just load all data here
                data2 = section2.get_group_data(grouping=self.grouping,
                                                values=group2, where=self.where,
                                               ordering=["sample"])

                for sample in range(1):
                    rows1 = range(sample*500,sample*500+len(data1)/500)
                    rows2 = range(sample*500,sample*500+len(data2)/500)

                    values = data1[rows1]
                    values = np.array([[line[2]] for line in values])

                    chi12 = section2.estimate(data2[rows2], ["T"], values)
                    values = [data1[rows1[i]][5]/chi12[i] for i in range(len(chi12))]

                    for i in range(len(chi12)):
                        print ("%d %d %.4lf"+(" %.7lf"*4)) % tuple(list(data1[rows1[i]])+[values[i]])

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
