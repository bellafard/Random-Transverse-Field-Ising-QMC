#!/usr/bin/env python3
"""Activated (infinite-randomness) dynamical-scaling collapse of the Binder data.

At an infinite-randomness quantum critical point the imaginary-time and spatial
scales are related *activatedly*, ln L_tau ~ L^psi, rather than by a power law.
Plotting the Binder cumulant against the scaling variable

    x = ln(L_tau) / L^psi

collapses the curves for different L onto one another when psi is chosen
correctly (here psi ~ 0.45, the RTFIM tunneling exponent).  Reads the
vmL{L}J442.txt tables produced by binder_reduce.py.

(Python-3 port of the original vmlt_scaled_act.py.)

Usage:  python3 plot_activated_scaling.py [psi] [out.png]
"""

import sys
import glob
import itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PSI = float(sys.argv[1]) if len(sys.argv) > 1 else 0.45
OUT = sys.argv[2] if len(sys.argv) > 2 else "activated_scaling.png"

markers = itertools.cycle(("o", "s", "^", "v", "D", "p", "*"))
colors = itertools.cycle(plt.get_cmap("viridis")(np.linspace(0, 0.9, 7)))

fig, ax = plt.subplots(figsize=(7, 4.8))
for f in sorted(glob.glob("vmL*J442.txt")):
    d = np.loadtxt(f)
    if d.ndim == 1:
        d = d[None, :]
    L, Lt, vm = d[:, 0], d[:, 1], d[:, 2]
    err = d[:, 3] if d.shape[1] > 3 else None
    x = np.log(Lt) / (L ** PSI)
    ax.errorbar(x, vm, yerr=err, marker=next(markers), ms=5, lw=1.2, capsize=2,
                color=next(colors), label=r"$L=%d$" % int(L[0]))

ax.set_xlabel(r"$\ln(L_\tau)\,/\,L^{\psi}$   ($\psi=%.2f$)" % PSI)
ax.set_ylabel(r"Binder cumulant  $V_m$")
ax.set_title("Activated dynamical scaling collapse (infinite-randomness QCP)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
