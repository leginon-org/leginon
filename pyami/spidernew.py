#!/usr/bin/env python

import numpy

'''
Spider I/O functions based on docs at:
	http://www.wadsworth.org/spider_doc/spider/docs/image_doc.html
'''

class InvalidSpiderHeader(Exception):
	pass

def make_header_dtype(endianness='>'):
	'''
	This creates a numpy dtype that allows parsing the Spider
	header into a numpy record object.  You must choose either
	big endian ('>') or little endian ('<').
	'''
	ftype = '%sf4' % (endianness,)
	header_dtype = [
		('NSLICE', ftype),       # 1
		('NROW', ftype),         # 2
		('IREC', ftype),         # 3
		('', ftype),             # 4
		('IFORM', ftype),        # 5
		('IMAMI', ftype),        # 6
		('FMAX', ftype),         # 7
		('FMIN', ftype),         # 8
		('AV', ftype),           # 9
		('SIG', ftype),          # 10
		('', ftype),             # 11
		('NSAM', ftype),         # 12
		('LABREC', ftype),       # 13
		('IANGLE', ftype),       # 14
		('PHI', ftype),          # 15
		('THETA', ftype),        # 16
		('GAMMA', ftype),        # 17
		('XOFF', ftype),         # 18
		('YOFF', ftype),         # 19
		('ZOFF', ftype),         # 20
		('SCALE', ftype),        # 21
		('LABBYT', ftype),       # 22
		('LENBYT', ftype),       # 23
		('ISTACK', ftype),       # 24
		('', ftype),             # 25
		('MAXIM', ftype),        # 26
		('IMGNUM', ftype),       # 27
		('LASTINDX', ftype),     # 28
		# ... remainder into a raw buffer
		('remainder', 'V912')    # 4*(256-28)=912
	]
	return header_dtype

# The IFORM field of the header contains one of these codes
iform_codes = {
	1.0: '2D image',
	3.0: '3D volume',
	-11.0: '2D Fourier, odd',
	-12.0: '2D Fourier, even',
	-21.0: '3D Fourier, odd',
	-22.0: '3D Fourier, even',
}

def validate_header(header_array):
	'''
	Required fields according to doc:  1,2,5,12,13,22,23 (indexed from 1).
	These are:  NSLICE, NROW, IFORM, NSAM, LABREC, LABBYT, LENBYT.
	Here we check if those required values make sense.
	If problems are found, InvalidSpiderHeader is raised.
	'''
	## check if they are integers
	for key in ('NSLICE', 'NROW', 'IFORM', 'NSAM', 'LABREC', 'LABBYT', 'LENBYT'):
		flt_val = header_array[key]
		int_val = int(flt_val)
		if flt_val != int_val:
			raise InvalidSpiderHeader('%s=%e is not an integer value.' % (key, flt_val))
	if header_array['IFORM'] not in iform_codes:
		raise InvalidSpiderHeader('IFORM=%e not in %s' % (header_array['IFORM'], iform_codes.keys()))
	if (4*header_array['NSAM']) != header_array['LENBYT']:
		raise InvalidSpiderHeader('NSAM=%(NSAM)e, LENBYT=%(LENBYT)e ... Fails LENBYT == 4*NSAM' % header_array)
	if (4*header_array['NSAM']*header_array['LABREC']) != header_array['LABBYT']:
		raise InvalidSpiderHeader('NSAM=%(NSAM)e, LABREC=%(LABREC)e, LABBYT=%(LABBYT)e ... Fails LABBYT == 4*NSAM*LABREC' % header_array)

def header_fromfile(f, endianness):
	dt = make_header_dtype(endianness)
	a = numpy.fromfile(f, dtype=dt, count=1)[0]
	return a

def header_byteorder(header_array):
	'''
	return '>' or '<' depending on byte order of the given header array
	'''
	return header_array.dtype.fields['NSLICE'][0].byteorder

def position_of(master_header, header_or_data, slice=None):
	'''
	Determine byte offset of slice header or data within a Spider file.
	You must give this function the master header, "header" or "data",
	and which slice.  For a single image non-stack file, slice indicates
	which z slice of a 3-D image or set it to None to get the start pos.
	'''
	if header_or_data not in ('header', 'data'):
		raise ValueError('header_or_data must be "header" or "data')

	headerlen = master_header['LABBYT']

	# indexed stack
	if master_header['ISTACK'] < 0:
		raise NotImplementedError('Spider indexed stack not supported')

	# single image file
	elif master_header['ISTACK'] == 0.0:
		if header_or_data == 'header':
			if slice:
				raise ValueError('slice=%s not valid in single Spider image file' % (master_header['ISTACK'],))
			else:
				pos = 0
		else:
			if slice:
				if slice >= master_header['NSLICE']:
					raise ValueError('slice=%s invalid for this image' % (slice,))
				pos = headerlen + slice * master_header['NROW'] * master_header['LENBYT']
			else:
				pos = headerlen

	# stack
	elif master_header['ISTACK'] > 0:
		if slice is None or slice >= master_header['MAXIM']:
			raise ValueError('slice=%s invalid for this image' % (slice,))
		datalen = master_header['NSLICE'] * master_header['NROW'] * master_header['LENBYT']
		pos = headerlen + slice * (headerlen + datalen)
		if header_or_data == 'data':
			pos += headerlen

	return int(pos)

def shape_of(header):
	'''
	Using info in the header, return the image shape (could be 2-D or 3-D).
	'''
	zlen = header['NSLICE']
	# from doc: "In some ancient 2D images this may be -1"
	if zlen < 1:
		zlen = 1
	shape = zlen, int(header['NROW']), int(header['NSAM'])
	return shape

def read_header(f, slice=None):
	'''
	Read a spider header into a numpy record data type.
	If slice is given, return the header for the particular slice.
	Otherwise, return the master header.
	After the read, file position will be immediately after the 1024 byte
	header, not including any additional header padding that may be added.
	ie. you will probably not be positioned at the start of image data!
	'''

	if not hasattr(f, 'tell'):
		f = open(f)

	# determine start position of header
	if slice is None:
		startpos = 0
	else:
		# get master header first to determine offset of other headers
		master_header = read_header(f)
		startpos = position_of(master_header, 'header', slice)

	f.seek(startpos)
	a = header_fromfile(f, '<')
	try:
		validate_header(a)
	except InvalidSpiderHeader:
		# return to start of header before retry
		f.seek(startpos)
		a = header_fromfile(f, '>')
		validate_header(a)
	return a

def header_dict(header_array):
	'''
	Normally you can use a header array like a dictionary, accessing fields
	by name.  When you need a true dictionary, use this to do the conversion.
	'''
	header_dict = dict(zip(header_array.dtype.names,header_array.tolist()))
	return header_dict

def read_info(filename, slice=None):
	header = read_header(filename, slice)
	header_dict = dict(zip(header.dtype.names,header.tolist()))
	return header_dict

def read(filename, slice=None):
	master_header = read_header(filename)
	byteorder = header_byteorder(master_header)
	dt = '%sf4' % (byteorder,)
	startpos = position_of(master_header, 'data', slice)
	shape = shape_of(master_header)
	if shape[0] == 1 or (master_header['ISTACK'] == 0.0 and slice is not None):
		shape = shape[1:]  # 2-D only
	count = numpy.product(shape)
	fobj = open(filename)
	fobj.seek(startpos)
	a = numpy.fromfile(fobj, dtype=dt, count=count)
	a.shape = shape
	return a

def test():
	import sys
	filename = sys.argv[1]
	header = read_header(filename)
	print header

def test2():
	import sys
	import pyami.numpil
	filename = sys.argv[1]
	z = int(sys.argv[2])
	a = read(filename, z)
	pyami.numpil.write(a, format='PNG')  # stdout, pipe it to display!!!

def test3():
	import sys
	filename = sys.argv[1]
	d = read_info(filename)
	print 'MAXIM', d['MAXIM']
	print 'IMGNUM', d['IMGNUM']
	print 'IMAMI', d['IMAMI']
	print 'FMAX', d['FMAX']
	print 'FMIN', d['FMIN']
	print 'AV', d['AV']
	print 'SIG', d['SIG']
	print 'remainder', type(d['remainder'])

if __name__ == '__main__':
	test3()
