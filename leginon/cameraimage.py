import Numeric

## Numeric seems to use infinity as a result of zero
## division, but I can find no infinity constant or any other way of 
## producing infinity without first doing a zero division
## Here is my infinity contant
inf = 1.0 / Numeric.array(0.0, Numeric.Float32)

def centerOffset(camerasize, imagesize):
	'''
	determine offset to use image from camera center
	useful for the 'offset' parameter in camera state
	'''
	r = (camerasize[0]/2 - imagesize[0]/2, camerasize[1]/2 - imagesize[1]/2)
	return r

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

def averageSeries(series):
	slen = len(series)
	if slen == 0:
		return None
	sum = Numeric.sum(series)
	divisor = Numeric.array(slen, Numeric.Float32)
	avg = sum / divisor
	return avg
