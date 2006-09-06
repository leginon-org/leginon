#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#
import numarray
import numarray.image
import numarray.nd_image
import fftengine
import numextension

ffteng = fftengine.fftEngine()

## numarray seems to use infinity as a result of zero
## division, but I can find no infinity constant or any other way of 
## producing infinity without first doing a zero division
## Here is my infinity contant
inf = 1e500

def toFloat(inputarray):
	'''
	if inputarray is an integer type:
		return a Float32 version of it
	else:
		return inputarray
	'''
	if isinstance(inputarray.type(), numarray.IntegralType):
		return inputarray.astype(numarray.Float32)
	else:
		return inputarray

def stdev(inputarray, known_mean=None):
	return numarray.nd_image.standard_deviation(inputarray)

def mean(inputarray):
	return numarray.nd_image.mean(inputarray)

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

def scaleToShape(array, scaledshape):
	scale = (float(scaledshape[0])/float(array.shape[0]),
						float(scaledshape[1])/float(array.shape[1]))
	return scale(array, scale)

def scale(array, scale):
	if scale == (1.0, 1.0):
		return array

	indices = [None, None]
	for i in range(2):
		index = numarray.arrayrange(int(round(scale[i]*array.shape[i])))
		index = index / scale[i]
		## mystery stuff:
		#index = numarray.floor(index+scale[i]/2.0+0.5).astype(numarray.Int)
		index = numarray.floor(index).astype(numarray.Int)
		indices[i] = index

	return numarray.take(numarray.take(array, indices[0]), indices[1], 1)

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

## see the correlator.py module for a more efficient way to do
## correlations on a series of images
def cross_correlate(im1, im2):
	im1fft = ffteng.transform(im1)
	if im1 is im2:
		im2fft = im1fft
	else:
		im2fft = ffteng.transform(im2)
	xcor = numarray.multiply(numarray.conjugate(im2fft), im1fft)
	result = ffteng.itransform(xcor)
	return result

def auto_correlate(image):
	'''
	minor speed up over cross_correlate
	'''
	imfft = ffteng.transform(image)
	xcor = numarray.absolute(imfft) ** 2
	result = ffteng.itransform(xcor)
	return result

def phase_correlate(im1, im2):
	im1fft = ffteng.transform(im1)
	if im1 is im2:
		im2fft = im1fft
	else:
		im2fft = ffteng.transform(im2)
	xcor = numarray.multiply(numarray.conjugate(im2fft), im1fft)
	xcor_abs = numarray.absolute(xcor) + 0.00000000000000001
	phasecor = xcor / xcor_abs
	pc = ffteng.itransform(phasecor)
	## average out the artifical peak at 0,0
	pc[0,0] = (pc[0,1] + pc[0,-1] + pc[1,0] + pc[-1,0]) /4.0
	return pc

## The Blob.add_point method below is recursive while searching for neighbors.
## Here we make sure that python will allow enough recursion to get decent
## sized blobs.
import sys
reclim = sys.getrecursionlimit()
if reclim < 20000:
	sys.setrecursionlimit(20000)

class OLDBlob(object):
	'''
	a Blob instance represets a connected set of pixels
	'''
	neighbor_deltas = numarray.array(((-1,-1),(-1,0),(-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)))
	#maxpoints = 2000
	def __init__(self, image, mask):
		self.image = image
		self.mask = mask
		self.pixel_list = []
		self.value_list = []
		self.stats = {}
		self.recursionerror = False

	def calc_stats(self):
		if self.stats:
			return
		pixel_array = numarray.array(self.pixel_list, numarray.Float32)
		sum = numarray.sum(pixel_array)
		squares = pixel_array**2
		sumsquares = numarray.sum(squares)
		n = len(pixel_array)
		self.stats['n'] = n

		## center
		self.stats['center'] = sum / n

		## size
		if n > 1:
			tmp1 = n * sumsquares - sum * sum
			tmp2 = (n - 1) * n
			self.stats['size'] = numarray.sqrt(tmp1 / tmp2)
		else:
			self.stats['size'] = numarray.zeros((2,),numarray.Float32)
		
		## get value array using pixel list
		pixel_array.transpose()
		rows = pixel_array[0]
		cols = pixel_array[1]
		try:
			value_array = self.image[rows,cols]
		except:
			print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
			print 'SHAPE', self.image.shape
			print 'LEN RC', len(rows), len(cols)
			print 'ROWS', minmax(rows)
			print 'COLS', minmax(cols)
			print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
			raise

		self.value_array = value_array.astype(numarray.Float32)
		valuesum = numarray.sum(self.value_array)
		valuesquares = self.value_array ** 2
		sumvaluesquares = numarray.sum(valuesquares)

		## mean pixel value
		self.stats['mean'] = valuesum / n

		## stddev pixel value
		if n > 1:
			tmp1 = n * sumvaluesquares - valuesum * valuesum
			if tmp1 < 0:
				tmp1 = 0.0
			self.stats['stddev'] = float(numarray.sqrt(tmp1 / tmp2))
		else:
			self.stats['stddev'] = 0.0

		## whether this blob is complete because of recursion error
		self.stats['complete'] = not self.recursionerror
		if self.recursionerror:
			print 'ERROR', n

	def print_stats(self):
		for stat in ('complete', 'n', 'center', 'size', 'mean', 'stddev'):
			print '\t%s:\t%s' % (stat, self.stats[stat])

class Blob(object):
	def __init__(self, image, mask, n, center, mean, stddev):
		self.image = image
		self.mask = mask
		self.stats = {'center': center, 'n':n, 'mean':mean, 'stddev':stddev,'size':0}

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

## using numarray.nd_image to implement numextension.blobs
labelstruct = numarray.array(((1,1,1),(1,1,1),(1,1,1)))
def numarrayblobs(im,mask):
	labels,n = numarray.nd_image.label(mask, labelstruct)
	## too bad nd_image module is inconsistent with what is returned from
	## the following functions.  Sometiems a list, sometimes a single value...
	if n==0:
		centers = []
		sizes = []
		stds = []
		means = []
	else:
		centers = numarray.nd_image.center_of_mass(im,labels,range(1,n+1))
		sizes = numarray.nd_image.histogram(labels,1,n+1,n)
		stds = numarray.nd_image.standard_deviation(im,labels,range(1,n+1))
		means = numarray.nd_image.mean(im,labels,range(1,n+1))
		if n==1:
			centers = [centers]
			stds = [stds]
			means = [means]
		else:
			centers = map(numarray.array, centers)

	blobs = []
	for i in range(n):
		blobs.append({'center':centers[i], 'n':sizes[i], 'mean':means[i],'stddev':stds[i]})
	return blobs

def OLDnumarrayblobs(im):
	labels,n = numarray.nd_image.label(im, labelstruct)
	slices = numarray.nd_image.find_objects(labels)
	## should cache indices arrays
	indices = numarray.indices(im.shape)

	blobs = []
	for i in range(n):
		s = slices[i]
		roi_im = im[s]
		roi_lab = labels[s]
		roi_rows = indices[0][s]
		roi_cols = indices[1][s]

		## which elements are in this object
		condition = roi_lab == i+1

		blob = {}
		blob['pixelrow'] = numarray.compress(condition, roi_rows)
		blob['pixelcol'] = numarray.compress(condition, roi_cols)
		blob['pixelv'] = numarray.compress(condition, roi_im)

		blobs.append(blob)
	return blobs

def find_blobs(image, mask, border=0, maxblobs=300, maxblobsize=100, minblobsize=0):
	shape = image.shape

	### create copy of mask since it will be modified now
	tmpmask = numarray.array(mask, numarray.Int32)
	## zero out tmpmask outside of border
	if border:
		tmpmask[:border] = 0
		tmpmask[-border:] = 0
		tmpmask[:,:border] = 0
		tmpmask[:,-border:] = 0

	'''
	## find blobs the new way
	blobs = numextension.blobs(tmpmask)

	## then fake them into the original blob class
	fakeblobs = []
	toobig = 0
	toosmall = 0
	for blob in blobs:
		fakeblob = OLDBlob(image, mask)
		fakeblob.pixel_list = zip(blob['pixelrow'], blob['pixelcol'])
		if len(fakeblob.pixel_list) >= maxblobsize:
			toobig += 1
			continue
		if len(fakeblob.pixel_list) < minblobsize:
			toosmall += 1
			continue
		fakeblob.calc_stats()
		fakeblobs.append(fakeblob)
	'''

	blobs = numarrayblobs(image,tmpmask)
	fakeblobs = []
	toobig = 0
	toosmall = 0
	for blob in blobs:
		fakeblob = Blob(image, mask, blob['n'], blob['center'], blob['mean'], blob['stddev'])
		if blob['n'] >= maxblobsize:
			toobig += 1
			continue
		if blob['n'] < minblobsize:
			toosmall += 1
			continue
		fakeblobs.append(fakeblob)

	## limit to maxblobs
	if (maxblobs is not None) and (len(blobs) > maxblobs):
		blobs = near_center(shape, fakeblobs, maxblobs)
		print 'trimming number of blobs to %s closest to center' % (maxblobs,)
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

### python implementation of some Viewit functions

def threshold(a, limit):
	return a >= limit

def zscore(image):
	m = mean(image)
	s = stdev(image, known_mean=m)
	return (image - m) / s
