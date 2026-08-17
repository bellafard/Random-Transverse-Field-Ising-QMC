#!/usr/bin/env python3
"""Reduce raw magnetization time series to the Binder cumulant V_m(L, L_tau).

Production runs write, per disorder realization, one line holding the Monte
Carlo time series of |m| (the format emitted by the full research code).  For
each system size this script forms, with a jackknife over realizations, the
disorder-averaged Binder cumulant

    V_m = 1 - [<m^4>] / (3 [<m^2>]^2)

and writes a table  "L  L_tau  V_m"  (one row per L_tau).  Point DATA_DIR at the
directory of raw files and set the filename pattern.

(Python-3 port of the original vmlt_process.py.)
"""

import os
import glob
import numpy as np

DATA_DIR = os.environ.get("RTFIM_DATA", ".")
OUT_TMPL = "vmL{L}J442.txt"


def jackknife_mean(x):
    """Leave-one-out jackknife means of a 1D array."""
    n = len(x)
    total = x.sum()
    return (total - x) / (n - 1)


def binder(m2_series, m4_series):
    """V_m and its jackknife error from per-realization <m^2>, <m^4>."""
    j2 = jackknife_mean(m2_series)
    j4 = jackknife_mean(m4_series)
    vm_jk = 1.0 - j4 / (3.0 * j2 ** 2)
    vm = 1.0 - m4_series.mean() / (3.0 * m2_series.mean() ** 2)
    n = len(m2_series)
    err = np.sqrt((n - 1) * np.mean((vm_jk - vm_jk.mean()) ** 2))
    return vm, err


def reduce_size(L):
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "vm*L%02i*J442" % L))):
        # one row per realization; each row is a |m| time series
        series = np.genfromtxt(f)[:, :-1]      # drop trailing empty (tab) column
        m2 = (series ** 2).mean(axis=1)
        m4 = (series ** 4).mean(axis=1)
        Lt = int(f.split("x")[-1].split("J")[0])   # L_tau from the filename
        vm, err = binder(m2, m4)
        rows.append((L, Lt, vm, err))
    return sorted(rows, key=lambda r: r[1])


if __name__ == "__main__":
    for L in (8, 16, 32, 64, 128, 256):
        rows = reduce_size(L)
        if not rows:
            continue
        with open(OUT_TMPL.format(L=L), "w") as f:
            for L_, Lt, vm, err in rows:
                f.write("%d\t%d\t%.6f\t%.6f\n" % (L_, Lt, vm, err))
        print("wrote", OUT_TMPL.format(L=L), "(%d L_tau values)" % len(rows))
