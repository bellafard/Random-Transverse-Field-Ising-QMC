#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

__author__ = "Ruben Andrist"
__email__ = "andrist@gmail.com"
__date__ = "2014-08-09"
__status__ = "Development"

import sys, re

def print_normalized(filename, J, J_step):
    obs = re.sub(r'.*/([^/]*)L\d+',r'\1',filename)
    print "# cols: run J", obs+'2', obs+'4'
    for line in open(filename).readlines():
        cols = line.split()
        for i in range(0,len(cols),2):
            print i/2, '%.4f' % J, ' '.join(cols[i:i+2])
        J += J_step

if __name__ == '__main__':
    for filename in sys.argv[1:]:	
        # print_normalized(filename, 0.3307, 0.0002) #g05d20 0.3307-0.3327
        # print_normalized(filename, 0.2425, 0.0002) #g10d10 0.2425-0.2445
        print_normalized(filename, 0.2317, 0.0002) #g10d20 0.2317-0.2341

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:
