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


class Plot(TabledSection):
    """
    TODO
    """
    def get_dbcolumns(self):
        grouping = self.config.get_columns('grouping', default=[])
        labels = self.config.get_columns('labels', default=[])
        #params = self.config.get_columns('params', default=[])
        #params += parse_columns(' '.join(self.fitting_parameters()))
        return grouping + labels

    def __init__(self, name, config):
        super(Plot, self).__init__(name, config)
        # TODO also group by boot id
        self.xdata = self.config.get_list('xdata')
        self.ydata = self.config.get_list('ydata')
        self.grouping = self.config.get_columns('grouping', default=[])
        self.labels = self.config.get_columns('labels', default=[])
        self.where = self.config.get('where', default=None)

    def update(self, analysis):
        if not (analysis.args.force or analysis.args.plot):
            return
        assert(len(self.source)==1)
        print(self.name)

        section = analysis.get_section(self.source[0])
        # TODO: add grouping by bootstrap id if the source is a bootstrap
        strgrouping = [(c if type(c) is StringType else c.name) for c in self.grouping]
        groups = section.get_groups(strgrouping)
        colors = ['b','r','#0000cc','#006666','#ff6600','#006600',
                  '#660066','#aa2222', '#666666']
        for group in groups:
            groupcolnames = [(c if type(c) is StringType else c.name) for c in self.grouping]
            groupkv = [(k,str(v)) for k,v in zip(groupcolnames, group)]
            title = ', '.join([('%s=%s'%kv) for kv in groupkv])
            filename = '-'.join([''.join(kv) for kv in groupkv])

            assert(len(self.ydata)==1)
            colnames = ['sample']+self.labels+self.xdata+self.ydata
            colnames = [(c if type(c) is StringType else c.name) for c in colnames]
            colnames = list(set(colnames))
            data = section.get_group_data(columns=colnames, grouping=self.grouping,
                values=group, ordering=self.labels+self.xdata, where=self.where)

            labelstrings = [(c if type(c) is StringType else c.name) for c in self.labels]

            rows = range(0, len(data), 500)
            labels = data[rows][labelstrings]
            xdata = np.array(data[self.xdata].tolist())
            ydata = np.array(data[self.ydata[0]].tolist())
            xdata = xdata.reshape((-1,500))
            ydata = ydata.reshape((-1,500))
            xdata_mean = np.mean(xdata, axis=1)
            xdata_std = np.std(xdata, axis=1)
            ydata_mean = np.mean(ydata, axis=1)
            ydata_std = np.std(ydata, axis=1)

            # calculate pos'
            if len(labels)>0:
                pos = np.where(labels[:-1]!=labels[1:])[0]+1
                pos = np.array([0]+list(pos)+[len(xdata_mean)])
            else:
                pos = np.array([0,len(xdata_mean)])

            fname = self.name+'-'+filename+'.txt'
            fname = re.sub(r'-+([\.-])',r'\1',fname)
            outfile = open(fname, 'w')
            #print(self.name+'-'+filename)
            for i in range(1,len(pos)):
                c = colors[i%len(colors)]
                rng = slice(pos[i-1],pos[i])
                label = None
                if len(labels)>0:
                    label = ' '.join([('%s=%s,'%(k,str(v))) for k,v in
                                      zip(labelstrings, labels[pos[i-1]])])
                plot.plot(xdata_mean[rng],ydata_mean[rng],'-',color=c,label=label)
                # TODO also plot x errors if necessary ...

                # TODO only do this for energy
                # show numbers on screen
                if label == "L=64,":
                    #outfile.write("# %s\n" % (label,))
                    outfile.write("T e e_err\n")
                    for i in range(pos[i-1],pos[i]):
                        outfile.write("%e %e %e\n" % (
                            xdata_mean[i], ydata_mean[i], ydata_std[i]))

                plot.errorbar(xdata_mean[rng], ydata_mean[rng],
                                   yerr=ydata_std[rng], color=c)
                plot.plot(xdata_mean[rng],ydata_mean[rng],'+',color=c)

            # TODO allow change of location
            plot.legend(loc='best')
            plot.xlabel(self.xdata[0])
            plot.ylabel(self.ydata[0])
            fname = self.name+'-'+filename+'.pdf'
            fname = re.sub(r'-+([\.-])',r'\1',fname)
            ptitle = self.name.replace('_',' ')+', '+title
            plot.title(ptitle)
            plot.savefig(fname)
            plot.close()

            # TODO also output as data file and as gnuplot
            gpfile = open(fname[:-3]+'gp','w')
            gpfile.write("#!/usr/bin/gnuplot\n\n")
            gpfile.write("set title \"%s\"\n" % ptitle)
            gpfile.write("set xlabel \"$ %s $\"\n" % self.xdata[0])
            gpfile.write("set ylabel \"$ %s $\"\n" % self.ydata[0])

            gpfile.write("set key off\n\nplot \\\n")

            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                if len(labels)>0:
                    label = ' '.join([('%s=%s, '%(k, str(v))) for k, v in
                                      zip(labelstrings, labels[pos[i-1]])])
                    gpfile.write("\t\"-\" u 1:2:3 t \"$ %s $\" w e ls %d" % (
                        label, i))
                else:
                    gpfile.write("\t\"-\" u 1:2:3 t \"\" w e ls %d" % (i))
                gpfile.write(", \\\n" if i<len(pos)-1 else "\n")

            gpdata = zip(list(xdata_mean),list(ydata_mean),list(ydata_std))
            for i in range(1, len(pos)):
                rng = slice(pos[i-1], pos[i])
                for tpl in gpdata[rng]:
                    gpfile.write("\t%.7e %.7e %.7e\n" % tpl)
                gpfile.write("end\n")
            gpfile.close()


# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
