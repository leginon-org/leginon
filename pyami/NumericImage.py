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
		minfrom = min(input.flat)
	if maxfrom == None:
		maxfrom = max(input.flat)

	rangefrom = float(maxfrom - minfrom)
	rangeto = float(maxto - minto)

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	output = (input - minfrom) * rangeto / rangefrom
	return output


class NumericImage:
	"""
	NumericImage couples a Numeric array with a PIL Image instance.
	"""
	def __init__(self, orig_array):
		self.use_numeric(orig_array)
		self.transform = {'clip':(None,None), 'zoom':1.0}
		self.update_image()

	def __setitem__(self, key, value):
		if key not in self.transform.keys():
			raise KeyError, 'key must be one of: ' + `self.transform.keys()`
		self.transform[key] = value

	def use_numeric(self, num_data):
		shape = num_data.shape
		if len(shape) != 2:
			raise RuntimeError, 'orig_array must be 2-D Numeric array'
		self.orig_array = num_data
		h,w = shape  # transpose Numeric array
		self.orig_size = w,h
		self.extrema =  min(self.orig_array.flat), max(self.orig_array.flat)

	def get(self, x, y):
		return self.orig_array[y,x]

	def zoom(self):
		pass

	def update_image(self):
		"""
		generates the PIL Image representation of this Numeric array
		"""

		clip = self.transform['clip']
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
		self.image = Image.fromstring(immode, imsize, nstr, 'raw', rawmode, stride, orientation)
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
