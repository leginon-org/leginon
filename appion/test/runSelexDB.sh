#!/bin/sh

rm -f `find .. -name "*.py[oc]"`
rm -f `find .. -name "*~"`
rm -fr selexdb

selexon.py dbimages=07mar09b,en templateIds=102 range=0,180,90 runid=selexdb outdir=. \
 diam=225 lp=0 bin=8 thresh=0.40 maxpeaks=200 commit
