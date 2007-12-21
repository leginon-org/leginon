#!/usr/bin/env python
# this should be passed a list of cls files as arguments. It will take each raw
# particle, apply the predetermined 2D alignment to it and write it to a common
# output file using the Eulers take from the reference projection

from EMAN import *
from sys import argv

for fsp in argv[1:]:
        n=fileCount(fsp)[0]

        b=EMData()
        b.readImage(fsp,0)
        e=b.getEuler()

        a=EMData()
        for i in range(1,n):
                a.readImage(fsp,i)
		a.edgeNormalize()
                a.rotateAndTranslate()
                a.setRAlign(e)
		if a.isFlipped():
			a.hFlip()
                a.writeImage("aligned.spi",-1)

