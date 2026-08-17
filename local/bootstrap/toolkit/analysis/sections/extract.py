#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

from sections.section import TabledSection
from sections.dataset import Dataset
from config import parse_columns

class Extract(TabledSection):
    """
    Configurable parser for plain text column data files

    This parser interprets a plain text file accoding to a set of patterns
    identifying each line as either a head, parameter, comment or data row.
    By adapting the patterns to identify and parse each type, a multitude of
    plain text file structures can be parsed.

    Limitations: Parsing is done line by line, if your file structure involves
    data spanning multiple lines, this parser is NOT for you. (Although you
    might be able to pre-digest the files to make them parseable).
    """
    def __init__(self, name, config):
        super(Extract, self).__init__(name, config)
        self.calculate = self.config.get_evals('calculate', default=[])

    def get_dbcolumns(self):
        columns = super(Extract, self).get_dbcolumns()
        return parse_columns('file=INT line=INT')+columns

    def update(self, analysis):
        """
        Do extraction from dependent data sections

        Parse the settings file meta.txt, read in all the data files
        described by data sections and extract the requested columns.
        """
        if not (analysis.args.force or analysis.args.extract):
            print(self.name,"not performed")
            return
        print(self.name)

        sections = dict([(sec.name,sec) for sec in analysis.sections])
        for section_name in self.source:
            assert(sections[section_name].__class__ is Dataset)
            sections[section_name].update(analysis)
            sections[section_name].extract(
                store = self.store,
                table = self._get_table(), # TODO fix this
                calculate = self.calculate,
            )


# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
