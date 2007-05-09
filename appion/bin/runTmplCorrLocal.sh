#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -fv `find . -name "*~"`
rm -frv tmplcorrlocal


./templateCorrelator.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  range1=0,180,30 templateIds=53 \
  diam=140 lp=10 bin=4 overlapmult=2 maxpeaks=150 \
  runid=tmplcorrlocal thresh=0.45 method=updated outdir=.
