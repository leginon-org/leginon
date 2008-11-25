#########################################################
# Imagic I/O
#########################################################

import os
import sys 
import re
import time
import math
import apDisplay
import apFile
import apImage
import numpy

#===============
def readImagic(filename):
	"""
	Rudimentary Imagic stack reader
	Could be improved with more sophisticated error testing and header parsing
	Currently  only reads image data as floats
	Currently reads header information for only first image in stack
	"""
	t0 = time.time()
	apDisplay.printMsg("reading stack from disk into memory: "+filename)
	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"
	stack={}
	stack['header'] = readImagicHeader(headerfilename)
	stack['images'] = readImagicData(datafilename, stack['header'])
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
def readImagicData(datafilename, headerdict):
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
def writeImagic(array, filename):
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
		avg1,stdev1,min1,max1 = apImage.getImageInfo(partimg)
		partnum = i+1
		headerstr = makeHeaderStr(partnum, array.shape, avg1, stdev1, min1, max1)
		headfile.write(headerstr)
		### scale image to maximize range
		scalepartimg = (partimg-min1)/(max1-min1)
		datafile.write(scalepartimg.tostring())
		i += 1
	headfile.close()
	datafile.close()
	apDisplay.printMsg("wrote "+str(partnum)+" particles to header file")

	apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))	
	return

#===============
def makeHeaderStr(partnum, shape, avg, stdev, maxval, minval):
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

