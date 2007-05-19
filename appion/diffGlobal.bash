#!/bin/bash

./clean.sh
for i in `find . -type f | egrep -v "(CVS|old)"`
do
	if [ -f /ami/sw/packages/pyappion/$i ]
	then
		#echo $i
		diff /ami/sw/packages/pyappion/$i $i
	else
		echo MISSING $i
	fi
done
