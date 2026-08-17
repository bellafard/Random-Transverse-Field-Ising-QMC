#!/usr/bin/env python3
"""Exact critical line of the McCoy-Wu / random transverse-field Ising chain.

The self-duality condition for the columnar-disordered (McCoy-Wu) Ising model
with couplings drawn from a rectangular distribution of mean J and width DeltaJ,

    2 J + < ln tanh(J') >  =  0 ,     J' ~ Uniform[J - DeltaJ/2, J + DeltaJ/2],

fixes the critical coupling J_c(DeltaJ).  In the clean limit DeltaJ -> 0 it
reduces to 2J + ln tanh(J) = 0, i.e. the exact 2D Ising point
J_c = (1/2) ln(1 + sqrt 2) = 0.440687.  This script solves the condition and
plots J_c vs DeltaJ, marking the clean point and the QMC estimate.

Usage:  python3 mccoy_wu_critical_line.py [out.png]
"""

import sys
import numpy as np
from scipy import integrate, optimize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else "mccoy_wu_critical_line.png"

def condition(J, dJ):
    # Couplings are restricted to positive values: clip the rectangular
    # distribution at 0 and renormalize over the surviving support.
    if dJ < 1e-9:
        avg_lntanh = np.log(np.tanh(J))
    else:
        lo, hi = max(1e-9, J - dJ / 2), J + dJ / 2
        val, _ = integrate.quad(lambda x: np.log(np.tanh(x)), lo, hi, limit=200)
        avg_lntanh = val / (hi - lo)
    return 2 * J + avg_lntanh

def Jc(dJ):
    return optimize.brentq(lambda J: condition(J, dJ), 0.05, 2.0)

# clean-limit check
Jc_clean_exact = 0.5 * np.log(1 + np.sqrt(2))
print("clean 2D Ising:  J_c (formula) = %.6f   (1/2)ln(1+sqrt2) = %.6f"
      % (Jc(0.0), Jc_clean_exact))
print("DeltaJ = 0.20 :  J_c = %.6f   (QMC estimate: 0.445 +/- 0.005)" % Jc(0.20))

dJs = np.linspace(0.0, 1.2, 60)
Jcs = np.array([Jc(d) for d in dJs])

fig, ax = plt.subplots(figsize=(7, 4.8))
ax.plot(dJs, Jcs, "-", lw=2, color="#2b6cb0", label=r"McCoy-Wu self-duality  $J_c(\Delta_J)$")
ax.plot(0.0, Jc_clean_exact, "s", ms=8, color="#c0392b",
        label=r"clean 2D Ising $J_c=\frac{1}{2}\ln(1+\sqrt{2})$")
ax.errorbar(0.20, 0.445, yerr=0.005, fmt="o", ms=7, color="#16a34a", capsize=3,
            label=r"Wolff QMC estimate ($\Delta_J=0.2$)")
ax.plot(0.20, Jc(0.20), "^", ms=8, color="#7b2d8e",
        label=r"self-duality $J_c(\Delta_J{=}0.2)=%.3f$" % Jc(0.20))
ax.set_xlabel(r"disorder width  $\Delta_J$")
ax.set_ylabel(r"critical coupling  $J_c$")
ax.set_title("Exact critical line of the McCoy-Wu random Ising model")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
