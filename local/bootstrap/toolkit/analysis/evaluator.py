#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2013-10-19"
__status__ = "Development"

import math

class Evaluator(object):
    """ Docstring """
    def __init__(self):
        safe_list = ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh',
                     'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp',
                     'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow',
                     'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']
        self.__mathdict = dict([(k, getattr(math, k, None)) for k in safe_list])
        self.__mathdict['abs'] = abs
        self.__mathdict['max'] = max
        self.__mathdict['min'] = min
        self.__mathdict['math'] = dict(self.__mathdict)
        self.__mathdict['__builtins__'] = None
    def __call__(self, expression, data):
        return self.eval(expression, data)
    def eval(self, expression, data):
        """
        Evaluates an expresssion with user data

        If the expression is entered in a config file, you should NOT type
        any spaces to allow for proper splitting of multiple expressions.

        These math functions are made available: abs, acos, asin, atan, atan2,
        ceil, cos, cosh, degrees, e, exp, fabs, floor, fmod, frexp, hypot,
        ldexp, log, log10, modf, pi, pow, radians, sin, sinh, sqrt, tan, tanh.
        """
        return eval(expression, self.__mathdict, data)



# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
