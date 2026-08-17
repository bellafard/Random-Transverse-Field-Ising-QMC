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

plt.figure(1)
plt.rc('text', usetex=True)

J = 445

for Lx in [16, 32, 64]:
	output_file = 'vmL' + str(Lx).zfill(2) + 'J' + str(J) + '.txt'
	f = open(output_file, 'w')
	
	for input_file in natural_sort(os.listdir(".")):
		if input_file.startswith('vmK00DK00DJ20L' + str(Lx).zfill(2)) and input_file.endswith(str(J)):
			input_data = np.loadtxt(input_file, dtype=float, delimiter='\t')[:-1]

			N = len(input_data)//2
			x4avg = input_data[::2]
			x2avg = input_data[1::2]

			cum = [ 1 - (x4avg[x]/(3*x2avg[x]*x2avg[x])) for x in range(N) ]

			sum2 = np.sum(x2avg)
			sum4 = np.sum(x4avg)
			x2avg_jk = [ (sum2 - x) / N for x in x2avg ]
			x4avg_jk = [ (sum4 - x) / N for x in x4avg ]
			cum_jk = [ 1 - x4avg_jk[x]/(3*x2avg_jk[x]*x2avg_jk[x]) for x in range(N) ]

			Lt = re.search('x(.*)J', input_file).group(1)
			Lt = np.log(int(Lt))/pow(Lx,0.37)

			print >>f, Lt, "\t", np.mean(cum_jk), "\t", np.mean(cum)

	f.close()

	X = np.loadtxt(output_file, dtype=float, delimiter='\t')[:,0]
	Y = np.loadtxt(output_file, dtype=float, delimiter='\t')[:,1]
	
	plt.plot(X, Y, marker = marker.next(), color = markercolor.next(), label=str(Lx), linestyle='--')

# # plt.title(fileName[-6:])
plt.xlabel(r'$L_\tau/L^\psi$', fontsize=20, color='black')
plt.ylabel(r'$V_m$', fontsize=20, color='black')
plt.xscale('log')
plt.legend(loc='best')
plt.savefig('plotActJ' + str(J) + '.pdf')

