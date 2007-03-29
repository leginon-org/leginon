#!/bin/bash

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr tiltdb1 tiltdb2


./tiltCorrelator.py \
  dbimages=07feb02b,en \
  outdir=tiltdb1 diam=140 \
  runid=icetilts prtlrunid=96 commit

./tiltCorrelator2.py \
  dbimages=07jan05b,en  \
  outdir=tiltdb2 diam=140 \
  runid=negtilts prtlrunId=59 commit

