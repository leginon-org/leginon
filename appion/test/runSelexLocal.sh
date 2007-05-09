#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -frv selexlocal


../particle_manager/selexon.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  range=0,180,235 templateIds=53 \
  diam=140 lp=0 bin=8 overlapmult=2 \
  maxpeaks=150 \
  runid=selexlocal4 outdir=. thresh=0.45 method=updated
