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
	numarray.UInt16: ('I', 'I;16NS'),
	numarray.UInt32: ('I', 'I;32NS'),
	numarray.UInt64: ('I', 'I;64NS'),
	numarray.Int16: ('I', 'I;16S'),
	numarray.Int32: ('I', 'I;32S'),
	numarray.Int64: ('I', 'I;64S'),
	numarray.Float32: ('F', 'F;32NF'),
	numarray.Float64: ('F', 'F;64NF')
}

def numarray2Image(array):
	arraytype = array.type()
	imagemode, rawmode = typemap[arraytype]
	height, width = array.shape
	imagesize = width, height
	return Image.frombuffer(imagemode, imagesize, array.tostring(), 'raw', rawmode, 0, 1)

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

	array = Mrc.mrc_to_numeric(sys.argv[1])
	print numarray2wxImage(array)

