import Numeric
import fftengine

if fftengine.fftFFTW is None:
	ffteng = fftengine.fftNumeric()
#	print 'USING Numeric FFT'
else:
	ffteng = fftengine.fftFFTW()
#	print 'USING FFTW'

## Numeric seems to use infinity as a result of zero
## division, but I can find no infinity constant or any other way of 
## producing infinity without first doing a zero division
## Here is my infinity contant
inf = 1.0 / Numeric.array(0.0, Numeric.Float32)

def toFloat(inputarray):
	'''
	if inputarray is an integer type ('1','l','s','i'):
		return a Float32 version of it
	else:
		return inputarray
	'''
	if inputarray.typecode() in ('1lsi'):
		return inputarray.astype(Numeric.Float32)
	else:
		return inputarray

def stdev(inputarray):
	im = toFloat(inputarray)
	f = Numeric.ravel(im)
	inlen = len(f)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(f) / divisor
	try:
		bigsum = Numeric.sum((f - m)**2)
	except OverflowError:
		print 'OverflowError:  stdev returning None'
		return None
	stdev = Numeric.sqrt(bigsum / (len(f)-1))
	return stdev

def mean(inputarray):
	im = toFloat(inputarray)
	f = Numeric.ravel(im)
	inlen = len(f)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(f) / divisor
	return m

def min(inputarray):
	f = Numeric.ravel(inputarray)
	i = Numeric.argmin(f)
	return f[i]

def max(inputarray):
	f = Numeric.ravel(inputarray)
	i = Numeric.argmax(f)
	return f[i]

def sumSeries(series):
	if len(series) == 0:
		return None
	if len(series) == 1:
		return series[0]
	first = series[0]
	others = series[1:]
	sum = first.astype(Numeric.Float64)
	for other in others:
		sum += other
	return sum

def averageSeries(series):
	slen = len(series)
	if slen == 0:
		return None
	if slen == 1:
		return series[0]

	## this didn't work if a sum was too big for the type
	#sum = Numeric.sum(series)
	sum = sumSeries(series)

	divisor = Numeric.array(slen, Numeric.Float32)
	avg = sum / divisor
	return avg

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
			minfrom = Numeric.argmin(Numeric.ravel(input))
			minfrom = Numeric.ravel(input)[minfrom]
	if maxfrom is None:
		if extrema:
			maxfrom = extrema[1]
		else:
			maxfrom = Numeric.argmax(Numeric.ravel(input))
			maxfrom = Numeric.ravel(input)[maxfrom]

	## prepare for fast math
	rangefrom = Numeric.array((maxfrom - minfrom)).astype('f')
	rangeto = Numeric.array((maxto - minto)).astype('f')
	minfrom = Numeric.array(minfrom).astype('f')

	# this is a hack to prevent zero division
	# is there a better way to do this with some sort of 
	# float limits module rather than hard coding 1e-99?
	if not rangefrom:
		rangefrom = 1e-99

	#output = (input - minfrom) * rangeto / rangefrom
	scale = rangeto / rangefrom
	offset = minfrom * scale
	output = input * scale - offset

	return output

# resize and rotate filters:  NEAREST, BILINEAR, BICUBIC

def center_fill(input, size, value=0):
	rows,cols = input.shape
	center = rows/2, cols/2
	cenr, cenc = center
	input[cenr-size/2:cenr+size/2, cenc-size/2:cenc+size/2] = value

def power(numericarray):
	fft = ffteng.transform(numericarray)
	## should I square this?
	pow = Numeric.absolute(fft)
	pow = Numeric.log(pow)
	pow = Numeric.clip(pow, 8, 14)
	pow = shuffle(pow)
	return pow

def shuffle(narray):
	'''
	take a half fft/power spectrum centered at 0,0
	and convert to full fft/power centered at center of image
	'''
	oldr,oldc = narray.shape
	r,c = newshape = oldr, (oldc-1)*2

	## create new full size array 
	new = Numeric.zeros(newshape, narray.typecode())

	## fill in right half
	new[r/2:,c/2:] = narray[:r/2,1:]
	new[:r/2,c/2:] = narray[r/2:,1:]

	## fill in left half
	reverserows = -Numeric.arrayrange(r) - 1
	reversecols = -Numeric.arrayrange(c/2) - 1
	new[:,:c/2] = Numeric.take(new[:,c/2:], reverserows, 0)
	new[:,:c/2] = Numeric.take(new[:,:c/2], reversecols, 1)

	return new

def swap(numericarray):
	rows,cols = numericarray.shape
	newarray = Numeric.zeros(numericarray.shape, numericarray.typecode())
	newarray[:rows/2] = numericarray[rows/2:]
	newarray[rows/2:] = numericarray[:rows/2]
	return newarray

def zeroRow(inputarray, row):
	inputarray[row] = 0
	return inputarray

def zeroCol(inputarray, col):
	inputarray[:,col] = 0
	return inputarray

def fakeRows(inputarray, badrows, goodrow):
	fakerow = inputarray[goodrow]
	for row in badrows:
		inputarray[row] = fakerow
	return inputarray
	
def fakeCols(inputarray, badcols, goodcol):
	fakecol = inputarray[:,goodcol]
	for col in badcols:
		inputarray[:,col] = fakecol
	return inputarray

## see the correlator.py module for a more efficient way to do
## correlations on a series of images
def cross_correlate(im1, im2):
	im1fft = ffteng.transform(im1)
	if im1 is im2:
		im2fft = im1fft
	else:
		im2fft = ffteng.transform(im2)
	xcor = Numeric.multiply(Numeric.conjugate(im2fft), im1fft)
	result = ffteng.itransform(xcor)
	return result

def phase_correlate(im1, im2):
	im1fft = ffteng.transform(im1)
	if im1 is im2:
		im2fft = im1fft
	else:
		im2fft = ffteng.transform(im2)
	xcor = Numeric.multiply(Numeric.conjugate(im2fft), im1fft)
	phasecor = xcor / Numeric.absolute(xcor)
	pc = ffteng.itransform(phasecor)
	## average out the artifical peak at 0,0
	pc[0,0] = (pc[0,1] + pc[0,-1] + pc[1,0] + pc[-1,0]) /4.0
	return pc

## The Blob.add_point method below is recursive while searching for neighbors.
## Here we make sure that python will allow enough recursion to get decent
## sized blobs.
import sys
reclim = sys.getrecursionlimit()
if reclim < 2000:
	sys.setrecursionlimit(2000)

class Blob(object):
	'''
	a Blob instance represets a connected set of pixels
	'''
	neighbor_deltas = Numeric.array(((-1,-1),(-1,0),(-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)))
	maxpoints = 2000
	def __init__(self, image, mask):
		self.image = image
		self.mask = mask
		self.pixel_list = []
		self.value_list = []
		self.stats = {}
		self.recursionerror = False

	def add_point(self, row, col, tmpmask):
		'''
		attempt to add 
		'''
		recursionerror = False
		self.pixel_list.append((row, col))
		## turn off pixel in mask
		tmpmask[row,col] = 0
		## reset stats
		self.stats = {}

		# abort this blob if too many points
		# if we don't abort, we will hit a recursion limit
		if len(self.pixel_list) > self.maxpoints:
			return False

		# check neighbors
		neighbors = self.neighbor_deltas + (row,col)
		for neighbor in neighbors:
			if self.recursionerror:
				break
			try:
				value = tmpmask[neighbor]
			except IndexError:
				continue
			if value:
				try:
					self.add_point(neighbor[0],neighbor[1],tmpmask)
				except RuntimeError:
					self.recursionerror = True
					break
		return self.recursionerror

	def calc_stats(self):
		if self.stats:
			return
		pixel_array = Numeric.array(self.pixel_list, Numeric.Float32)
		sum = Numeric.sum(pixel_array)
		squares = pixel_array**2
		sumsquares = Numeric.sum(squares)
		n = len(pixel_array)
		self.stats['n'] = n

		## center
		self.stats['center'] = sum / n

		## size
		if n > 1:
			tmp1 = n * sumsquares - sum * sum
			tmp2 = (n - 1) * n
			self.stats['size'] = Numeric.sqrt(tmp1 / tmp2)
		else:
			self.stats['size'] = Numeric.zeros((2,),Numeric.Float32)
		
		## need to calculate value list here
		# this is fake:
		self.value_list = [2]

		value_array = Numeric.array(self.value_list, Numeric.Float32)
		valuesum = Numeric.sum(value_array)
		valuesquares = value_array ** 2
		sumvaluesquares = Numeric.sum(valuesquares)

		## mean pixel value
		self.stats['mean'] = valuesum / n

		## stddev pixel value
		if n > 1:
			tmp1 = n * sumvaluesquares - valuesum * valuesum
			if tmp1 < 0:
				tmp1 = 0.0
			self.stats['stddev'] = float(Numeric.sqrt(tmp1 / tmp2))
		else:
			self.stats['stddev'] = 0.0

		## whether this blob is complete because of recursion error
		self.stats['complete'] = not self.recursionerror
		if self.recursionerror:
			print 'ERROR', n

	def print_stats(self):
		for stat in ('complete', 'n', 'center', 'size', 'mean', 'stddev'):
			print '\t%s:\t%s' % (stat, self.stats[stat])

class TooManyBlobs(Exception):
	pass

def find_blobs(image, mask, border=0, maxblobs=300, maxblobsize=50):
	shape = image.shape
	blobs = []
	## create a copy of mask that will be modified
	tmpmask = mask.astype(Numeric.Int8)
	for row in range(border,shape[0]-border):
		for col in range(border,shape[1]-border):
			if tmpmask[row,col]:
				newblob = Blob(image, mask)
				err = newblob.add_point(row, col, tmpmask)
				if (maxblobsize is not None) and (len(newblob.pixel_list) > maxblobsize):
					continue
				if err:
					continue
				blobs.append(newblob)	
				if (maxblobs is not None) and (len(blobs) > maxblobs):
					raise TooManyBlobs('found more than %s blobs' % (maxblobs,))

	t.stop()

	print 'Found %s blobs.' % (len(blobs),)
	print 'Calculating blob stats'
	for blob in blobs:
		blob.calc_stats()
	t.stop()
	return blobs

def mark_image(image, coord, value):
	'''
	burn a mark on an image
	'''
	size = 15
	row,col = int(coord[0]), int(coord[1])
	for r in range(row-size,row+size):
		if 0 <= r < image.shape[0]:
			image[r,col] = value
	for c in range(col-size,col+size):
		if 0 <= c < image.shape[1]:
			image[row,c] = value

### python implementation of some Viewit functions

def threshold(a, limit):
	return a >= limit

def zscore(image):
	m = mean(image)
	s = stdev(image)
	return (image - m) / s
