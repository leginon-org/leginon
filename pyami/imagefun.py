#
# COPYRIGHT:
#			 The Leginon software is Copyright under
#			 Apache License, Version 2.0
#			 For terms of the license agreement
#			 see	http://leginon.org
#
from builtins import map
from builtins import range
from builtins import object
import functools

import numpy
from pyami import quietscipy
import scipy.ndimage
from pyami import fftengine
import sys
import numextension
import math
from pyami import arraystats
from scipy import stats

ffteng = fftengine.fftEngine()

### wrap some functions that are in numextension
def minmax(image):
	return (image.min(), image.max())

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
	if rangefrom == 0:
		# if min==max, do simple thresholding
		output = numpy.where(input>maxfrom, maxto, minto)
	else:
		rangeto = maxto - minto
		scale = float(rangeto)/rangefrom
		offset = minfrom * scale
		output = input * scale - offset

	return output

def phase_spectrum(a):
	fft = ffteng.transform(a)
	phase = numpy.angle(fft, deg=True)
	### neil half pixel shift or powerspectra are not centered!
	phase = scipy.ndimage.interpolation.shift(phase, (-1, -1), order=1, mode='wrap')
	phase = swap_quadrants(phase)
	return phase

def power(a, mask_radius=1.0, thresh=3):
	fft = ffteng.transform(a)
	pow = numpy.absolute(fft)
	### neil half pixel shift or powerspectra are not centered!
	pow = scipy.ndimage.interpolation.shift(pow, (-1, -1), order=1, mode='wrap')
	try:
		pow = numpy.log(pow)
	except OverflowError:
		pow = numpy.log(pow+1e-20)
	except:
		print('numpy.log failed, bypass')
		pass
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

def filled_sphere(shape, radius, center=None):
	"""
	creates a spherical mask of defined radius and center
	in an array of the provided shape
	with value of 0 inside the sphere and 1 outside the sphere
	"""
	r2 = radius*radius
	if center is None:
		### set to center of array
		center = ((shape[0]-1)/2.0),((shape[1]-1)/2.0),((shape[2]-1)/2.0)
	def func(i0, i1, i2):
		ii0 = i0 - center[0]
		ii1 = i1 - center[1]
		ii2 = i2 - center[2]
		rr2 = ii0**2 + ii1**2 + ii2**2
		c = numpy.where(rr2<r2, 0.0, 1.0)
		return c
	return numpy.fromfunction(func, shape)

def filled_circle(shape, radius=None, center=None):
	"""
	creates a circle mask of defined radius and center
	in an array of the provided shape
	with value of 0 inside the circle and 1 outside the circle
	"""
	if radius is None:
		radius = (min(shape)//2)
	r2 = radius*radius
	if center is None:
		### set to center of array
		center = ((shape[0]-1)/2.0),((shape[1]-1)/2.0)
	def func(i0, i1):
		ii0 = i0 - center[0]
		ii1 = i1 - center[1]
		rr2 = ii0**2 + ii1**2
		c = numpy.where(rr2<r2, 0.0, 1.0)
		return c
	return numpy.fromfunction(func, shape)

def fromRadialFunction(funcrad, shape, **kwargs):
	center_r = ((shape[0] - 1)/2.0)
	center_c = ((shape[1] - 1)/2.0)
	def funcrc(r, c, **kwargs):
		rr = r - center_r
		cc = c - center_c
		rad = numpy.hypot(rr,cc)
		return funcrad(rad, **kwargs)
	result = numpy.fromfunction(funcrc, shape, **kwargs)
	return result

def fromPolarBinFunction(funcpolar, shape, **kwargs):
	center_r = ((shape[0] - 1)/2.0)
	center_c = ((shape[1] - 1)/2.0)
	def funcrc(r, c, **kwargs):
		rr = r - center_r
		cc = c - center_c
		rad = numpy.hypot(rr,cc)
		phi = numpy.arctan2(rr,cc)
		return funcpolar(rad, phi, **kwargs)
	result = numpy.fromfunction(funcrc, shape, **kwargs)
	return result

def center_mask(a, mask_radius, copy=False):
	if copy:
		a = numpy.array(a)
	shape = a.shape
	center = (shape[0]//2), (shape[1]//2)
	center_square = a[center[0]-mask_radius:center[0]+mask_radius, center[1]-mask_radius:center[1]+mask_radius]
	cs_shape = center_square.shape
	cs_center = (cs_shape[0]//2), (cs_shape[1]//2)
	circ = filled_circle(cs_shape,mask_radius)
	center_square[:] = center_square * circ.astype(center_square.dtype)
	if copy:
		return a

def swap_quadrants(a):
	shift0 = (a.shape[0]//2)
	shift1 = (a.shape[1]//2)
	a = numpy.roll(a, shift0, 0)
	a = numpy.roll(a, shift1, 1)
	return a

def pad(im, value=None, factor=None):
	# maybe use numpy.concatenate instead?
	if value is None:
		value = arraystats.mean(im)
	if factor is None:
		factor = 2
	padshape = im.shape[0]*factor, im.shape[1]*factor
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
	def __init__(self, image, mask, n, center, mean, stddev, roundness, maxpos, label_index=1):   #wjr
		self.image = image
		self.mask = mask
		self.stats = {"center":center, "n":n, "mean":mean, "stddev":stddev, "size":0, "roundness":roundness, "maximum_position":maxpos, "label_index":label_index}  #wjr

def highest_peaks(blobs, n):
	"""
	filter out no more than n blobs that have the highest mean
	"""
	## sort blobs based on mean
	def blob_compare(x,y):
		if float(x.stats['mean']) < float(y.stats['mean']): return 1
		else: return -1
	sortedblobs = list(blobs)
	sortedblobs.sort(key=functools.cmp_to_key(blob_compare))
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
	sortedblobs.sort(key=functools.cmp_to_key(blob_compare))
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
	imcenter = (shape[0]//2), (shape[1]//2)
	distmap = {}
	for blob in blobs:
		center = blob.stats['center']
		distance = numpy.hypot(center[0]-imcenter[0],center[1]-imcenter[1])
		distmap[blob] = distance
	## sort blobs based on distance
	def dist_cmp(x,y):
		if (distmap[x] > distmap[y]):
			return 1
		elif distmap[x] < distmap[y]:
			return -1
		else:
			return 0
	sortedblobs = list(blobs)
	sortedblobs.sort(key=functools.cmp_to_key(dist_cmp))
	sortedblobs = sortedblobs[:n]
	## make new list of blobs with n closest, same order as before
	newblobs = []
	for blob in blobs:
		if blob in sortedblobs:
			newblobs.append(blob)
	return newblobs


## using scipy.ndimage to find blobs
def scipylabels(mask):
	labelstruct = numpy.ones((3,3))
	labels,n = scipy.ndimage.label(mask, labelstruct)
	return labels, n

def scipyblobs(im,mask):
	labels,n = scipylabels(mask)
	## too bad ndimage module is inconsistent with what is returned from
	## the following functions.  Sometiems a list, sometimes a single value...
	if n==0:
		centers = []
		sizes = []
		stds = []
		means = []
		maxpos = []
	else:
		centers = scipy.ndimage.center_of_mass(im,labels,list(range(1,n+1)))
		sizes = numpy.histogram(labels,n,(1,n+1))[0]
		stds = scipy.ndimage.standard_deviation(im,labels,list(range(1,n+1)))
		means = scipy.ndimage.mean(im,labels,list(range(1,n+1)))
		perimeters = calc_perimeter(mask,labels)
		maxpos = scipy.ndimage.maximum_position(im,labels,list(range(1,n+1)))
		## scipy has changed to return array when there is one answer in 0.9
		## This single value case for n=1 only needed for older versions
		if n==1 and isinstance(means,float):
			centers = [centers]
			stds = [stds]
			means = [means]
			maxpos = [maxpos]
			perimeters = [perimeters]    # wjr
		else:
			centers = list(map(numpy.array, centers))

	blobs = []
# wjr replace moment of inertia with ration of area to perimeter: see somments below
# change variable 'moment' to 'roundness'
# wjr replacing moment-of-inertial calculation with a ratio of (4 pi * area) to perimeter**2
# for circles, should be 1 (4 pi * pi r**2 = 4 Pi**2 r**2 == (2pi * r) **2 == perimiter**2
# other shapes will be <1
	fourpi = 4 * math.pi
	for i in range(n):
		blobs.append({'center':centers[i], 'n':sizes[i], 'mean':means[i],'stddev':stds[i],'roundness':fourpi * sizes[i]/(perimeters[i]*perimeters[i]), 'maximum_position':maxpos[i], 'label_index':i})
	return blobs

def calc_perimeter(input, labels):
	"""
	Calculate the perimeter of the shape in the array.
 	Perimeter is calculated by seeing how many active neighbors every active point has and subtracting them from 4

	"""
	#input = numpy.asarray(input)
	if labels is None:
		raise RuntimeError('labels are needed')
	if labels.shape != input.shape:
		raise RuntimeError('input and labels shape are not equal')
	perimeters = []
	for label in scipy.ndimage.find_objects(labels):
		#submask = input[label].copy()
		submask = input[label]
		perimeter = _perimeter(submask)
		perimeters.append(perimeter)
	return perimeters

def _perimeter(mat):
	perimeter = 0;
	root2 = math.sqrt(2)
	Row,Col = mat.shape	
	# Traversing the matrix and finding ones to
	# calculate their contribution.
	for i in range(0, Row):
		for j in range(0, Col):
			if (mat[i][j]):
				sides = (4 - _numofneighbour(mat, i, j, Row, Col));
				if sides == 2:  # wjr correct for pixelation of perimter
					sides = root2
				perimeter += sides 
	#print("Row=%i Col=%i,      perimeter is %i and area is %i, this calc of roundness is %f \n" %(Row,Col,perimeter,a, r))
	return perimeter;


def _numofneighbour(mat, i, j, R, C):
# wjr add code to determine perimeter, this function counts the number of non-zero neighbors a point has
# This code is contributed by Akanksha Rai
	count = 0;
	# UP
	if (i > 0 and mat[i - 1][j]):
		count+= 1;
	# LEFT
	if (j > 0 and mat[i][j - 1]):
 		count+= 1;
	# DOWN
	if (i < R-1 and mat[i + 1][j]):
  		count+= 1
	# RIGHT
	if (j < C-1 and mat[i][j + 1]):
		count+= 1;
	return count;

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

def find_blobs(image, mask, border=0, maxblobs=300, maxblobsize=100, minblobsize=0, minblobroundness=0.8, method="central", summary=False):
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
	isinf = 0
	isnan = 0
	toobig = 0
	toosmall = 0
	toooblong = 0
	for blob in blobs:
		fakeblob = Blob(image, mask, blob['n'], blob['center'], blob['mean'], blob['stddev'], blob['roundness'], blob['maximum_position'], blob['label_index'])
		# scipy.ndimage.center_of_mass may return inf or nan which we don't want.
		if math.isinf(blob['center'][0]) or math.isinf(blob['center'][1]):
			isinf += 1
			continue
		if math.isnan(blob['center'][0]) or math.isnan(blob['center'][1]):
			isnan += 1
			continue
		if blob['n'] >= maxblobsize:
			toobig += 1
			continue
		if blob['n'] < minblobsize:
			toosmall += 1
			continue
		if minblobroundness is not None and blob['roundness'] <= minblobroundness:   # wjr change > to < since moment is now redefined as roundness, where 1 is circular, <1 is non circular
			toooblong += 1
			#print( "ignored because roundness = %f and minimum is %f \n" %(blob['roundness'],minblobroundness))
#			print("size of blob is %d\n" %blob['n'])
			continue
		fakeblobs.append(fakeblob)
	if summary is True:
		sys.stderr.write("BLOB summary: %d total / %d invalid number / %d too big / %d too small / %d too oblong\n"
			%(len(fakeblobs),isinf+isnan, toobig,toosmall,toooblong,))

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

def hasPointsInLabel(labels, n, points_of_interest):
	'''
	Return a list of boolean.
	Value is True if any of pointis_of_interest is in the labeled area.
	Input is a list of points in (row,col)
	'''
	p_labels = []
	for p in points_of_interest:
		# row, col
		p_labels.append(labels[p[0],p[1]])
	return list(map((lambda x: x+1 in p_labels), range(n)))

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

def bin(image, binning0, binning1=0):
	if binning1 == 0:
		binning1 = binning0
	if binning0==1 and binning1==1:
		return image
	return numextension.bin(image, binning0, binning1)

def bin2(a, factor):
	'''
	This is based on: http://scipy.org/Cookbook/Rebinning
	It is simplified to the case of a 2D array with the same
	binning factor in both dimensions.
	'''
	oldshape = a.shape
	newshape = (numpy.asarray(oldshape)//factor).astype(int)
	tmpshape = (newshape[0], factor, newshape[1], factor)
	f = factor * factor
	binned = numpy.sum(numpy.sum(numpy.reshape(a, tmpshape), 1), 2)/ float(f)
	return binned

def bin2m(a, factor):
	'''
	Median instead of mean for bin2
	'''
	oldshape = a.shape
	newshape = (numpy.asarray(oldshape)//factor)
	tmpshape = (newshape[0], factor, newshape[1], factor)
	binned = stats.median(stats.median(numpy.reshape(a, tmpshape), 1), 2)
	return binned

def bin2f(a, factor):
	'''
	Binning in Fourier space
	'''
	fft = ffteng.transform(a)
	fft = numpy.fft.fftshift(fft)
	xstart = int( fft.shape[0]/2 * (1 - (1.0/factor)))
	xend   = int( fft.shape[0]/2 * (1 + (1.0/factor)))
	ystart = int( fft.shape[1]/2 * (1 - (1.0/factor)))
	yend   = int( fft.shape[1]/2 * (1 + (1.0/factor)))
	#print("%d:%d  ,  %d:%d\n"%(xstart,xend,ystart,yend,))
	cutfft = fft[xstart:xend, ystart:yend]
	cutfft = numpy.fft.fftshift(cutfft)
	#print(cutfft.shape, fft.shape)
	binned = (ffteng.itransform(cutfft)/float(factor**2))
	return binned

def fourier_scale(a, boxsize):
	'''
	Scaling in Fourier space
	'''
	fft = ffteng.transform(a)
	fft = numpy.fft.fftshift(fft)
	initboxsize = max(a.shape)
	if initboxsize == boxsize:
		return a
	factor = (initboxsize/float(boxsize))
	xstart = int( (fft.shape[0]//2) - (boxsize//2) )
	xend   = int( (fft.shape[0]//2) + (boxsize//2) )
	ystart = int( (fft.shape[1]//2) - (boxsize//2) )
	yend   = int( (fft.shape[1]//2) + (boxsize//2) )
	#print("%d:%d  ,  %d:%d\n"%(xstart,xend,ystart,yend,))
	cutfft = fft[xstart:xend, ystart:yend]
	cutfft = numpy.fft.fftshift(cutfft)
	#print(cutfft.shape, fft.shape)
	binned = (ffteng.itransform(cutfft)/float(factor**2))
	return binned

def bin3(a, factor):
	'''
	This is based on: http://scipy.org/Cookbook/Rebinning
	It is simplified to the case of a 3D array with the same
	binning factor in both dimensions.
	'''
	oldshape = a.shape
	newshape = (numpy.asarray(oldshape)/factor)
	tmpshape = (newshape[0], factor, newshape[1], factor, newshape[2], factor)
	f = factor * factor * factor
	binned = (numpy.sum(numpy.sum(numpy.sum(numpy.reshape(a, tmpshape), 1), 2), 3)/ f)
	#binned = stats.median(stats.median(numpy.reshape(a, tmpshape), 1), 2)
	return binned

def bin3f(a, factor):
	'''
	Binning in Fourier space
	'''
	fft = ffteng.transform(a)
	fft = numpy.fft.fftshift(fft)
	xstart = int( fft.shape[0]/2 * (1 - (1.0/factor)))
	xend   = int( fft.shape[0]/2 * (1 + (1.0/factor)))
	ystart = int( fft.shape[1]/2 * (1 - (1.0/factor)))
	yend   = int( fft.shape[1]/2 * (1 + (1.0/factor)))
	zstart = int( fft.shape[2]/2 * (1 - (1.0/factor)))
	zend   = int( fft.shape[2]/2 * (1 + (1.0/factor)))
	cutfft = fft[
		xstart:xend,
		ystart:yend,
		zstart:zend,
	]
	cutfft = numpy.fft.fftshift(cutfft)
	binned = (ffteng.itransform(cutfft)/float(factor**3))
	return binned

def shrink_factor(shape):
	'''
	Return the binning to keep correlation efficient.
	'''
	max_dim = max(shape)
	for b in (1,2,4,8):
		if max_dim // b <= 1440: # based on k3 dimension
			break
	return b

def shrink_offset(oldshape):
	'''
	Return the offset for shrinking to keep correlation efficient.
	'''
	b = shrink_factor(oldshape)
	if b > 1:
		newshape = (b*(oldshape[0]//b), b*(oldshape[1]//b))
		offset = ((oldshape[0] - newshape[0]) // 2, (oldshape[1] - newshape[1]) // 2)
	else:
		offset = (0,0)
	return offset

def shrink(image):
	oldshape = image.shape
	offset = (0,0)
	b = shrink_factor(oldshape)
	if b > 1:
		newshape = (b*(oldshape[0]//b), b*(oldshape[1]//b))
		offset = shrink_offset(oldshape)
		image = image[offset[0]:offset[0]+newshape[0], offset[0]:offset[1]+newshape[1]]
	return bin(image, b)

def crop_at(im, center, shape, mode='wrap', cval=None):
	'''
	Crops an image such that the resulting image has im[center] at the center
	Image is treatead as wrapping around at the edges.
	'''
	## can't crop area larger than image
	if shape[0]>im.shape[0] or shape[1]>im.shape[1]:
		raise ValueError('crop_at: crop shape %s must not be larger than image shape %s' % (shape, im.shape))
	if center == 'center':
		center = (im.shape[0]/2.0) - 0.5, (im.shape[1]/2.0) - 0.5
	croppedcenter = (shape[0]/2.0) - 0.5, (shape[1]/2.0) - 0.5
	shift = croppedcenter[0]-center[0], croppedcenter[1]-center[1]
	if mode == 'constant':
		shifted = scipy.ndimage.shift(im, shift, mode=mode, cval=cval, order=1)
	else:
		shifted = scipy.ndimage.shift(im, shift, mode=mode, order=1)
	cropped = shifted[:shape[0], :shape[1]]
	return cropped

def center_from_shape(shape):
	'''
Calculate the center coordinate of an image based on its shape.
Each value in the coordinate is calculated independently and could
result in either a float or int.  Result may be mixed floats and ints.
	'''
	center = []
	for x in shape:
		if x < 1:
			raise ValueError('Invalid shape: %s' % (shape,))
		half_floor = x//2
		if x % 2:
			center.append(int(half_floor))
		else:
			center.append(float(half_floor-0.5))
	return center

crop_modes = ('wrap','zero')
def crop(im, shape, center=None, mode='wrap', output_type=None):
	'''
Crop an nd-array to given shape.

If center is given, it indicates what position of the input image will
become the center of the output image. It will default to the center of
the input image.

mode may either be 'wrap' or 'zero' to indicate what happens out of bounds.

output_type indicates the desired numpy dtype of the output array.  If not
given, it defaults to the same as the input (interpolations may be rounded
to integers, for example).
	'''
	ndims_in = len(im.shape)
	ndims_out = len(shape)
	if ndims_in != ndims_out:
		raise ValueError('crop: dimension mismatch, input is %d-D, output is %d-D' % (ndims_in, ndims_out))

	if mode not in crop_modes:
		raise ValueError('Invalid mode "%s".  Must select from %s.' % (mode, crop_modes,))

	if center is None:
		center = center_from_shape(im.shape)
	out_center = center_from_shape(shape)

	interp = False  # turn on if interpolation is necessary
	shift = []
	for i in range(ndims_in):
		s = out_center[i]-center[i]
		if isinstance(s,float) and not s.is_integer():
			interp = True
		else:
			s = int(-s)
		shift.append(s)

	if interp:
		if mode == 'zero':
			shifted = scipy.ndimage.shift(im, shift, output=output_type, mode='constant', cval=0, order=1)
		else:
			shifted = scipy.ndimage.shift(im, shift, output=output_type, mode='wrap', order=1)
		cropped = shifted[:shape[0], :shape[1]]
	else:
		if mode == 'wrap':
			cropped = im
			for i in range(ndims_in):
				indices = list(range(shift[i],shift[i]+shape[i]))
				cropped = cropped.take(indices, axis=i, mode='wrap')
			if output_type is not None:
				cropped = numpy.asarray(cropped, output_type)
		else:
			if output_type:
				dtype = output_type
			else:
				dtype = im.dtype
			cropped = numpy.zeros(shape, dtype)
			slices_in = []
			slices_out = []
			do_it = True
			for i in range(ndims_in):
				start = shift[i]
				end = start+shape[i]
				if start < 0:
					start_in = 0
					start_out = -start
				elif start >= im.shape[i]:
					do_it = False
					break
				else:
					start_in = start
					start_out = 0
				if end <= 0:
					do_it = False
					break
				elif end > im.shape[i]:
					end_in = im.shape[i]
					end_out = shape[i]-end+im.shape[i]
				else:
					end_in = end
					end_out = shape[i]
				slices_in.append(slice(start_in,end_in))
				slices_out.append(slice(start_out,end_out))
			if do_it:
				cropped[slices_out] = im[slices_in]
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
	im[0] = ((im[0] + im[-1])/ 2.0)
	im[-1] = im[0]

	im[:,0] = ((im[:,0] + im[:,-1])/ 2.0)
	im[:,-1] = im[:,0]

	for sign in (-1,1):
		for i in range(1,boundary):
			im[sign*i] = (im[sign*i]*0.1 + im[sign*i-sign]*0.9)
			im[:,sign*i] = (im[:,sign*i]*0.1 + im[:,sign*i-sign]*0.9)

def polarBin(input, nbins_r, nbins_t):
	'''
Polar binning of a real space image.  The polar transform is centered at
the center of the image
input: an image
nbins_r: number of radial bins.
nbins_t: the number of angular bins.
Returns:  (bins, r_centers, t_centers)
     where:
          bins: result 2-D image with r on the first axis, t on the second axis
          r_centers: The sequence of radial values represented in the bins
          t_centers: The sequence of angular values represented in the bins
	'''
	## Full radial range (result will have empty bins):
	r_min = 0.0
	r_max = numpy.hypot((input.shape[0]/ 2.0), (input.shape[1]/ 2.0))

	r_bins,r_inc = numpy.linspace(r_min, r_max, num=nbins_r+1, retstep=True)
	# excluding r_min
	r_centers = r_bins[1:] - (r_inc/2.0)

	## Full angular range from -pi to pi
	t_min = -numpy.pi
	t_max = numpy.pi
	t_bins,t_inc = numpy.linspace(t_min, t_max, num=nbins_t+1, retstep=True)
	t_centers = t_bins[1:] - (t_inc/2.0)

	## Determine coordinates on center
	indices = numpy.indices(input.shape)
	center_row = int(((input.shape[0]+1)// 2) ) # integer division intended
	center_col = int(((input.shape[1]+1)// 2) ) # integer division intended
	indices[0][:] -= center_row
	indices[:][1] -= center_col

	## Determine r,theta polar coords of each row,column coord.
	r_indices = numpy.hypot(*indices)
	t_indices = numpy.arctan2(*indices)

	## split up image into bins by radius and angle
	r_labels = numpy.digitize(r_indices.flat, r_bins) - 1
	r_labels.shape = r_indices.shape
	t_labels = numpy.digitize(t_indices.flat, t_bins) - 1
	t_labels.shape = t_indices.shape

	## combine r_labels and t_labels into full set of labels:
	rt_labels = nbins_t * r_labels + t_labels + 1

	## calculate mean value of each bin
	rt_bins = scipy.ndimage.mean(input, rt_labels, numpy.arange(nbins_r*nbins_t)+1)

	## turn result into 2-D array
	rt_bins = numpy.asarray(rt_bins)
	rt_bins.shape = nbins_r, nbins_t

	# interpolate NaN in the array which came from bins with no item
	for tbin in range(nbins_t):
		rt = rt_bins[:,tbin]
		nan_indices = numpy.where(numpy.isnan(rt))
		if not nan_indices:
			continue
		ind = numpy.where(~numpy.isnan(rt))[0]
		values = rt[ind]
		for nan_ind in numpy.where(numpy.isnan(rt))[0]:
			good_value = numpy.interp(nan_ind, ind, values, left=values[0], right=values[-1])
			rt[nan_ind] = good_value
		rt_bins[:,tbin] = rt
	return rt_bins, r_centers, t_centers

def radialAverageImage(a):
	'''
	Make radial average image of the same shape. Origin of the polar transform is
	at the center of the image
	'''
	bins =  min(a.shape)
	# doing one bin in angle
	nbins_t = 1
	pbin, r_center, t_center = polarBin(a, bins, nbins_t)
	radial_avg = pbin[:,0]

	def radial_value(rho, **kwargs):
		return numpy.interp(rho, r_center, radial_avg, right=radial_avg[-1])

	return fromRadialFunction(radial_value, a.shape)

def flipImageTopBottom(imagearray):
	return numpy.flipud(imagearray)

def flipImageLeftRight(imagearray):
	return numpy.fliplr(imagearray)

def rotateImage90Degrees(imagearray,ntimes=1):
	'''
	Rotation without interpolation. Rotation is clockwise.
	'''
	return numpy.rot90(imagearray,ntimes)

def clipImage(imagearray,npixels):
	'''
	Clips a given image from the center by npixels and returns a new clipped array with new dimensions
	'''
	return imagearray[npixels:-npixels,npixels:-npixels]

def padImage(imagearray, npixels):
	'''
	Pads a given image by npixels and returns a new padded array with new dimensions. The new pixels are given the mean value of imagearray.
	'''
	#Note this can be done more efficiently in  numpy 1.10 and greater with numpy.fill or numpy.full
	newshape=[n+(2*npixels) for n in imagearray.shape]
	newarray=numpy.ones(newshape,dtype=imagearray.dtype)
	#mean=imagearray.mean()
	#### There is a bug in numpy 1.6 where mean doesn't work for 8K images. Instead using edge mean for now
	stats=edgeStats(imagearray)
	mean=stats['mean']
	newarray=newarray*mean
	newarray[npixels:-npixels,npixels:-npixels]=imagearray
	return newarray

def clipAndPadImage(imagearray,npixels):
	'''
	Clips an image by npixels and pads it back out to its original dimensions substituting the pixels at the edges with the mean
	'''
	newarray=clipImage(imagearray,npixels)
	newarray=padImage(newarray,npixels)
	return newarray

def edgeStats(imagearray):
	'''
	Returns the mean and standard deviation for the edge pixels of imagearray
	'''
	edgepix=numpy.append(imagearray[0,0:],imagearray[-1,0:])
	edgepix=numpy.append(edgepix,imagearray[0:,0])
	edgepix=numpy.append(edgepix,imagearray[0:,-1])
	#print(edgepix)
	mean=edgepix.mean()
	std=edgepix.std()
	return {'mean':mean,'std':std}

###############################################
# functions for correcting raw images
###############################################

def normalizeImageArray(rawarray, darkarray, normarray, darkscale=1, badrowlist=None, badcolumnlist=None):
	if darkscale != 1:
		darkarray=(darkarray/darkscale)
	diff = rawarray - darkarray
	r = diff * normarray
	## remove nan and inf
	r = numpy.where(numpy.isfinite(r), r, 0)
	if badrowlist is not None or badcolumnlist is not None:
		r = replaceBadRowsAndColumns(r,badrowlist,badcolumnlist)
	return r

def normalizeFromDarkAndBright(rawarray, darkarray, brightarray, scale=1, badrowlist=None, badcolumnlist=None, border=None):
	if scale != 1:
		darkarray=(darkarray/scale)
		brightarray=(brightarray/scale)
	bminusd=(brightarray-darkarray)
	m=bminusd.mean()
	gain=(m/bminusd)
	correctedarray=(rawarray-darkarray)*gain
	## remove nan and inf
	correctedarray = numpy.where(numpy.isfinite(correctedarray), correctedarray, 0)
	if badrowlist is not None or badcolumnlist is not None:
		correctedarray = replaceBadRowsAndColumns(correctedarray,badrowlist,badcolumnlist)
	if border is not None:
		correctedarray = clipAndPadImage(correctedarray,border)
	return correctedarray

def replaceBadRowsAndColumns(imagearray,badrowlist=[], badcolumnlist=[]):
	def _getGoodNeighbors(badindividual, badlist, maxallowed):
		for n in badlist:
			lowerneighbor=n-1
			higherneighbor=n+1
			while lowerneighbor in badlist:
				lowerneighbor -=1
			while higherneighbor in badlist:
				higherneighbor +=1
			if lowerneighbor <= 0 :
				lowerneighbor=higherneighbor
			if higherneighbor >= maxallowed:
				higherneighbor=lowerneighbor
		return (lowerneighbor,higherneighbor)
	for badrow in badrowlist:
		lowerneighbor,higherneighbor=_getGoodNeighbors(badrow,badrowlist,imagearray.shape[1])
		newrow=((imagearray[lowerneighbor,:] + imagearray[higherneighbor,:])//2)
		imagearray[badrow,:]=newrow
	for badcol in badcolumnlist:
		lowerneighbor,higherneighbor=_getGoodNeighbors(badcol,badcolumnlist,imagearray.shape[0])
		newcol=((imagearray[:,lowerneighbor] + imagearray[:,higherneighbor])//2)
		imagearray[:,badcol]=newcol
	return imagearray

