#!/bin/sh

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr acelocal

./pyace.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  runid=acelocal edgethcarbon=0.8 edgethice=0.6 pfcarbon=0.9 pfice=0.3 \
  overlap=2 fieldsize=512 resamplefr=1 tempdir=/tmp/vossman \
  medium=carbon cs=2.0 drange=0 \
  outdir=acelocal display=1 stig=0 continue reprocess=0.8 commit
