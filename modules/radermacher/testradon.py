#!/usr/bin/python -O

import sys
import math
import numpy
import radermacher
from pyami import mem, imagefun
from scipy import ndimage
from appionlib.apImage import imagefile, imagenorm

def radonTransform(image, stepsize=2, maskrad=None):
	"""
	computes Radon transform of image
	"""
	radonlist = []
	if maskrad is None:
		maskrad = image.shape[0]/2	
	blackcircle = imagefun.filled_circle(image.shape, maskrad)
	mask = 1 - blackcircle
	maskline = mask.sum(axis=0) + 1

	nsteps = int(math.ceil(180/stepsize))
	for i in range(nsteps):
		rotated = ndimage.rotate(image, -i*stepsize, reshape=False, order=1)
		rotated = mask*rotated
		line = rotated.sum(axis=0)
		radonlist.append(line/maskline)
	radon = numpy.array(radonlist)
	#radonlr = numpy.fliplr(radon)
	#radon = numpy.vstack((radon, radonlr))
	return radon

def createDots(angle=0.0, noiselevel=3.0, shape=(128,128), shift=None):
	a = numpy.zeros(shape, dtype=numpy.float64)
	a30 = int(min(shape)*.30) #25%
	a40 = int(2*min(shape)/5.0) #40%
	a50 = int(min(shape)/2.0) #50%
	a60 = int(3*min(shape)/5.0) #60%
	a70 = int(min(shape)*.70) #75%
	a[a30:a40,a30:a40] = 1
	a[a50:a60,a30:a40] = 1
	a[a60:a70,a40:a50] = 1
	a[a40:a50,a50:a60] = 1
	a[a30:a40,a60:a70] = 1
	a[a60:a70,a60:a70] = 1
	b = a
	b = ndimage.rotate(b, angle, reshape=False, order=1)
	if shift is not None:
		b = ndimage.shift(b, shift=shift, mode='wrap', order=1)
	bnoise = b + noiselevel*numpy.random.random(shape)
	bnoise = ndimage.median_filter(bnoise, size=2)
	bnoise = imagenorm.normStdev(bnoise)

	return bnoise

if __name__ == "__main__":
	u = mem.used()
	stepsize = 1.0
	shape = (256,256)
	noiselevel = 2.0

	a = createDots(angle=0., noiselevel=noiselevel, shape=shape)
	b = createDots(angle=-30., noiselevel=noiselevel, shape=shape, shift=(3,4))
	imagefile.arrayToJpeg(a, "imagea.jpg")
	imagefile.arrayToJpeg(b, "imageb.jpg")

	ar = radonTransform(a, stepsize)
	br = radonTransform(b, stepsize)
	imagefile.arrayToJpeg(ar, "radona.jpg")
	imagefile.arrayToJpeg(br, "radonb.jpg")

	#print "%.3f"%(a[1,0])
	#print "%.3f"%(b[1,0])
	for radius in range(0,11,2):
		e = radermacher.radonshift(ar,br,radius)
		e = e / (ar.std()*br.std()) # result is not normalized properly
		val = e.argmax()
		y = val%e.shape[1]
		x = int(val/e.shape[1])
		anglelist = radermacher.getAngles(radius)
		shiftangle = anglelist[y]
		xshift = radius*math.sin(shiftangle)
		yshift = radius*math.cos(shiftangle)
		rotangle = stepsize*x
		print "Radius %02d, Max value %.16f at rot=%d, shift=%.1f,%.1f"%(radius, e.max(), rotangle, xshift, yshift)
		imagefile.arrayToJpeg(e, "radoncc%02d.jpg"%(radius), msg=False)
	print "mem used = %.1f MB"%((mem.used()-u)/1024.)
	print "done"
	#sys.exit(1)

