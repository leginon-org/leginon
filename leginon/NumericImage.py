#!/usr/bin/env python

from wxPython.wx import *
## commenting this while Tk is broken
#from Tkinter import *
#import ImageTk
import Image
import Numeric
import math,sys
import time

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


def linearscale(input, boundfrom, boundto, extrema=None):
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
	if minfrom is None:
		if extrema:
			minfrom = extrema[0]
		else:
			minfrom = Numeric.argmin(Numeric.ravel(input))
			minfrom = Numeric.ravel(input)[minfrom]
	if maxfrom is None:
		if extrema:
			maxfrom = extrema[1]
		else:
			maxfrom = Numeric.argmax(Numeric.ravel(input))
			maxfrom = Numeric.ravel(input)[maxfrom]

	## prepare for fast math
	rangefrom = Numeric.array((maxfrom - minfrom)).astype('f')
	rangeto = Numeric.array((maxto - minto)).astype('f')
	minfrom = Numeric.array(minfrom).astype('f')

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	#output = (input - minfrom) * rangeto / rangefrom
	scale = rangeto / rangefrom
	offset = minfrom * scale
	output = input * scale - offset

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

# 1024x1024:  0.1
def extrema(numarray):
		t0 = time.clock()

		flat = Numeric.ravel(numarray)
		extmin = Numeric.argmin(flat)
		extmax = Numeric.argmax(flat)
		minval = flat[extmin]
		maxval = flat[extmax]
		ext = (minval, maxval)

		t1 = time.clock()
		t = t1 - t0
		print 'time: %.3f' % (t,)
		return ext

class NumericImage:
	"""
	NumericImage couples a Numeric array with a PIL Image instance.
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
			raise RuntimeError, 'orig_array must be 2-D Numeric array'
		## experimenting with clipping to eliminate infinity
		#self.orig_array = Numeric.clip(num_data, -10000, 10000)
		self.orig_array = num_data

		h,w = shape  # transpose Numeric array
		self.orig_size = w,h

		### if output size and clip are not set, use defaults
		if not self.transform['output_size']:
			self.transform['output_size'] = self.orig_size

		flat = Numeric.ravel(self.orig_array)
		extmin = Numeric.argmin(flat)
		extmax = Numeric.argmax(flat)
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
		generates the PIL Image representation of this Numeric array
		"""

		clip = self.transform['clip']
		final = linearscale(self.orig_array, clip, (0,255), self.extrema)
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
		wximage = wxEmptyImage(self.image.size[0], self.image.size[1])
		wximage.SetData(self.image.convert('RGB').tostring())
		return wximage

	def jpeg(self, filename, quality=100):
		'Convert numeric -> JPEG [quality]'
		img = self.update_image()
		img.convert('L').save(filename, "JPEG", quality=quality)



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
