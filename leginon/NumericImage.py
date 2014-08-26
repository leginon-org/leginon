#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from wx import EmptyImage
from PIL import Image
import numpy
import math
import sys
import time
from pyami import imagefun

## (numpy dtype,size) => (PIL mode,  PIL rawmode)
ntype_itype = {
	(numpy.uint8,1) : ('L','L'),
	(numpy.int16,2) : ('I','I;16NS'),
	(numpy.int,2) : ('I','I;16NS'),
	(numpy.int,4) : ('I','I;32NS'),
	(numpy.int32,4) : ('I','I;32NS'),
	(numpy.float,4) : ('F','F;32NF'),
	(numpy.float,8) : ('F','F;64NF'),
	(numpy.float32,4) : ('F','F;32NF'),
	(numpy.float64,8) : ('F','F;64NF')
	}

def numpy2PILImage(numericarray, scale=False):
	if scale:
		numericarray = imagefun.linearscale(numericarray, (None, None), (0, 255)).astype(numpy.uint8)
	type = numericarray.dtype
	h, w = numericarray.shape
	imsize = w, h
	itemsize = numericarray.itemsize()
	immode = ntype_itype[type.type, itemsize][0]
	rawmode = ntype_itype[type.type, itemsize][1]
	nstr = numericarray.tostring()
	return Image.fromstring(immode, imsize, nstr, 'raw', rawmode, 0, 1)

def numpy2wxImage(numericarray):
	image = numpy2PILImage(numericarray)
	wximage = EmptyImage(image.size[0], image.size[1])
	wximage.SetData(image.convert('RGB').tostring())
	return wximage

# resize and rotate filters:  NEAREST, BILINEAR, BICUBIC

def resize(pil_image, size):
	if size:
		if size != pil_image.size:
			new_image = pil_image.resize(size, Image.NEAREST)
		else:
			new_image = pil_image
	else:
		new_image = pil_image
	return new_image

class NumericImage:
	"""
	NumericImage couples a numpy array with a PIL Image instance.
	"""
	def __init__(self, orig_array, clip=(None,None), output_size=None):
		self.transform = {'clip':clip, 'output_size':output_size}
		self.__use_numeric(orig_array)

	def __setitem__(self, key, value):
		if key not in self.transform.keys():
			raise KeyError, 'key must be one of: ' + `self.transform.keys()`
		self.transform[key] = value

	def __use_numeric(self, num_data):
		shape = num_data.shape
		if len(shape) != 2:
			raise RuntimeError, 'orig_array must be 2-D numpy array'
		## experimenting with clipping to eliminate infinity
		#self.orig_array = numpy.clip(num_data, -10000, 10000)
		self.orig_array = num_data

		h,w = shape  # transpose numpy array
		self.orig_size = w,h

		### if output size and clip are not set, use defaults
		if not self.transform['output_size']:
			self.transform['output_size'] = self.orig_size

		flat = numpy.ravel(self.orig_array)
		extmin = numpy.argmin(flat)
		extmax = numpy.argmax(flat)
		minval = flat[extmin]
		maxval = flat[extmax]
		self.extrema = (minval, maxval)
		if not self.transform['clip']:
			self.transform['clip'] = self.extrema

	def get_crvalue(self, col_row):
		try:
			val = self.orig_array[ col_row[1], col_row[0]]
			val = float(val)
		except IndexError:
			val = None
		return val

	def imagexy_to_numericrc(self, coord):
		if not coord:
			return None
		orig_size = self.orig_size
		output_size = self.transform['output_size']
		numc = (float(coord[0]) / output_size[0]) * orig_size[0]
		numr = (float(coord[1]) / output_size[1]) * orig_size[1]
		if 0 <= numc < orig_size[0] and 0 <= numr < orig_size[1]:
			numr = int(numr)
			numc = int(numc)
			return numr,numc
		else:
			return None

	def update_image(self):
		"""
		generates the PIL Image representation of this numpy array
		"""

		clip = self.transform['clip']
		final = imagefun.linearscale(self.orig_array, clip, (0,255), self.extrema)
		type = final.dtype
		h,w = final.shape
		imsize = w,h
		itemsize = final.itemsize
		immode = ntype_itype[type.type,itemsize][0]
		rawmode = ntype_itype[type.type,itemsize][1]

		nstr = final.tostring()

		stride = 0
		orientation = 1
		image = Image.fromstring(immode, imsize, nstr, 'raw', rawmode, stride, orientation)

		image = resize(image, self.transform['output_size'])

		self.image = image
		return self.image

	def photoimage(self):
		"""
		generates a PhotoImage object representing this PIL Image
		"""
		photo = ImageTk.PhotoImage(self.image)
		return photo

	def somethingwxImage(self):
		#self.clearImage()
		#stream = cStringIO.StringIO(imagestring)
		#self.image = Image.open(stream)

		min, max = self.image.getextrema()
		if max > 255.0 or min < 0.0:
			r = max - min
			if r:
				scale = 255.0 / r
				offset = -255.0 * min / r
				image = self.image.point(lambda p: p * scale + offset)
			else:
				image = self.image
		else:
			image = self.image

	def wxImage(self):
		wximage = EmptyImage(self.image.size[0], self.image.size[1])
		wximage.SetData(self.image.convert('RGB').tostring())
		return wximage

	def jpeg(self, filename=None, quality=100, newsize=None):
		'''
		Convert numeric -> JPEG [quality]
		filename defaults to stdout
		quality defaults to 100
		'''
		img = self.update_image()
		if filename is None:
			filename = sys.stdout
		if newsize is None:
			img.convert('L').save(filename, "JPEG", quality=quality)
		else:
			img.convert('L').resize(newsize).save(filename, "JPEG", quality=quality)

	def read_jpeg(self, filename):
                '''
                read a grey JPEG
                '''
                i = Image.open(filename)
                i.load()
                s = i.tostring()
                n = numpy.fromstring(s, '1')
                n.shape = i.size
                self.__use_numeric(n)

if __name__ == '__main__':
	from numpy import *

	a = array([5,6,7,8,9], Float)
	print 'a', a
	b = imagefun.linearscale(a, (None,None), (0,1))
	print 'b', b
	b = imagefun.linearscale(a, (6,8), (0,1))
	print 'b', b
	b = imagefun.linearscale(a, (8,6), (0,1))
	print 'b', b
	b = imagefun.linearscale(a, (6,8), (1.0,-1.0))
	print 'b', b

	#a1 = reshape(arrayrange(128**2), (128,128))
	#n1 = NumericImage(a)
