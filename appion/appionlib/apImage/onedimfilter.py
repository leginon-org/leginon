#!/usr/bin/env python

## pythonlib
## numpy
import numpy
import pyami.quietscipy
## appion
from appionlib import apDisplay

#=========================
def tanhHighPassFilter(data, radius, apix=1.0, bin=1, fuzzyEdge=4):
	"""
	performs a hyperbolic tangent high pass filter
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d

	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	size = len(data)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for high pass filter")
		return data
	if len(data) % 2 != 0:
		apDisplay.printWarning("data must be even dimension or use reflect filter")
		return data
	fftdata = numpy.fft.fft(data)
	fftdata = numpy.fft.fftshift(fftdata)
	filterResult = tanhFilter(pixelradius, size/2, fuzzyEdge=fuzzyEdge)
	filterComplete = numpy.hstack([filterResult[::-1], filterResult])
	fftdata *= filterComplete
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft(fftdata))
	return flipdata

#=========================
def tanhLowPassFilter(data, radius, apix=1.0, bin=1, fuzzyEdge=4):
	"""
	performs a hyperbolic tangent high pass filter
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d

	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	size = len(data)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for low pass filter")
		return data
	if len(data) % 2 != 0:
		apDisplay.printWarning("data must be even dimension or use reflect filter")
		return data
	#opposite of HP filter
	fftdata = numpy.fft.fft(data)
	fftdata = numpy.fft.fftshift(fftdata)
	filterResult = 1.0 - tanhFilter(pixelradius, size/2, fuzzyEdge=fuzzyEdge)
	filterComplete = numpy.hstack([filterResult[::-1], filterResult])
	fftdata *= filterComplete
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft(fftdata))
	return flipdata

#=========================
def reflectTanhLowPassFilter(data, radius, apix=1.0, bin=1, fuzzyEdge=4):
	"""
	performs a hyperbolic tangent high pass filter
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d

	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	halfsize = len(data)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for low pass filter")
		return data
	reflect = numpy.hstack([data, data[::-1]])

	#opposite of HP filter
	fftdata = numpy.fft.fft(reflect)
	fftdata = numpy.fft.fftshift(fftdata)
	filterResult = 1.0 - tanhFilter(pixelradius, halfsize, fuzzyEdge=fuzzyEdge)
	filterComplete = numpy.hstack([filterResult[::-1], filterResult])
	fftdata *= filterComplete
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft(fftdata))
	truncate = numpy.copy(flipdata[:halfsize])
	if numpy.any(numpy.isnan(truncate)):  #note does not work with 'is True'
		print(numpy.around(data[:15]))
		apDisplay.printError("All values NaN from tanh filter")
	return truncate

#=========================
def reflectTanhHighPassFilter(data, radius, apix=1.0, bin=1, fuzzyEdge=4):
	"""
	performs a hyperbolic tangent high pass filter
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d

	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	halfsize = len(data)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for low pass filter")
		return data
	reflect = numpy.hstack([data, data[::-1]])

	#opposite of HP filter
	fftdata = numpy.fft.fft(reflect)
	fftdata = numpy.fft.fftshift(fftdata)
	filterResult = tanhFilter(pixelradius, halfsize, fuzzyEdge=fuzzyEdge)
	filterComplete = numpy.hstack([filterResult[::-1], filterResult])
	fftdata *= filterComplete
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft(fftdata))
	truncate = numpy.copy(flipdata[:halfsize])
	if numpy.any(numpy.isnan(truncate)):  #note does not work with 'is True'
		print(numpy.around(data[:15]))
		apDisplay.printError("All values NaN from tanh filter")
	return truncate


filterCache = {}

#=========================
def tanhFilter(pixelradius, size, fuzzyEdge=2):
	"""
	creates hyperbolic tangent mask of size pixelradius
	into a numpy array of defined shape

	fuzzyEdge makes the edge of the hyperbolic tangent more fuzzy
	"""
	filterKey = "%.3f-%d-%.3f"%(pixelradius, size, fuzzyEdge)
	try:
		return filterCache[filterKey]
	except KeyError:
		pass
	radial = numpy.arange(0, size, 1)
	filterResult = numpy.tanh(radial/fuzzyEdge - 1.01*size/float(pixelradius)/fuzzyEdge)/2.0 + 0.5
	filterCache[filterKey] = filterResult
	return filterResult

####
# This is a low-level file with NO database connections
# Please keep it this way
####

if __name__ == '__main__':
	import scipy.ndimage
	a = numpy.array([0.994,0.994,0.989,0.978,0.974,0.974,0.979,0.987,0.986,0.983,0.980,0.960,0.955,0.951,
						  0.942,0.968,0.958,0.940,0.936,0.924,0.936,0.921,0.923,0.925,0.943,0.922,0.914,0.899,
						  0.886,0.878,0.862,0.856,0.858,0.840,0.845,0.854,0.884,0.888,0.893,0.730,0.707,0.666,
						  0.623,0.727,0.704,0.702,0.723,0.631,0.645,0.575,0.460,0.458,0.336,0.529,0.834,0.833,
						  0.681,0.531,0.379,0.262,0.470,0.280,0.150,-0.297,-0.246,-0.244,-0.120,0.081,0.266,
						  0.467,0.450,0.126,0.188,0.146,0.185,0.395,0.156,-0.184,-0.298,-0.246,-0.287,
						  ])
	#a = numpy.hstack([a[::-1], a])
	print len(a)
	b = tanhLowPassFilter(a, 3)
	c = reflectTanhLowPassFilter(a, 3)
	d = scipy.ndimage.gaussian_filter1d(a, 2)
	f = tanhHighPassFilter(a, len(a)/3)
	g = reflectTanhHighPassFilter(a, len(a)/3)
	import matplotlib
	#matplotlib.use('agg')
	from matplotlib import pyplot
	pyplot.plot(a, label='data', linewidth=2)
	pyplot.plot(b, label='lowpass')
	pyplot.plot(c, label='reflect lowpass')
	pyplot.plot(d, label='gauss')
	pyplot.plot(f, label='highpass')
	pyplot.plot(g, label='reflect highpass')
	pyplot.legend()
	#pyplot.xlim(xmin=len(a)/2, xmax=3*len(a)/4)
	#pyplot.ylim(0.3, 1.)
	pyplot.ylabel('confidence')
	pyplot.show()

