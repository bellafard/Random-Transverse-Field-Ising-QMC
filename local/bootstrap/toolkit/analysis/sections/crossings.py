#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import re
from scipy.optimize import curve_fit, newton, bisect, brentq
import matplotlib
matplotlib.use('Agg', warn=False)
import matplotlib.pyplot as plot
import numpy as np

from database import SqliteDB
from config import parse_columns
from sections.section import TabledSection
from types import StringType


class Crossings(TabledSection):
    """
    TODO
    """
    def build_function(self, return_value):
        func = None
        exec(self.body+'\n    return '+return_value)
        return func

    def fitting_function(self):
        self.order = int(self.config.get('order', default=3))
        poly = '+'.join([('p%d*_x**%d'%(i, i)) for i in range(0, self.order+1)])
        poly = poly.replace('p0*_x**0', 'p0').replace('p1*_x**1', 'p1*_x')
        return poly

    def fitting_parameters(self):
        self.order = int(self.config.get('order'))
        return [('p%d'%i) for i in range(0, self.order+1)]

    def get_dbcolumns(self):
        grouping = self.config.get_columns('grouping', default=[])
        #labels = self.config.get_columns('labels', default=[])
        params = self.config.get_columns('params', default=[])
        params += parse_columns(' '.join(self.fitting_parameters()))
        return grouping + params

    def __init__(self, name, config):
        super(Crossings, self).__init__(name, config)
        # TODO also group by boot id
        self.xdata = self.config.get_list('xdata')
        self.ydata = self.config.get_list('ydata')
        self.defines = self.config.get_list('defines', default=[])
        self.params = self.config.get_list('params', default=[])
        self.params += self.fitting_parameters()
        self.grouping = self.config.get_columns('grouping', default=[])
        self.labels = self.config.get_columns('labels', default=[])
        self.where = self.config.get('where', default=None)

        return_value = self.fitting_function()
        self.body = 'def func(xdata, %s):' % ', '.join(self.params)
        for i in range(len(self.xdata)):
            self.body += '\n    %s = xdata[:, %s]' % (self.xdata[i], i)
        self.body += '\n    _x = '+self.xdata[0]
        print(self.body)
        self.fitfunc = self.build_function(return_value)

    def update(self, analysis):
        #if not (analysis.args.force or analysis.args.fitting):
        #    return
        assert(len(self.source)==1)
        assert(len(self.ydata)==1)
        section = analysis.get_section(self.source[0])

        strgrouping = [(c if type(c) is StringType else c.name) for c in self.grouping]
        groups = section.get_groups(strgrouping)
        colnames = ['sample']+self.labels+self.xdata+self.ydata
        colnames = [(c if type(c) is StringType else c.name) for c in colnames]
        colnames = list(set(colnames))

        for group1 in groups:
            data1 = section.get_group_data(
                columns=colnames, grouping=self.grouping, values=group1,
                ordering=self.labels+self.xdata, where=self.where)
            for group2 in groups:
                if group2<=group1: continue
                data2 = section.get_group_data(
                    columns=colnames, grouping=self.grouping, values=group2,
                    ordering=self.labels+self.xdata, where=self.where)

                fitsample = np.array([])
                failed = 0
                for boot_id in range(0, 500):
                    rows = range(boot_id, len(data1), 500)
                    xdata = np.array(data1[rows][self.xdata].tolist())
                    ydata = np.array(data1[rows][self.ydata[0]].tolist())
                    popt1, pcov1 = curve_fit(self.fitfunc, xdata, ydata)

                    rows = range(boot_id, len(data2), 500)
                    xdata = np.array(data2[rows][self.xdata].tolist())
                    ydata = np.array(data2[rows][self.ydata[0]].tolist())
                    popt2, pcov2 = curve_fit(self.fitfunc, xdata, ydata)

                    popt = tuple(popt1-popt2)
                    poly = lambda x: self.fitfunc(np.array([[x]]), *popt)[0]
                    #z = brentq(poly, 0.3, 1.0, maxiter=1000, full_output=True)
                    try:
                        z = newton(poly, 0.75, maxiter=1000)
                        fitsample = np.append(fitsample, z)
                    except:
                        failed += 1
                tablerow = group1 + group2
                tablerow += (np.mean(fitsample), np.std(fitsample), failed/500.)
                print(tablerow)
                #self.insert(tablerow)
                pass

        return

        # TODO: add grouping by bootstrap id if the source is a bootstrap
        colors = ['b', 'r', '#0000cc', '#006666', '#ff6600', '#006600',
                  '#660066', '#aa2222', '#666666']
        for group in groups:
            groupcolnames = [(c if type(c) is StringType else c.name) for c in self.grouping]
            groupkv = [(k, str(v)) for k, v in zip(groupcolnames, group)]
            title = ', '.join([('%s=%s'%kv) for kv in groupkv])
            filename = '-'.join([''.join(kv) for kv in groupkv])
            labelstrings = [(c if type(c) is StringType else c.name) for c in self.labels]

            data = section.get_group_data(columns=colnames, grouping=self.grouping,
                values=group, ordering=self.labels+self.xdata, where=self.where)

            # perform the fitting for each sample
            fitsample = np.array([])
            for boot_id in range(0, 500):
                rows = range(boot_id, len(data), 500)
                labels = data[rows][labelstrings]
                xdata = np.array(data[rows][self.xdata].tolist())
                ydata = np.array(data[rows][self.ydata[0]].tolist())
                popt, pcov = curve_fit(self.fitfunc, xdata, ydata)
                fitsample = np.append(fitsample, popt)

                tablerow = list(group)+list(popt)
                self.insert(tablerow)

            # compute popt mean
            popt_dev = np.std(fitsample.reshape(-1,len(popt)), axis=0)
            popt = np.mean(fitsample.reshape(-1,len(popt)), axis=0)
            text = ""
            for i in range(len(self.params)):
                if not re.match(r'^p\d+$', self.params[i]):
                    text += "%s = %lf +- %lf\n" % (self.params[i], popt[i], popt_dev[i])
            if text != "":
                ax = plot.axes()
                plot.text(0.5, 0.8, text, horizontalalignment='center',
                          verticalalignment='center', transform=ax.transAxes)

            # perfrom plotting
            assert(len(self.ydata)==1)
            rows = range(0, len(data), 500)
            labels = data[rows][labelstrings]
            xdata = np.array(data[self.xdata].tolist())
            ydata = np.array(data[self.ydata[0]].tolist())
            xdata = xdata.reshape((-1, 500, len(self.xdata)))
            ydata = ydata.reshape((-1, 500))
            xdata_mean = np.mean(xdata, axis=1)
            #xdata_std = np.std(xdata, axis=1)
            ydata_mean = np.mean(ydata, axis=1)
            ydata_std = np.std(ydata, axis=1)

            x = xdata_mean[:,0]
            y = ydata_mean
            yerr = ydata_std
            z = self.fitfunc(xdata_mean, *popt)

            # calculate pos'
            if len(labels)>0:
                pos = np.where(labels[:-1]!=labels[1:])[0]+1
                pos = np.array([0]+list(pos)+[len(xdata_mean)])
            else:
                pos = np.array([0, len(xdata_mean)])

            for i in range(1, len(pos)):
                c = colors[i%len(colors)]
                rng = slice(pos[i-1], pos[i])
                label = None
                if len(labels)>0:
                    label = ' '.join([('%s=%s, '%(k, str(v))) for k, v in
                                      zip(labelstrings, labels[pos[i-1]])])
                # TODO also plot x errors if necessary ...
                plot.errorbar(x[rng], y[rng], yerr=yerr[rng], fmt='+', color=c)
                plot.plot(x[rng], z[rng], '-', color=c, label=label)

            plot.legend(loc='best')
            plot.xlabel(self.xdata[0])
            plot.ylabel(self.ydata[0])
            plot.title(self.name.replace('_', ' ')+', '+title)
            plot.savefig(self.name+'-'+filename+'.pdf')
            plot.close()


# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
