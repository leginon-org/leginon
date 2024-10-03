#!/usr/bin/env python

from PIL import Image
import numpy

def getPilFromStringFuncName():
	# PIL function name changes #4237
	# same as in numpil but do not want to import that
	if hasattr(Image,'frombytes'):
		func_name = 'frombytes'
	else:
		func_name = 'fromstring'
	return func_name


def save(a, min, max, filename, quality):
	a = numpy.clip(a, min, max)
	scale = 255.0 / (max - min)
	a = scale * (a - min)
	print(a)
	a = a.astype(numpy.uint8)
	imsize = a.shape[1], a.shape[0]
	nstr = a.tobytes()
	image = getattr(Image,getPilFromStringFuncName())('L', imsize, nstr, 'raw', 'L', 0, 1)
	image.convert('L').save(filename, "JPEG", quality=quality)
