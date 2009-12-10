#!/usr/bin/env python

#python
import os
import sys
import glob
import time
import math
import numpy
import subprocess
#scipy
from pyami import quietscipy
from scipy import fftpack, ndimage
#leginon
from pyami import mrc, imagefun
#appion
import apDisplay
import apImage
import apFile
import apParam
import apImagicFile

####
# This is a low-level file with NO database connections
# Please keep it this way
####

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
def real_fft3d(volume, *args, **kwargs):
	padshape = numpy.asarray(volume.shape)*1
	padvolume = apImage.frame_constant(volume, padshape, volume.mean())
	fft = fftpack.fftn(padvolume, *args, **kwargs)
	return fft

#===========
def inverse_real_fft3d(volume, *args, **kwargs):
	return fftpack.ifftn(volume, *args, **kwargs).real

#===========
def normImage(image):
	return (image - image.mean())/image.std()

#===========
def fourierRingCorrelation(imgarray1, imgarray2, apix=1.0):
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
	length = int(max(fftshape)/2.0)
	linear = numpy.zeros((length), dtype=numpy.float32)
	linear[0] = 1.0

	### figure out which pixels go with which ring
	ringdict = getLinearIndices2d(fftshape)

	### for each ring calculate the FRC
	keys = ringdict.keys()
	keys.sort()
	lastfrc = 1.0
	K = float(2)
	for key in keys:
		sys.stderr.write(".")
		indexlist = ringdict[key]
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
		lastfrc = frc
	sys.stderr.write("\n")

	### output
	writeFrcPlot("frc.dat", linear, apix)
	res = getResolution(linear, apix, boxsize=linear.shape[0]*2)
	apDisplay.printMsg("Finished FRC of res %.3f Angstroms in %s"%(res, apDisplay.timeString(time.time()-t0)))
	return res

#===========
def spectralSNRStack(stackfile, apix=1.0, partlist=None, msg=False):
	### calculate the Fmean for each Fourier location
	fs = fourierSum(msg=msg)
	fs.start(stackfile, partlist)

	### calculate the denominator
	fsd = fourierSqDiff(msg=msg)
	fsd.fmean = fs.fsumimg / fs.numpart #need to set mean value
	fsd.start(stackfile, partlist)

	### calculate the SSNR
	denomring = fsd.denomring
	numerring = fs.fsumring
	ssnr = numerring / fsd.denomring - 1.0
	ssnr[0] = 1e10 #division by zero fix

	### calculate the FRC
	frcdata = ssnr / (ssnr + 1.0)

	### calculate the FRC 0.5 resolution	
	#res = getResolution(frc, apix=apix, boxsize=fs.boxsize)
	return frcdata

#===========
def spectralSNR(partarray, apix=1.0):
	"""
	Compute the Spectral Signal-to-Noise Ratio (SSNR) of a given series of images. 
	"""
	t0 = time.time()
	### initialization
	part0 = partarray[0]
	if isinstance(partarray, list):
		numimg = len(partarray)
	else:
		numimg = partarray.shape[0]
	if numimg < 2:
		apDisplay.printWarning("Cannot calculate the SSNR for less than 2 images")
		return 0.0
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
	ringdict = getLinearIndices2d(fftshape)

	### for each ring calculate the FRC
	keys = ringdict.keys()
	keys.sort()
	for key in keys:
		sys.stderr.write(".")
		indexlist = ringdict[key]
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
		K = len(indexlist)
		ssnr = numer / ( K/(K-1.0) * denom ) - 1.0
		frc = ssnr / (ssnr + 1)
		if key >= 3  and key <= 5:
			print "======================"
			print "numerring=", key, numer
			print "denomring=", key, denom
			print "ssnr=", key, ssnr
		#print "%02d %.3f %.3f (%.3f / %.3f)"%(key, ssnr, frc, numer/K, denom/K)
		#print key, frc
		linear[key] = frc
	sys.stderr.write("\n")

	### output
	writeFrcPlot("ssnr.dat", linear, apix)
	res = getResolution(linear, apix, boxsize=linear.shape[0]*2)
	apDisplay.printMsg("Finished SSNR of res %.3f Angstroms in %s"%(res, apDisplay.timeString(time.time()-t0)))
	return res

#===========
def mini_ssnr1fft(fftlist, indextuple):
	"""
	this function works and is fast, calculates spectral signal to noise ratio for each
	fourier pixel in the fftlist. index tuple refers to the dimensions of the image, e.g. (i, j) 
	for 2D, (i, j, k) for 3D
	"""
	fsum = 0.0
	K = float(len(fftlist))
	for fftim in fftlist:
		F = fftim[indextuple]
		fsum += F
	fmean = fsum/K
	#if i ==10 and j==10:
	#	print "Fmean10,10=", fmean
	#print "Fmean=", fmean
	numer = abs(fsum)**2
	denom = 0.0
	### this next part cannot be done as a running average
	### because F - fmean is a complex subtraction
	for fftim in fftlist:
		F = fftim[indextuple]
		denom += abs(F - fmean)**2
		#if i ==10 and j==10:
		#	print "denom10,10=", abs(F - fmean)**2
		#	print "denomSUM10,10=", denom
	return numer, denom

#===========
def writeFrcPlot(filename, frcdata, apix=1.0, boxsize=None, msg=False):
	if boxsize is None:
		boxsize = 2*frcdata.shape[0]
	f = open(filename, "w")
	f.write("#resolution\tfrc_value\n")
	for i in range(1, frcdata.shape[0]):
		res = boxsize*apix/float(i)
		value = frcdata[i]
		f.write("%.5f\t%.8f\n"%(res, value))
	f.close()
	if msg is True:
		apDisplay.printMsg("wrote data to: "+filename)

#===========
def getResolution(fscdata, apix=1.0, boxsize=None, filtradius=3):
	if boxsize is None:
		boxsize = fscdata.shape[0]*2
	lastx=0
	lasty=0
	if filtradius is not None and filtradius > 1:
		localfscdata = ndimage.gaussian_filter1d(fscdata, sigma=filtradius, mode='reflect')
	if localfscdata.min() > 0.5:
		apDisplay.printWarning("Resolution is at Nyquist")
		return apix*2.0
	for i in range(localfscdata.shape[0]):
		x = float(i)
		y = localfscdata[i]
		if x != 0.0 and x < 0.9:
			apDisplay.printWarning("FSC is wrong data format")
		if y > 0.5:
			#store values for later
			lastx = x
			lasty = y
		else:
			# get difference of fsc
			diffy = lasty-y
			# get distance from 0.5
			distfsc = (0.5-y) / diffy
			# get interpolated spatial freq
			intfsc = x - distfsc * (x-lastx)
			# convert to Angstroms
			res = boxsize * apix / intfsc
			return res
	end = localfscdata.shape[0]
	for value in localfscdata:
		sys.stderr.write("%.3f > "%(value))
	sys.stderr.write("\n")
	apDisplay.printWarning("Failed to determine resolution")
	return 0.0

#===========
def getLinearIndices2d(fftshape):
	"""
	for a given size categorize pixels into ring shells
	i.e. figure out which pixels go with which ring
	"""
	length = int(max(fftshape)/2.0)
	ringdict = {}
	for i in range(length):
		for j in range(length):
			k, m = wrap_coord((i,j), fftshape)
			r, a = cartToPolar(k, m)
			index = int(r*1.0)
			if index < 1 or index >= length:
				continue
			if not index in ringdict:
				ringdict[index] = []
			ringdict[index].append((i,j))
	#apDisplay.printMsg("Number of rings: "+str(len(ringdict)))
	return ringdict

#===========
def getLinearIndices3d(fftshape):
	"""
	for a given size categorize voxels into shells
	i.e. figure out which voxels go with which shell
	"""
	length = int(max(fftshape)/2.0)
	shelldict = {}
	for i in range(length):
		for j in range(length):
			for k in range(length):
				l, m = wrap_coord((i,j,k), fftshape)
				r, a = cartToPolar(l, m)
				index = int(r*1.0)
				if index < 1 or index >= length:
					continue
				if not index in shelldict:
					shelldict[index] = []
				shelldict[index].append((i,j,k))
	apDisplay.printMsg("Number of shells: "+str(len(shelldict)))
	return shelldict

#===========
def wrap_coord(coord, shape):
	if len(coord) == 2:
		wraplimit = (shape[0]/2, shape[1]/2)
	elif len(coord) == 3:
		wraplimit = (shape[0]/2, shape[1]/2, shape[2]/2)
		
	# if coord is past halfway, shift is negative, wrap
	if coord[0] < wraplimit[0]:
		wrapped0 = coord[0]
	else:
		wrapped0 = coord[0] - shape[0]
	if coord[1] < wraplimit[1]:
		wrapped1 = coord[1]
	else:
		wrapped1 = coord[1] - shape[1]
	if len(coord) == 3 and coord[2] < wraplimit[2]:
		wrapped2 = coord[2]
	else:
		wrapped2 = coord[2] - shape[2]

	return (wrapped0, wrapped1)

#===========
def cartToPolar(x, y):
	x1 = float(x)
	y1 = float(y)
	r = math.hypot(x1,y1)
	th = math.atan2(y1,x1)
	return r, th*180.0/math.pi



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

	### read image 2
	b = mrc.read("/ami/data00/appion/09mar04b/align/kerden11/09apr13q11.8.mrc")
	#b = mrc.read("/home/vossman/appion/lib/test02.mrc")
	#b = mrc.read("/home/vossman/leginon/holetemplate2.mrc")
	#b = mrc.read("/home/vossman/appion/lib/pickwei2.mrc")
	b = normImage(b)
	b = imagefun.bin2(b, bin)

	#spectralSNR([a, b])
	#fourierRingCorrelation(a, b)

	#sys.exit(1)

	files = glob.glob("/ami/data00/appion/09mar04b/align/kerden11/09apr13q11*.mrc")
	imlist = []
	for fname in files:
		c = mrc.read(fname)
		c = normImage(c)
		c = imagefun.bin2(c, bin)
		imlist.append(c)
	spectralSNR(imlist)

#=============================
##############################
#=============================
class fourierSum(apImagicFile.processStack):
	#===============
	def preLoop(self):
		shape = (self.boxsize, self.boxsize)
		self.ringdict = getLinearIndices2d(shape)
		self.numrings = len(self.ringdict.keys())+1
		self.fsumimg = numpy.zeros(shape, dtype=numpy.complex128)
		self.keys = self.ringdict.keys()
		self.keys.sort()
		return

	#===============
	def processParticle(self, partarray):
		fftim = real_fft2d(partarray)
		for key in self.keys:
			indexlist = self.ringdict[key]
			for indextuple in indexlist:
				i,j = indextuple
				F = fftim[i,j]
				self.fsumimg[i,j] += F
		return

	#===============
	def postLoop(self):
		self.fsumring = numpy.zeros((self.numrings), dtype=numpy.float64)
		for key in self.keys:
			indexlist = self.ringdict[key]
			numer = 0.0
			for indextuple in indexlist:
				i,j = indextuple
				numer += abs(self.fsumimg[i,j])**2
			self.fsumring[key] = numer
		return

#=============================
##############################
#=============================
class fourierSqDiff(apImagicFile.processStack):
	#===============
	def preLoop(self):
		shape = (self.boxsize, self.boxsize)
		self.ringdict = getLinearIndices(shape)
		self.numrings = len(self.ringdict.keys())+1
		self.denomimg = numpy.zeros(shape, dtype=numpy.float64)
		#self.denomring = numpy.zeros((self.numrings), dtype=numpy.float64)
		self.keys = self.ringdict.keys()
		self.keys.sort()
		return

	#===============
	def processParticle(self, partarray):
		fftim = real_fft2d(partarray)
		for key in self.keys:
			indexlist = self.ringdict[key]
			for indextuple in indexlist:
				i,j = indextuple
				fmean = self.fmean[i,j]
				F = fftim[i,j]
				self.denomimg[i,j] += abs(F - fmean)**2
		return

	#===============
	def postLoop(self):
		self.denomring = numpy.zeros((self.numrings), dtype=numpy.float64)
		for key in self.keys:
			indexlist = self.ringdict[key]
			K = float(len(indexlist))
			if K <= 1:
				self.denomring[key] = 1.0
				continue
			for indextuple in indexlist:
				i,j = indextuple
				self.denomring[key] += ( K/(K-1.0) * self.denomimg[i,j] )
		return

####
# This is a low-level file with NO database connections
# Please keep it this way
####



