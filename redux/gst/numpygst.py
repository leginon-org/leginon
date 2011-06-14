#!/usr/bin/env python

'''
Various objects and functions to be used to pass numpy ndarray objects
between gst elements.
'''

import numpy
import gst

# this is not an official mime type, I just made it up
ndarray_mimetype = 'application/x-ndarray'

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
		shape = []
		if mimetype[0] == 'video':
			shape.append(cap['width'])
			shape.append(cap['height'])
			if mimetype[1] == 'x-raw-rgb':

				bpp = cap['bpp']
				rgb_depth = cap['depth']
				if rgb_depth != 24:
					raise ValueError('unsupported depth: %s.  must be 24' % (rgb_depth,))
				if bpp == rgb_depth:
					shape.append(3) # RGB
				else:
					shape.append(4) # RGB plus something else

				endianness = cap['endianness']
				if endianness == 1234:
					raise ValueError('little endian not supported')
				elif endianness == 4321:
					endianchar = '>'

				## determine the order of R,G,B channels, from 'red_mask', etc
				int_type = '%su4' % (endianchar,)

				## byte position of R,G,B,A channels within each pixel
				channel_positions = {}
				for channel in ('red','green','blue','alpha'):
					try:
						mask = numpy.array(cap[channel+'_mask'], 'i4')
					except KeyError:
						continue
					mask = mask.view(numpy.uint8)
					for pos in range(4):
						if mask[pos] == 255:
							channel_position[channel] = pos

			elif mimetype[1] == 'x-raw-yuv':
				pass

		print 'depth', cap['depth']
		print 'endianness', cap['endianness']
		# keys:  ['width', 'height', 'bpp', 'framerate', 'depth', 'endianness', 'red_mask', 'green_mask', 'blue_mask']
		print 'DATA'
		print type(buf.data)
		print dir(buf.data)
		print 'LEN', len(buf.data)
		print ''

		dt = numpy.dtype(numpy.uint8)
		input_array = numpy.frombuffer(buf.data, dt)
		bytes_per_pixel = bpp / 8
		input_shape = height, width, bytes_per_pixel
		print 'INPUT SHAPE', input_shape
		input_array.shape = input_shape

class

def test_mask():
	test = numpy.array((0,255,0,0), dtype=numpy.uint8)
	test = test.view('<u4')
	for i in range(4):
		ref = numpy.zeros(4, dtype=numpy.uint8)
		ref[i] = 255
		ref = ref.view('<u4')
		print 'TEST', test
		print 'REF', ref
		print '&', numpy.bitwise_and(test, ref)

	return

	reference = numpy.array((255,0,0,0), dtype=numpy.uint8)
	reflittle = reference.view('<u4')
	refbig = reference.view('>u4')
	print 'REFS', reference, reflittle, refbig

	buf = numpy.newbuffer(4)
	big = numpy.frombuffer(buf, dtype='>u4')
	little = numpy.frombuffer(buf, dtype='<u4')
	char = numpy.frombuffer(buf, dtype=numpy.uint8)
	char.shape = 4,1
	big[0] = 0
	print 'big', big, 'little', little
	print numpy.unpackbits(char, 1)

	big[0] = 0xff
	print 'big', big, 'little', little
	print numpy.unpackbits(char, 1)

	#big[0] <<= 8
	little[0] >>= 8
	print 'big', big, 'little', little
	print numpy.unpackbits(char, 1)


if __name__ == '__main__':
	test_mask()
