#!/bin/bash
# ---------------------------------------------------------------------------
# Binder-cumulant sweep for the (1+1)-D McCoy-Wu / RTFIM Ising model.
# Runs the Wolff QMC over a grid of system sizes L (with Ltau = L) and tuning
# couplings J, for a chosen disorder width DeltaJ.  Each (L) accumulates all J
# values into vm_L<L>_Lt<L>.dat (columns: J DeltaJ L Ltau <m2> <m4>).
# ---------------------------------------------------------------------------
set -e

BIN=../bin/rtfim_wolff_qmc
DELTAJ=${1:-0.0}          # 0.0 = pure Ising (validation); 0.2 = random (McCoy-Wu)
NREAL=${2:-40}            # disorder realizations / independent seeds
NEQ=300                   # Wolff equilibration steps
NMEAS=1500               # measurement steps

rm -f vm_L*.dat
for L in 8 16 24 32; do
    for J in 0.40 0.42 0.43 0.44 0.4407 0.45 0.46 0.47 0.49; do
        "$BIN" "$L" "$L" "$J" "$DELTAJ" "$NREAL" "$NEQ" "$NMEAS" $((RANDOM+1))
    done
    echo "L=$L done"
done
echo "sweep complete (DeltaJ=$DELTAJ)"
