#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Image
import math
import numarray
import wx

typemap = {
	numarray.UInt8: ('L', 'L'),
	numarray.UInt16: ('I', 'I;16N'),
	numarray.UInt32: ('I', 'I;32N'),
	numarray.Int16: ('I', 'I;16NS'),
	numarray.Int32: ('I', 'I;32NS'),
	numarray.Float32: ('F', 'F;32NF'),
	numarray.Float64: ('F', 'F;64NF')
}

def numarray2Image(array):
	arraytype = array.type()
	try:
		mode, rawmode = typemap[arraytype]
	except KeyError:
		raise TypeError
	height, width = array.shape
	size = width, height
	if 0 in size:
		raise ValueError
	stride = 0
	orientation = 1
	args = (mode, size, array.tostring(), 'raw', rawmode, stride, orientation)
	return Image.frombuffer(*args)

def scaleImage(image, fromrange, torange):
	scale = float(torange[1] - torange[0])/float(fromrange[1] - fromrange[0])
	offset = scale*(torange[0] - fromrange[0])
	return image.point(lambda i: i * scale + offset)

def numarray2RGBImage(array, x=0, y=0, width=None, height=None, xscale=1.0, yscale=1.0, fromrange=None, filter=Image.BICUBIC):
	if width is None:
		width = int(round(array.shape[1]*xscale))
	if height is None:
		height = int(round(array.shape[0]*yscale))

	sx = x/xscale
	sy = y/yscale
	swidth = width/xscale
	sheight = height/yscale

	if filter == Image.NEAREST:
		pad = 1
	elif filter == Image.BILINEAR:
		pad = 1
	elif filter == Image.BICUBIC:
		pad = 2
	else:
		pad = 0
	row1 = max(0, int(math.floor(sy)) - pad)
	row2 = min(array.shape[0], int(math.ceil(sy + sheight)) + pad)
	column1 = max(0, int(math.floor(sx)) - pad)
	column2 = min(array.shape[1], int(math.ceil(sx + swidth)) + pad)

	image = numarray2Image(array[row1:row2, column1:column2])

	if fromrange is None:
		fromrange = image.getextrema()

	image = scaleImage(image, fromrange, (0, 255))

	size = int(round(image.size[0]*xscale)), int(round(image.size[1]*yscale))
	image = image.resize(size, filter)
	left = int(round((sx - column1)*xscale))
	upper = int(round((sy - row1)*yscale))
	right = left + width
	bottom = upper + height
	image = image.crop((left, upper, right, bottom))

	return image.convert('RGB')

def numarray2wxImage(*args, **kwargs):
	rgbimage = numarray2RGBImage(*args, **kwargs)
	wximage = wx.EmptyImage(*rgbimage.size)
	wximage.SetData(rgbimage.tostring())
	return wximage

def numarray2wxBitmap(*args, **kwargs):
	return wx.BitmapFromImage(numarray2wxImage(*args, **kwargs))

if __name__ == '__main__':
	import Mrc
	import sys

	array = Mrc.mrc_to_numeric(sys.argv[1])

	#app = wx.App(0)
	#print numarray2wxBitmap(array)

	numarray2RGBImage(array).show()
