#!/bin/sh

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr dogdb

dogPicker.py dbimages=07mar09b,en diam=225 bin=16 outdir=. runid=dogdb \
	numslices=2 sizerange=1
