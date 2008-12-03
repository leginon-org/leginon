#!/bin/bash
 
./clean.sh
for i in `find . -type f | egrep -v "(\.svn|old|tilting|ctftest|data|travel)"`
do
	if [ -f /ami/sw/packages/pyappion/$i ]
	then
		echo $i > /dev/null
		#diff --brief /ami/sw/packages/pyappion/$i $i
	else
		echo MISSING $i
	fi
done

for i in `find /ami/sw/packages/pyappion -type f | egrep -v "(\.pyo|\.pyc|\.svn)"`
do
	j=`echo $i | sed 's/^\/ami\/sw\/packages\/pyappion/./'`
        if [ -f $j ]
        then
                #echo $i
                diff --brief $j $i
        else
                echo EXTRA $i
        fi
done

echo "rsync -rltouvPCn lib/ /ami/sw/packages/pyappion/lib/"
echo "rsync -rltouvPCn bin/ /ami/sw/packages/pyappion/bin/"
