#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`

runid1=icetiltsdb
runid2=negtiltsdb
rm -frv ${runid1} ${runid2}

reset
../bin/tiltCorrelator.py \
  dbimages=07feb02b,en limit=10 \
  outdir=. diam=140 bin=4 \
  runid=${runid1} prtlrunId=90

clear
../bin/tiltCorrelator2.py \
  dbimages=07jan05b,en limit=10 \
  outdir=. diam=140 bin=4 \
  runid=${runid2} prtlrunId=53 

