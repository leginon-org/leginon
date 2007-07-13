#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -fv `find . -name "*~"`
runid=doglocal
rm -frv ${runid}

reset
../bin/dogPicker.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  diam=140 lp=0 bin=8 overlapmult=2 maxpeaks=50 \
  runid=doglocal thresh=0.60 outdir=. background
