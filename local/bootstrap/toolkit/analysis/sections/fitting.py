#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import re
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg', warn=False)
import matplotlib.pyplot as plot
import numpy as np

from database import SqliteDB
from config import parse_columns
from sections.section import TabledSection
from types import StringType


class Fitting(TabledSection):
    """
    TODO
    """
    def build_function(self, return_value):
        func = None
        exec(self.body+'\n    return '+return_value)
        return func

    def fitting_function(self):
        return self.config.get('function')

    def fitting_parameters(self):
        return []

    def get_dbcolumns(self):
        grouping = self.config.get_columns('grouping', default=[])
        #labels = self.config.get_columns('labels', default=[])
        params = self.config.get_columns('params', default=[])
        params += parse_columns(' '.join(self.fitting_parameters()))
        return parse_columns('sample=INT') + grouping + params

    def __init__(self, name, config):
        super(Fitting, self).__init__(name, config)
        # TODO also group by boot id
        self.xdata = self.config.get_list('xdata')
        self.ydata = self.config.get_list('ydata')
        self.defines = self.config.get_list('defines', default=[])
        self.variable = self.config.get('variable', default=self.xdata[0])
        self.prefactor = self.config.get('prefactor', default='1')
        self.params = self.config.get_list('params', default=[])
        self.params += self.fitting_parameters()
        self.initial = self.config.get_list('initial', default=None)
        if self.initial is not None:
            self.initial = [float(x) for x in self.initial]
            while len(self.initial) < len(self.params):
                self.initial += [1]
        self.grouping = self.config.get_columns('grouping', default=[])
        self.labels = self.config.get_columns('labels', default=[])
        self.where = self.config.get('where', default=None)
        return_value = self.fitting_function()
        if self.prefactor!='1':
            return_value = '(%s)*(%s)' % (self.prefactor, return_value)

        self.body = 'def func(xdata, %s):' % ', '.join(self.params)
        for i in range(len(self.xdata)):
            self.body += '\n    %s = xdata[:, %s]' % (self.xdata[i], i)
        for define in self.defines:
            self.body += '\n    '+ define
        self.body += '\n    x_ = '+self.variable

        self.varfunc = self.build_function('x_')
        self.prefunc = self.build_function(self.prefactor)
        self.fitfunc = self.build_function(return_value)

    def estimate(self, params, columns, values):
        params = list(params[0])[2:]
        return self.fitfunc(values, *params)

    # TODO make sure this works by inheritance, not local overwrite
    def do_update(self, analysis, callers):
        return True

    def update(self, analysis):
        #if not (analysis.args.force or analysis.args.fitting):
        #    print(self.name,"NOT performed")
        #    return
        assert(len(self.source)==1)

        section = analysis.get_section(self.source[0])
        # TODO: add grouping by bootstrap id if the source is a bootstrap
        strgrouping = [(c if type(c) is StringType else c.name) for c in self.grouping]
        groups = section.get_groups(strgrouping)
        colors = ['b', 'r', '#0000cc', '#006666', '#ff6600', '#006600',
                  '#660066', '#aa2222', '#666666']
        for group in groups:
            groupcolnames = [(c if type(c) is StringType else c.name) for c in self.grouping]
            groupkv = [(k, str(v)) for k, v in zip(groupcolnames, group)]
            title = ', '.join([('%s=%s'%kv) for kv in groupkv])
            filename = '-'.join([''.join(kv) for kv in groupkv])
            labelstrings = [(c if type(c) is StringType else c.name) for c in self.labels]

            assert(len(self.ydata)==1)
            colnames = ['sample']+self.labels+self.xdata+self.ydata
            colnames = [(c if type(c) is StringType else c.name) for c in colnames]
            colnames = list(set(colnames))
            data = section.get_group_data(columns=colnames, grouping=self.grouping,
                values=group, ordering=self.labels+self.xdata, where=self.where)

            # perform the fitting for each sample
            fitsample = np.array([])
            count = 0
            for boot_id in range(0, 500):
                rows = range(boot_id, len(data), 500)
                labels = data[rows][labelstrings]
                xdata = np.array(data[rows][self.xdata].tolist())
                ydata = np.array(data[rows][self.ydata[0]].tolist())
                try:
                    popt, pcov = curve_fit(self.fitfunc, xdata, ydata,
                                           p0=self.initial, maxfev=10000)
                    fitsample = np.append(fitsample, popt)
                    # TODO sample should probably be done better
                    tablerow = [boot_id+1]+list(group)+list(popt)
                    self.insert(tablerow)
                    count += 1
                except Exception as e:
                    #for i in range(len(ydata)):
                    #    print ' '.join(["%f" % x for x in xdata[i]]), ydata[i]
                    raise e
            print(count,"/",500)

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

            plot.legend()
            plot.xlabel(self.xdata[0])
            plot.ylabel(self.ydata[0])
            ptitle = self.name.replace('_', ' ')+', '+title
            plot.title(ptitle)
            fname = self.name+'-'+filename+'.pdf'
            fname = re.sub(r'-+([\.-])',r'\1',fname)
            plot.savefig(fname)
            plot.close()

            # also render as gp
            gpfile = open(fname[:-3]+'gp','w')
            gpfile.write("#!/usr/bin/gnuplot\n\n")
            gpfile.write("set title \"%s\"\n" % ptitle)
            gpfile.write("set xlabel \"$ %s $\"\n" % self.xdata[0])
            gpfile.write("set ylabel \"$ %s $\"\n" % self.ydata[0])

            for i in range(len(self.params)):
                gpfile.write("%s=%lf\n" % (self.params[i], popt[i]))
                if not re.match(r'^p\d+$', self.params[i]):
                    gpfile.write("# %s = %lf +- %lf\n" % (self.params[i],
                                                          popt[i], popt_dev[i]))
            gpparams = ','.join(self.xdata)
            gpfile.write("pre(%s)=%s\n" % (gpparams, self.prefactor))
            gpfile.write("var(%s)=%s\n" % (gpparams, self.variable))
            for i in range(len(self.defines)):
                gpfile.write("# %s\n" % self.defines[i])
            gpfile.write("fit(x_)=%s\n" % self.fitting_function())
            gpfile.write("set key off\n\nplot \\\n")

            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                if len(labels)>0:
                    label = ' '.join([('%s=%s, '%(k, str(v))) for k, v in
                                      zip(labelstrings, labels[pos[i-1]])])
                    label = label.strip(", ")
                    gpfile.write("\t\"-\" u 1:2:3 t \"$ %s $\" w e ls %d" % (
                        label, i))
                else:
                    gpfile.write("\t\"-\" u 1:2:3 t \"\" w e ls %d" % (i))
                var = 'x'
                for p in self.xdata[1:]:
                    for j in range(len(labelstrings)):
                        if labelstrings[j]==p:
                            var+=","+str(labels[pos[i-1]][j])
                gpfile.write(", \\\n\tfit(var(%s))*pre(%s) t \"\" ls %d" %
                             (var, var, i))
                gpfile.write(", \\\n" if i<len(pos)-1 else "\n")

            gpdata = zip(list(x),list(y),list(yerr))
            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                for tpl in gpdata[rng]:
                    gpfile.write("\t%.7e %.7e %.7e\n" % tpl)
                gpfile.write("end\n")
            gpfile.close()

            # also plot the unrescaled data
            if re.match(r'^[A-Za-z0-9_]+$', self.variable) \
               and self.prefactor=='1':
                continue # nothing to be rescaled

            x = self.varfunc(xdata_mean, *popt)
            y = ydata_mean/self.prefunc(xdata_mean, *popt)
            yerr = ydata_std/self.prefunc(xdata_mean, *popt)
            z = self.fitfunc(xdata_mean, *popt)/self.prefunc(xdata_mean, *popt)

            for i in range(1, len(pos)):
                c = colors[i%len(colors)]
                rng = slice(pos[i-1], pos[i])
                label = None
                if len(labels)>0:
                    label = ' '.join([('%s=%s, '%(k, str(v))) for k, v in
                                      zip(labelstrings, labels[pos[i-1]])])
                plot.errorbar(x[rng], y[rng], yerr=yerr[rng], fmt='+', color=c)
                plot.plot(x[rng], z[rng], '-', color=c, label=label)

            plot.legend()
            plot.xlabel(self.variable)
            if self.prefactor != '1':
                plot.ylabel('(%s)/(%s)' % (self.ydata[0], self.prefactor))
            else:
                plot.ylabel(self.ydata[0])
            ptitle = self.name.replace('_', ' ')+' rescaled, '+title
            plot.title(ptitle)
            fname = self.name+'-'+filename+'-rescaled.pdf'
            fname = re.sub(r'-+([\.-])',r'\1',fname)
            plot.savefig(fname)
            plot.close()

            # also render as gp
            gpfile = open(fname[:-3]+'gp','w')
            gpfile.write("#!/usr/bin/gnuplot\n\n")
            gpfile.write("set title \"%s\"\n" % ptitle)
            gpfile.write("set xlabel \"$ %s $\"\n" % self.variable)
            if self.prefactor != '1':
                gpfile.write("set ylabel \"$ (%s)*(%s) $\"\n" % (self.prefactor, self.ydata[0]))
            else:
                gpfile.write("set ylabel \"$ %s $\"\n" % self.ydata[0])

            for i in range(len(self.params)):
                gpfile.write("%s=%lf\n" % (self.params[i], popt[i]))
                if not re.match(r'^p\d+$', self.params[i]):
                    gpfile.write("# %s = %lf +- %lf\n" % (self.params[i],
                                                          popt[i], popt_dev[i]))
            gpparams = ','.join(self.xdata)
            #gpfile.write("pre(%s)=%s\n" % (gpparams, self.prefactor))
            #gpfile.write("var(%s)=%s\n" % (gpparams, self.variable))
            for i in range(len(self.defines)):
                gpfile.write("# %s\n" % self.defines[i])
            gpfile.write("fit(x_)=%s\n" % self.fitting_function())

            gpfile.write("set key off\n\nplot \\\n")

            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                if len(labels)>0:
                    label = ' '.join([('%s=%s, '%(k, str(v))) for k, v in
                                      zip(labelstrings, labels[pos[i-1]])])
                    label = label.strip(", ")
                    gpfile.write("\t\"-\" u 1:2:3 t \"$ %s $\" w e ls %d" % (
                        label, i))
                else:
                    gpfile.write("\t\"-\" u 1:2:3 t \"\" w e ls %d" % (i))
                var = 'x'
                for p in self.xdata[1:]:
                    for j in range(len(labelstrings)):
                        if labelstrings[j]==p:
                            var+=","+str(labels[pos[i-1]][j])
                gpfile.write(", \\\n\tfit(x) t \"\" ls %d" % (i))
                gpfile.write(", \\\n" if i<len(pos)-1 else "\n")

            gpdata = zip(list(x),list(y),list(yerr))
            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                for tpl in gpdata[rng]:
                    gpfile.write("\t%.7e %.7e %.7e\n" % tpl)
                gpfile.write("end\n")
            gpfile.close()

class Polyfit(Fitting):
    def fitting_function(self):
        self.order = int(self.config.get('order', default=3))
        poly = '+'.join([('p%d*x_**%d'%(i, i)) for i in range(0, self.order+1)])
        poly = poly.replace('p0*x_**0', 'p0').replace('p1*x_**1', 'p1*x_')
        return poly
    def fitting_parameters(self):
        self.order = int(self.config.get('order'))
        return [('p%d'%i) for i in range(0, self.order+1)]

class Fsscale(Polyfit):
    pass

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
