#!/bin/bash

./clean.sh
for i in `find . -type f | egrep -v "(CVS|old)"`
do
	if [ -f /ami/sw/packages/pyappion/$i ]
	then
		#echo $i
		diff --brief /ami/sw/packages/pyappion/$i $i
	else
		echo MISSING $i
	fi
done

for i in `find /ami/sw/packages/pyappion -type f | egrep -v "(CVS|old|\.pyc|\.pyo)"`
do
	j=`echo $i | sed 's/^\/ami\/sw\/packages\/pyappion/./'`
        if [ -f $j ]
        then
                #echo $i
                diff --brief $i $j
        else
                echo EXTRA $i
        fi
done

