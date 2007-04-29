#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#
import numarray
import numarray.image
import numarray.nd_image as nd_image
import fftengine
import numextension
import math

ffteng = fftengine.fftEngine()

## These following stats functions have been replaced by they
## arraystats module
def stdev(inputarray, known_mean=None):
	return nd_image.standard_deviation(inputarray)

def mean(inputarray):
	return nd_image.mean(inputarray)

def min(inputarray):
	f = numarray.ravel(inputarray)
	i = numarray.argmin(f)
	return float(f[i])

def max(inputarray):
	f = numarray.ravel(inputarray)
	i = numarray.argmax(f)
	return float(f[i])

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
	return numarray.image.median(series)

def averageSeries(series):
	return numarray.image.average(series)

def scale(array, scale):
	if scale == 1.0:
		return array
	return numarray.nd_image.zoom(array, scale, order=1)

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
			minfrom = numarray.argmin(numarray.ravel(input))
			minfrom = numarray.ravel(input)[minfrom]
	if maxfrom is None:
		if extrema:
			maxfrom = extrema[1]
		else:
			maxfrom = numarray.argmax(numarray.ravel(input))
			maxfrom = numarray.ravel(input)[maxfrom]

	## prepare for fast math
	## with numarray, this is not necessary anymore
	#rangefrom = numarray.array((maxfrom - minfrom)).astype('f')
	#rangeto = numarray.array((maxto - minto)).astype('f')
	#minfrom = numarray.array(minfrom).astype('f')
	rangefrom = maxfrom - minfrom
	rangeto = maxto - minto

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	#output = (input - minfrom) * rangeto / rangefrom
	scale = float(rangeto) / rangefrom
	offset = minfrom * scale
	output = input * scale - offset

	return output

# resize and rotate filters:	NEAREST, BILINEAR, BICUBIC

def power(numericarray, mask_radius=1.0, thresh=3):
	fft = ffteng.transform(numericarray)
	pow = numarray.absolute(fft)
	try:
		pow = numarray.log(pow)
	except OverflowError:
		pow = numarray.log(pow+1e-20)

	pow = shuffle(pow)

	mask_radius = int(mask_radius / 100.0 * pow.shape[0])
	if mask_radius:
					center_mask(pow, mask_radius)

	m = mean(pow)
	s = stdev(pow, known_mean=m)
	minval = numarray.array(m-thresh*s, numarray.Float32)
	maxval = numarray.array(m+thresh*s, numarray.Float32)
	pow = numarray.clip(pow, minval, maxval)

	return pow

def filled_circle(shape, radius):
	r2 = radius*radius
	center = shape[0]/2,shape[1]/2
	def func(i0, i1):
		ii0 = i0 - center[0]
		ii1 = i1 - center[1]
		rr2 = numarray.power(ii0,2) + numarray.power(ii1,2)
		c = numarray.where(rr2<r2, 0.0, 1.0)
		return c
	return numarray.fromfunction(func, shape)

def center_mask(numericarray, mask_radius):
	shape = numericarray.shape
	center = shape[0]/2, shape[1]/2
	center_square = numericarray[center[0]-mask_radius:center[0]+mask_radius, center[1]-mask_radius:center[1]+mask_radius]
	m = mean(numericarray)
	cs_shape = center_square.shape
	cs_center = cs_shape[0]/2, cs_shape[1]/2
	circ = filled_circle(cs_shape,mask_radius)
	center_square[:] = center_square * circ.astype(center_square.type())

def shuffle(narray):
	'''
	take a half fft/power spectrum centered at 0,0
	and convert to full fft/power centered at center of image
	'''
	oldr,oldc = narray.shape
	r,c = newshape = oldr, (oldc-1)*2

	## create new full size array 
	new = numarray.zeros(newshape, narray.type())

	## fill in right half
	new[r/2:,c/2:] = narray[:r/2,1:]
	new[:r/2,c/2:] = narray[r/2:,1:]

	## fill in left half
	reverserows = -numarray.arrayrange(r) - 1
	reversecols = -numarray.arrayrange(c/2) - 1
	new[:,:c/2] = numarray.take(new[:,c/2:], reverserows, 0)
	new[:,:c/2] = numarray.take(new[:,:c/2], reversecols, 1)

	return new

def swap(numericarray):
	rows,cols = numericarray.shape
	newarray = numarray.zeros(numericarray.shape, numericarray.type())
	newarray[:rows/2] = numericarray[rows/2:]
	newarray[rows/2:] = numericarray[:rows/2]
	return newarray

def swap_row_halves(numericarray):
	rows,cols = numericarray.shape
	newarray = numarray.zeros(numericarray.shape, numericarray.type())
	newarray[:rows/2] = numericarray[rows/2:]
	newarray[rows/2:] = numericarray[:rows/2]
	return newarray

def swap_col_halves(numericarray):
	rows,cols = numericarray.shape
	newarray = numarray.zeros(numericarray.shape, numericarray.type())
	newarray[:,:cols/2] = numericarray[:,cols/2:]
	newarray[:,cols/2:] = numericarray[:,:cols/2]
	return newarray

def swap_quadrants(numericarray):
	newarray = swap_row_halves(numericarray)
	newarray = swap_col_halves(newarray)
	return newarray

def pad(im, value=None):
	# maybe use numarray.concatenate instead?
	if value is None:
		value = mean(im)
	padshape = im.shape[0]*2, im.shape[1]*2
	paddedimage = value * numarray.ones(padshape, im.type())
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
	def __init__(self, image, mask, n, center, mean, stddev, moment):
		self.image = image
		self.mask = mask
		self.stats = {"center":center, "n":n, "mean":mean, "stddev":stddev, "size":0, "moment":moment}

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
		distance = numarray.hypot(center[0]-imcenter[0],center[1]-imcenter[1])
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

## using nd_image to find blobs
labelstruct = numarray.array(((1,1,1),(1,1,1),(1,1,1)))
def numarrayblobs(im,mask):
	labels,n = nd_image.label(mask, labelstruct)
	## too bad nd_image module is inconsistent with what is returned from
	## the following functions.  Sometiems a list, sometimes a single value...
	if n==0:
		centers = []
		sizes = []
		stds = []
		means = []
	else:
		centers = nd_image.center_of_mass(im,labels,range(1,n+1))
		sizes = nd_image.histogram(labels,1,n+1,n)
		stds = nd_image.standard_deviation(im,labels,range(1,n+1))
		means = nd_image.mean(im,labels,range(1,n+1))
		moments = moment_of_inertia(im,labels,range(1,n+1))
		if n==1:
			centers = [centers]
			stds = [stds]
			means = [means]
		else:
			centers = map(numarray.array, centers)

	blobs = []
	for i in range(n):
		blobs.append({'center':centers[i], 'n':sizes[i], 'mean':means[i],'stddev':stds[i],'moment':moments[i]})
	return blobs

def moment_of_inertia(input, labels, index = None):
	"""
	Calculate the moment of inertia of of the array.

	The index parameter is a single label number or a sequence of
	label numbers of the objects to be measured. If index is None, all
	values are used where labels is larger than zero.
	"""
	input = numarray.asarray(input)
	if isinstance(input.type(), numarray.ComplexType):
		raise TypeError, 'Complex type not supported'
	if labels == None:
		raise RuntimeError, 'labels are needed'
	if labels.shape != input.shape:
		raise RuntimeError, 'input and labels shape are not equal'
	moments = []
	for label in nd_image.find_objects(labels):
		submask = input[label].copy()
		moment = _moment(submask)
		moments.append(moment)
	return moments


def _moment(subimage):
	if(subimage.shape[0]+subimage.shape[1] < 4):
		return 1.0
	twopi = 2*math.pi
	r0 = nd_image.center_of_mass(subimage)
	sqmat = _distsqmat(r0,subimage.shape)
	moi = nd_image.sum(subimage*sqmat)/(nd_image.sum(subimage)**2)*twopi
	return moi

def _distsqmat(r0,shape):
	indices = numarray.indices(shape)
	dx, dy = indices[0]-r0[0],indices[1]-r0[1]
	return (dx**2+dy**2)

def find_blobs(image, mask, border=0, maxblobs=300, maxblobsize=100, minblobsize=0, maxmoment=None, method="central"):
	shape = image.shape

	### create copy of mask since it will be modified now
	tmpmask = numarray.array(mask, numarray.Int32)
	## zero out tmpmask outside of border
	if border:
		tmpmask[:border] = 0
		tmpmask[-border:] = 0
		tmpmask[:,:border] = 0
		tmpmask[:,-border:] = 0

	blobs = numarrayblobs(image,tmpmask)
	fakeblobs = []
	toobig = 0
	toosmall = 0
	toooblong = 0
	for blob in blobs:
		fakeblob = Blob(image, mask, blob['n'], blob['center'], blob['mean'], blob['stddev'], blob['moment'])
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

	#print " ... blob summary:",len(fakeblobs),"total /",toobig,"toobig /",toosmall,"toosmall /",toooblong,"toooblong"

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
		if 0 <= r < image.shape[0]:
			image[r,col] = value
	for c in range(col-size,col+size):
		if 0 <= c < image.shape[1]:
			image[row,c] = value

def bin(image, binning):
	return numextension.bin(image, binning)

def bin2(a, factor):
	'''
	This is based on: http://scipy.org/Cookbook/Rebinning
	This version is modified to use numarray instead of numpy.
	It is also simplified to the case of a 2D array with the same
	binning factor in both dimensions.
	'''
	oldshape = a.shape
	newshape = numarray.asarray(oldshape)/factor
	tmpshape = (newshape[0], factor, newshape[1], factor)
	f = factor * factor
	binned = numarray.sum(numarray.sum(numarray.reshape(a, tmpshape), 1), 2) / f
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
		shifted = nd_image.shift(im, shift, mode=mode, cval=cval)
	else:
		shifted = nd_image.shift(im, shift, mode=mode)
	cropped = shifted[:shape[0], :shape[1]]
	return cropped

### python implementation of some Viewit functions

def threshold(a, limit):
	return a >= limit

def zscore(image):
	m = mean(image)
	s = stdev(image, known_mean=m)
	return (image - m) / s
