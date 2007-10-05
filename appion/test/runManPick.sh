#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
runid=testmanpick1
rm -frv ${runid}

reset
../bin/manualpicker.py \
  dbimages=06nov29b,en diam=225 \
  outdir=. runid=${runid} \
  limit=3 shape=square shapesize=48 \
  nocontinue \
  median=2 lp=20 hp=400 bin=4 pixlimit=2.0 \
  pickrunid=21
