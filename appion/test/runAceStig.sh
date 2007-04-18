#!/bin/sh

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr acelocal

../ace/pyace.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  runid=acestig edgethcarbon=0.8 edgethice=0.6 pfcarbon=0.9 pfice=0.3 \
  overlap=2 fieldsize=512 resamplefr=1 tempdir=./tmp \
  medium=carbon cs=2.0 drange=0 \
  outdir=. display=1 stig=1 continue reprocess=1.1 commit
