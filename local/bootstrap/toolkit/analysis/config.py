#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to parse semi-generic text files
"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-09-23"
__status__ = "Development"

import re
from ConfigParser import ConfigParser
from database import parse_columns

class ParseError(Exception):
    """ Exception class to notify of parsing issues """
    pass

class Config(ConfigParser, object):
    """
    Extended ConfigParser Class

    Adds methods for parsing options to a list of strings or items.
    """
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.section = None
    def set_section(self, name):
        """ TODO """
        assert super(Config, self).has_section(name)
        self.section = name
    def has_option(self, option):
        return super(Config, self).has_option(self.section, option)
    def get(self, option, **kwargs):
        if 'default' in kwargs and not self.has_option(option):
            return kwargs['default']
        if 'default' in kwargs:
            del kwargs['default']
        value = super(Config, self).get(self.section, option, **kwargs)
        return re.sub(r'\s*\n\s*', ' ', str(value).strip())
    def get_list(self, option, **kwargs):
        """Returns section property as a list (split on whitepace)"""
        if 'default' in kwargs and not self.has_option(option):
            return kwargs['default']
        value = self.get(option, **kwargs)
        return str(value).split()
    def get_items(self, option, **kwargs):
        """Returns section property as a list of key=val tuples"""
        if 'default' in kwargs and not self.has_option(option):
            return kwargs['default']
        return parse_items(self.get(option, **kwargs))
    def get_columns(self, option, **kwargs):
        """Returns the column type definition for option"""
        if 'default' in kwargs and not self.has_option(option):
            return kwargs['default']
        return parse_columns(self.get(option, **kwargs))
    def get_evals(self, option, **kwargs):
        """Returns the list of eval items for option"""
        if 'default' in kwargs and not self.has_option(option):
            return kwargs['default']
        return compile_items(self.get_items(option, **kwargs))
    def sections(self, pattern=''):
        secs = super(Config, self).sections()
        return [sec for sec in secs if re.match(pattern, sec)]

def parse_items(string):
    """
    Parse a string into a list of items

    Arguments:
    string -- A string of key=value items (white space separated)

    The string is converted to a list using split and each item
    is parsed to a key=value pair by splitting at the first '='
    symbol. The left hand side must match [A-Za-z][A-Za-z0-9_]*.
    """
    items = [tuple(x.split('=', 1)) for x in string.split()]
    for item in items:
        if not re.match(r'[A-Za-z][A-Za-z0-9_]*$', item[0]):
            raise ParseError('Invalid variable name %s' % item[0])
    return items

def compile_items(items):
    """
    Compile a list of items for evaluation

    Given an item list of (key, value) tuples, this compiles the
    second part of each tuple to an expression for eval().
    """
    return [(x[0], compile(x[1], x[0], 'eval')) for x in items]


# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
