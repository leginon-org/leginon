#!/usr/bin/env python

import Numeric
import array
import struct
import sys
import cStringIO

mrcmode_typecode = {
	0: (1, Numeric.UnsignedInt8),
	1: (2, Numeric.Int16),
	2: (4, Numeric.Float32),
	3: (2, Numeric.UInt16)
	}
typecode_mrcmode = {
	Numeric.UnsignedInt8: 0,
	Numeric.Int16: 1,
	Numeric.UInt16: 3,
	Numeric.Float32: 2,
	Numeric.Float: 2,
	Numeric.Float64: 2,
	Numeric.Int: 2,
	Numeric.Int32: 2,
	Numeric.Int8: 1
	}

def min(inputarray):
	f = Numeric.ravel(inputarray)
	i = Numeric.argmin(f)
	return f[i]

def max(inputarray):
	f = Numeric.ravel(inputarray)
	i = Numeric.argmax(f)
	return f[i]

def mean(inputarray):
	f = Numeric.ravel(inputarray)
	inlen = len(f)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(f) / divisor
	return m

def mrc_to_numeric(filename):
	try:
		f = open(filename, 'rb')
		image = mrc_read(f)
		f.close()
		return image
	except Exception, detail:
		print detail
		return None

def numeric_to_mrc(ndata, filename):
	if type(ndata) is not Numeric.ArrayType:
		raise TypeError('ndata must be Numeric array')
	f = open(filename, 'wb')
	mrc_write(f, ndata)
	f.close()

def mrcstr_to_numeric(mrcstr):
	try:
		f = cStringIO.StringIO(mrcstr)
		image = mrc_read(f)
		f.close()
		return image
	except Exception, detail:
		print detail
		return None

def numeric_to_mrcstr(ndata):
	if type(ndata) is not Numeric.ArrayType:
		raise TypeError('ndata must be Numeric array')
	f = cStringIO.StringIO()
	mrc_write(f, ndata)
	mrcstr = f.getvalue()
	return mrcstr

def mrc_read(mrcfile):
	hdr = MrcHeader(mrcfile)
	dat = MrcData()
	dat.useheader(hdr)
	dat.fromfile(mrcfile)
	return dat.toNumeric()

def mrc_write(mrcfile, image):
	hdr = MrcHeader()
	dat = MrcData()
	dat.fromNumeric(image)
	hdr.usedata(dat)
	hdr.tofile(mrcfile)
	dat.tofile(mrcfile)

class MrcData:
	def __init__(self):
		self.data = None
		self.mode = None
		self.width = None
		self.height = None
		self.depth = None
		self.min = None
		self.max = None
		self.mean = None

	def useheader(self, head):
		self.describe(head['width'], head['height'], head['depth'], head['mode'], head['min'], head['max'], head['mean'])

	def describe(self, width, height, depth, mode, min, max, mean):
		self.mode = mode
		self.width = width
		self.height = height
		self.depth = depth
		self.min = min
		self.max = max
		self.mean = mean

	def fromfile(self, fobj):
		elementsize = mrcmode_typecode[self.mode][0]
		elements = self.width * self.height * self.depth
		self.data = fobj.read(elements * elementsize)

	def tofile(self, fobj):
		fobj.write(self.data)

	def toNumeric(self):
		typecode = mrcmode_typecode[self.mode][1]
		narray = Numeric.fromstring(self.data, typecode)
		## for now, using little endian as standard
		if sys.byteorder != 'little':
			narray = narray.byteswapped()

		## reshape based on my description
		if self.height < 2 and self.depth < 2:
			shape = (self.width, )
		elif self.depth < 2:
			shape = (self.height, self.width)
		else:
			shape = (self.depth, self.height, self.width)
		narray.shape = shape

		return narray

	def fromNumeric(self, narray):
		typecode = narray.typecode()
		self.mode = typecode_mrcmode[typecode]

		# array to the proper typecode
		newtypecode = mrcmode_typecode[self.mode][1]
		narray = narray.astype(newtypecode)
			
		## get my description from Numeric shape
		shape = narray.shape
		if len(shape) == 1:
			# x data only
			self.width = shape[0]
			self.height = 1
			self.depth = 1
		elif len(shape) == 2:
			# x,y data
			self.height = shape[0]
			self.width = shape[1]
			self.depth = 1
		elif len(shape) == 3:
			# x,y,z data
			self.depth = shape[0]
			self.height = shape[1]
			self.width = shape[2]
		else:
			raise 'unsupported'

		## these are defined previously in this module
		## (not Python built-ins)
		self.min = min(narray)
		self.max = max(narray)
		self.mean = mean(narray)

		## for now, using little endian as standard
		if sys.byteorder != 'little':
			narray = narray.byteswapped()
		self.data = narray.tostring()

## MrcHeader uses a dictionaray to store MRC header data
class MrcHeader:
	"""Handles MRC header parsing, creation, and I/O.
	optionally initialized with file object to read from"""

	## bytes in a full MRC header
	headerlen = 1024

	def __init__(self, fobj=None):
		self.data = {}
		if fobj:
			self.fromfile(fobj)

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
		self.data[key] = value

	def usedata(self, mrcdata):
		self['width'] = mrcdata.width
		self['height'] = mrcdata.height
		self['depth'] = mrcdata.depth
		self['mode'] = mrcdata.mode
		self['min'] = mrcdata.min
		self['max'] = mrcdata.max
		self['mean'] = mrcdata.mean

	def fromstring(self, headstr):
		"get data from a string representation of MRC header"

		## first chunk includes width,height,depth,type
		chunk = headstr[:16]
		width,height,depth,mode = struct.unpack('<4i', chunk)
		self['width'] = width
		self['height'] = height
		self['depth'] = depth
		self['mode'] = mode 

		## I'm starting to impliment the other fields of the header...
		chunk = headstr[16:28]
		nxstart,nystart,nzstart = struct.unpack('<3i', chunk)
		self['nxstart'] = nxstart
		self['nystart'] = nystart
		self['nzstart'] = nzstart

		## after skipping some fields, here are image stats
		chunk = headstr[76:88]
		datamin,datamax,datamean = struct.unpack('3f', chunk)
		self['min'] = datamin
		self['max'] = datamax
		self['mean'] = datamean

		## rest of headstr ignored for now

	def tostring(self):
		"create string representation of header data"

		#### create a struct format string
		# first 16 byte chunk includes width,height,depth,mode
		dims = '<4i'
		# some padding, then the stats
		pad1 = '60x'
		stats = '3f'
		## already done 16 + 60 + 12 = 88 bytes
		## pad the rest 1024 - 88 = 936
		pad2 = '936x'

		fmtstr = dims + pad1 + stats + pad2

		headstr = struct.pack(fmtstr, 
			self['width'], self['height'],
			self['depth'], self['mode'] ,
			self['min'], self['max'], self['mean'])
		return headstr

	def fromfile(self, fobj):
		headstr = fobj.read(self.headerlen)
		self.fromstring(headstr)

	def tofile(self, fobj):
		headstr = self.tostring()
		fobj.write(headstr)

if __name__ == '__main__':
	filename = 'test1.mrc'
	f = open(filename)
	h = MrcHeader(f)
	print h.data
