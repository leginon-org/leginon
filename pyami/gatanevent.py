#!/usr/bin/env python
import numpy
from pyami import weakattr

## structure of Gatan CELTIC/K3F event file 
## This is a sequence of fields where each field is defined by a sequence:
##  (name, type, default, length)
##    length in bytes is only necessary for strings
##    type can be one of: numpy dtype and python type 'string'
##  ** maybe look into something like http://construct.wikispaces.com/
header_fields = (
	('magic_header', 'string', 4),
	('header_size', 'int32'),
	('file_version', 'int32'),
	('event_encoding_version', 'int32'),
	('frame_width', 'int32'),
	('frame_height', 'int32'),
)
frame_data_header_fields = (
	('frame_start_marker', 'string', 4),
	('frame_id', 'int32'),
	('event_count', 'int32'),
)
frame_data_location_fields = (
	('x', 'int16'),
	('y', 'int16'),
)

def zeros(n):
	'''
Create n bytes of data initialized to zeros, returned as a python bytes.
	'''
	return bytes(n)

def _parseHeader(headerbytes, my_header_fields):
	headerarray = {}
	byte_count = len(headerbytes)
	## create an array of int32 to make it easier to designate.
	itype = numpy.dtype('int32')
	headerarray['int32'] = numpy.frombuffer(headerbytes, dtype=itype)
	## fill in header dictionary with all the info
	newheader = {}
	pos = 0
	for field in my_header_fields:
		name = field[0]
		ftype = field[1]
		if ftype == 'string':
			length = field[2]
			full_string = headerbytes[pos:pos+length]
			newheader[name] = full_string
		else:
			length = 4
			word = pos//4
			newheader[name] = headerarray[ftype][word]
		pos += length
	return newheader

def parseHeader(headerbytes):
	'''
	Parse the file header into a header dictionary.
	'''
	return _parseHeader(headerbytes, header_fields)

def read_file_header(filename):
	'''
	get K3F event header from a file in the form of a dict
	'''
	f = open(filename, 'rb')
	# get header length
	f.seek(4,0)
	headerbytes = f.read(4)
	itype = numpy.dtype('int32')
	header_length = numpy.frombuffer(headerbytes, dtype=itype, count=1)[0]
	f.seek(0,0)
	# read and parse the header
	headerbytes = f.read(header_length)
	return parseHeader(headerbytes)

def parseFrameHeader(headerbytes):
	'''
	Parse the frame header into a header dictionary.
	'''
	return _parseHeader(headerbytes, frame_data_header_fields)

def readEventLocations(eventbytes, event_count):
	event_count
	## header is comprised of int32
	itype = numpy.dtype('int16')
	locationarray = numpy.frombuffer(eventbytes, dtype=itype)
	return locationarray.reshape((event_count,2))

def readRenderedFrameFromFileObject(fobj, headerdict, endbytes, frame_start=0, nframe_to_sum=10):
	'''
	Read a slice of data of event file from the file object fobj.
	fobj cursor should be at start of a frame header.
	Returns a new numpy two-dimensional ndarray object.
	nframe_to_sum is the number of frames integrated into the slice
	'''
	# row, col as in numpy
	shape = headerdict['frame_height'], headerdict['frame_width']
	sum_array = numpy.zeros(shape, dtype=numpy.int16) # use int16 for now.
	bytes_per_pixel = 4
	if frame_start > 0:
		for skip_i in range(frame_start):
			frame_headerbytes = fobj.read(12)
			frame_headerdict = parseFrameHeader(frame_headerbytes)
			# There are some bytes at the end with invalid frame header that translated
			# to int32 as [-1 -1 -1]
			if frame_headerdict['event_count'] < 0:
				raise ValueError('skipping to frame %d is not possible because data has ended before ' % skip_i)
			event_count = frame_headerdict['event_count']
			fobj.seek(event_count*4+8, 1)
	# read frames
	for j in range(nframe_to_sum):
			# read next 12 bytes as frame header
			frame_headerbytes = fobj.read(12)
			frame_headerdict = parseFrameHeader(frame_headerbytes)
			event_count = frame_headerdict['event_count']
			# There are some bytes at the end with invalid frame header that translated
			# to int32 as [-1 -1 -1]
			if event_count <= 0:
				#in complete number of frames to construct the z-slice.
				break
			eventbytes = fobj.read(event_count*4)
			event_locations = readEventLocations(eventbytes, event_count)
			locations = event_locations.tolist()
			for r,c in locations:
				sum_array[r][c] += 1
			frame_footerbytes = fobj.read(8)
	return sum_array

def setHeader(a, headerdict):
	"""
	Attach file header to the array.
	"""
	weakattr.set(a, 'celticheader', headerdict)

def get_number_of_frames(filename):
	"""
	Return number of the valid frames in the file.
	"""
	headerdict = read_file_header(filename)
	f = open(filename, 'rb')
	endbytes = f.seek(0,2)
	f.seek(0,0)
	f.seek(24)
	i = 0
	while endbytes - f.tell() > 20:
		frame_headerbytes = f.read(12)
		frame_headerdict = parseFrameHeader(frame_headerbytes)
		event_count = frame_headerdict['event_count']
		i += 1
		if event_count < 0 or endbytes -f.tell() < event_count*4+8:
			break
		f.seek(event_count*4+8, 1)
	f.close()
	return i

def get_endbytes(filename):
	"""
	Seek the end of the file.
	"""
	f = open(filename, 'rb')
	endbytes = f.seek(0,2)
	f.close()
	return endbytes

def read(filename, slice_z=0, nframe_to_sum=10):
	"""
	Return rendered frame starting at slice_z value after rendering.
	nframe_to_sum is the number of frames used to render the output frame.
	"""
	endbytes = get_endbytes(filename)
	headerdict = read_file_header(filename)
	f = open(filename, 'rb')
	f.seek(24) # skip header
	#
	frame_start = slice_z * nframe_to_sum
	a = _readRenderedFrameFromFileObject(f, headerdict, endbytes, frame_start, nframe_to_sum)
	f.close()
	## store keep header with image
	setHeader(a, headerdict)
	return a
