#!/usr/bin/env python

from Tkinter import *
import Numeric
import Image
import ImageTk

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
		self.num_min = min(Numeric.ravel(self.orig_array))
		self.num_max = max(Numeric.ravel(self.orig_array))
		print 'stats', self.num_min, self.num_max

	def zoom(self):
		pass

	def clip(self, input):
		"""
		Scale Numeric data to a viewable range (0-255).
		clip tuple specifies (min, max) where min scales to 0, and
		max scales to 255.
		"""
		minval = self.transform['clip'][0]
		maxval = self.transform['clip'][1]
		## if no clip specified, use min or max of array
		if minval == None:
			minval = self.num_min
		if maxval == None:
			maxval = self.num_max

		range = maxval - minval
		try:
			scl = 255.0 / range
			off = -255.0 * minval / range
		except ZeroDivisionError:
			scl = 0.0
			off = 0.0

		output = scl * input + off
		return output

	def update_image(self):
		"""
		generates the PIL Image representation of this Numeric array
		"""

		final = self.clip(self.orig_array)
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
	a1 = reshape(arrayrange(128**2), (128,128))
	n1 = NumericImage(a)
