import Numeric
import fftengine

if fftengine.fftFFTW is None:
	ffteng = fftengine.fftNumeric()
	print 'USING Numeric FFT'
else:
	ffteng = fftengine.fftFFTW()
	print 'USING FFTW'

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
	print 'CENTER', center
	input[cenr-size/2:cenr+size/2, cenc-size/2:cenc+size/2] = value

def power(numericarray):
	fft = ffteng.transform(numericarray)
	#pow = Numeric.absolute(fft) ** 2
	pow = Numeric.absolute(fft)
	#pow = swap(pow)
	pow = shuffle(pow)
	center_fill(pow, 15, 0)
	pow = linearscale(pow, (None, None), (1,100))
	pow = Numeric.clip(pow, 1, 100)
	print 'type', pow.typecode()
	print 'min', min(pow)
	print 'max', max(pow)
	pow = Numeric.log(pow)
	return pow

def shuffle(narray):
	'''
	take a half fft/power spectrum centered at 0,0
	and convert to full fft/power centered at center of image
	'''
	## create new full size array 
	r,oldc = narray.shape
	c = 2*(oldc-1)
	newshape = r,c
	new = Numeric.zeros(newshape, narray.typecode())

	## fill in right half
	new[r/2:,c/2-1:] = narray[:r/2,:]
	new[:r/2,c/2-1:] = narray[r/2:,:]

	## fill in left half
	for row in range(1,r):
		for col in range(c/2-1):
			new[row,col] = new[-1-row,-2-col]

	new[r/2,c/2-1] = new[r/2,c/2]
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

def convolve(image, kernel):
	imfft = ffteng.transform(image)
	kerfft = ffteng.transform(kernel)
	conv = Numeric.multiply(imfft, kerfft)
	result = ffteng.itransform(conv)
	return result

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

class Filter(object):
	def __init__(self):
		self.history = {}
		
	def kernel_image(self, shape):
		if shape in self.history:
			return self.history[shape]
		im = Numeric.zeros(shape, Numeric.Float32)
		r,c = self.kernel.shape
		im[:r,:c] = self.kernel
		self.history[shape] = im
		return im

	def NEWkernel_image(self, shape):
		if shape in self.history:
			return self.history[shape]
		im = Numeric.zeros(shape, Numeric.Float32)

		r,c = self.kernel.shape
		r2 = r/2
		c2 = c/2
		## split into 4
		k1 = self.kernel[:r2,:c2]
		k2 = self.kernel[:r2,c2:]
		k3 = self.kernel[r2:,:c2]
		k4 = self.kernel[r2:,c2:]
		
		k1r,k1c = k1.shape
		k2r,k2c = k2.shape
		k3r,k3c = k3.shape
		k4r,k4c = k4.shape

		im[:k4r,:k4c] = k4
		im[:k3r,-k3c:] = k3
		im[-k2r:,:k2c] = k2
		im[-k1r:,-k1c:] = k1

		self.history[shape] = im
		return im
		
	def run(self, image):
		im = image.astype(Numeric.Float32)
		kimage = self.kernel_image(im.shape)
		result = convolve(im, kimage)
		# ## get rid of invalid data at beginning
		r = self.kernel.shape[0]/2
		c = self.kernel.shape[1]/2
		result = result[r:,c:]
		return result

def laplacian_kernel():
	k1 = Numeric.array((1,-1,1,-1,0,-1,1,-1,1),Numeric.Float32)
	k2 = Numeric.array((0,1,0,1,-4,1,0,1,0), Numeric.Float32)
	k = 1.0 / 2 * (k1 + k2)
	k.shape = (3,3)
	return k.astype(Numeric.Float32)

def gaussian_kernel(n, sigma):
	if not n % 2:
		raise RuntimeError('guassian kernel must have odd size')
	half = int(n / 2)
	k1 = 1.0 / (2.0 * Numeric.pi * sigma**2)
	def i(rows,cols):
		rows = rows.astype(Numeric.Float32)
		cols = cols.astype(Numeric.Float32)
		rows = rows - half
		cols = cols - half
		k2 = Numeric.exp(-(rows**2+cols**2) / 2.0 / sigma**2)
		return k1 * k2
	k = Numeric.fromfunction(i, (n,n))
	return k

def laplacian_of_gaussian_kernel(size, sigma):
	if not size % 2:
		raise ValueError('kernel size must be odd')
	half = (size - 1) / 2
	def func(x,y):
		f1 = (x**2 + y**2) / 2.0 / sigma**2
		f2 = -1.0 / Numeric.pi / (sigma**4)
		f3 = 1 - f1
		f4 = Numeric.exp(-f1)
		return f2 * f3 * f4
	k = Numeric.zeros((size,size), Numeric.Float32)
	for row in range(size):
		x = row - half
		for col in range(size):
			y = col - half
			k[row,col] = func(x,y)
	return k

class LaplacianGaussianFilter(Filter):
	def __init__(self, n, sigma):
		Filter.__init__(self)
		self.kernel = laplacian_of_gaussian_kernel(n, sigma)

class LaplacianFilter(Filter):
	def __init__(self):
		Filter.__init__(self)
		self.kernel = laplacian_kernel()

class GaussianFilter(Filter):
	def __init__(self, n, sigma):
		Filter.__init__(self)
		self.kernel = gaussian_kernel(n, sigma)

## The Blob.add_point method below is recursive while searching for neighbors.
## Here we make sure that python will allow enough recursion to get decent
## sized blobs.
import sys
reclim = sys.getrecursionlimit()
if reclim < 1000:
	sys.setrecursionlimit(1000)

class Blob(object):
	'''
	a Blob instance represets a connected set of pixels
	'''
	neighbors = ((-1,-1),(-1,0),(-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1))
	maxpoints = 200
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
		self.pixel_list.append(Numeric.array((row, col), Numeric.Float32))
		self.value_list.append(Numeric.array(self.image[row,col], Numeric.Float32))
		## turn off pixel in mask
		tmpmask[row,col] = 0
		## reset stats
		self.stats = {}

		# abort this blob if too many points
		# if we don't abort, we will hit a recursion limit
		if len(self.pixel_list) > self.maxpoints:
			return

		# check neighbors
		for neighbor in self.neighbors:
			if self.recursionerror:
				break
			nrow = row + neighbor[0]
			ncol = col + neighbor[1]
			if nrow < 0 or nrow >= self.image.shape[0]:
				continue
			if ncol < 0 or ncol >= self.image.shape[1]:
				continue
			if tmpmask[nrow,ncol]:
				try:
					self.add_point(nrow,ncol,tmpmask)
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

def find_blobs(image, mask, border=0):
	shape = image.shape
	blobs = []
	## create a copy of mask that will be modified
	tmpmask = mask.astype(Numeric.Int8)
	for row in range(border,shape[0]-border):
		for col in range(border,shape[1]-border):
			if tmpmask[row,col]:
				newblob = Blob(image, mask)
				err = newblob.add_point(row, col, tmpmask)
				if not err:
					blobs.append(newblob)	
	print 'Found %s blobs.' % (len(blobs),)
	print 'Calculating blob stats'
	for blob in blobs:
		blob.calc_stats()
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
