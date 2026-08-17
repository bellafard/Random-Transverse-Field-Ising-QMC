#!/bin/bash

# @author = Ruben S. Andrist
# @email = andrist@gmail.com
# @date = 2014-08-09

# for i in 48 56 64 72 80 88 96 104 112 120 128; do
# minimum=$(wc -w vmG*L"$i"J* | awk 'BEGIN {min = 50000}{if ($1<min) {min=$1}} END {print min}')
# echo $minimum
# for j in vmG*L"$i"J*; do
# awk '{for (i = 1; i <= '$minimum'; i++) printf $i"\t"} END {printf "\n"}' $j >> vmL$i
# done
# done

folder=g10d20

rm -f analysis/*.db data/*.norm *.gp *.pdf *.txt

find $folder/raw -type f | while read file; do 
    ./raw2norm.py "$file" > "${file/$folder\/raw/data}.norm"
done

toolkit/analysis/analysis.py --extract --bootstrap --plot

# vim: set ff=unix ai tw=80 ts=4 sts=4 sw=4 et:

# toolkit/analysis/analysis.py --extract --bootstrap --plot
