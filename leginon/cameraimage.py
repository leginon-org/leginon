import Numeric

## Numeric seems to use infinity as a result of zero
## division, but I can find no infinity constant or any other way of 
## producing infinity without first doing a zero division
## Here is my infinity contant
inf = 1.0 / Numeric.array(0.0, Numeric.Float32)


def stdev(inputarray):
	f = inputarray.flat
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
	f = inputarray.flat
	inlen = len(f)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(f) / divisor
	return m

def min(inputarray):
	f = inputarray.flat
	i = Numeric.argmin(f)
	return f[i]

def max(inputarray):
	f = inputarray.flat
	i = Numeric.argmax(f)
	return f[i]

def sumSeries(series):
	if len(series) == 0:
		return None
	if len(series) == 1:
		return series[0]
	first = series[0]
	others = series[1:]
	sum = first.astype(Numeric.Float32)
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

