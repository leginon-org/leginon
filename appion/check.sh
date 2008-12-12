#!/bin/sh

for i in bin/*.py;
do
	j=`basename $i | sed 's/\.py//'`
	echo $j
	#cmd=`echo import $j`
	python -d -tt $i -h > $j.out
done
