#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
#rm -frv icetiltsdb negtiltsdb


tiltCorrelator.py \
  dbimages=07feb02b,en \
  outdir=. diam=140 bin=4 \
  runid=icetiltsdb prtlrunid=96 commit

tiltCorrelator2.py \
  dbimages=07jan05b,en  \
  outdir=. diam=140 bin=4 \
  runid=negtiltsdb prtlrunId=59 commit

