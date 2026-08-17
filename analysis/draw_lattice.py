#!/usr/bin/env python3
"""Schematic of the (1+1)-D McCoy-Wu lattice with columnar disorder.

Draws the classical L x Ltau lattice onto which the random transverse-field
Ising chain maps: horizontal (spatial) bonds are random but identical down each
column (quenched, correlated in imaginary time), vertical (imaginary-time) bonds
are uniform.  Produces figures/mccoy_wu_lattice.png.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "mccoy_wu_lattice.png"
L, Lt = 7, 5
rng = np.random.default_rng(3)
col_strength = rng.uniform(0.3, 1.0, L)          # one random coupling per column

fig, ax = plt.subplots(figsize=(7.5, 4.6))

# vertical (imaginary-time) bonds: uniform
for i in range(L):
    for t in range(Lt - 1):
        ax.plot([i, i], [t, t + 1], color="#9aa5b1", lw=1.6, zorder=1)

# horizontal (spatial) bonds: random per column, identical for all tau
cmap = plt.get_cmap("plasma")
for i in range(L - 1):
    c = cmap(col_strength[i])
    lw = 1.0 + 3.5 * col_strength[i]
    for t in range(Lt):
        ax.plot([i, i + 1], [t, t], color=c, lw=lw, zorder=1)

# spins
for i in range(L):
    for t in range(Lt):
        ax.plot(i, t, "o", ms=11, color="#33415c", zorder=2)

ax.annotate("", xy=(-0.75, Lt - 1), xytext=(-0.75, 0),
            arrowprops=dict(arrowstyle="->", color="#33415c"))
ax.text(-1.15, (Lt - 1) / 2, r"imaginary time  $\tau\;(L_\tau)$", rotation=90,
        va="center", ha="center", fontsize=12)
ax.annotate("", xy=(L - 1, -0.75), xytext=(0, -0.75),
            arrowprops=dict(arrowstyle="->", color="#33415c"))
ax.text((L - 1) / 2, -1.15, r"space  $i\;(L)$", va="center", ha="center", fontsize=12)

ax.text(L - 1.0, Lt - 0.4,
        "horizontal bonds: random per column,\nidentical along $\\tau$ (quenched disorder)",
        fontsize=9, color="#7b2d8e", ha="right")
ax.text(L - 1.0, -0.15, "vertical bonds: uniform", fontsize=9, color="#5b6b7b", ha="right")

ax.set_aspect("equal")
ax.axis("off")
ax.set_xlim(-1.6, L - 0.2)
ax.set_ylim(-1.5, Lt - 0.2)
fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("wrote", OUT)
