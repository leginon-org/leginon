#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -fv `find . -name "*~"`
runid="tmplcorrlocal2"
rm -frv ${runid}

reset
../bin/templateCorrelator.py \
  06nov29b_b_00031gr_00041sq_v01_00019hl_00002en.mrc \
  06nov29b_b_00031gr_00041sq_v01_00019hl_00003en.mrc \
  06nov29b_b_00031gr_00041sq_v01_00019hl_00004en.mrc \
  06nov29b_b_00031gr_00041sq_v01_00019hl_00005en.mrc \
  templateIds=26,27 range1=0,51,10 range2=0,180,10 \
  diam=160 lp=25 hp=400 median=2 bin=4 outdir=. maxpeaks=70 \
  runid=${runid} thresh=0.5 keepall background \
  overlapmult=1.5
