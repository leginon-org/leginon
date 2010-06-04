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
from appionlib import apDisplay
from appionlib import apFile
import numpy
from pyami import mrc, mem
import pyami.quietscipy
from scipy import ndimage

#maximum allowed stack size in gigabytes (GB)
memorylimit = 1.9
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
	numimg1 = imgnum+imgfollow
	numimg2 = int('%d' % (os.stat(headerfilename)[6]/1024))
	if numimg1 != numimg2 and imgnum!=0:
		apDisplay.printWarning("Number of particles from header (%d) does not match the data (%d)"
			%(numimg1, numimg2))
		#apDisplay.printWarning("Sadly, this is fairly common, so I will use the number from the data")
	header['nimg'] = numimg2
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
			if len(boxsizes) > 1:
				apDisplay.printError("your particles have different boxsizes: "+str(boxsizes))
			apDisplay.printError("unknown error in particle list to numpy array conversion")

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
	### image number (1)
	headerstr += intToFourByte(partnum)
	### number of images, less one (2)
	headerstr += intToFourByte(shape[0]-1)
	### always 0,1 ??? (3,4)
	headerstr += intToFourByte(0)
	headerstr += intToFourByte(1)
	### creation date: month, day, year, hour, min, sec (5-10)
	headerstr += intToFourByte(time.localtime()[1]) #month
	headerstr += intToFourByte(time.localtime()[2]) #day
	headerstr += intToFourByte(time.localtime()[0]) #year
	headerstr += intToFourByte(time.localtime()[3]) #hour
	headerstr += intToFourByte(time.localtime()[4]) #min
	headerstr += intToFourByte(time.localtime()[5]) #sec
	### total number of pixels (11,12)
	headerstr += intToFourByte(shape[1]*shape[2])
	headerstr += intToFourByte(shape[1]*shape[2])
	### number of columns (13)
	headerstr += intToFourByte(shape[2])
	### number of rows (14)
	headerstr += intToFourByte(shape[1])
	### data type (15)
	headerstr += "REAL"
	### zero coordinates (16,17)
	headerstr += intToFourByte(0)
	headerstr += intToFourByte(0)
	### average density as float (18)
	headerstr += floatToFourByte(avg)
	### standard deviation of densities (19)
	headerstr += floatToFourByte(stdev)
	### variance of densities in image (20)
	headerstr += floatToFourByte(stdev*stdev)
	### old average density of this image (21)
	headerstr += floatToFourByte(0)
	### highest density in image (22)
	headerstr += floatToFourByte(maxval)
	### minimal density in image (23)
	headerstr += floatToFourByte(minval)
	for i in range(37):
		headerstr += intToFourByte(0)
	### number of z slices
	headerstr += intToFourByte(1)
	### image number, EMAN does this, IMAGIC says num 3d in 4d
	headerstr += intToFourByte(1)
	for i in range(6):
		headerstr += intToFourByte(0)	
	headerstr += intToFourByte(33686018)
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
	partnum = 1
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
			headerstr += intToFourByte(numpart-partnum)
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
			headerstr += data[10*4:60*4]
			### number of z slices
			headerstr += intToFourByte(1)
			### first image number, EMAN does this
			headerstr += intToFourByte(partnum)
			### append other header info, 4 character per item
			headerstr += data[62*4:68*4]
			headerstr += intToFourByte(33686018)
			headerstr += data[69*4:]
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
def checkImagic4DHeader(oldhedfile,machineonly=False):
	### check IMAGIC header values:
	### IDAT(61) - int - # sections in 3D volume (1)
	### IDAT(62) - int - # objects (number of particles)
	### IDAT(69) - machine stamp (33686019 for Linux)
	if oldhedfile[-4:] != ".hed":
		oldhedfile = os.path.splitext(oldhedfile)[0]+".hed"

	# number of particles in file based on hed size:
	fnump = int(os.stat(oldhedfile)[6]/1024)
	
	of = open(oldhedfile, "rb")
	data = of.read(1024)
	of.close()
	if machineonly is not True:
		if fourByteToInt(data[60*4:61*4])!=1:
			return False
		if fourByteToInt(data[61*4:62*4])!=fnump:
			return False
	if fourByteToInt(data[68*4:69*4])!=33686018:
		return False
	return True

#===============	
def setImagic4DHeader(oldhedfile,machineonly=False):
	### set IMAGIC header values for 2D stack:
	### IDAT(61) - int - # sections in 3D volume (1)
	### IDAT(62) - int - # objects (number of particles)
	### IDAT(69) - machine stamp (33686019 for Linux)
	if oldhedfile[-4:] != ".hed":
		oldhedfile = os.path.splitext(oldhedfile)[0]+".hed"

	if checkImagic4DHeader(oldhedfile,machineonly) is True:
		return

	newhedfile = oldhedfile+".temp"

	numimg = int(os.stat(oldhedfile)[6]/1024)
	of = open(oldhedfile, "rb")
	nf = open(newhedfile, "wb")
	for i in range(numimg):
		data = of.read(1024)		
		headerstr = data[0:60*4]
		if machineonly is not True:
			headerstr += intToFourByte(1)
			headerstr += intToFourByte(numimg)
		else:
			headerstr += data[60*4:62*4]
		headerstr += data[62*4:68*4]
		headerstr += intToFourByte(33686018)
		headerstr += data[69*4:]
		nf.write(headerstr)
	of.close()
	nf.close()
	if not os.path.isfile(newhedfile):
		apDisplay.printError("failed to imagic header in file %s"%oldhedfile)
	oldsize = apFile.fileSize(oldhedfile)
	newsize = apFile.fileSize(newhedfile)
	if oldsize != newsize:
		apDisplay.printError("failed to imagic header in file %s"%oldhedfile)
	shutil.move(newhedfile, oldhedfile)
	return

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
	unames=os.uname()
	for partnum in partlist:
		if msg is True:
			apDisplay.printMsg("reading particle %d from stack %s into memory"
				%(partnum, os.path.basename(datafilename)))

		seekpos = partbytes*(partnum-prevpartnum-1)

		### for 64 bit machines, skip to desired particles 
		if unames[-1].find('64') >= 0:
                        f.seek(seekpos)
		### for 32-bit machines, seek incrementally
		else:
			seekpos = int(seekpos)%2**32
			f.seek(0)
			if seekpos > sys.maxint:
				while seekpos > sys.maxint:
					f.seek(sys.maxint,1)
					seekpos-=sys.maxint
			f.seek(seekpos,1)

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


########################################
########################################
########################################
class processStack(object):
	"""
	This is class to help process particles in a stack
	that are bigger than the amount of memory on the machine
	"""
	#===============
	def __init__(self, msg=True):
		self.msg = msg
		self.numpart = None

	#===============
	def message(self, msg):
		if self.msg is True:
			apDisplay.printMsg("processStack: "+msg)

	#===============
	def initValues(self, stackfile, numrequest=None):
		### check for stack
		if not os.path.isfile(stackfile):
			apDisplay.printError("stackfile does not exist: "+stackfile)
		### amount of free memory on machine (converted to bytes)
		self.freememory = mem.free()*1024
		self.message("Free memory: %s"%(apDisplay.bytes(self.freememory)))
		### box size of particle
		self.boxsize = apFile.getBoxSize(stackfile)[0]
		self.message("Box size: %d"%(self.boxsize))
		### amount of memory used per particles (4 bytes per pixel)
		self.memperpart = self.boxsize**2 * 4.0
		self.message("Memory used per part: %s"%(apDisplay.bytes(self.memperpart)))
		### maximum number particles that fit into memory
		self.maxpartinmem = self.freememory/self.memperpart
		self.message("Max particles in memory: %d"%(self.maxpartinmem))
		### number particles to fit into memory
		self.partallowed = int(self.maxpartinmem/20.0)
		self.message("Particles allowed in memory: %d"%(self.partallowed))
		### number particles in stack
		numpart = apFile.numImagesInStack(stackfile)
		if self.numpart is None or self.numpart > numpart:
			self.numpart = numpart
		if numrequest is not None and self.numpart > numrequest:
			self.numpart = numrequest
		self.message("Number of particles in stack: %d"%(self.numpart))
		if self.numpart > self.partallowed:
			numchucks = math.ceil(self.numpart/float(self.partallowed))
			self.stepsize = int(self.numpart/numchucks)
		else:
			numchucks = 1
			self.stepsize = self.numpart
		self.message("Particle loop num chunks: %d"%(numchucks))
		self.message("Particle loop step size: %d"%(self.stepsize))

	#===============
	def start(self, stackfile, partlist=None):
		self.stackfile = stackfile
		self.starttime = time.time()
		if partlist is not None:
			partlist.sort()
			numrequest = len(partlist)
		else:
			numrequest = None
		self.initValues(stackfile, numrequest)

		### custom pre-loop command
		self.preLoop()

		first = 1
		last = self.stepsize
		self.index = 0
		t0 = time.time()

		while self.index < self.numpart and first <= self.numpart:
			### print message
			if self.index > 10:
				esttime = (time.time()-t0)/float(self.index+1)*float(self.numpart-self.index)
				self.message("partnum %d to %d of %d, %s remain"
					%(first, last, self.numpart, apDisplay.timeString(esttime)))
			else:
				self.message("partnum %d to %d of %d"
					%(first, last, self.numpart))

			### read images
			if partlist is None:
				stackdata = readImagic(stackfile, first=first, last=last, msg=False)
				stackarray = stackdata['images']
			else:
				sublist = partlist[first-1:last]
				self.message("actual partnum %d to %d"
					%(sublist[0], sublist[len(sublist)-1]))
				stackarray = readParticleListFromStack(stackfile, sublist, msg=False)

			### process images
			self.processStack(stackarray)

			### check for proper implementation
			if self.index == 0:
				apDisplay.printError("No particles were processed in stack loop")

			### setup for next iteration
			first = last+1
			last += self.stepsize
			if last > self.numpart:
				last = self.numpart
			### END LOOP

		### check for off-one reading errors
		if self.index < self.numpart-1:
			print "INDEX %d -- NUMPART %d"%(self.index, self.numpart)
			apDisplay.printError("Did not properly process all particles")

		### custom post-loop command
		self.postLoop()

		self.message("finished processing stack in "
			+apDisplay.timeString(time.time()-self.starttime))
		return

	########################################
	# CUSTOMIZED FUNCTIONS
	########################################

	#===============
	def preLoop(self):
		return

	#===============
	def processStack(self, stackarray):
		for partarray in stackarray:
			self.processParticle(partarray)
			self.index += 1 #you must have this line in your loop
		return

	#===============
	def processParticle(self, partarray):
		raise NotImplementedError

	#===============
	def postLoop(self):
		return



