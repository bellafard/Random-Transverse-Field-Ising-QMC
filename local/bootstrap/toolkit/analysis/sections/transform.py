#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-18"
__status__ = "Development"

import numpy as np
from numpy import random as npr

from database import SqliteDB
from sections.section import Section

class Transform(Section):
    """
    TODO
    """
    def __init__(self, name, config):
        super(Transform, self).__init__(name, config)
        self.source = self.config.get_list('source')
        self.calculate = self.config.get_evals('calculate')
        self.columns = self.config.get_columns('store')
        self.grouping = self.config.get_list('grouping')

    def update(self, analysis):
        """
        TODO
        """

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
