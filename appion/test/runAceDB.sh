#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
runid=acedb
rm -frv ${runid}

reset
../bin/pyace.py \
  runid=${runid} dbimages=07mar09b,en edgethcarbon=0.8 edgethice=0.6 pfcarbon=0.9 pfice=0.3 \
  overlap=2 fieldsize=512 resamplefr=1 tempdir=/tmp/vossman medium=carbon cs=2.0 drange=0 \
  outdir=. display=1 stig=0 nocontinue reprocess=0.8 limit=10
