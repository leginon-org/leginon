#!/bin/sh

uploadAppionParticles.py --filename=/emg/sw/particledata.dat --session=06jul12a --diam=180 \
  --commit --rundir=/emg/data/appion/06jul12a/extract/manual1 --runname=manual1 \
  --projectid=1 --expid=2 --jobtype=uploadparticles 


makestack2.py --single=start.hed --selectionid=1 --pixlimit=4 --invert \
  --normalize-method=edgenorm --boxsize=320 --bin=2 --forceInsert \
  --description="testing average stack" --runname=stack1 \
  --rundir=/emg/data/appion/06jul12a/stacks/stack1 --commit \
  --preset=upload --projectid=1 --session=06jul12a --no-rejects --no-wait \
  --continue --expid=2 --jobtype=makestack2 


maxlikeAlignment.py --description="long1" --stack=1 --lowpass=20 --highpass=2000 \
  --num-part=595 --num-ref=3 --bin=2 --angle-interval=5 --max-iter=30 \
  --fast --fast-mode=wide --mirror --savemem --commit --converge=slow \
  --rundir=/emg/data/appion/06jul12a/align/maxlike1 --runname=maxlike1 --projectid=1 \
  --expid=2 --jobtype=partalign
