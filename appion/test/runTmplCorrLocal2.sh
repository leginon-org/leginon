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
  templateIds=26,27,28 range1=0,51,10 range2=0,180,10 range3=0,180,10 \
  diam=150 lp=15 bin=8 outdir=. maxpeaks=50 \
  runid=${runid} thresh=0.45 background \
  overlapmult=2 method=updated
