#!/usr/bin/env python

import glob
import numpy
import math
from pyami import quietscipy
from scipy import fftpack
from pyami import mrc, imagefun
import apDisplay
import apImage

#===========
def real_fft2d(image, *args, **kwargs):
	padshape = numpy.asarray(image.shape)*4
	padimage = apImage.frame_constant(image, padshape, image.mean())
	fft = fftpack.fft2(padimage, *args, **kwargs)
	#normfft = (fft - fft.mean())/fft.std()
	return fft

#===========
def inverse_real_fft2d(image, *args, **kwargs):
	return fftpack.ifft2(image, *args, **kwargs).real

#===========
def normImage(image):
	return (image - image.mean())/image.std()

#===========
def polarToCart(rad, thrad):
	#thrad = thdeg*math.pi/180.0
	x = rad*math.cos(thrad)
	y = rad*math.sin(thrad)
	return x,y

#===========
def cartToPolar(x, y):
	r = math.hypot(x,y)
	if x > 0:
		if y < 0:
			th = math.atan2(y,x)
		else:
			th = math.atan2(y,x) + 2*math.pi
	elif x < 0:
		th = math.atan2(y,x) + math.pi
	else:
		#x = 0
		if y > 0:
			th = 3*math.pi/2.0
		elif y < 0:
			th = math.pi/2.0
		else:
			#x,y = 0
			th = 0
	return r, th*180.0/math.pi

#===========
def linearizeFourierShell(fftim):
	fftshape = numpy.asarray(fftim.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	print fftshape
	print fftcenter
	length = int(math.ceil(max(fftshape)/math.sqrt(2.0)/2.0))
	print length
	linear = numpy.zeros((length), dtype=numpy.uint8)

	for i in range(fftshape[0]):
		for j in range(fftshape[1]):
			x = float(i - fftcenter[0])
			y = float(j - fftcenter[1])
			r, a = cartToPolar(x, y)
			linear[int(r*0.5)] += 1
	print linear 

#===========
def fourierRingCorrelation(fftim1, fftim2):
	"""
	Formula taken from:
		http://www.imagescience.de/fsc/index.htm
	"""
	### initialization
	if fftim1.shape != fftim2.shape:
		apDisplay.printError("Cannot calculate the FRC for images of different sizes")
	if len(fftim1.shape) != 2 or len(fftim2.shape) != 2:
		apDisplay.printError("Cannot calculate the FRC non-2D images")
	fftshape = numpy.asarray(fftim1.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	print fftshape, fftshape
	print fftcenter, fftcenter
	length = int(max(fftshape)/2.0)
	print "linear length", length
	linear = numpy.zeros((length), dtype=numpy.float32)

	### figure out which pixels go with which ring
	lineardict = {}
	for i in range(fftshape[0]):
		for j in range(fftshape[1]):
			x = float(i - fftcenter[0])
			y = float(j - fftcenter[1])
			r, a = cartToPolar(x, y)
			index = int(r*1.0)
			if index == 0 or index >= length:
				continue
			if not index in lineardict:
				lineardict[index] = []
			lineardict[index].append((i,j))

	### for each ring calculate the FRC
	keys = lineardict.keys()
	keys.sort()
	for key in keys:
		indexlist = lineardict[key]
		numer = 0.0
		f1sum = 0.0
		f2sum = 0.0
		count = 0
		for indextuple in indexlist:
			i,j = indextuple
			F1 = fftim1[i,j]
			F2 = fftim2[i,j]
			numer += abs(F1*F2.conjugate())
			f1sum += abs(F1)**2
			f2sum += abs(F2)**2
			count += 1
		frc = numer / math.sqrt(f1sum*f2sum)
		print "%02d %03d %.3f (%.4f / %.4f %.4f)"%(key, count, frc, numer/count, f1sum/count, f2sum/count)
		#print key, frc
		linear[key] = frc

	### output
	f = open("frc.dat", "w")
	#f.write("0\t1.0\n")
	apix = 1.55
	for i in range(length):
		f.write("%d\t%.5f\n"%(i, linear[i]))
	#f.write("%d\t0.0\n&\n"%(length+1))
	f.close()
	print linear


#===========
def spectralSNR(fftimlist):
	"""
	Formula taken from:
		http://www.imagescience.de/fsc/index.htm
	"""
	### initialization
	fftim1 = fftimlist[0]
	for fftim in fftimlist:
		if fftim1.shape != fftim.shape:
			apDisplay.printError("Cannot calculate the FRC for images of different sizes")
		if len(fftim1.shape) != 2 or len(fftim.shape) != 2:
			apDisplay.printError("Cannot calculate the FRC non-2D images")
	fftshape = numpy.asarray(fftim1.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	print fftshape, fftshape
	print fftcenter, fftcenter
	length = int(max(fftshape)/2.0)
	print "linear length", length
	linear = numpy.zeros((length), dtype=numpy.float32)

	### figure out which pixels go with which ring
	lineardict = {}
	for i in range(fftshape[0]):
		for j in range(fftshape[1]):
			x = float(i - fftcenter[0])
			y = float(j - fftcenter[1])
			r, a = cartToPolar(x, y)
			index = int(r*1.0)
			if index >= length:
				continue
			if not index in lineardict:
				lineardict[index] = []
			lineardict[index].append((i,j))

	### for each ring calculate the FRC
	keys = lineardict.keys()
	keys.sort()
	for key in keys:
		indexlist = lineardict[key]
		count = 0
		numer = 0.0
		denom = 0.0
		for indextuple in indexlist:
			count += 1
			i,j = indextuple
			fsum = 0.0
			K = float(len(fftimlist))
			for fftim in fftimlist:
				F = fftim[i,j]
				fsum += F
			fmean = fsum/K
			numer += abs(fsum)**2
			for fftim in fftimlist:
				F = fftim[i,j]
				denom += abs(F - fmean)**2
		ssnr = numer / ( K/(K-1.0) * denom ) - 1.0
		frc = ssnr / (ssnr + 1)
		print "%02d %03d %.3f %.3f (%.3f / %.3f)"%(key, count, ssnr, frc, numer/count, denom/count)
		#print key, frc
		linear[key] = frc

	### output
	f = open("ssnr.dat", "w")
	#f.write("0\t1.0\n")
	apix = 1.55
	for i in range(length):
		f.write("%d\t%.5f\n"%(i, linear[i]))
	#f.write("%d\t0.0\n&\n"%(length+1))
	f.close()
	print linear

#===========
def printImageInfo(image):
	print "+++++++++++++"
	print image.shape
	print image.dtype
	print abs(image.mean()), image.std()
	print image.min(), image.max()
	print "============="

#===========
if __name__ == "__main__":
	bin = 1
	### read image 1
	a = mrc.read("/home/vossman/appion/lib/test01.mrc")
	#a = mrc.read("/home/vossman/leginon/holetemplate.mrc")
	a = normImage(a)
	a = imagefun.bin2(a, bin)
	printImageInfo(a)
	afft = real_fft2d(a)
	printImageInfo(afft)

	### read image 2
	b = mrc.read("/home/vossman/appion/lib/test02.mrc")
	#b = mrc.read("/home/vossman/leginon/holetemplate2.mrc")
	b = normImage(b)
	b = imagefun.bin2(b, bin)
	bfft = real_fft2d(b)
	printImageInfo(bfft)
	#fourierRingCorrelation(afft, bfft)

	files = glob.glob("/home/vossman/appion/lib/test*.mrc")
	fftlist = []
	for fname in files:
		c = mrc.read(fname)
		c = normImage(c)
		c = imagefun.bin2(c, bin)
		cfft = real_fft2d(c)
		fftlist.append(cfft)
	spectralSNR(fftlist)

