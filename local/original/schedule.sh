#!/bin/bash

counter=0

while [[ $counter -lt 100 ]]; do
	
	# active=$(echo $(bjobs | grep -w RUN | wc -l) + $(bjobs | grep -w PEND | wc -l) | bc)
	 active=$(echo $(myjob | grep -w r | wc -l) + $(myjob | grep -w qw | wc -l) | bc)

	if [[ $active -lt 400 ]]; then
		bash submit.sh
		let counter++
	else
		sleep 5m
	fi
done

echo $PWD > tmp
echo While loop is over. >> tmp
mailx -s "Job Submissions" arash@physics.ucla.edu < tmp
rm -f tmp
