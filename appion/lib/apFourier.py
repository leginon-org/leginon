#!/usr/bin/env python

import sys
import glob
import numpy
import time
import math
from pyami import quietscipy
from scipy import fftpack, ndimage
from pyami import mrc, imagefun, spider
import apDisplay
import apImage

#===========
def savePower(fft, fname="power.mrc"):
	image = abs(fft)
	half = numpy.asarray(image.shape)/2
	imagecent = ndimage.shift(image, half, mode='wrap', order=0)
	mrc.write(imagecent, fname)

#===========
def real_fft2d(image, *args, **kwargs):
	padshape = numpy.asarray(image.shape)*1
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
def fourierRingCorrelation(imgarray1, imgarray2):
	"""
	Formula taken from:
		http://www.imagescience.de/fsc/index.htm
	"""
	t0 = time.time()

	### get FFTs
	fftim1 = real_fft2d(imgarray1)
	fftim2 = real_fft2d(imgarray2)

	### initialization
	if fftim1.shape != fftim2.shape:
		apDisplay.printError("Cannot calculate the FRC for images of different sizes")
	if len(fftim1.shape) != 2 or len(fftim2.shape) != 2:
		apDisplay.printError("Cannot calculate the FRC non-2D images")
	fftshape = numpy.asarray(fftim1.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	#print fftshape, fftshape
	#print fftcenter, fftcenter
	length = int(max(fftshape)/2.0)
	#print "linear length", length
	linear = numpy.zeros((length), dtype=numpy.float32)
	linear[0] = 1.0

	### figure out which pixels go with which ring
	lineardict = getLinearIndices(fftshape)

	### for each ring calculate the FRC
	keys = lineardict.keys()
	keys.sort()
	lastfrc = 1.0
	K = float(2)
	for key in keys:
		indexlist = lineardict[key]
		numer = 0.0
		f1sum = 0.0
		f2sum = 0.0
		for indextuple in indexlist:
			i,j = indextuple
			F1 = fftim1[i,j]
			F2 = fftim2[i,j]
			#print (i,j), abs(F1), abs(F2), math.atan2(F1.imag, F1.real), math.atan2(F2.imag, F2.real)
			numer += F1*F2.conjugate()
			f1sum += abs(F1)**2
			f2sum += abs(F2)**2
		frc = numer / math.sqrt(f1sum*f2sum)
		#print "*** %02d %03d %.3f (%.4f / %.4f %.4f)"%(key, K, frc, numer/K, f1sum/K, f2sum/K)
		#print key, frc
		linear[key] = frc
		#if key > 2:
		#	sys.exit(1)
		if frc < 0 and lastfrc < 0:
			break
		lastfrc = frc

	### output
	writeFrcPlot("frc.dat", linear)
	apDisplay.printMsg("Finished FRC in "+apDisplay.timeString(time.time()-t0))
	return

#===========
def spectralSNRfft(fftimlist):
	"""
	Compute the Spectral Signal-to-Noise Ratio (SSNR) of a given series of transforms. 
	"""
	t0 = time.time()
	### initialization
	fftim1 = fftimlist[0]
	for fftim in fftimlist:
		if fftim1.shape != fftim.shape:
			apDisplay.printError("Cannot calculate the SSNR for images of different sizes")
		if len(fftim1.shape) != 2 or len(fftim.shape) != 2:
			apDisplay.printError("Cannot calculate the SSNR non-2D images")
	fftshape = numpy.asarray(fftim1.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	#print fftshape, fftshape
	#print fftcenter, fftcenter
	length = int(max(fftshape)/2.0)
	#print "linear length", length
	linear = numpy.zeros((length), dtype=numpy.float32)
	linear[0] = 1.0

	### figure out which pixels go with which ring
	lineardict = getLinearIndices(fftshape)

	### for each ring calculate the FRC
	keys = lineardict.keys()
	keys.sort()
	K = float(len(fftimlist))
	for key in keys:
		sys.stderr.write(".")
		indexlist = lineardict[key]
		numer = 0.0
		denom = 0.0
		for indextuple in indexlist:
			i,j = indextuple
			fsum = 0.0
			for fftim in fftimlist:
				F = fftim[i,j]
				fsum += F
			fmean = fsum/K
			n1 = abs(fsum)**2
			d1 = 0.0
			for fftim in fftimlist:
				F = fftim[i,j]
				d1 += abs(F - fmean)**2
			#if i == 5 and j == 5:
			#print ("%d,%d (%.3f / %.3f) %.3f"%(indextuple[0], indextuple[1], n1, d1, n1/d1))
			#return
			numer += n1
			denom += d1
		ssnr = numer / ( K/(K-1.0) * denom ) - 1.0
		frc = ssnr / (ssnr + 1)
		#print "%02d %.3f %.3f (%.3f / %.3f)"%(key, ssnr, frc, numer/K, denom/K)
		#print key, frc
		linear[key] = frc
	sys.stderr.write("\n")

	### output
	writeFrcPlot("ssnrfft.dat", linear)

	apDisplay.printMsg("Finished SSNR (fft) in "+apDisplay.timeString(time.time()-t0))

	return

#===========
def spectralSNR(partarray):
	"""
	Compute the Spectral Signal-to-Noise Ratio (SSNR) of a given series of images. 
	"""
	t0 = time.time()
	### initialization
	part0 = partarray[0]
	for partimg in partarray:
		if part0.shape != partimg.shape:
			apDisplay.printError("Cannot calculate the SSNR for images of different sizes")
		if len(partimg.shape) != 2:
			apDisplay.printError("Cannot calculate the SSNR non-2D images")

	### get fft
	fftlist = []
	for partimg in partarray:
		fftim = real_fft2d(partimg)
		fftlist.append(fftim)

	### dimension init
	fftim0 = real_fft2d(partarray[0])
	fftshape = numpy.asarray(fftim0.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	length = int(max(fftshape)/2.0)
	linear = numpy.zeros((length), dtype=numpy.float32)
	linear[0] = 1.0

	### figure out which pixels go with which ring
	lineardict = getLinearIndices(fftshape)

	### for each ring calculate the FRC
	keys = lineardict.keys()
	keys.sort()
	K = float(len(partarray))
	for key in keys:
		sys.stderr.write(".")
		indexlist = lineardict[key]
		numer = 0.0
		denom = 0.0
		for indextuple in indexlist:
			n1, d1 = mini_ssnr1fft(fftlist, indextuple)
			#n1, d1 = mini_ssnr1(partarray, indextuple)
			#n2, d2 = mini_ssnr2(partarray, indextuple)
			#if indextuple[0] == 5 and indextuple[1] == 5:
			#print "%d,%d (%.3f / %.3f) vs (%.3f / %.3f) %.3f"%(indextuple[0], indextuple[1], n1, d1, n2, d2, n1/d1)
			#return
			numer += n1
			denom += d1
		ssnr = numer / ( K/(K-1.0) * denom ) - 2.0
		frc = ssnr / (ssnr + 1)
		#print "%02d %.3f %.3f (%.3f / %.3f)"%(key, ssnr, frc, numer/K, denom/K)
		#print key, frc
		linear[key] = frc
	sys.stderr.write("\n")

	### output
	writeFrcPlot("ssnr.dat", linear)

	apDisplay.printMsg("Finished SSNR in "+apDisplay.timeString(time.time()-t0))


#===========
def writeFrcPlot(fname, linear, apix=1.0):
	length = linear.shape[0]
	f = open(fname, "w")
	#f.write("0\t1.0\n")
	for i in range(1, length):
		f.write("%.1f\t%.5f\n"%(length/float(i), linear[i]))
		if linear[i] < 0 and linear[i-1] < 0:
			break
	#f.write("%d\t0.0\n&\n"%(length+1))
	f.close()
	apDisplay.printMsg("wrote data to: "+fname)

#===========
def getLinearIndices(fftshape):
	### figure out which pixels go with which ring
	length = int(max(fftshape)/2.0)
	lineardict = {}
	for i in range(length):
		for j in range(length):
			k, m = wrap_coord((i,j), fftshape)
			r, a = cartToPolar(k, m)
			index = int(r*1.0)
			if index < 1 or index >= length:
				continue
			if not index in lineardict:
				lineardict[index] = []
			lineardict[index].append((i,j))
	apDisplay.printMsg("Number of rings: "+str(len(lineardict)))
	return lineardict

#===========
def wrap_coord(coord, shape):
	wraplimit = (shape[0]/2, shape[1]/2)
	# if coord is past halfway, shift is negative, wrap
	if coord[0] < wraplimit[0]:
		wrapped0 = coord[0]
	else:
		wrapped0 = coord[0] - shape[0]
	if coord[1] < wraplimit[1]:
		wrapped1 = coord[1]
	else:
		wrapped1 = coord[1] - shape[1]
	return (wrapped0, wrapped1)

#===========
def cartToPolar(x, y):
	x1 = float(x)
	y1 = float(y)
	r = math.hypot(x1,y1)
	th = math.atan2(y1,x1)
	return r, th*180.0/math.pi

#===========
def mini_ssnr1fft(fftlist, indextuple):
	"""
	this function works and is fast
	"""
	i,j = indextuple
	fsum = 0.0
	K = float(len(fftlist))
	for fftim in fftlist:
		F = fftim[i,j]
		fsum += F
	fmean = fsum/K
	numer = abs(fsum)**2
	denom = 0.0
	for fftim in fftlist:
		F = fftim[i,j]
		denom += abs(F - fmean)**2
	return numer, denom

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
	#a = mrc.read("/home/vossman/appion/lib/test01.mrc")
	#a = mrc.read("/home/vossman/appion/lib/waylon2.mrc")
	#a = mrc.read("/home/vossman/leginon/holetemplate.mrc")
	a = mrc.read("/ami/data00/appion/09mar04b/align/kerden11/09apr13q11.7.mrc")
	a = normImage(a)
	a = imagefun.bin2(a, bin)
	#printImageInfo(a)
	afft = real_fft2d(a)
	#printImageInfo(afft)

	### read image 2
	b = mrc.read("/ami/data00/appion/09mar04b/align/kerden11/09apr13q11.8.mrc")
	#b = mrc.read("/home/vossman/appion/lib/test02.mrc")
	#b = mrc.read("/home/vossman/leginon/holetemplate2.mrc")
	#b = mrc.read("/home/vossman/appion/lib/pickwei2.mrc")
	b = normImage(b)
	b = imagefun.bin2(b, bin)
	bfft = real_fft2d(b)
	#printImageInfo(bfft)

	#afft = afft/afft.std()
	#bfft = bfft/bfft.std()
	#savePower(afft, "power1.mrc")
	#savePower(bfft, "power2.mrc")
	spectralSNR([a, b])
	fourierRingCorrelation(a, b)
	spectralSNRfft([afft, bfft])

	sys.exit(1)

	files = glob.glob("/ami/data00/appion/09mar04b/align/kerden11/09apr13q11*.mrc")
	fftlist = []
	imlist = []
	t0 = time.time()
	for fname in files:
		c = mrc.read(fname)
		c = normImage(c)
		c = imagefun.bin2(c, bin)
		cfft = real_fft2d(c)
		imlist.append(c)
		fftlist.append(cfft)
	apDisplay.printMsg("Finished conversion in "+apDisplay.timeString(time.time()-t0))
	spectralSNR(imlist)
	spectralSNRfft(fftlist)




