#!/bin/bash

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr icetiltsdb negtiltsdb


tiltCorrelator.py \
  dbimages=07feb02b,en \
  outdir=. diam=140 bin=4 \
  runid=icetiltsdb prtlrunid=96 commit

tiltCorrelator2.py \
  dbimages=07jan05b,en  \
  outdir=. diam=140 bin=4 \
  runid=negtiltsdb prtlrunId=59 commit

