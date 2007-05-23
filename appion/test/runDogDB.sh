#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
runid=dogdb
rm -frv ${runid}

reset
../bin/dogPicker.py \
  dbimages=07mar09b,en diam=225 bin=8 \
  outdir=. runid=${runid} limit=5 \
  background
  #numslices=2 sizerange=1
