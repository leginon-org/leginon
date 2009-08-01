#########################################################
# Imagic I/O
#########################################################

#python
import os
import sys 
import re
import time
import math
import shutil
#appion
import apDisplay
import apFile
import numpy
from pyami import mrc
import pyami.quietscipy
from scipy import ndimage

#maximum allowed stack size in gigabytes (GB)
memorylimit = 1.2
bytelimit = memorylimit*(1024**3)

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
def readImagic(filename, first=1, last=None, msg=True):
	"""
	Rudimentary Imagic stack reader
	Could be improved with more sophisticated error testing and header parsing
	Currently  only reads image data as floats
	Currently reads header information for only first image in stack
	"""
	t0 = time.time()
	if first < 1:
		apDisplay.printError("particle numbering starts at 1")
	if last is not None and first > last:
		apDisplay.printError("requested first particle %d is greater than last particle %d"%(first,last))
	if msg is True:
		apDisplay.printMsg("reading stack from disk into memory: "+os.path.basename(filename))
		if last is not None:
			apDisplay.printMsg("particles %d through %d"%(first, last))
	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"

	### check file size, no more than 2 GB is possible 
	### it takes double memory on machine to read stack
	filesize = apFile.fileSize(datafilename)
	if first is None and last is None and filesize > bytelimit:
		apDisplay.printError("Stack is too large to read %s"%(apDisplay.bytes(filesize)))

	### read stack header

	headerdict = readImagicHeader(headerfilename)

	### determine amount of memory needed
	partbytes = 4*headerdict['rows']*headerdict['lines']
	if last is None:
		last = headerdict['nimg']
	elif last > headerdict['nimg']:
		apDisplay.printWarning("requested particle %d from stack of length %d"%(last, headerdict['nimg']))
		last = headerdict['nimg']
	numpart = last - first + 1
	if partbytes*numpart > filesize:
		apDisplay.printError("requested particle %d from stack of length %d"%(last, filesize/partbytes))
	if partbytes*numpart > bytelimit:
		apDisplay.printError("Stack is too large to read %d particles, requesting %s"
			%(numpart, apDisplay.bytes(partbytes*numpart)))

	### read stack images
	images = readImagicData(datafilename, headerdict, first, numpart)
	stack = {'header': headerdict, 'images': images}

	if msg is True:
		apDisplay.printMsg("read %d particles equaling %s in size"%(numpart, apDisplay.bytes(partbytes*numpart)))
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
def readImagicData(datafilename, headerdict, firstpart=1, numpart=1):
	### calculate number of bytes in particle image
	partbytes = 4*headerdict['rows']*headerdict['lines']

	### open file
	f = open(datafilename, 'rb')

	### skip ahead to desired first particle
	f.seek(partbytes*(firstpart-1))

	### read particle images
	data = f.read(partbytes*numpart)

	### close file
	f.close()

	shape = (numpart, headerdict['rows'], headerdict['lines'])
	rawarray = numpy.fromstring(data, dtype=numpy.float32)
	try:
		images = rawarray.reshape(shape)
		images = numpy.fliplr(images)
	except:
		mult = numpart*headerdict['rows']*headerdict['lines']
		print mult, shape, rawarray.shape, numpart, headerdict['nimg'], headerdict['rows'], headerdict['lines']
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
	if isinstance(array, list):
		if len(array) == 0:
			apDisplay.printWarning("writeImagic: no particles to write")
			return
		try:
			array = numpy.asarray(array, dtype=numpy.float32)
		except:
			boxsizes = []
			for part in array:
				shape = part.shape
				if not shape in boxsizes:
					boxsizes.append(shape)
			apDisplay.printError("your particles have different boxsizes: "+str(boxsizes))

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
	headfile = open(headerfilename, 'wb')
	datafile = open(datafilename, 'wb')
	partnum = 0
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
	if partnum < 1:
		apDisplay.printWarning("did not write any particles to file")
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

#===============
def getBoxsize(filename):
	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"
	headerdict = readImagicHeader(headerfilename)
	boxsize = headerdict['rows']
	return boxsize

#===============
def readSingleParticleFromStack(filename, partnum=1, boxsize=None, msg=True):
	"""
	reads a single particle from imagic stack
	particle number starts at 1
	assumes particles have squares boxes
	"""
	t0 = time.time()
	if partnum < 1:
		apDisplay.printError("particle numbering starts at 1")

	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"

	if msg is True:
		apDisplay.printMsg("reading particle %d from stack %s into memory"%(partnum, os.path.basename(filename)))

	### determine boxsize
	if boxsize is None:
		headerdict = readImagicHeader(headerfilename)
		boxsize = headerdict['rows']
		if partnum > headerdict['nimg']:
			apDisplay.printError("requested particle %d from stack of length %d"%(partnum, headerdict['nimg']))
	filesize = apFile.fileSize(datafilename)

	### calculate number of bytes per particle
	partbytes = boxsize**2*4
	if partbytes*partnum > filesize:
		apDisplay.printError("requested particle %d from stack of length %d"%(partnum, filesize/partbytes))

	### open file
	f = open(datafilename, 'rb')

	### skip ahead to desired particle
	f.seek(partbytes*(partnum-1))

	### read particle image
	data = f.read(partbytes)
	f.close()

	shape = (boxsize, boxsize)
	partimg = numpy.fromstring(data, dtype=numpy.float32)
	try:
		partimg = partimg.reshape(boxsize, boxsize)
		partimg = numpy.fliplr(partimg)
	except:
		print partimg
		print boxsize, boxsize*boxsize, partimg.shape
		apDisplay.printError("could not read particle from stack")
	return partimg

#===============
def mergeStacks(stacklist, mergestack):
	### initialization
	t0 = time.time()
	apFile.removeStack(mergestack)
	root=os.path.splitext(mergestack)[0]
	mergeheader = root+".hed"
	mergedata   = root+".img"

	### merge data files
	fout = file(mergedata, 'wb')
	numpart = 0
	totalsize = 0
	for stackfile in stacklist:
		stackdatafile = os.path.splitext(stackfile)[0]+ ".img"
		### size checks
		npart = apFile.numImagesInStack(stackdatafile)
		size = apFile.fileSize(stackdatafile)
		apDisplay.printMsg("%d particles in %s (%s)"%(npart, stackdatafile, apDisplay.bytes(size)))
		totalsize += size
		numpart += npart

		fin = file(stackdatafile, 'rb')
		shutil.copyfileobj(fin, fout, 65536)
		fin.close()
	fout.close()
	if numpart < 1:
		apDisplay.printError("found %d particles"%(numpart))
	apDisplay.printMsg("found %d particles"%(numpart))
	finalsize = apFile.fileSize(mergedata)
	if finalsize != totalsize:
		apDisplay.printError("size mismatch %s vs. %s"%(apDisplay.bytes(finalsize), apDisplay.bytes(totalsize)))
	apDisplay.printMsg("size match %s vs. %s"%(apDisplay.bytes(finalsize), apDisplay.bytes(totalsize)))

	### merge header files
	#apDisplay.printError("not finished")
	mergehead = open(mergeheader, 'wb')
	partnum = 0
	totalsize = 0
	for stackfile in stacklist:
		headerfilename = os.path.splitext(stackfile)[0]+ ".hed"
		headfile = open(headerfilename, 'rb')
		### size checks
		size = apFile.fileSize(headerfilename)
		apDisplay.printMsg("%s (%d kB)"%(headerfilename, size/1024))
		totalsize += size

		#apDisplay.printMsg("%d\t%s"%(npart, stackfile))
		i = 0
		npart = apFile.numImagesInStack(stackfile)
		while i < npart:
			#print i, npart, partnum
			### read old header
			data = headfile.read(1024)
			### start new string
			headerstr = ""
			### first image number
			headerstr += intToFourByte(partnum)
			### number of images, less one
			headerstr += intToFourByte(numpart-1)
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
			headerstr += intToFourByte(partnum)
			### append other header info, 4 character per item
			headerstr += data[62*4:]
			mergehead.write(headerstr)
			partnum += 1
			i += 1
	mergehead.close()
	apDisplay.printMsg("wrote %d particles"%(numpart))
	finalsize = apFile.fileSize(mergeheader)
	if finalsize != totalsize:
		apDisplay.printError("size mismatch %s vs. %s"%(apDisplay.bytes(finalsize), apDisplay.bytes(totalsize)))
	apDisplay.printMsg("size match %s vs. %s"%(apDisplay.bytes(finalsize), apDisplay.bytes(totalsize)))
	apDisplay.printMsg("finished stack merge in "+apDisplay.timeString(time.time()-t0))	

#===============
def readParticleListFromStack(filename, partlist, boxsize=None, msg=True):
	"""
	reads a single particle from imagic stack
	particle number starts at 1
	assumes particles have squares boxes
	"""
	t0 = time.time()

	### sort list
	partlist.sort()
	firstpartnum = partlist[0]
	lastpartnum = partlist[len(partlist)-1]
	if firstpartnum < 1:
		apDisplay.printError("particle numbering starts at 1")

	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"

	### determine boxsize
	if boxsize is None:
		headerdict = readImagicHeader(headerfilename)
		boxsize = headerdict['rows']
		if lastpartnum > headerdict['nimg']:
			apDisplay.printError("requested particle %d from stack %s of length %d"
				%(lastpartnum, os.path.basename(datafilename), headerdict['nimg']))
	filesize = apFile.fileSize(datafilename)

	### calculate number of bytes per particle
	partbytes = boxsize**2*4
	if partbytes*lastpartnum > filesize:
		apDisplay.printError("requested particle %d from stack %s of length %d"
			%(lastpartnum, os.path.basename(datafilename), filesize/partbytes))

	### open file
	f = open(datafilename, 'rb')
	partdatalist = []
	prevpartnum = 0
	for partnum in partlist:
		if msg is True:
			apDisplay.printMsg("reading particle %d from stack %s into memory"
				%(partnum, os.path.basename(datafilename)))

		### skip ahead to desired particle
		f.seek(partbytes*(partnum-prevpartnum-1))

		### read particle image
		data = f.read(partbytes)

		shape = (boxsize, boxsize)
		partimg = numpy.fromstring(data, dtype=numpy.float32)
		try:
			partimg = partimg.reshape(boxsize, boxsize)
			partimg = numpy.fliplr(partimg)
		except:
			print partimg
			print boxsize, boxsize*boxsize, partimg.shape
			apDisplay.printError("could not read particle from stack")
		partdatalist.append(partimg)
	f.close()
	return partdatalist

