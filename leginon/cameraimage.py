import Numeric

def centerOffset(camerasize, imagesize):
	'''
	determine offset to use image from camera center
	useful for the 'offset' parameter in camera state
	'''
	r = (camerasize[0]/2 - imagesize[0]/2, camerasize[1]/2 - imagesize[1]/2)
	return r

def stdev(inputarray):
	inlen = len(inputarray.flat)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(inputarray.flat) / divisor
	stdev = Numeric.sqrt(Numeric.sum((Numeric.ravel(input) - m)**2) / len(Numeric.ravel(input)))
	return stdev

def mean(inputarray):
	inlen = len(input.flat)
	divisor = Numeric.array(inlen, Numeric.Float32)
	m = Numeric.sum(input.flat) / divisor
	return m

def averageSeries(self, series):
	slen = len(series)
	if slen == 0:
		return None
	sum = Numeric.sum(series)
	divisor = Numeric.array(slen, Numeric.Float32)
	avg = sum / divisor
	return avg
