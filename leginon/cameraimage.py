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


def stdev(inputarray):
	f = Numeric.ravel(inputarray)
	inlen = len(f)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(f) / divisor
	try:
		bigsum = Numeric.sum((f - m)**2)
	except OverflowError:
		print 'OverflowError:  stdev returning None'
		return None
	stdev = Numeric.sqrt(bigsum / len(f))
	return stdev

def mean(inputarray):
	f = Numeric.ravel(inputarray)
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

### This will hopefully be a class that contains a lot of the above
### functionality.  The name NumericImage is currently being used
### in the NumericImage module/class.  I would like that class to become
### something like PILNumericImage and this class will absorb some of
### its functionality.  PILNumericImage can then become the glue between this
### NumericImage and the PIL library.
class NumericImage(object):
	'''
	This is a class wrapper around a Numeric array
	'''
	def __init__(self, numdata):
		self.numeric(numdata)
		self.stats = None

	def init_stats(self):
		pass

	def numeric(self, numdata=None):
		if numdata is not None:
			self.numdata = Numeric.array(numdata)
		return self.numdata

