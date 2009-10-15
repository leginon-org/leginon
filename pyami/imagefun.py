#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import numpy
import quietscipy
import scipy.ndimage
import fftengine
try:
	import numextension
except:
	pass
import math
import arraystats
from scipy import stats

ffteng = fftengine.fftEngine()

### wrap some functions that are in numextension
def minmax(image):
	return numextension.minmax(image)

def despike(image, size=11, sigma=3.5, debug=0):
	'''
	size is the neighborhood size.  wide spikes require a wider
	neighborhood.  size = 11 has been shown to work well on spikes
	up to 3 or 4 pixels wide.

	sigma is the threshold for spike intensity.
	the mean and std. dev. are calculated in a neighborhood around
	each pixel.  if the pixel value varies by more than sigma * std
	dev. then the pixel will be set to the mean value.
	'''
	# last argument is debug flag
	numextension.despike(image, size, sigma, debug)

def medianSeries(series):
	try:
		return numpy.median(series, 0)
	except:
		return numpy.median(series)

def averageSeries(series):
	try:
		return numpy.mean(series, 0)
	except:
		return numpy.mean(series)

def scale(a, scale):
	if scale == 1.0:
		return a
	return scipy.ndimage.zoom(a, scale, order=1)

def linearscale(input, boundfrom, boundto, extrema=None):
	"""
	Rescale the data in the range 'boundfrom' to the range 'boundto'.
	"""

	minfrom,maxfrom = boundfrom
	minto,maxto = boundto
	if minfrom is not None and maxfrom is not None:
		if minfrom == maxfrom:
			raise RuntimeError('Invalid range: %s' % (boundfrom,))

	### default from bounds are min,max of the input
	if minfrom is None:
		if extrema:
			minfrom = extrema[0]
		else:
			minfrom = arraystats.min(input)
	if maxfrom is None:
		if extrema:
			maxfrom = extrema[1]
		else:
			maxfrom = arraystats.max(input)

	rangefrom = maxfrom - minfrom
	rangeto = maxto - minto

	scale = float(rangeto) / rangefrom
	offset = minfrom * scale
	output = input * scale - offset

	return output

def power(a, mask_radius=1.0, thresh=3):
	fft = ffteng.transform(a)
	pow = numpy.absolute(fft)
	try:
		pow = numpy.log(pow)
	except OverflowError:
		pow = numpy.log(pow+1e-20)
	pow = swap_quadrants(pow)

	mask_radius = int(mask_radius / 100.0 * pow.shape[0])
	if mask_radius:
		center_mask(pow, mask_radius)

	return clip_power(pow,thresh)

def clip_power(pow,thresh=3):
	m = arraystats.mean(pow)
	s = arraystats.std(pow)
	minval = m-thresh*s*0.5
	maxval = m+thresh*s
	pow = numpy.clip(pow, minval, maxval)

	return pow

def filled_circle(shape, radius):
	r2 = radius*radius
	center = shape[0]/2,shape[1]/2
	def func(i0, i1):
		ii0 = i0 - center[0]
		ii1 = i1 - center[1]
		rr2 = ii0**2 + ii1**2
		c = numpy.where(rr2<r2, 0.0, 1.0)
		return c
	return numpy.fromfunction(func, shape)

def fromRadialFunction(funcrad, shape):
	center_r = shape[0] / 2.0 - 0.5
	center_c = shape[1] / 2.0 - 0.5
	def funcrc(r,c):
		rr = r - center_r
		cc = c - center_c
		rad = numpy.hypot(rr,cc)
		return funcrad(rad)
	result = numpy.fromfunction(funcrc, shape)
	return result

def center_mask(a, mask_radius):
	shape = a.shape
	center = shape[0]/2, shape[1]/2
	center_square = a[center[0]-mask_radius:center[0]+mask_radius, center[1]-mask_radius:center[1]+mask_radius]
	m = arraystats.mean(a)
	cs_shape = center_square.shape
	cs_center = cs_shape[0]/2, cs_shape[1]/2
	circ = filled_circle(cs_shape,mask_radius)
	center_square[:] = center_square * circ.astype(center_square.dtype)

def swap_row_halves(a):
	rows,cols = a.shape
	b = numpy.zeros(a.shape, a.dtype)
	b[:rows/2] = a[-(rows/2):]
	b[rows/2:] = a[:-(rows/2)]
	return b

swap = swap_row_halves

def swap_col_halves(a):
	rows,cols = a.shape
	b = numpy.zeros(a.shape, a.dtype)
	b[:,:cols/2] = a[:,-(cols/2):]
	b[:,cols/2:] = a[:,:-(cols/2)]
	return b

def swap_quadrants(a):
	b = swap_row_halves(a)
	b = swap_col_halves(b)
	return b

def pad(im, value=None):
	# maybe use numpy.concatenate instead?
	if value is None:
		value = arraystats.mean(im)
	padshape = im.shape[0]*2, im.shape[1]*2
	paddedimage = value * numpy.ones(padshape, im.dtype)
	paddedimage[:im.shape[0], :im.shape[1]] = im
	return paddedimage

## The Blob.add_point method below is recursive while searching for neighbors.
## Here we make sure that python will allow enough recursion to get decent
## sized blobs.
import sys
reclim = sys.getrecursionlimit()
if reclim < 20000:
	sys.setrecursionlimit(20000)

class Blob(object):
	def __init__(self, image, mask, n, center, mean, stddev, moment, maxpos):
		self.image = image
		self.mask = mask
		self.stats = {"center":center, "n":n, "mean":mean, "stddev":stddev, "size":0, "moment":moment, "maximum_position":maxpos}

def highest_peaks(blobs, n):
	"""
	filter out no more than n blobs that have the highest mean
	"""
	## sort blobs based on mean
	def blob_compare(x,y):
		if float(x.stats['mean']) < float(y.stats['mean']): return 1
		else: return -1
	sortedblobs = list(blobs)
	sortedblobs.sort(blob_compare)
	sortedblobs = sortedblobs[:n]
	## make new list of blobs that have the highest mean
	newblobs = []
	for blob in blobs:
		if blob in sortedblobs:
			newblobs.append(blob)
	return newblobs

def biggest_peaks(blobs, n):
	"""
	filter out no more than n blobs that have the biggest size
	"""
	## sort blobs based on mean
	def blob_compare(x,y):
		if float(x.stats['n']) < float(y.stats['n']): return 1
		else: return -1
	sortedblobs = list(blobs)
	sortedblobs.sort(blob_compare)
	sortedblobs = sortedblobs[:n]
	## make new list of blobs that have the highest mean
	newblobs = []
	for blob in blobs:
		if blob in sortedblobs:
			newblobs.append(blob)
	return newblobs

def near_center(shape, blobs, n):
	'''
	filter out no more than n blobs that are closest to image center
	'''
	
	# create distance mapping
	imcenter = shape[0]/2, shape[1]/2
	distmap = {}
	for blob in blobs:
		center = blob.stats['center']
		distance = numpy.hypot(center[0]-imcenter[0],center[1]-imcenter[1])
		distmap[blob] = distance
	## sort blobs based on distance
	def dist_cmp(x,y):
		return cmp(distmap[x],distmap[y])
	sortedblobs = list(blobs)
	sortedblobs.sort(dist_cmp)
	sortedblobs = sortedblobs[:n]
	## make new list of blobs with n closest, same order as before
	newblobs = []
	for blob in blobs:
		if blob in sortedblobs:
			newblobs.append(blob)
	return newblobs

## using scipy.ndimage to find blobs
labelstruct = numpy.ones((3,3))
def scipyblobs(im,mask):
	labels,n = scipy.ndimage.label(mask, labelstruct)
	## too bad ndimage module is inconsistent with what is returned from
	## the following functions.  Sometiems a list, sometimes a single value...
	if n==0:
		centers = []
		sizes = []
		stds = []
		means = []
		maxpos = []
	else:
		centers = scipy.ndimage.center_of_mass(im,labels,range(1,n+1))
		sizes = scipy.ndimage.histogram(labels,1,n+1,n)
		stds = scipy.ndimage.standard_deviation(im,labels,range(1,n+1))
		means = scipy.ndimage.mean(im,labels,range(1,n+1))
		moments = moment_of_inertia(im,labels,range(1,n+1))
		maxpos = scipy.ndimage.maximum_position(im,labels,range(1,n+1))
		if n==1:
			centers = [centers]
			stds = [stds]
			means = [means]
			maxpos = [maxpos]
		else:
			centers = map(numpy.array, centers)

	blobs = []
	for i in range(n):
		blobs.append({'center':centers[i], 'n':sizes[i], 'mean':means[i],'stddev':stds[i],'moment':moments[i], 'maximum_position':maxpos[i]})
	return blobs

def moment_of_inertia(input, labels, index = None):
	"""
	Calculate the moment of inertia of of the array.

	The index parameter is a single label number or a sequence of
	label numbers of the objects to be measured. If index is None, all
	values are used where labels is larger than zero.
	"""
	input = numpy.asarray(input)
	if labels == None:
		raise RuntimeError, 'labels are needed'
	if labels.shape != input.shape:
		raise RuntimeError, 'input and labels shape are not equal'
	moments = []
	for label in scipy.ndimage.find_objects(labels):
		submask = input[label].copy()
		moment = _moment(submask)
		moments.append(moment)
	return moments


def _moment(subimage):
	if(subimage.shape[0]+subimage.shape[1] < 4):
		return 1.0
	twopi = 2*math.pi
	r0 = scipy.ndimage.center_of_mass(subimage)
	sqmat = _distsqmat(r0,subimage.shape)
	## could be zero division in the following
	try:
		moi = scipy.ndimage.sum(subimage*sqmat)/(scipy.ndimage.sum(subimage)**2)*twopi
	except:
		moi = 0.0
	return moi

def _distsqmat(r0,shape):
	indices = numpy.indices(shape)
	dx, dy = indices[0]-r0[0],indices[1]-r0[1]
	return (dx**2+dy**2)

def find_blobs(image, mask, border=0, maxblobs=300, maxblobsize=100, minblobsize=0, maxmoment=None, method="central", summary=False):
	"""
	find blobs with particular features in a map
	"""

	shape = image.shape
	### create copy of mask since it will be modified now
	tmpmask = numpy.array(mask, numpy.int32)
	## zero out tmpmask outside of border
	if border:
		tmpmask[:border] = 0
		tmpmask[-border:] = 0
		tmpmask[:,:border] = 0
		tmpmask[:,-border:] = 0

	blobs = scipyblobs(image,tmpmask)
	fakeblobs = []
	toobig = 0
	toosmall = 0
	toooblong = 0
	for blob in blobs:
		fakeblob = Blob(image, mask, blob['n'], blob['center'], blob['mean'], blob['stddev'], blob['moment'], blob['maximum_position'])
		if blob['n'] >= maxblobsize:
			toobig += 1
			continue
		if blob['n'] < minblobsize:
			toosmall += 1
			continue
		if maxmoment is not None and blob['moment'] >= maxmoment:
			toooblong += 1
			continue
		fakeblobs.append(fakeblob)

	if summary is True:
		print "BLOB summary:",len(fakeblobs),"total /",toobig,"toobig /",toosmall,"toosmall /",toooblong,"toooblong"

	## limit to maxblobs
	if (maxblobs is not None) and (len(blobs) > maxblobs):
		if(method == "highest"):
			blobs = highest_peaks(fakeblobs, int(maxblobs))
		elif(method == "biggest"):
			blobs = biggest_peaks(fakeblobs, int(maxblobs))
		else:
			blobs = near_center(shape, fakeblobs, maxblobs)
	else:
		blobs = fakeblobs

	return blobs

def mark_image(image, coord, value, size=15):
	'''
	burn a mark on an image
	'''
	row,col = int(coord[0]), int(coord[1])
	for r in range(row-size,row+size):
		if 0 <= r < image.shape[0] and 0 <= col < image.shape[1]:
			image[r,col] = value
	for c in range(col-size,col+size):
		if 0 <= c < image.shape[1] and 0 <= row < image.shape[0]:
			image[row,c] = value

def bin(image, binning):
	if binning==1:
		return image
	return numextension.bin(image, binning)

def bin2(a, factor):
	'''
	This is based on: http://scipy.org/Cookbook/Rebinning
	It is simplified to the case of a 2D array with the same
	binning factor in both dimensions.
	'''
	oldshape = a.shape
	newshape = numpy.asarray(oldshape)/factor
	tmpshape = (newshape[0], factor, newshape[1], factor)
	f = factor * factor
	binned = numpy.sum(numpy.sum(numpy.reshape(a, tmpshape), 1), 2) / f
	return binned

def bin2m(a, factor):
	'''
	Median instead of mean for bin2
	'''
	oldshape = a.shape
	newshape = numpy.asarray(oldshape)/factor
	tmpshape = (newshape[0], factor, newshape[1], factor)
	f = factor * factor
	binned = stats.median(stats.median(numpy.reshape(a, tmpshape), 1), 2)
	return binned

def bin2f(a, factor):
	'''
	Binning in Fourier space
	'''
	fft = ffteng.transform(a)
	fft = numpy.fft.fftshift(fft)
	half = fft.shape[0]/2
	xstart = int( fft.shape[0]/2 * (1 - 1.0/factor))
	xend   = int( fft.shape[0]/2 * (1 + 1.0/factor))
	ystart = int( fft.shape[1]/2 * (1 - 1.0/factor))
	yend   = int( fft.shape[1]/2 * (1 + 1.0/factor))
	#print ("%d:%d  ,  %d:%d\n"%(xstart,xend,ystart,yend,))
	cutfft = fft[xstart:xend, ystart:yend]
	cutfft = numpy.fft.fftshift(cutfft)
	#print cutfft.shape, fft.shape
	binned = ffteng.itransform(cutfft)/float(factor**2)
	return binned

def bin3(a, factor):
	'''
	This is based on: http://scipy.org/Cookbook/Rebinning
	It is simplified to the case of a 3D array with the same
	binning factor in both dimensions.
	'''
	oldshape = a.shape
	newshape = numpy.asarray(oldshape)/factor
	tmpshape = (newshape[0], factor, newshape[1], factor, newshape[2], factor)
	f = factor * factor * factor
	binned = numpy.sum(numpy.sum(numpy.sum(numpy.reshape(a, tmpshape), 1), 2), 3) / f
	#binned = stats.median(stats.median(numpy.reshape(a, tmpshape), 1), 2)
	return binned

def bin3f(a, factor):
	'''
	Binning in Fourier space
	'''
	fft = ffteng.transform(a)
	fft = numpy.fft.fftshift(fft)
	xstart = int( fft.shape[0]/2 * (1 - 1.0/factor))
	xend   = int( fft.shape[0]/2 * (1 + 1.0/factor))
	ystart = int( fft.shape[1]/2 * (1 - 1.0/factor))
	yend   = int( fft.shape[1]/2 * (1 + 1.0/factor))
	zstart = int( fft.shape[2]/2 * (1 - 1.0/factor))
	zend   = int( fft.shape[2]/2 * (1 + 1.0/factor))
	cutfft = fft[
		xstart:xend,
		ystart:yend,
		zstart:zend,
	]
	cutfft = numpy.fft.fftshift(cutfft)
	binned = ffteng.itransform(cutfft)/float(factor**3)
	return binned

def crop_at(im, center, shape, mode='wrap', cval=None):
	'''
	Crops an image such that the resulting image has im[center] at the center
	Image is treatead as wrapping around at the edges.
	'''
	## can't crop area larger than image
	if shape[0]>im.shape[0] or shape[1]>im.shape[1]:
		raise ValueError('crop_at: crop shape %s must not be larger than image shape %s' % (shape, im.shape))
	if center == 'center':
		center = im.shape[0]/2.0 - 0.5, im.shape[1]/2.0 - 0.5
	croppedcenter = shape[0]/2.0 - 0.5, shape[1]/2.0 - 0.5
	shift = croppedcenter[0]-center[0], croppedcenter[1]-center[1]
	if mode == 'constant':
		shifted = scipy.ndimage.shift(im, shift, mode=mode, cval=cval)
	else:
		shifted = scipy.ndimage.shift(im, shift, mode=mode)
	cropped = shifted[:shape[0], :shape[1]]
	return cropped

def threshold(a, limit):
	return a >= limit

def pasteInto(a, b, pos):
	'''paste image a into image b at position pos'''
	b[pos[0]:pos[0]+a.shape[0], pos[1]:pos[1]+a.shape[1]] = a

def taper(im, boundary):
	'''
	in place taper of image boundary
	'''
	im[0] = (im[0] + im[-1]) / 2.0
	im[-1] = im[0]

	im[:,0] = (im[:,0] + im[:,-1]) / 2.0
	im[:,-1] = im[:,0]

	for sign in (-1,1):
		for i in range(1,boundary):
			im[sign*i] = (im[sign*i]*0.1 + im[sign*i-sign]*0.9)
			im[:,sign*i] = (im[:,sign*i]*0.1 + im[:,sign*i-sign]*0.9)
