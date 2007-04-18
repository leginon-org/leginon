#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
rm -frv selexdb

selexon.py dbimages=07mar09b,en templateIds=102 range=0,180,90 runid=selexdb outdir=. \
 diam=225 lp=0 bin=8 thresh=0.40 maxpeaks=200 commit
