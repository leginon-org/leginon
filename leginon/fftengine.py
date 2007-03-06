#!/usr/bin/env python

import numarray
try:
	import scipy.fftpack
	import scipy.__config__
	if not scipy.__config__.get_info('fftw3_info'):
		raise ImportError

	def real_fft2d(*args, **kwargs):
		return numarray.asarray(scipy.fftpack.fft2(*args, **kwargs))

	def inverse_real_fft2d(*args, **kwargs):
		return numarray.asarray(scipy.fftpack.ifft2(*args, **kwargs).real)

except ImportError:
	from numarray.fft import real_fft2d
	from numarray.fft import inverse_real_fft2d

import time
import sys

class _fftEngine(object):
	'''base class for a FFT engine'''
	def __init__(self, *args, **kwargs):
		self.showtime = 0

	def transform(self, image):
		transimage = self.timer(self._transform, (image,))
		return transimage

	def itransform(self, image):
		itransimage = self.timer(self._itransform, (image,))
		return itransimage

	def timer(self, func, args=()):
		t0 = time.time()
		ret = apply(func, args)
		t1 = time.time()
		total = t1 - t0
		if self.showtime:
			print '%s %.5f' % (func.__name__, total)

		return ret

	def _transform(self, image):
		raise NotImplementedError()

	def _itransform(self, image):
		raise NotImplementedError()


### this attempts to use fftw single and double
### if that fails, it will use numarray
fftw_mods = []

try:
	import fftw.single
	fftw_mods.append(fftw.single)
	import fftw.double
	fftw_mods.append(fftw.double)
except ImportError:
	pass
	#print 'could not import fftw modules'



if len(fftw_mods) != 2:
	#print 'Warning:  you are using numarray for FFTs.'
	#print 'Compile the fftw modules for faster FFTs.'
	### use numarray if fftw not available
	class fftEngine(_fftEngine):
		'''subclass of fftEngine which uses FFT from numarray module'''
		def __init__(self, *args, **kwargs):
			_fftEngine.__init__(self)

		def _transform(self, im):
			fftim = real_fft2d(im)
			return fftim

		def _itransform(self, fftim):
			im = inverse_real_fft2d(fftim)
			return im

else:
	for mod in fftw_mods:
		mod.plans = {}
		mod.iplans = {}
	# mapping numarray type to (fftwmodule, transformed type)
	type_module = {
		numarray.Float32: fftw.single,
		numarray.Float64: fftw.double,
		numarray.Complex32: fftw.single,
		numarray.Complex64: fftw.double,
	}
	real_complex = {
		numarray.Float32: numarray.Complex32,
		numarray.Float64: numarray.Complex64,
	}
	complex_real = {
		numarray.Complex32: numarray.Float32,
		numarray.Complex64: numarray.Float64,
	}

	class fftEngine(_fftEngine):
		'''
		Subclass of fftEngine which uses FFTW
		This can be initialized with a sequence of plan shapes
		that should be initialized to start with.  Plans are also created
		as needed.  Plans are stored at the module level, so many fftFFTW
		objects will share plans.

		Setting measure to True will cause a longer plan creation
		time (although this is only done once per image shape).  This
		is supposed to result in faster fft, but so far I have not
		noticed a difference, even on 4kx4k images, so for now the
		default is False.
		'''
		def __init__(self, planshapes=(), measure=False, *args, **kwargs):
			_fftEngine.__init__(self)
			self.measure = measure
			#if planshapes:
			#	print 'calculating fftw plans'
			for mod in fftw_mods:
				for shape in planshapes:
					self.timer(self.plan, (shape,mod))
					self.timer(self.iplan, (shape,mod))
					#print 'fftw plans done'

		def _transform(self, im):
			if im.type() not in complex_real.values():
				try:
					realtype = complex_real[im.type()]
				except KeyError:
					realtype = numarray.Float32
				im = numarray.asarray(im, realtype)

			fftshape = (im.shape[1], im.shape[0] / 2 + 1)
			imfft = numarray.zeros(fftshape, real_complex[im.type()])
			mod = type_module[im.type()]
			plan = self.timer(self.plan, (im.shape,mod))
			mod.rfftwnd_one_real_to_complex(plan, im, imfft)
			return imfft

		def _itransform(self, fftim):
			if fftim.type() not in real_complex.values():
				try:
					complextype = real_complex[fftim.type()]
				except KeyError:
					complextype = numarray.Complex32
				fftim = numarray.asarray(fftim, complextype)

			imshape = (2*(fftim.shape[1]-1), fftim.shape[0])

			im = numarray.zeros(imshape, complex_real[fftim.type()])
			mod = type_module[fftim.type()]
			plan = self.timer(self.iplan, (imshape,mod))
			### the input image will be destroyed, so make copy
			fftimcopy = fftim.copy()
			mod.rfftwnd_one_complex_to_real(plan, fftimcopy, im)
			norm = imshape[0] * imshape[1]
			im = numarray.divide(im, norm)
			return im

		def plan(self, shape, mod):
			shapekey = (long(shape[0]), long(shape[1]))
			if shapekey not in mod.plans:
				#print 'creating %s plan for %s' % (mod.__name__, shapekey)
				r,c = shape
				if self.measure:
					mod.plans[shapekey] = mod.rfftw2d_create_plan(r,c,mod.FFTW_REAL_TO_COMPLEX, mod.FFTW_MEASURE|mod.FFTW_USE_WISDOM)
				else:
					mod.plans[shapekey] = mod.rfftw2d_create_plan(r,c,mod.FFTW_REAL_TO_COMPLEX, mod.FFTW_ESTIMATE|mod.FFTW_USE_WISDOM)

			return mod.plans[shapekey]

		def iplan(self, shape, mod):
			shapekey = (long(shape[0]), long(shape[1]))
			if shapekey not in mod.iplans:
				#print 'creating %s iplan for %s' % (mod.__name__, shapekey)
				r,c = shape
				if self.measure:
					mod.iplans[shapekey] = mod.rfftw2d_create_plan(r,c,mod.FFTW_COMPLEX_TO_REAL, mod.FFTW_MEASURE|mod.FFTW_USE_WISDOM)
				else:
					mod.iplans[shapekey] = mod.rfftw2d_create_plan(r,c,mod.FFTW_COMPLEX_TO_REAL, mod.FFTW_ESTIMATE|mod.FFTW_USE_WISDOM)
			return mod.iplans[shapekey]

if __name__ == '__main__':
	import Mrc
	import imagefun

	def stats(im):
		print '   MEAN', imagefun.mean(im)
		print '   STD', imagefun.stdev(im)
		print '   MIN', imagefun.min(im)
		print '   MAX', imagefun.max(im)

	print 'reading'
	im = Mrc.mrc_to_numeric('../test_images/spiketest.mrc')
	print 'IM TYPE', im.type()
	stats(im)
	ffteng = fftEngine()
	fft = ffteng.transform(im)
	print 'FFT TYPE', fft.type()
	ifft = ffteng.itransform(fft)
	print 'IFFT TYPE', ifft.type()
	stats(ifft)
