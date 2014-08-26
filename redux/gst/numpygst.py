#!/usr/bin/env python

'''
Various objects and functions to be used to pass numpy ndarray objects
between gst elements.
'''

import numpy
import gst
import sys
import operator

# this is not an official mime type, I just made it up
ndarray_mimetype = 'application/x-ndarray'

def print_caps(caps):
	for cap in caps:
		print '===================================================='
		print cap.get_name()
		for key in cap.keys():
			print '  %s:  %s' % (key, cap[key])
		print '===================================================='

## Caps to use in pad template for an element that converts to/from ndarray.
## These are types that can easily convert to ndarray through buffer interface.
## see:  http://gstreamer.freedesktop.org/data/doc/gstreamer/head/pwg/html/section-types-definitions.html
## 
## application/x-ndarray
##   ...
##
## video/x-raw-yuv
##   format(fourcc)
##   width
##   height
##
## video/x-raw-rgb
##   ...
def caps_ndarray():
	caps = gst.Caps(ndarray_mimetype)
	return caps

def caps_new_from_description(shape, dtype):
	if len(shape) != 2:
		raise ValueError('Bad shape: %s.  This only works with 2-D numpy arrays.' % (shape,))
	shape0, shape1 = shape
	caps = gst.Caps(
		ndarray_mimetype,
		shape0=shape0,
		shape1=shape1,
		dtype_num=dtype.num,
		dtype_byteorder=dtype.byteorder
		)
	return caps

def caps_new_from_ndarray(a):
	shape = a.shape
	dtype = a.dtype
	caps = caps_new_from_description(shape, dtype)
	return caps

def ndarray_from_gst_buffer(buf):
	'''wrap ndarray around any gst buffer that is compatible'''
	## Inspect caps to determine ndarray shape and dtype.
	cap = buf.get_caps()[0]
	mimetype = cap.get_name().split('/')
	if mimetype[0] == 'video':
		shape = [cap['height'],cap['width']]
		if mimetype[1] == 'x-raw-rgb':

			bpp = cap['bpp']
			bytespp = bpp / 8
			rgb_depth = cap['depth']
			if rgb_depth != 24:
				raise ValueError('unsupported depth: %s.  must be 24' % (rgb_depth,))
			if bpp == rgb_depth:
				# RGB
				channels = [None,None,None]
			else:
				# RGBA
				channels = [None,None,None,None]

			endianness = cap['endianness']
			if endianness == 4321:
				endianness = 'big'
				mask_type = '>i4'
				significant = slice(4-bytespp,4)
			else:
				endianness = 'little'
				mask_type = '<i4'
				significant = slice(0,bytespp)

			## byte position of R,G,B channels within each pixel
			for channel in ('red','green','blue'):
				mask = numpy.array([cap[channel+'_mask']], mask_type)
				mask = mask.view(numpy.uint8) # split the bytes
				mask = mask[significant] # reduce from 4 bytes to size of pixel
				pos = mask.argmax() # assuming mask is all zeros and one 255
				channels[pos] = channel
			## if 4th channel, it is alpha or undefined
			if len(channels) == 4:
				pos = channels.index(None)
				if cap.has_key('alpha_mask'):
					channels[pos] = 'alpha'
				else:
					channels[pos] = 'X'

			## make the dtype for a pixel
			dtype = numpy.dtype({
				'names': channels,
				'formats': len(channels) * ['u1']
			})

		elif mimetype[1] == 'x-raw-yuv':
			pass

	bufarray = numpy.frombuffer(buf.data, dtype)
	bufarray.shape = shape
	return bufarray

def gst_buffer_from_ndarray(ndarray):
	'''
	Wrap a gst buffer object around the given ndarray object.
	The input must be a 2-D record array.  dtype should define the fields:
	 "red", "green", "blue" and optionally "alpha".  The type of the 
	fields must be uint8.
	'''
	width = ndarray.shape[1]
	height = ndarray.shape[0]
	print 'WIDTHHEIGHT', width,height

	dtype = ndarray.dtype

	## must at least have 'red','green','blue' fields to be RGB image
	required_fields = ('red','green','blue')
	hasrgb = reduce(operator.and_, map(dtype.fields.__contains__, required_fields))
	if not hasrgb:
		raise ValueError('array must have at least fields: %s' % (required_fields,))

	## fields must all be uint8 (dtype.char == 'B')
	hasbytes = reduce(operator.and_, [desc[0].char == 'B' for desc in dtype.fields.values()])
	if not hasbytes:
		raise ValueError('all fields in array records must be uint8')

	mimetype = 'video/x-raw-rgb'
	buffer_endianness = 'big'
	mask_type = '>i4'

	nfields = len(dtype.fields)
	channels = filter(dtype.fields.__contains__, ('red','green','blue','alpha'))

	## only going to deal with 8 bit channels
	bytespp = len(channels)
	bpp = 8 * bytespp
	rgb_depth = 24
	if buffer_endianness == 'big':
		offset = 4 - bytespp
	else:
		offset = 0

	# create channel masks for Caps
	masks = {}
	for channel in channels:
		mask = numpy.zeros(4, dtype=numpy.uint8)
		pos = dtype.fields[channel][1]
		mask[pos+offset] = 255
		mask = mask.view(mask_type)
		mask = int(mask[0])
		masks[channel+'_mask'] = mask

	## make caps based on type of array
	if buffer_endianness == 'big':
		endianness = 4321
	elif buffer_endianness == 'little':
		endianness = 1234
	#caps = gst.caps_new_simple(mimetype, width=width, height=height, framerate=gst.Fraction(0), bpp=bpp, depth=rgb_depth, endianness=endianness, **masks)
	caps = gst.Caps(mimetype)
	cap = caps[0]
	cap['width'] = 182
	cap['height'] = 126
	cap['framerate'] = gst.Fraction(0)
	cap['bpp']=bpp
	cap['depth']=rgb_depth
	cap['endianness'] = endianness
	for key,value in masks.items():
		cap[key] = value

	print 'NEW BUFFER CAPS'
	print_caps(caps)
	print ''

	# make buffer and attach array data and new caps
	buf = gst.Buffer(ndarray.data)
	buf.set_caps(caps)

	return buf

if __name__ == '__main__':
	pass
