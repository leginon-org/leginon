#!/bin/bash

rm -f `find .. -name "*.py[oc]"`
rm -fr icetiltslocal negtiltslocal

tiltCorrelator.py \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00004en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00005en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00006en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00007en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00008en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_00_00009en_00.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00004en_01.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00005en_01.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00006en_01.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00007en_01.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00008en_01.mrc \
  07feb02b_a_00006gr_00019sq_v01_00002sq_01_00009en_01.mrc \
  outdir=. diam=140 \
  runid=icetiltslocal prtlrunid=96 commit

tiltCorrelator2.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00007en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00008en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00009en_00.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00004en_01.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00005en_01.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00006en_01.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00007en_01.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00008en_01.mrc  \
  07jan05b_00012gr_00001sq_v01_00002sq_01_00009en_01.mrc  \
  outdir=. diam=140 \
  runid=negtiltslocal prtlrunId=59 commit
