#!/bin/sh

rm -fv `find .. -name "*.py[oc]"`
runid=testmanpick1
rm -frv ${runid}

reset
../bin/manualpicker.py \
  dbimages=06nov29b,en diam=225 \
  outdir=. runid=${runid} \
  limit=10 shape=diamond shapesize=48 \
  norejects nocontinue \
  median=2 lp=20 hp=400 bin=4 \
  pickrunid=21
