#!/usr/bin/env python

from Tkinter import *
import Numeric
import Image
import ImageTk
import math,sys

## (Numeric typcode,size) => (PIL mode,  PIL rawmode)
ntype_itype = {
	(Numeric.UnsignedInt8,1) : ('L','L'),
	(Numeric.Int16,2) : ('I','I;16NS'),
	(Numeric.Int,2) : ('I','I;16NS'),
	(Numeric.Int,4) : ('I','I;32NS'),
	(Numeric.Int32,4) : ('I','I;32NS'),
	(Numeric.Float,4) : ('F','F;32NF'),
	(Numeric.Float,8) : ('F','F;64NF'),
	(Numeric.Float32,4) : ('F','F;32NF'),
	(Numeric.Float64,8) : ('F','F;64NF')
	}

def numeric_bin(ndata, bin):
	shape = ndata.shape
	if len(shape) != 2:
		raise RuntimeError, 'ndata must be 2-D Numeric array'
	if len(bin) != 2:
		raise RuntimeError, 'bin must be 2-tuple'
	if shape[0] % bin[0] or shape[1] % bin[1]:
		raise RuntimeError, 'shape must be multiple of bin'

	newshape = shape[0]/bin[0], shape[1]/bin[1]

def linearscale(input, boundfrom, boundto):
	"""
	Rescale the data in the range 'boundfrom' to the range 'boundto'.
	"""

	### check args
	if len(input) < 1:
		return input
	if len(boundfrom) != 2:
		raise ValueError, 'boundfrom must be length 2'
	if len(boundto) != 2:
		raise ValueError, 'boundto must be length 2'

	minfrom,maxfrom = boundfrom
	minto,maxto = boundto

	### default from bounds are min,max of the input
	if minfrom == None:
		minfrom = min(Numeric.ravel(input))
	if maxfrom == None:
		maxfrom = max(Numeric.ravel(input))

	rangefrom = float(maxfrom - minfrom)
	rangeto = float(maxto - minto)

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	output = (input - minfrom) * rangeto / rangefrom
	return output

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
	NumericImage couples a Numeric array with a PIL Image instance.
	"""
	def __init__(self, orig_array, clip=(None,None), output_size=None):
		self.transform = {'clip':clip, 'output_size':output_size}
		self.__use_numeric(orig_array)
		print 'NumericImage initialized:', self.transform['clip']

	def __setitem__(self, key, value):
		if key not in self.transform.keys():
			raise KeyError, 'key must be one of: ' + `self.transform.keys()`
		self.transform[key] = value

	def __use_numeric(self, num_data):
		shape = num_data.shape
		if len(shape) != 2:
			raise RuntimeError, 'orig_array must be 2-D Numeric array'
		self.orig_array = num_data
		h,w = shape  # transpose Numeric array
		self.orig_size = w,h

		### if output size and clip are not set, use defaults
		if not self.transform['output_size']:
			self.transform['output_size'] = self.orig_size
		self.extrema =  min(Numeric.ravel(self.orig_array)), max(Numeric.ravel(self.orig_array))
		print 'numeric extrema set'
		if not self.transform['clip']:
			self.transform['clip'] = self.extrema

	def get(self, numcoord):
		try:
			val = self.orig_array[ numcoord[1], numcoord[0]]
		except IndexError:
			val = None
		return val

	def imagexy_to_numericxy(self, coord):
		if not coord:
			return None
		orig_size = self.orig_size
		output_size = self.transform['output_size']
		numx = (float(coord[0]) / output_size[0]) * orig_size[0]
		numy = (float(coord[1]) / output_size[1]) * orig_size[1]
		if 0 <= numx < orig_size[0] and 0 <= numy < orig_size[1]:
			numx = int(numx)
			numy = int(numy)
			return numx,numy
		else:
			return None

	def update_image(self):
		"""
		generates the PIL Image representation of this Numeric array
		"""

		clip = self.transform['clip']
		print 'UPDATE IMAGE with clip', clip
		final = linearscale(self.orig_array, clip, (0,255))
		type = final.typecode()
		h,w = final.shape
		imsize = w,h
		itemsize = final.itemsize()
		immode = ntype_itype[type,itemsize][0]
		rawmode = ntype_itype[type,itemsize][1]

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


if __name__ == '__main__':
	from Numeric import *

	a = array([5,6,7,8,9], Float)
	print 'a', a
	b = linearscale(a, (None,None), (0,1))
	print 'b', b
	b = linearscale(a, (6,8), (0,1))
	print 'b', b
	b = linearscale(a, (8,6), (0,1))
	print 'b', b
	b = linearscale(a, (6,8), (1.0,-1.0))
	print 'b', b

	#a1 = reshape(arrayrange(128**2), (128,128))
	#n1 = NumericImage(a)
