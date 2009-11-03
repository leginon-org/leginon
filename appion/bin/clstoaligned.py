#!/usr/bin/env python
# this should be passed a list of cls files as arguments. It will take each raw
# particle, apply the predetermined 2D alignment to it and write it to a common
# output file using the Eulers take from the reference projection

from EMAN import *
from sys import argv
import os

if __name__ == "__main__":
	format = "spider"
	clean = None 
	if len(argv) > 2: 
		format = argv[2]
		clean = argv[3]

	if argv[1] == "-h":
		print "this should be passed a cls file. It will take each raw"
		print "particle, apply the predetermined 2D alignment to it and write it to a common"
		print "output file using the Eulers take from the reference projection\n\n"
	fsp=argv[1]

	# if only want particles that passed coran,
	# create new list file with only good particles
	if clean is not None:
		f=open(fsp,'r')
		lines=f.readlines()
		f.close()
		fsp=fsp.split('.')[0]+'.good.lst'
		f=open(fsp,'w')
		for l in lines:
			d=l.strip().split()
			if len(d) < 3:
				f.write(l)
				continue
			if d[3][-1]=='1':
				f.write(l)
		f.close()
	n=fileCount(fsp)[0]
	
	classnamepath = fsp.split('.')[0]+'.dir'
	b=EMData()
	b.readImage(fsp,0)
	e=b.getEuler()

	a=EMData()
	if format== "eman":
		outname="aligned.hed"
	else:
		outname="aligned.spi"
	for i in range(1,n):
		a.readImage(fsp,i)
		a.edgeNormalize()
		a.rotateAndTranslate()
		a.setRAlign(e)
		if a.isFlipped():
			a.hFlip()
		output = os.path.join(classnamepath,outname)
		a.writeImage(output,-1)


