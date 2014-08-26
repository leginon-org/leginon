#!/usr/bin/env python

from PIL import Image
import numpy

def save(a, min, max, filename, quality):
	a = numpy.clip(a, min, max)
	scale = 255.0 / (max - min)
	a = scale * (a - min)
	print a
	a = a.astype(numpy.uint8)
	imsize = a.shape[1], a.shape[0]
	nstr = a.tostring()
	image = Image.fromstring('L', imsize, nstr, 'raw', 'L', 0, 1)
	image.convert('L').save(filename, "JPEG", quality=quality)
