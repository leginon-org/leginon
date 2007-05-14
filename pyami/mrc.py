#!/usr/bin/env python
'''
MRC I/O functions:
	Note:
		Only 2-D MRC is supported.
		Complex data is not yet supported.

  write(a, filename, header=None)
    Write your numpy ndarray object to an MRC file.
		  a - the numpy ndarray object
      filename - the filename you want to write to
      header - (optional) dictionary of additional header information

  read(filename)
		Read MRC file into a numpy ndarray object.
      filename - the MRC filename

  mmap(filename)  
    Open MRC as a memory mapped file.  This is the most efficient way
    to read data if you only need to access part of a large MRC file.
    Only the parts you actually access are read from the disk into memory.
			filename - the MRC filename

  numarray_read(filename)
    convenience function if you want your array returned as numarray instead.
  numarray_write(a, filename, header=None)
    convenience function if you want to write a numarray array instead.
'''

import numpy
import struct
import sys
import weakref
import arraystats

#### for numarray compatibility
import numarray
def numarray_read(filename):
	a1 = read(filename)
	a2 = numarray.array(a1)
	return a1
def numarray_write(a, filename, header=None):
	a2 = numpy.asarray(a)
	write(a2, filename, header)


## mapping of MRC mode to numpy dtype string
mrc2numpy = {
	0: 'uint8',
	1: 'int16',
	2: 'float32',
#	3: 'complex',
	6: 'uint16',
}

## mapping of MRC mode to number of bytes per element
mrcitemsize = {
	0: 1,
	1: 2,
	2: 4,
#	3: 8,,
	6: 2,
}

## mapping of numpy dtype string to MRC mode
numpy2mrc = {
	'uint8': 0,
	'bool': 0,

	'int16': 1,
	'int8': 1,

	'float32': 2,
	'float64': 2,
	'int32': 2,
	'int': 2,

#	'complex': 3,
#	'complex': 3,

	'uint16': 6,
}

def readData(fobj, mrcmode, shape):
	'''
	Read data portion of MRC file from the file object fobj.
	Both mrcmode and shape have been determined from the MRC header.
	fobj already points to beginning of data, not header.
	Returns a new numpy ndarray object.
	'''
	try:
		elementsize = mrcitemsize[mrcmode]
	except KeyError:
		print 'Unknown MRC mode', mrcmode
		raise
	nelements = 1
	for x in shape:
		nelements *= x
	numtype = mrc2numpy[mrcmode]
	data = fobj.read(nelements * elementsize)
	narray = numpy.fromstring(data, numtype)
	if sys.byteorder != 'little':
		narray = narray.byteswapped()
	narray.shape = shape
	return narray

def newHeader(shape, mode):
	'''
	Creates a new MRC header dictionary.
	Shape and MRC mode must be specified.
	Everything else is filled in with defaults.
	'''
	header = {}
	nx = shape[1]
	ny = shape[0]
	nz = 1
	header['nx'] = shape[1]
	header['ny'] = shape[0]
	header['nz'] = 1
	header['mode'] = mode
	header['nxstart'] = 0
	header['nystart'] = 0
	header['nzstart'] = 0
	header['mx'] = nx
	header['my'] = ny
	header['mz'] = nz
	header['xlen'] = nx
	header['ylen'] = ny
	header['zlen'] = nz
	header['alpha'] = 90
	header['beta'] = 90
	header['gamma'] = 90
	header['mapc'] = 1
	header['mapr'] = 2
	header['maps'] = 3
	header['amin'] = 0
	header['amax'] = 0
	header['amean'] = 0
	header['origin_x'] = nx / 2.0 
	header['origin_y'] = ny / 2.0
	header['origin_z'] = nz / 2.0
	header['identstr'] = 'MAP '
	header['machstamp'] = 'DA'
	header['rms'] = 0
	header['nlabl'] = 0
	return header

def readHeader(fobj):
	'''
	Read the MRC header from the file object fobj.  fobj must point
	to the beginning of the MRC file.  The header is returned as a 
	dictionary.
	'''
	headstr = fobj.read(1024)
	header = {}
	## first chunk includes nx,ny,nz,type
	chunk = headstr[:16]
	nx,ny,nz,mode = struct.unpack('<4i', chunk)
	header['nx'] = nx
	header['ny'] = ny
	header['nz'] = nz
	header['mode'] = mode 

	chunk = headstr[16:40]
	nxstart,nystart,nzstart,mx,my,mz = struct.unpack('<6i', chunk)
	header['nxstart'] = nxstart
	header['nystart'] = nystart
	header['nzstart'] = nzstart
	header['mx'] = mx
	header['my'] = my
	header['mz'] = mz

	chunk = headstr[40:64]
	xlen,ylen,zlen,alpha,beta,gamma = struct.unpack('<6f', chunk)
	header['xlen'] = xlen
	header['ylen'] = ylen
	header['zlen'] = zlen
	header['alpha'] = alpha
	header['beta'] = beta
	header['gamma'] = gamma

	chunk = headstr[64:88]
	mapc,mapr,maps,amin,amax,amean = struct.unpack('<3i 3f', chunk)
	header['mapc'] = mapc
	header['mapr'] = mapr
	header['maps'] = maps
	header['amin'] = amin
	header['amax'] = amax
	header['amean'] = amean

	## Origin, File identifier ('MAP ') & machine stamp ('DA')
	chunk = headstr[196:214]
	ox,oy,oz,identstr,machstamp = struct.unpack('<3f 4s 2s', chunk)
	header['origin_x'] = ox
	header['origin_y'] = oy
	header['origin_z'] = oz
	header['identstr'] = identstr
	header['machstamp'] = machstamp

	# Density standard deviation
	chunk = headstr[216:220]
	header['rms'] = struct.unpack('1f', chunk)[0]

	# Number of labels and labels themselves ignored for now
	return header

def writeHeader(header, fobj):
	'''
	Giving an MRC header in the form of a dictionary, write it to
	the file object fobj.
	'''
	#### create a struct format string
	# first 28 byte chunk includes nx,ny,nz,mode,n[xyz]start
	dims = '<7i '
	# Then m[xyz] and [xyz]len,(both essentially n[xyz] again),
	# followed by alpha,beta,gamma, followed by map[crs]:
	mxyz = '3i 3f 3f 3i'
	# then min/max/mean
	stats = '3f '
	pad1 = '108x '
	# Origin, file identifier, machine stamp
	origin = '3f '
	ident =  '4s '
	stamp = '2s '
	pad2 = '2x '
	rms = '1f '
	## already done 16 + 60 + 12 + 120 + 12 = 220 bytes
	## pad the rest 1024 - 220 = 804
	pad3 = '804x'

	fmtstr = dims + mxyz + stats + pad1 + origin + ident + stamp + pad2 + rms + pad3

	headstr = struct.pack(fmtstr, 
		header['nx'], header['ny'], header['nz'], header['mode'], 
		header['nxstart'], header['nystart'], header['nzstart'], 
		header['mx'], header['my'], header['mz'],
		header['xlen'], header['ylen'], header['zlen'],
		header['alpha'], header['beta'], header['gamma'],
		header['mapc'], header['mapr'], header['maps'],
		header['amin'], header['amax'], header['amean'],
		header['origin_x'], header['origin_y'], header['origin_z'],
		header['identstr'], header['machstamp'], header['rms'] )

	fobj.write(headstr)

def writeData(a, fobj):
	'''
Write the numpy ndarray object to a file object.  This assumes that the
header has already been written and fobj points to immediately after the
header.
	'''
	if sys.byteorder != 'little':
		narray = narray.byteswapped()
	data = a.tostring()
	fobj.write(data)

def asMRCtype(a):
	'''
If necessary, convert a numpy ndarray to type that is compatible
with MRC.
	'''
	if not isinstance(a, numpy.ndarray):
		raise TypeError('Value must be a numpy array')

	t = str(a.dtype)
	if t in numpy2mrc:
		numtype = t
	else:
		raise TypeError('Invalid Numeric array type for MRC conversion: %s' % (t,))
	numtype = mrc2numpy[numpy2mrc[numtype]]
	narray = a.astype(numtype)
	return narray

def write(a, filename, header=None):
	'''
Write ndarray to a file
a = numpy ndarray to be written
filename = filename of MRC
header (optional) = dictionary of header parameters
	'''
	stats = arraystats.all(a)
	a = asMRCtype(a)
	mode = numpy2mrc[str(a.dtype)]
	h = newHeader(a.shape, mode)
	if header is not None:
		h.update(header)

	h['amin'] = stats['min']
	h['amax'] = stats['max']
	h['amean'] = stats['mean']
	h['rms'] = stats['std']

	f = open(filename, 'w')
	writeHeader(h, f)
	writeData(a, f)
	f.close()

def read(filename):
	'''
Read the MRC file given by filename, return numpy ndarray object
	'''
	f = open(filename)
	readHeader
	h = readHeader(f)
	mode = h['mode']
	shape = h['ny'], h['nx']
	a = readData(f, mode, shape)
	return a

mmaps = weakref.WeakValueDictionary()

def mmap(filename):
	'''
Open filename as a memory mapped MRC file.  The returned object is
a numpy ndarray object wrapped around the memory mapped file.
	'''
	mrc = numpy.memmap(name=filename, mode='r')

	# get dimensions of image from header
	mrcdims_slice = mrc[:12]
	mrcdims = numpy.ndarray(buffer=mrcdims_slice, shape=(3,), dtype=numpy.int32)
	c,r,s = mrcdims
	if s < 2:
		numshape = r,c
	else:
		numshape = s,r,c
	
	# get data type from header
	mrctype_slice = mrc[12:16]
	mrctype = numpy.ndarray(buffer=mrctype_slice, shape=(1,), dtype=numpy.int32)
	mrctype = mrctype[0]
	numtype = mrc2numpy[mrctype]
	
	## !!! assuming this is 2-D MRC only
	mrcdata_slice = mrc[1024:]
	mrcdata = numpy.ndarray(buffer=mrcdata_slice, shape=numshape, dtype=numtype)
	# hold reference to open memmap so it doesn't close
	mmaps[mrc] = mrcdata
	return mrcdata


if __name__ == '__main__':
	infilename = sys.argv[1]
	outfilename = sys.argv[2]

	a = read(infilename)
	a = a.astype(numpy.uint16)
	h = {}
	h['amean'] = a.mean()
	h['amin'] = a.min()
	h['amax'] = a.max()
	h['rms'] = a.std()
	write(a, outfilename, header=h)

