#!/usr/bin/env python

"""
Source material taken from the spipylib package at Wadsworth

* Spiderarray.py
http://www.wadsworth.org/spider_doc/spider/docs/python/spipylib/array.html

AND

* Spiderutils.py
http://www.wadsworth.org/spider_doc/spider/docs/python/spipylib/library.html

	# Spider Python Library: Spiderarray.py 
	# Copyright (C) 2006  Health Research Inc.
	#
	# HEALTH RESEARCH INCORPORATED (HRI),
	# ONE UNIVERSITY PLACE, RENSSELAER, NY 12144-3455
	#
	# Email:  spider@wadsworth.org
	#
	# This program is free software; you can redistribute it and/or
	# modify it under the terms of the GNU General Public License as
	# published by the Free Software Foundation; either version 2 of the
	# License, or (at your option) any later version.
	#
	# This program is distributed in the hope that it will be useful,
	# but WITHOUT ANY WARRANTY; without even the implied warranty of
	# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
	# General Public License for more details.

Modified on March 14, 2008 by Neil Voss:
* Merged Spiderutils.py and Spiderarray.py
* Removed unnecessary DOC file stuff
* Changed Numeric to numpy
* Allowed read first image of a stack

"""

import sys, struct
import numpy
import os

# --------------------------------------------------------------------
iforms = [1,3,-11,-12,-21,-22]

# --------------------------------------------------------------------
SpiderHeaderDict = { 
	1  : 'nslice ', 	2  : 'nrow ',  	3  : 'irec ',  	4 : 'nhistrec ',
	5  : 'iform ', 	6  : 'imami ', 	7  : 'fmax ',  	8 : 'fmin ',
	9  : 'av ',    	10 : 'sig ',   	11 : 'ihist ', 	12 : 'nsam ',
	13 : 'labrec ',	14 : 'iangle ',	15 : 'phi ',   	16 : 'theta ',
	17 : 'gamma ', 	18 : 'xoff ',  	19 : 'yoff ',  	20 : 'zoff ',
	21 : 'scale ', 	22 : 'labbyt ',	23 : 'lenbyt ',	24 : 'istack ',
	25 : 'NOTUSED ',	26 : 'maxim ', 	27 : 'imgnum ',	28 : 'lastindx ',
	29 : 'unused ',	30 : 'unused ',	31 : 'Kangle ',	32 : 'phi1 ',
	33 : 'theta1 ',	34 : 'psi1 ',  	35 : 'phi2 ',  	36 : 'theta2 ',
	37 : 'psi2 '}

# --------------------------------------------------------------------
def getHeaderDict(hdr):
	hdrdict = {}
	#hdrdict['header'] = hdr
	hdrlen = len(hdr)
	hdrdict['bigendian'] = hdr[0]

	for i in range(1, hdrlen):
		if i in SpiderHeaderDict:
			name = SpiderHeaderDict[i]
			if name in ['NOTUSED', 'unused']:
				continue
			val = hdr[i]
			hdrdict[name.strip()] = val

	if hdrlen > 9:
		hdrdict['avg'] = hdr[9]  # alternate access format
	if hdrlen > 31:
		hdrdict['kangle']  = hdr[31]
	#import pprint
	#pprint.pprint(hdrdict)
	return hdrdict

# --------------------------------------------------------------------
def read(filename):
	" Convert a SPIDER file into a numpy array "
	#print "reading SPIDER file "+filename
	return spider2array(filename)

# --------------------------------------------------------------------
def spider2array(filename):
	if not os.path.isfile(filename):
		return None
	" Convert a SPIDER file into a numpy array "
	hdr = getSpiderHeader(filename)
	hdrdict = getHeaderDict(hdr) # a class that simplifies accessing header elements 
	hdrbytes = int(hdrdict['labbyt'])

	iform = int(hdrdict['iform'])
	#for val in hdrdict:
	#	print val, hdrdict[val]

	if iform == 1:
		isVolume = False
	elif iform == 3:
		print "opening volume"
		isVolume = True	# to do: support for Fourier iforms
	else:
		print "iform %d not supported" % iform
		return None

	if hdrdict['istack'] > 0:
		isStack = True
	else:
		isStack = False

	xsize = int(hdrdict['nsam'])
	ysize = int(hdrdict['nrow'])
	if isVolume:
		zsize = int(hdrdict['nslice'])
		datawords = xsize * ysize * zsize
	elif isStack:
		ysize += 2
		datawords = xsize * ysize
	else:
		datawords = xsize * ysize
	databytes = datawords * 4

	# seek ahead to the data
	#print "read"
	fp = open(filename,'rb')
	fp.seek(hdrbytes)
	if int(hdrdict['bigendian']):
		#print "using big endian"
		fmt = '>%df' % datawords
	else:
		#print "using small endian"
		fmt = '<%df' % datawords
	arr = numpy.fromfile(fp, dtype=numpy.dtype(fmt))
	"""
	if hdrdict['bigendian']:

		data = fp.read(databytes)

		#print "unpack"
		t = struct.unpack(fmt, data)

		# the numpy function 'array' will automatically upcast
		# to 64 bits if you don't use savespace
		#print "convert"
		arr = numpy.array(t, dtype=numpy.dtype(fmt))
		arr = numpy.fromfile(fp, dtype=numpy.dtype(fmt))
	"""


	fp.close()

	if isVolume:
		arr.shape = zsize, ysize, xsize
	elif isStack:
		arr.shape = ysize, xsize
		arr = arr[2:ysize,:]
	else:
		arr.shape = ysize, xsize
	return arr

# --------------------------------------------------------------------
def write(arr, filename):
	" Convert a numpy array into a SPIDER file "
	#print "writing SPIDER file "+filename
	return array2spider(arr, filename)

# --------------------------------------------------------------------
def array2spider(arr, filename):
	" Convert a numpy array into a SPIDER file "
	# create and write the SPIDER header
	hdr = makeSpiderHeader(arr.shape)
	if len(hdr) < 256:
		raise IOError, "Error creating Spider header" 
	try:
		fp = open(filename, 'wb')
		fp.writelines(hdr)
	except:
		raise IOError, "Unable to open %s for writing" % filename

	# write image data
	farr = numpy.array(arr, dtype=numpy.dtype('>f4'))
	farr.tofile(fp)
	#fp.write(farr.tostring())
	fp.close

# --------------------------------------------------------------------
def getSpiderHeader(filename, n=27):
	" returns first n numbers, with Spider indices (starting at 1)"
	" if n = 'all', returns entire header "
	if not os.path.exists(filename):
		print "file does not exist"
		return 0
	getall = 0
	if not isInt(n):
		n = 27
		getall = 1
	nwords = n * 4  # no. floating point words 
		
	if os.path.getsize(filename) < nwords:
		print "file is the wrong size"
		return 0
	try:
		fp = open(filename,'rb')
		f = fp.read(nwords)	# read 27 * 4 bytes
		fp.close()
	except:
		print "failed to open file"
		return 0
	bigendian = 1
	bigformat = '>%df' % n
	t = struct.unpack(bigformat,f)	 # try big-endian first
	hdr = isSpiderHeader(t)
	if hdr == 0:
		print "reading small endian"
		bigendian = 0
		littleformat = '<%df' % n
		t = struct.unpack(littleformat,f)  # little-endian
		hdr = isSpiderHeader(t)

	if hdr == 0:
		print "header is null"
		return 0
	else:
		# check if user requested the entire header
		if getall:
			labbyt = int(hdr[22])	# total no. of bytes in header
			hdr = getSpiderHeader(filename, n=labbyt)
		hdr = list(hdr)
		hdr[0] = bigendian
		return hdr

# --------------------------------------------------------------------
def makeSpiderHeader(dims):
	" dims must be (nsam, nrow), or (nsam, nrow, nslice) "
	if len(dims) == 2:
		nsam, nrow = dims[1], dims[0]
		nslice = 1.0
		iform = 1.0
		isVolume = 0
	elif len(dims) == 3:
		nsam, nrow, nslice = dims[1], dims[0], dims[2]
		iform = 3.0
		isVolume = 1
	else:
		return []

	lenbyt = nsam * 4  # There are labrec records in the header
	labrec = 1024 / lenbyt
	if 1024%lenbyt != 0: labrec += 1
	labbyt = labrec * lenbyt
	hdr = []
	nvalues = labbyt / 4
	for i in range(nvalues):
		hdr.append(0.0)
		
	if len(hdr) < 23:
		return []

	# NB these are Fortran indices
	hdr[1]  = float(nslice) # nslice (=1 for an image) 
	hdr[2]  = float(nrow)	# number of rows per slice
	hdr[5]  = iform			# iform for 2D image
	hdr[12] = float(nsam)	# number of pixels per line
	hdr[13] = float(labrec) # number of records in file header
	hdr[22] = float(labbyt) # total number ofu bytes in header
	hdr[23] = float(lenbyt) # record length in bytes

	# adjust for Fortran indexing
	hdr = hdr[1:]
	hdr.append(1.0)
	# pack binary data into a string
	hdrstr = []
	#print "WRITING HEADER"
	getHeaderDict(hdr)
	for v in hdr:
		hdrstr.append(struct.pack('>f', v))
	return hdrstr

# --------------------------------------------------------------------
def isSpiderHeader(t):
	"returns tuple of values from a valid SPIDER header, else 0"
	h = (99,) + t	# add 1 value so can use spider header index start=1
	# header values 1,2,5,12,13,22,23 should be integers
	for i in [1,2,5,12,13,22,23]:
		if not isInt(h[i]): return 0
	# check iform
	iform = int(h[5])
	if not iform in iforms: return 0
	# check other header values
	labrec = int(h[13])	# no. records in file header
	labbyt = int(h[22])	# total no. of bytes in header
	lenbyt = int(h[23])	# record length in bytes
	#print "labrec = %d, labbyt = %d, lenbyt = %d" % (labrec,labbyt,lenbyt)
	if labbyt != (labrec * lenbyt): return 0
	# looks like a valid header
	return h

# --------------------------------------------------------------------
def isInt(f):
	"returns 1 if input is an integer"
	try:
		i = int(f)
		if f-i == 0: return 1
		else:	return 0
	except:
		return 0

# --------------------------------------------------------------------
def randTest():
	print "Running read/write test"

	### create random array
	array1 = numpy.random.random((160,160))
	print "********", array1.mean(), array1.std(), array1.shape

	### write to file
	write(array1, "rand1.spi")

	### read array back in
	array2 = read("rand1.spi")
	print "********", array2.mean(), array2.std(), array2.shape

	### convert using eman
	import subprocess
	emancmd = "proc2d rand1.spi rand3.spi spiderswap-single"
	proc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()

	### read eman array
	array3 = read("rand3.spi")
	print "********", array3.mean(), array3.std(), array3.shape

	### copy with spider
	import spyder
	spider = spyder.SpiderSession(logo=False)
	spider.toSpider("CP", "rand1", "rand2")
	spider.toSpider("CP", "rand3", "rand4")
	spider.close()
	
	### read arrays
	array4 = read("rand2.spi")
	print "********", array4.mean(), array4.std(), array4.shape
	array5 = read("rand4.spi")
	print "********", array5.mean(), array5.std(), array5.shape

	### direct convert using eman
	from pyami import mrc
	mrc.write(array1, "rand1.mrc")
	emancmd = "proc2d rand1.mrc rand5.spi spiderswap-single"
	proc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()

	### read eman array
	array6 = read("rand5.spi")
	print "********", array6.mean(), array6.std(), array6.shape

# --------------------------------------------------------------------
if __name__ == '__main__':
	if len(sys.argv[1:]) < 2:
		randTest()
		print "Usage: spi2arr.py spiderfile outfile"
		sys.exit(1)
	filename = sys.argv[1]
	outfile = sys.argv[2]
	arr = read(filename)
	b = arr * -1  # perform a simple array operation
	write(b, outfile)




