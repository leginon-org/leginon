#!/bin/sh

templateCorrelator.py \
 --runname=tmplrun2 --rundir=/emg/data/appion/06jul12a/extract/tmplrun2 \
 --commit --preset=upload --projectid=1 --session=06jul12a --no-rejects \
 --no-wait --continue --peaktype=maximum --maxpeaks=150 --thresh=0.45 \
 --median=2 --lowpass=25 --highpass=500 --planereg --bin=4 --diam=240 \
 --pixlimit=6.0 --template-list=2,1 --range-list=0,180,10x0,52,10 \
 --expid=2 --jobtype=templatecorrelator --invert

makestack2.py \
 --single=start.hed --selectionid=1 --invert \
 --lp=3 --hp=2000 --pixlimit=6.0 --bin=2 \
 --normalize-method=edgenorm --boxsize=480 --forceInsert \
 --description="testing average stack" --runname=stack1 \
 --rundir=/emg/data/appion/06jul12a/stacks/stack1 --commit \
 --preset=upload --projectid=1 --session=06jul12a --no-rejects --no-wait \
 --continue --expid=2 --jobtype=makestack2

dogPicker.py \
  --runname=dogrun1 --rundir=/emg/data/appion/06jul12a/extract/dogrun1 \
  --kfactor=1.2 --commit --preset=upload --projectid=1 --session=06jul12a \
  --no-rejects --no-wait --continue --pdiam=150 --lpval=0 --hpval=0 \
  --medianval=2 --pixlimit=4 --binval=4 --planereg --invert --minthresh=0.5 \
  --maxthresh=1.5 --maxpeaks=1500 --peaktype=centerofmass --maxsize=1.0 \
  --overlapmult=1.5 --expid=2 --jobtype=dogpicker 

centerParticleStack.py \
 --stack-id=1 --description="test center run" \
 --rundir=/emg/data/appion/06jul12a/stacks/centered8 --runname=centered8 \
 --projectid=1 --expid=2 --jobtype=makestack --commit 

maxlikeAlignment.py \
 --description="long1" --stack=2 --lowpass=10 --highpass=1000 \
 --num-ref=3 --clip=96 --bin=2 --angle-interval=5 --max-iter=30 \
 --fast --fast-mode=wide --mirror --savemem --commit --converge=slow \
 --rundir=/emg/data/appion/06jul12a/align/maxlike1 --runname=maxlike1 \
 --projectid=1 --expid=2 --jobtype=partalign

uploadMaxlikeAlignment.py \
 --rundir=/emg/data/appion/06jul12a/align/maxlike1 \
 --commit --projectid=1 --runname=1 --expid=2 --jobtype=partalign 

relionMaxlikeAlignment.py --bin=2 --lowpass=10 --highpass=1000 --max-iter=30 --commit \
 --description='relion 2d' --angStep=5 --clip=96 --partDiam=190 \
 --runname=maxlike2 --rundir=/emg/data/appion/06jul12a/align/maxlike2 \
 --stack=2 --num-ref=3 --numpart=538 --nproc=1 \
 --projectid=1 --expid=2 --jobtype=partalign
