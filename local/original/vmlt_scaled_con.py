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

J = 443
psi = 0.45

for Lx in [8, 16, 32, 64]:
	input_data = np.genfromtxt('vmL' + str(Lx).zfill(2) + 'J' + str(J) + '.txt', dtype=float, delimiter='\t')

	# Lx = input_data[0:0,0]
	Lt = input_data[:,1]
	Lt = [ np.log(int(t))/pow(Lx,psi) for t in Lt ]

	Vm = input_data[:,2]
	
	plt.plot(Lt, Vm, marker = marker.next(), color = markercolor.next(), label=str(Lx), linestyle='--')

# # plt.title(fileName[-6:])
plt.xlabel(r'$\ln(L_\tau)/L^\psi$', fontsize=20, color='black')
plt.ylabel(r'$V_m$', fontsize=20, color='black')
plt.xscale('log')
plt.legend(loc='best')
plt.savefig('plot_activated_J' + str(J) + '_Psi' + str(psi) + '.pdf')

