#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TODO
"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import argparse, os
from config import Config
import sections
#from sections import *

class Analysis(object):
    """ TODO """
    def __init__(self):
        """ TODO """
        self.args = self.parse_args()
        self.config = self._get_config()
        self.sections = self._get_sections()

    def parse_args(self):
        """ TODO """
        parser = argparse.ArgumentParser(
            description='Perform numerical Aanalysis.')
        parser.add_argument('--data', dest='data', default=os.getcwd(),
                            help='directory where the data resides')
        parser.add_argument('--analysis', dest='analysis',
                            default = os.sep.join((os.getcwd(),'analysis')),
                            help='where to store the analysis data')
        parser.add_argument('--bootstrap', dest='bootstrap', action='store_true',
                            help='whether to perform bootstrap')
        parser.add_argument('--crossings', dest='crossings', action='store_true',
                            help='whether to perform crossings')
        parser.add_argument('--fitting', dest='fitting', action='store_true',
                            help='whether to perform fitting')
        parser.add_argument('--plot', dest='plot', action='store_true',
                            help='whether to perform plot')
        parser.add_argument('--paired', dest='paired', action='store_true',
                            help='whether to perform pairing')
        parser.add_argument('--extract', dest='extract', action='store_true',
                            help='whether to perform extraction')
        parser.add_argument('--force', dest='force', action='store_true',
                            help="force recalculation")
        parser.add_argument('--clean', dest='clean', action='store_true',
                            help="perform cleaning")
        return parser.parse_args()

    def _get_sections(self):
        secs = self.config.sections()
        return [sections.Section(s, self.config) for s in secs]

    def _get_config(self):
        """ TODO """
        config = Config(defaults = {
            # usefull defaults:
            'sep' : r'(?:\s*, \s*|\s+)',
            'dbl' : r'(?:[-+]?(?:\d+\.?\d*|\d*\.?\d+)(?:[eE][-+]?\d+)?)',
            'dbls' : r'(?P<dbls>%(dbl)s(?:%(sep)s%(dbl)s)*)',
            'var' : r'(?:[A-Za-z][A-Za-z0-9_]*)',
            'vars' : r'(?P<vars>%(var)s(?:%(sep)s%(var)s)*)',
            # default actions
            'paramset' : r'(?P<key>%(var)s)\s*=\s*(?P<value>%(dbl)s)',
            # default tags
            'headtag' : r'#\s*(?:cols|columns|colnames)\s*:\s*',
            'paramtag' : r'#\s*',
            'comment' : r'\s*#\s*',
            'datatag' : r'\s*',
            # patterns for line recognition
            'head' : r'^%(headtag)s(?P<columns>%(vars)s)\s*$',
            'param' : r'^%(paramtag)s%(paramset)s\s*$',
            'ignore' : r'^(\s*|%(comment)s.*)$',
            'data' : r'^%(datatag)s%(dbls)s\s*$',
            # additional things to calculate
            'calculate': '',
        })
        config.read(os.sep.join((self.args.analysis,'config.txt')))
        return config

    def get_section(self, name):
        for section in self.sections:
            if section.name == name:
                return section
        raise Exception('cannot find section %s.' % name)

    def run(self):
        """ TODO """
        # TODO topological ordering of sections
        for section in self.sections:
            # TODO for some stupid reason need to specify callers here,
            # otherwise it does not take the default value WTF
            if section.do_update(analysis=self, callers=[]):
                print("updating %s" % section.name)
                section.update(analysis=self)

if __name__ == '__main__':
    Analysis().run()





# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
