#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

try:
	import numarray as Numeric
except:
	import Numeric
import array
import struct
import sys
import cStringIO
import arraystats

## MRC supported types
mrcmode_type = {
	0: (1, Numeric.UInt8),
	1: (2, Numeric.Int16),
	2: (4, Numeric.Float32),
	3: (8, Numeric.Complex32),
	6: (2, Numeric.UInt16),
}
type_mrcmode = {
	Numeric.UInt8: 0,
	Numeric.Int16: 1,
	Numeric.Float32: 2,
	Numeric.Complex32: 3,
	Numeric.UInt16: 6,
}

## MRC is lame because it only supports a few of the C types
## The following allows other C types to be converted to 
## MRC supported types by up/down casting.
unsupported_types = {
	Numeric.Complex64: Numeric.Complex32, # precision loss
	Numeric.Float64:   Numeric.Float32,   # precision loss
	Numeric.Int32:     Numeric.Float32,   # precision loss
	Numeric.Int:       Numeric.Float32,   # precision loss
	Numeric.Int8:      Numeric.Int16,     # 1 byte wasted
	Numeric.Bool:      Numeric.UInt8,     # 1 byte wasted
}

def mrc_to_numeric(filename):
	f = open(filename, 'rb')
	image = mrc_read(f)
	f.close()
	return image

def numeric_to_mrc(ndata, filename):
	if not isinstance(ndata, Numeric.ArrayType):
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
	if not isinstance(ndata, Numeric.ArrayType):
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
		self.nx = None
		self.ny = None
		self.nz = None
		self.mode = None
		self.nxstart = None
		self.nystart = None
		self.nzstart = None
		self.mx = None
		self.my = None
		self.mz = None
		self.xlen = None
		self.ylen = None
		self.zlen = None
		self.alpha = 90.0
		self.beta = 90.0
		self.gamma = 90.0
		self.mapc = 1
		self.mapr = 2
		self.maps = 3
		self.amin = None
		self.amax = None
		self.amean = None
		self.origin_x = None
		self.origin_y = None
		self.origin_z = None
		self.identstr = 'MAP '
		## as with toNumeric (below) we use little endian as standard
		self.machstamp = 'DA'
		self.nlabl = 0


	def useheader(self, head):
		self.describe(head['nx'], head['ny'], head['nz'], head['mode'], head['amin'], head['amax'], head['amean'], head['rms'], head['identstr'], head['machstamp'])

	def describe(self, nx, ny, nz, mode, amin, amax, amean, rms, identstr, machstamp):
		self.nx = nx
		self.ny = ny
		self.nz = nz
		self.mode = mode
		self.nxstart = 0
		self.nystart = 0
		self.nzstart = 0
		self.mx = self.nx
		self.my = self.ny
		self.mz = self.nz
		self.xlen = self.nx
		self.ylen = self.ny
		self.zlen = self.nz
		self.origin_x = nx / 2.0
		self.origin_y = ny / 2.0
		self.origin_z = nz / 2.0
		self.amin = amin
		self.amax = amax
		self.amean = amean
		self.identstr = identstr
		self.machstamp = machstamp
		self.rms = rms

	def fromfile(self, fobj):
		try:
			elementsize = mrcmode_type[self.mode][0]
		except KeyError:
			print 'Unknown MRC mode', self.mode
			raise
		elements = self.nx * self.ny * self.nz
		self.data = fobj.read(elements * elementsize)

	def tofile(self, fobj):
		fobj.write(self.data)

	def toNumeric(self):
		numtype = mrcmode_type[self.mode][1]
		narray = Numeric.fromstring(self.data, numtype)
		## for now, using little endian as standard
		if sys.byteorder != 'little':
			narray = narray.byteswapped()

		## reshape based on my description
		if self.ny < 2 and self.nz < 2:
			shape = (self.nx, )
		elif self.nz < 2:
			shape = (self.ny, self.nx)
		else:
			shape = (self.nz, self.ny, self.nx)
		narray.shape = shape

		return narray

	def fromNumeric(self, narray):
		if not isinstance(narray, Numeric.ArrayType):
			raise TypeError('Value must be a Numeric array')

		t = narray.type()
		if t in type_mrcmode:
			numtype = t
		elif t in unsupported_types:
			numtype = unsupported_types[t]
			narray = Numeric.asarray(narray, numtype)
		else:
			raise TypeError('Invalid Numeric array type for MRC conversion: %s' % (t,))

		self.mode = type_mrcmode[numtype]

		## get my description from Numeric shape
		shape = narray.shape
		if len(shape) == 1:
			# x data only
			self.nx = shape[0]
			self.ny = 1
			self.nz = 1
		elif len(shape) == 2:
			# x,y data
			self.ny = shape[0]
			self.nx = shape[1]
			self.nz = 1
		elif len(shape) == 3:
			# x,y,z data
			self.nz = shape[0]
			self.ny = shape[1]
			self.nx = shape[2]
		else:
			raise 'unsupported'

		stats = arraystats.all(narray)
		self.amin = stats['min']
		self.amax = stats['max']
		self.amean = stats['mean']
		self.rms = stats['std']

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
		self['nx'] = mrcdata.nx
		self['ny'] = mrcdata.ny
		self['nz'] = mrcdata.nz
		self['mode'] = mrcdata.mode
		self['nxstart'] = mrcdata.nxstart or 0
		self['nystart'] = mrcdata.nystart or 0
		self['nzstart'] = mrcdata.nzstart or 0
		self['mx'] = mrcdata.mx or mrcdata.nx
		self['my'] = mrcdata.my or mrcdata.ny
		self['mz'] = mrcdata.mz or mrcdata.nz
		self['xlen'] = mrcdata.xlen or mrcdata.nx
		self['ylen'] = mrcdata.ylen or mrcdata.ny
		self['zlen'] = mrcdata.zlen or mrcdata.nz
		self['alpha'] = mrcdata.alpha or 90
		self['beta'] = mrcdata.beta or 90
		self['gamma'] = mrcdata.gamma or 90
		self['mapc'] = mrcdata.mapc or 1
		self['mapr'] = mrcdata.mapr or 2
		self['maps'] = mrcdata.maps or 3
		self['amin'] = mrcdata.amin or 0
		self['amax'] = mrcdata.amax or 0
		self['amean'] = mrcdata.amean or 0
		self['origin_x'] = mrcdata.origin_x or mrcdata.nx / 2.0 
		self['origin_y'] = mrcdata.origin_y or mrcdata.ny / 2.0
		self['origin_z'] = mrcdata.origin_z or mrcdata.nz / 2.0
		self['identstr'] = mrcdata.identstr
		self['machstamp'] = mrcdata.machstamp
		self['rms'] = mrcdata.rms or 0
		self['nlabl'] = mrcdata.nlabl or 0

	def fromstring(self, headstr):
		"get data from a string representation of MRC header"

		## first chunk includes nx,ny,nz,type
		chunk = headstr[:16]
		nx,ny,nz,mode = struct.unpack('<4i', chunk)
		self['nx'] = nx
		self['ny'] = ny
		self['nz'] = nz
		self['mode'] = mode 

		chunk = headstr[16:40]
		nxstart,nystart,nzstart,mx,my,mz = struct.unpack('<6i', chunk)
		self['nxstart'] = nxstart
		self['nystart'] = nystart
		self['nzstart'] = nzstart
		self['mx'] = mx
		self['my'] = my
		self['mz'] = mz

		chunk = headstr[40:64]
		xlen,ylen,zlen,alpha,beta,gamma = struct.unpack('<6f', chunk)
		self['xlen'] = xlen
		self['ylen'] = ylen
		self['zlen'] = zlen
		self['alpha'] = alpha
		self['beta'] = beta
		self['gamma'] = gamma

		chunk = headstr[64:88]
		mapc,mapr,maps,amin,amax,amean = struct.unpack('<3i 3f', chunk)
		self['mapc'] = mapc
		self['mapr'] = mapr
		self['maps'] = maps
		self['amin'] = amin
		self['amax'] = amax
		self['amean'] = amean

		## Origin, File identifier ('MAP ') & machine stamp ('DA')
		chunk = headstr[196:214]
		ox,oy,oz,identstr,machstamp = struct.unpack('<3f 4s 2s', chunk)
		self['origin_x'] = ox
		self['origin_y'] = oy
		self['origin_z'] = oz
		self['identstr'] = identstr
		self['machstamp'] = machstamp

		# Density standard deviation
		chunk = headstr[216:220]
		self['rms'] = struct.unpack('1f', chunk)

		# Number of labels and labels themselves ignored for now

	def tostring(self):
		"create string representation of header data"

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
			self['nx'], self['ny'], self['nz'], self['mode'], 
			self['nxstart'], self['nystart'], self['nzstart'], 
			self['mx'], self['my'], self['mz'],
			self['xlen'], self['ylen'], self['zlen'],
			self['alpha'], self['beta'], self['gamma'],
			self['mapc'], self['mapr'], self['maps'],
			self['amin'], self['amax'], self['amean'],
			self['origin_x'], self['origin_y'], self['origin_z'],
			self['identstr'], self['machstamp'], self['rms'] )
		return headstr

	def fromfile(self, fobj):
		headstr = fobj.read(self.headerlen)
		self.fromstring(headstr)

	def tofile(self, fobj):
		headstr = self.tostring()
		fobj.write(headstr)

if __name__ == '__main__':
	filename = 'test1.mrc'
	fileout  = 'test2.mrc'
	f = open(filename)
	h = MrcHeader(f)
	print h.data

	f.seek(0)
	im = mrc_read(f)

	g = open(fileout,'w')
	mrc_write(g,im)
	f.close()
	g.close()

	g = open(fileout)
	h = MrcHeader(g)
	print h.data
	g.close()
