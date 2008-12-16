#!/bin/bash

./clean.sh

echo "Trying to import all libraries"
echo "----------------"
rm -f importer.py
echo "#!/usr/bin/env python" > importer.py
echo "from pyami import quietscipy" >> importer.py
for i in lib/*.py;
do
   j=`basename $i | sed 's/\.py//'`
	#echo $j
   echo import $j >> importer.py
done
echo "import sys" >> importer.py
echo "sys.exit(1)" >> importer.py
chmod 775 importer.py
./importer.py
echo "----------------"
echo "SUCCESS"
echo ""
echo ""

sleep 1

echo "Trying to import all binaries"
echo "----------------"
cd bin
rm -f importer.py
echo "#!/usr/bin/env python" > importer.py
echo "from pyami import quietscipy" >> importer.py
for i in *.py;
do
   j=`basename $i | sed 's/\.py//'`
	#echo $j
   echo import $j >> importer.py
done
echo "import sys" >> importer.py
echo "sys.exit(1)" >> importer.py
chmod 775 importer.py
./importer.py
cd ..
echo "----------------"
echo "SUCCESS"
echo ""
echo ""

sleep 1
rm -fv bin/importer.py importer.py
exit;

echo "Trying to run all binaries"
echo "----------------"
rm -f runninglog.txt
for i in bin/*.py;
do
	j=`basename $i | sed 's/\.py//'`
	#echo $j
	#cmd=`echo import $j`
	python -d $i -h > runninglog.txt
	#python -d -tt $i -h > runninglog.txt
done
echo "----------------"
echo "SUCCESS"
echo ""
echo ""

sleep 1
rm -fv runninglog.txt *.log bin/importer.py importer.py
