#!/bin/bash

./clean.sh
for i in `find . -type f | grep -v CVS`
do
	if [ -f /ami/sw/packages/pyappion/$i ]
	then
		echo $i
		diff /ami/sw/packages/pyappion/$i $i
	fi
done
