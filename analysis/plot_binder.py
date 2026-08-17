#!/usr/bin/env python3
"""Disorder-averaged Binder cumulant vs coupling, with the finite-size crossing.

Reads the vm_L*.dat files (columns: J DeltaJ L Ltau <m2> <m4>) produced by the
Wolff QMC sweep, forms the magnetic Binder cumulant

    V_m = 1 - [<m^4>] / (3 [<m^2>]^2)     ([...] = disorder average),

with jackknife error bars, and plots V_m(J) for each L.  The size-independent
crossing point locates the critical coupling J_c.

Usage:  python3 plot_binder.py "vm_L*.dat" out.png [Jc_reference]
"""

import sys
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pattern = sys.argv[1] if len(sys.argv) > 1 else "vm_L*.dat"
OUT = sys.argv[2] if len(sys.argv) > 2 else "binder_crossing.png"
Jc_ref = float(sys.argv[3]) if len(sys.argv) > 3 else None

def binder_jackknife(m2, m4):
    """V_m = 1 - <m4>/(3 <m2>^2) with leave-one-out jackknife error."""
    n = len(m2)
    def vm(a2, a4):
        return 1.0 - a4.mean() / (3.0 * a2.mean() ** 2)
    full = vm(m2, m4)
    jk = np.array([vm(np.delete(m2, i), np.delete(m4, i)) for i in range(n)])
    err = np.sqrt((n - 1) * np.mean((jk - jk.mean()) ** 2)) if n > 1 else 0.0
    return full, err

files = sorted(glob.glob(pattern))
data = {}
for f in files:
    d = np.loadtxt(f).reshape(-1, 6)
    L = int(d[0, 2])
    for J in np.unique(d[:, 0]):
        sel = d[d[:, 0] == J]
        vm, err = binder_jackknife(sel[:, 4], sel[:, 5])
        data.setdefault(L, []).append((J, vm, err))

fig, ax = plt.subplots(figsize=(7, 4.8))
cmap = plt.get_cmap("viridis")
Ls = sorted(data)
for k, L in enumerate(Ls):
    arr = np.array(sorted(data[L]))
    ax.errorbar(arr[:, 0], arr[:, 1], yerr=arr[:, 2], marker="o", ms=4, lw=1.4,
                capsize=2, color=cmap(k / max(len(Ls) - 1, 1)), label=r"$L=%d$" % L)

if Jc_ref is not None:
    ax.axvline(Jc_ref, ls="--", color="#c0392b", lw=1.2)
    ax.text(Jc_ref, 0.05, r"  $J_c=%.4f$" % Jc_ref, color="#c0392b", fontsize=9,
            transform=ax.get_xaxis_transform())

ax.axhline(2.0 / 3.0, ls=":", color="gray", lw=1, alpha=0.7)
ax.text(ax.get_xlim()[0], 2/3, r" $2/3$ (ordered) ", va="bottom", fontsize=8, color="gray")
ax.set_xlabel(r"coupling  $J$")
ax.set_ylabel(r"Binder cumulant  $V_m = 1 - [\langle m^4\rangle]/(3[\langle m^2\rangle]^2)$")
ax.set_title("Finite-size Binder crossing locates the critical coupling")
ax.legend(title=r"$L_\tau = L$")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
