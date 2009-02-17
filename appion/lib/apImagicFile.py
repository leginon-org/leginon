#########################################################
# Imagic I/O
#########################################################

import os
import sys 
import re
import time
import math
import shutil
import apDisplay
import apFile
import numpy
from pyami import mrc
import pyami.quietscipy
from scipy import ndimage

#===============
def compareHeader(hfile1, hfile2, numround=1):
	"""
	useful in debugging
	"""
	f1 = open(hfile1, 'rb')
	f2 = open(hfile2, 'rb')
	for n in range(numround):
		print ""
		print "round", n+1
		data1 = f1.read(1024)
		data2 = f2.read(1024)
		ints1 = numpy.fromstring(data1, dtype=numpy.int32)
		ints2 = numpy.fromstring(data2, dtype=numpy.int32)
		for i in range(ints1.shape[0]):
			int1 = ints1[i]
			int2 = ints2[i]
			if int1 != int2:
				if -10 < int1 < 100 and -10 < int2 < 100:
					print "%02d\t%04d ==> %04d" % (i, int1, int2)
				else:
					float1 = fourByteToFloat(intToFourByte(int1))
					float2 = fourByteToFloat(intToFourByte(int2))
					print "%02d\t%03.3e ==> %03.3e" % (i, float1, float2)

#===============
def numberStackFile(oldheadfile, startnum=0):
	"""
	Takes an Imagic Stack header file and numbers the particles

	based on 
		http://www.imagescience.de/formats/formats.htm
	"""
	apDisplay.printMsg("saving particle numbers to stack header")
	t0 = time.time()
	newheadfile = (os.path.splitext(oldheadfile)[0]+"-temp.hed")

	numimg = apFile.numImagesInStack(oldheadfile)
	#print numimg
	numimg_fbyte = intToFourByte(numimg-1)

	of = open(oldheadfile, 'rb')
	nf = open(newheadfile, 'wb')
	i = startnum
	while i < numimg:
		imgnum_fbyte = intToFourByte(i)
		data = of.read(1024)
		### start new string
		headerstr = ""
		### first image number
		headerstr += intToFourByte(i)
		### number of images, less one
		headerstr += numimg_fbyte
		### always 0,1 ???
		headerstr += intToFourByte(0)
		headerstr += intToFourByte(1)
		### creation date: day, month, year, hour, min, sec
		headerstr += intToFourByte(time.localtime()[2])
		headerstr += intToFourByte(time.localtime()[1]) #eman always uses month-1?
		headerstr += intToFourByte(time.localtime()[0])
		headerstr += intToFourByte(time.localtime()[3])
		headerstr += intToFourByte(time.localtime()[4])
		headerstr += intToFourByte(time.localtime()[5])
		### append other header info, 4 character per item
		headerstr += data[10*4:61*4]
		### first image number, EMAN does this
		headerstr += intToFourByte(i)
		### append other header info, 4 character per item
		headerstr += data[62*4:]
		#print ""
		#print "old=", fourByteToInt(data[0:4]), fourByteToInt(data[4:8]), fourByteToInt(data[8:12])
		#print "new=", fourByteToInt(headerstr[0:4]), fourByteToInt(headerstr[4:8]), fourByteToInt(headerstr[8:12])
		nf.write(headerstr)
		i += 1
	if not os.path.isfile(newheadfile):
		apDisplay.printError("failed to number particles in stack file")
	apFile.removeFile(oldheadfile)
	shutil.move(newheadfile, oldheadfile)
	apDisplay.printMsg("completed %d particles in %s"%(numimg, apDisplay.timeString(time.time()-t0)))
	return True

#===============
def readImagic(filename, first=None, last=None, msg=True):
	"""
	Rudimentary Imagic stack reader
	Could be improved with more sophisticated error testing and header parsing
	Currently  only reads image data as floats
	Currently reads header information for only first image in stack
	"""
	t0 = time.time()
	if msg is True:
		apDisplay.printMsg("reading stack from disk into memory: "+filename)
	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"

	### check file size, no more than 2 GB is possible 
	### it takes double memory on machine to read stack
	stacksize = apFile.fileSize(datafilename)/1024.0/1024.0
	if stacksize > 1200:
		apDisplay.printWarning("Stack is too large to read "+str(round(stacksize,1))+" MB")
		return None

	### read stack
	stack={}
	stack['header'] = readImagicHeader(headerfilename)
	stack['images'] = readImagicData(datafilename, stack['header'], first, last)
	if msg is True:
		apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))	
	return stack

#===============	
def readImagicHeader(headerfilename):
	headfile=open(headerfilename,'rb')
	
	# Header information for each image contained in 256 4-byte chunks
	### actually its 1024 bytes, but 4 bytes (32 bits) per chuck (int32)
	# First image header contains all necessary info to read entire stack
	headerbytes=headfile.read(1024)
	headfile.close()
	
	i=numpy.fromstring(headerbytes, dtype=numpy.int32)
	f=numpy.fromstring(headerbytes, dtype=numpy.float32)
	
	header={}
	imgnum=i[0]
	imgfollow=i[1]
	header['nimg']=imgnum+imgfollow
	header['npix']=i[11]
	header['lines']=i[12]
	header['rows']=i[13]
	header['avg']=f[17]
	header['sig']=f[18]
	header['max']=f[21]
	header['min']=f[22]

	return header

#===============	
def readImagicData(datafilename, headerdict, first=None, last=None):
	shape = (headerdict['nimg'], headerdict['rows'], headerdict['lines'])
	images = numpy.fromfile(file=datafilename, dtype=numpy.float32)
	try:
		images = images.reshape(headerdict['nimg'], headerdict['rows'], headerdict['lines'])
		images = numpy.fliplr(images)
	except:
		mult = headerdict['nimg']*headerdict['rows']*headerdict['lines']
		print mult, images.shape, headerdict['nimg'], headerdict['rows'], headerdict['lines']
		apDisplay.printError("could not read image stack")
	return images

#===============
#===============
def writeImagic(array, filename, msg=True):
	"""
	Rudimentary Imagic stack writer
	Could be improved with more sophisticated error testing and header parsing
	Currently only reads image data as floats
	Currently reads header information for only first image in stack

	Inputs:
		3d numpy array (numimg x row x col)
		filename
	Modifies:
		overwrites files on disk
	Outputs:
		none
	"""
	t0 = time.time()
	if msg is True:
		apDisplay.printMsg("writing stack to disk from memory: "+filename)
	root=os.path.splitext(filename)[0]
	headerfilename = root+".hed"
	datafilename   = root+".img"
	if os.path.isfile(headerfilename) or os.path.isfile(datafilename):
		apDisplay.printWarning("stack files '"+headerfilename+"' already exist")

	### write header file info, and dump images to image file
	i = 0
	headfile = open(headerfilename,'wb')
	datafile = open(datafilename, 'wb')
	while i < array.shape[0]:
		partimg = array[i]
		avg1,stdev1,min1,max1 = getImageInfo(partimg)
		partnum = i+1
		headerstr = makeHeaderStr(partnum, array.shape, avg1, stdev1, min1, max1)
		headfile.write(headerstr)
		### scale image to maximize range
		scalepartimg = (partimg-min1)/(max1-min1)
		datafile.write(scalepartimg.tostring())
		i += 1
	headfile.close()
	datafile.close()
	if msg is True:
		apDisplay.printMsg("wrote "+str(partnum)+" particles to header file")
		apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))	
	return

#=========================
def getImageInfo(im):
	"""
	prints out image information good for debugging
	"""
	avg1=ndimage.mean(im)
	stdev1=ndimage.standard_deviation(im)
	min1=ndimage.minimum(im)
	max1=ndimage.maximum(im)

	return avg1,stdev1,min1,max1

#===============
def makeHeaderStr(partnum, shape, avg, stdev, maxval, minval):
	"""
	based on 
		http://www.imagescience.de/formats/formats.htm
	"""
	headerstr = ""
	### first image number
	headerstr += intToFourByte(partnum)
	### number of images, less one
	headerstr += intToFourByte(shape[0]-1)
	### always 0,1 ???
	headerstr += intToFourByte(0)
	headerstr += intToFourByte(1)
	### creation date: day, month, year, hour, min, sec
	headerstr += intToFourByte(time.localtime()[2])
	headerstr += intToFourByte(time.localtime()[1]) #eman always uses month-1?
	headerstr += intToFourByte(time.localtime()[0])
	headerstr += intToFourByte(time.localtime()[3])
	headerstr += intToFourByte(time.localtime()[4])
	headerstr += intToFourByte(time.localtime()[5])
	### total number of pixels
	headerstr += intToFourByte(shape[1]*shape[2])
	headerstr += intToFourByte(shape[1]*shape[2])
	### number of columns
	headerstr += intToFourByte(shape[2])
	### number of rows
	headerstr += intToFourByte(shape[1])
	### data type
	headerstr += "REAL"
	### zero coordinates
	headerstr += intToFourByte(0)
	headerstr += intToFourByte(0)
	### average density as float
	headerstr += floatToFourByte(avg)
	### standard deviation of densities
	headerstr += floatToFourByte(stdev)
	### variance of densities in image 
	headerstr += floatToFourByte(stdev*stdev)
	### old average density of this image 
	headerstr += floatToFourByte(0)
	### highest density in image 
	headerstr += floatToFourByte(maxval)
	### minimal density in image 
	headerstr += floatToFourByte(minval)
	while len(headerstr) < 1024:
		### fill in the rest with garbage
		headerstr += floatToFourByte(0)
	return headerstr


#===============
def intToFourByte(intnum):
	fourbyte = numpy.array((intnum), dtype=numpy.int32).tostring()
	return fourbyte
	if abs(intnum) > 2130706432:
		apDisplay.printError("integer overflow")
	usenum = intnum
	f1 = chr(usenum%256)
	usenum /= 256
	f2 = chr(usenum%256)
	usenum /= 256
	f3 = chr(usenum%256)
	usenum /= 256
	f4 = chr(usenum%256)
	return f1+f2+f3+f4

#===============
def fourByteToInt(fourbyte):
	intnum = numpy.fromstring(fourbyte, dtype=numpy.int32)
	return intnum[0]
	n1 = ord(fourbyte[0])
	n2 = ord(fourbyte[1])
	n3 = ord(fourbyte[2])
	n4 = ord(fourbyte[3])
	neg = False
	if n4 > 128:
		n1 = 256 - n1
		n2 = 255 - n2
		n3 = 255 - n3
		n4 = 255 - n4
		neg = True
	intnum = n1 + 256*n2 + (256**2)*n3 + (256**3)*n4
	if neg is True:
		intnum *= -1
	return intnum

#===============
def floatToFourByte(floatnum):
	"""
	convert float to a 4-byte string
	numpy.fromstring("\x02\x00\x00\x00", dtype=numpy.float32)

	\x02\x00\x00\x00 => 2.80259693e-45
	\x01\x00\x00\x00 => 1.40129846e-45
	"""
	fourbyte = numpy.array((floatnum), dtype=numpy.float32).tostring()
	return fourbyte

#===============
def fourByteToFloat(fourbyte):
	floatnum = numpy.fromstring(fourbyte, dtype=numpy.float32)
	return floatnum[0]

#===============	
def writeImagicData(array):
	shape = (headerdict['nimg'], headerdict['rows'], headerdict['lines'])
	images = numpy.fromfile(file=datafilename, dtype=numpy.float32)
	try:
		images = images.reshape(headerdict['nimg'], headerdict['rows'], headerdict['lines'])
		images = numpy.fliplr(images)
	except:
		mult = headerdict['nimg']*headerdict['rows']*headerdict['lines']
		print mult, images.shape, headerdict['nimg'], headerdict['rows'], headerdict['lines']
		apDisplay.printError("could not read image stack")
	return images

#===============	
def writeVarianceImage(imagicfile, varmrcfile):
	imgdict = readImagic(imagicfile)
	if imgdict is None:
		return
	vararray = imgdict['images'].std(0)
	mrc.write(vararray, varmrcfile)
	return vararray

