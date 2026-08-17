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

J = 445

for Lx in [32, 64, 128]:
	output_file = 'vmL' + str(Lx).zfill(2) + 'J' + str(J) + '.txt'
	f = open(output_file, 'w')
	
	for input_file in natural_sort(os.listdir(".")):
		if input_file.startswith('vmK00DK00DJ20L' + str(Lx).zfill(2)) and input_file.endswith(str(J)):
			input_data = np.genfromtxt(input_file, dtype=float, delimiter='\t')

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

			cumulant = 1 - np.mean( m4_avg ) / ( 3 * np.mean( m2_avg2 ) )

			Lt = re.search('x(.*)J', input_file).group(1)

			print >>f, Lt, "\t", cumulant

	f.close()

	X = np.loadtxt(output_file, dtype=float, delimiter='\t')[:,0]
	Y = np.loadtxt(output_file, dtype=float, delimiter='\t')[:,1]
	
	plt.plot(X, Y, marker = marker.next(), color = markercolor.next(), label=str(Lx), linestyle='--')

# # plt.title(fileName[-6:])
plt.xlabel(r'$L_\tau$', fontsize=20, color='black')
plt.ylabel(r'$V_m$', fontsize=20, color='black')
plt.xscale('log')
plt.legend(loc='best')
plt.savefig('plotJ' + str(J) + '.pdf')

