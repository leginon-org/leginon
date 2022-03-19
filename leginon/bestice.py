#!/usr/bin/env python
import numpy
from pyami import arraystats

def getBestHoleMeanIntensity(imarray):
	imshape = imarray.shape
	if max(imshape) < 256:
		# handel dmsem fake 8x8
		return arraystats.mean(imarray)
	qshape = (imshape[0]//4, imshape[1]//4)
	qstarts = []
	start_fractions = (0.25, 0.375, 0.5)
	for x in start_fractions:
		for y in start_fractions:
			starty = int(imshape[0]*y)
			startx = int(imshape[1]*x)
			qstarts.append((starty, startx))
	means = []
	stds = []
	for s in qstarts:
		qarray = imarray[s[0]:s[0]+qshape[0],s[1]:s[1]+qshape[1]]
		means.append(arraystats.mean(qarray))		
		stds.append(arraystats.std(qarray))
	return max(means)	
