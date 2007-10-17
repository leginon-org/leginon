#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
runid=dogdb
rm -frv ${runid}

reset
../bin/dogPicker.py \
  dbimages=07mar09b,en diam=225 bin=8 \
  outdir=. runid=${runid} maxpeaks=50 \
  background limit=2 commit
  #numslices=2 sizerange=1
