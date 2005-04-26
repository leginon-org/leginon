#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Image
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

def numarray2RGBImage(array, fromrange=None):
	image = numarray2Image(array)
	if fromrange is None:
		fromrange = image.getextrema()
	image = scaleImage(image, fromrange, (0, 255))
	return image.convert('RGB')

def numarray2wxImage(array, fromrange=None):
	rgbimage = numarray2RGBImage(array, fromrange)
	wximage = wx.EmptyImage(*rgbimage.size)
	wximage.SetData(rgbimage.tostring())
	return wximage

def numarray2wxBitmap(array, fromrange=None):
	return wx.BitmapFromImage(numarray2wxImage(array, fromrange))

if __name__ == '__main__':
	import Mrc
	import sys
	import time

	app = wx.App(0)

	array = Mrc.mrc_to_numeric(sys.argv[1])
	times = []
	for i in range(8):
		t = time.time()
		b = numarray2wxBitmap(array)
		times.append(time.time() - t)
	print times
	print sum(times)/len(times)

