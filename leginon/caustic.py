#!/usr/bin/env python
'''
Functions to identify the parameters of the caustic figure as described
by the following paper:
  "Practical procedure for coma-free alignment using caustic figure"
  Koji Kimoto, Kazuo Ishizuka, Nobuo Tanaka, Yoshio Matsui
  Ultramicroscopy 96 (2003) 219-227

Main function is:

'''

import numpy
import scipy
import scipy.ndimage as ndimage
import houghcircle
import Image
import ImageDraw
from pyami import imagefun

def saveMRC(image, name):
	from pyami import mrc
	mrc.write(image, name)

def gradient(a):
	a = ndimage.generic_gradient_magnitude(a, ndimage.sobel)
	a = numpy.abs(a)
	return a

def argmax3d(image):
	peaki = image.argmax()
	peakcol = peaki % image.shape[2]
	rows = peaki / image.shape[2]
	peakrow = rows % image.shape[1]
	rads = rows / image.shape[1]
	peakrad = rads % image.shape[0]
	return peakrad, peakrow, peakcol

def findBestCircle(image, radii):
	'search for circles with given radii, return the best one'
	hough = houghcircle.transform(image, radii)
	rad, row, col = argmax3d(hough)

	maxradius = max(radii)
	rad = radii[rad]
	row = row-maxradius
	col = col-maxradius

	return {'center': (row, col), 'radius': rad}

def findBestCircle2(image, radii, limit):
	'search for circles with given radii, return the best one'
	hough = houghcircle.transform2(image, radii, limit)
	rad, row, col = argmax3d(hough)

	maxradius = max(radii)
	rad = radii[rad]
	row = row+limit[0]
	col = col+limit[2]

	print 'LIMIT', limit
	print 'MAXRAD', maxradius
	print 'ROW', row
	print 'COL', col

	return {'center': (row, col), 'radius': rad}


def makeCircleMask(shape, circle):
	center = circle['center']
	rad = circle['radius']
	row0 = center[0]-rad
	row1 = center[0]+rad
	col0 = center[1]-rad
	col1 = center[1]+rad

	pilsize = shape[1], shape[0]
	mask = Image.new('L', pilsize, 1)
	draw = ImageDraw.Draw(mask)
	draw.ellipse(((col0,row0),(col1,row1)), outline=0, fill=0)
	mask = scipy.misc.fromimage(mask)
	return mask

def removeCircle(image, circle):
	mask = makeCircleMask(image.shape, circle)
	return image * mask

def findCaustic(input, smallrange, bigrange, mask, binning=None):
	'''
	Initial search for caustic figure in binned image, then in original.
	'''
	if binning is not None:
		## first run it with initial binning
		bin_input = imagefun.bin(input, binning)

		smallmin = int(numpy.floor(smallrange[0] / float(binning)))
		smallmax = int(numpy.ceil(smallrange[1] / float(binning)))+1
		bin_radii_small = numpy.arange(smallmin, smallmax)
		print 'BINRADIISMALL', len(bin_radii_small), bin_radii_small

		bigmin = int(numpy.floor(bigrange[0] / float(binning)))
		bigmax = int(numpy.ceil(bigrange[1] / float(binning)))+1
		bin_radii_big = numpy.arange(bigmin, bigmax)
		print 'BINRADIIBIG', len(bin_radii_big), bin_radii_big

		bin_mask = mask / binning

		small_circle, big_circle = __findCaustic(bin_input, bin_radii_small, bin_radii_big, bin_mask)
		print 'BINCIRCLES', small_circle, big_circle

		# set up ranges for full size image
		halfbin = binning / 2.0

		### XXX need to make sure new radii do not include more than original
		rsmall = small_circle['radius']
		smallmin = int(numpy.floor(rsmall * binning - 4 * binning))
		smallmax = int(numpy.ceil(rsmall * binning + 4 * binning))
		smallrange = smallmin, smallmax
		rbig = big_circle['radius']
		bigmin = int(numpy.floor(rbig * binning - 4 * binning))
		bigmax = int(numpy.ceil(rbig * binning + 4 * binning))
		bigrange = bigmin, bigmax
		print 'NEWRANGES', smallrange, bigrange

		small_row0 = binning * (small_circle['center'][0] - 2)
		small_row1 = binning * (small_circle['center'][0] + 2)
		small_col0 = binning * (small_circle['center'][1] - 2)
		small_col1 = binning * (small_circle['center'][1] + 2)
		small_limit = small_row0, small_row1, small_col0, small_col1
		big_row0 = binning * (big_circle['center'][0] - 2)
		big_row1 = binning * (big_circle['center'][0] + 2)
		big_col0 = binning * (big_circle['center'][1] - 2)
		big_col1 = binning * (big_circle['center'][1] + 2)
		big_limit = big_row0, big_row1, big_col0, big_col1

	radii_small = numpy.arange(smallrange[0], smallrange[1]+1, dtype=numpy.int)
	print 'RADIISMALL', len(radii_small), radii_small
	radii_big = numpy.arange(bigrange[0], bigrange[1]+1, dtype=numpy.int)
	print 'RADIIBIG', len(radii_big), radii_big

	small_circle, big_circle = __findCaustic(input, radii_small, radii_big, mask, small_limit, big_limit)
	print small_circle, big_circle
	return small_circle, big_circle

def __findCaustic(input, radii_small, radii_big, mask, small_limit=None, big_limit=None):
	'''
	Find a small circle, then mask it to find the second circle.
	'''
	## fastest dtype
	input = numpy.asarray(input, numpy.float32)

	# gradient of input image
	print 'calc gradient...'
	grad = gradient(input)

	# find small circle
	print 'finding bright-field spot'
	if small_limit is None:
		small_limit = 0, input.shape[0], 0, input.shape[1]
	circle_small = findBestCircle2(grad, radii_small, small_limit)

	# mask out area somewhat larger than small circle
	print 'removing bright-field spot'
	circle_mask = dict(circle_small)
	circle_mask['radius'] *= mask
	newgrad = removeCircle(grad, circle_mask)

	# find big circle
	print 'finding caustic curve'
	if big_limit is None:
		big_limit = 0, input.shape[0], 0, input.shape[1]
	circle_big = findBestCircle2(newgrad, radii_big, big_limit)

	return circle_small, circle_big

if __name__ == '__main__':
	from pyami import mrc
	import time

	#input = mrc.read('input16.mrc')
	radii_small = (6,40)
	radii_big = (80,100)

	input = mrc.read('input8.mrc')
	radii_small = numpy.multiply((6,40), 2)
	radii_big = numpy.multiply((80,100), 2)

	#input = mrc.read('09jul22caustic_00007ma_0.mrc')
	#radii_small = numpy.multiply((6,40), 16)
	#radii_big = numpy.multiply((80,100), 16)

	t0 = time.time()
	findCaustic(input, radii_small, radii_big, 1.8, 2)
	t1 = time.time()
	print 'TIME', t1-t0
