#!/usr/bin/python

from __future__ import division
import numpy as np
import os
import itertools
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re

marker = itertools.cycle(('s', 'o', '^', 'p', 'd', '*', 'h','+', 'x'))
markercolor = itertools.cycle(('black', 'red', 'blue', 'magenta', 'green', 'cyan'))

def natural_sort(l):
	convert = lambda text: int(text) if text.isdigit() else text.lower()
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
	return sorted(l, key = alphanum_key)

def jk(arr):
	summe = np.sum(arr)
	N = len(arr)
	arr_jk = [ (summe - x) / N for x in arr ]
	return arr_jk

plt.figure(1)
plt.rc('text', usetex=True)

J = 442

for Lx in [8, 16, 32, 64, 128, 256]:
	output_file = 'vmL' + str(Lx).zfill(2) + 'J' + str(J) + '.txt'
	f = open(output_file, 'w')
	
	for input_file in natural_sort(os.listdir(".")):
		if input_file.startswith('vmK00DK00DJ20L' + str(Lx).zfill(2)):
			input_data = np.genfromtxt(input_file, dtype=float, delimiter='\t')[:,:-1]

			print 'Handling ' + str(Lx) + 'x' + str(re.search('x(.*)J', input_file).group(1))

			m4_avg = []
			m2_avg = []

			for c in range(len(input_data)):
				m4 = [ x*x*x*x for x in input_data[c] ]
				m2 = [ x*x for x in input_data[c] ]

				m4_avg.append( np.mean( jk(m4) ) )
				m2_avg.append( np.mean( jk(m2) ) )

			del m4[:]
			del m2[:]

			m2_avg2 = [ x*x for x in m2_avg ]

			Vm = 1 - np.mean( jk(m4_avg) ) / ( 3 * np.mean( jk(m2_avg2) ) )

			Lt = re.search('x(.*)J', input_file).group(1)

			print >>f, Lx, "\t", int(Lt), "\t", Vm

	f.close()
