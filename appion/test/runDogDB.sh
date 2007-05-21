#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
rm -frv dogdb

../bin/dogPicker.py \
  dbimages=07mar09b,en diam=225 bin=16 outdir=. runid=dogdb \
  numslices=2 sizerange=1
