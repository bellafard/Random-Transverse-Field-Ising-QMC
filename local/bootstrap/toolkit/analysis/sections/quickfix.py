#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg', warn=False)
import matplotlib.pyplot as plot
import numpy as np

from database import SqliteDB
from config import parse_columns
from sections.section import Section


def func(x, a, b, c):
    return a*x**2 + x*b + c

class Quickfix(Section):
    """
    TODO
    """
    def __init__(self, name, config):
        super(Quickfix, self).__init__(name, config)
        self.settings = dict(self.config.items(self.name))
        self.source = self.config.get_list('source', default='bootstrap')
        # TODO also group by boot id
        self.grouping = self.config.get_list('grouping', default=[])
        self.pairing = self.config.get_list('pairing')
        self.plot = self.config.get_list('plot')
        self.params = ['a','b','c']

        # initialize the database
        #database_name = name
        # self.config.get( 'database')
        #table_name = 'crossings'
        #self.config.get( self.name, 'table')
        #self.database = SqliteDB(database_name)
        #self.database.create_table(table_name, TODO)

    def update(self, analysis):
        print("Quickfix")
        #if not (analysis.args.force or analysis.args.crossings):
        #    return
        assert(len(self.source)==1)
        section = analysis.get_section(self.source[0])
        groups = section.get_groups(self.grouping)
        for group1 in groups:
            data1 = section.get_group_data(['T']+self.plot, self.grouping,
                                           group1, ordering=['T',self.plot[0]])
            data1 = np.array(data1.tolist())
            for group2 in groups:
                is_pair = True
                for rule in self.pairing:
                    parts = rule.split('==')
                    lhs = self.eval(parts[0], dict(zip(self.grouping, group2)))
                    rhs = self.eval(parts[1], dict(zip(self.grouping, group1)))
                    if not lhs==rhs:
                        is_pair = False
                        break
                if not is_pair:
                    continue
                print(group1, group2)
                data2 = section.get_group_data(['T']+self.plot, self.grouping,
                                               group2, ordering=['T',self.plot[0]])
                data2 = np.array(data2.tolist())
                for boot_id in range(0,1):
                    rows1 = range(boot_id, len(data1),500)
                    rows2 = range(boot_id, len(data2),500)
                    popt2, pcov2 = curve_fit(func, data2[rows2,1], data2[rows2,2])
                    Qx = data1[rows1,2]/func(data1[rows1,1],*popt2)
                    plot.plot(data1[rows1,1],Qx,'o')
        #plot.ylim([0,1])
        plot.savefig('quickfix-%s.pdf' % boot_id)
        plot.close()
        pass
# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
