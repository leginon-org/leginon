#!/usr/bin/env python
import Numeric
import FFT
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


### this attempts to use sfftw to create the fft engine classs
### if that fails, it will use Numeric
fftw_mods = []

try:
	print 'importing sfftw...'
	import sfftw
	fftw_mods.append(sfftw)
	print 'importing fftw...'
	import fftw
	fftw_mods.append(fftw)
except ImportError:
	print 'could not import fftw modules'

if len(fftw_mods) != 2:
	print 'Warning:  you are using Numeric for FFTs.'
	print 'Compile the fftw modules for faster FFTs.'
	### use Numeric if fftw not available
	class fftEngine(_fftEngine):
		'''subclass of fftEngine which uses FFT from Numeric module'''
		def __init__(self, *args, **kwargs):
			_fftEngine.__init__(self)

		def _transform(self, im):
			fftim = FFT.real_fft2d(im)
			return fftim

		def _itransform(self, fftim):
			im = FFT.inverse_real_fft2d(fftim)
			return im

else:
	for mod in fftw_mods:
		mod.plans = {}
		mod.iplans = {}
	# mapping Numeric typecode to (fftwmodule, transformed type)
	type_info = {
		Numeric.Float32: {'module':sfftw, 'trans':Numeric.Complex32},
		Numeric.Float64: {'module':fftw, 'trans':Numeric.Complex64},
		Numeric.Complex32: {'module':sfftw, 'trans':Numeric.Float32},
		Numeric.Complex64: {'module':fftw, 'trans':Numeric.Float64}
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
			if planshapes:
				print 'calculating fftw plans'
			for mod in fftw_mods:
				for shape in planshapes:
					self.timer(self.plan, (shape,mod))
					self.timer(self.iplan, (shape,mod))
					print 'fftw plans done'

		def _transform(self, im):
			if im.typecode() not in type_info.keys():
				im = im.astype(Numeric.Float32)
			fftshape = (im.shape[1], im.shape[0] / 2 + 1)
			imfft = Numeric.zeros(fftshape, type_info[im.typecode()]['trans'])
			mod = type_info[im.typecode()]['module']
			plan = self.timer(self.plan, (im.shape,mod))
			mod.rfftwnd_one_real_to_complex(plan, im, imfft)
			return imfft

		def _itransform(self, fftim):
			if fftim.typecode() not in type_info.keys():
				im = im.astype(Numeric.Complex32)
			imshape = (2*(fftim.shape[1]-1), fftim.shape[0])

			im = Numeric.zeros(imshape, type_info[fftim.typecode()]['trans'])
			#im.savespace(1)  #prevent upcasting from float32 to float64
			mod = type_info[fftim.typecode()]['module']
			plan = self.timer(self.iplan, (imshape,mod))
			### the input image will be destroyed, so make copy
			fftimcopy = Numeric.array(fftim)
			mod.rfftwnd_one_complex_to_real(plan, fftimcopy, im)
			norm = imshape[0] * imshape[1]
			im = Numeric.divide(im, norm)
			return im

		def plan(self, shape, mod):
			if shape not in mod.plans:
				print 'creating %s plan for %s' % (mod.__name__, shape)
				r,c = shape
				if self.measure:
					mod.plans[shape] = mod.rfftw2d_create_plan(r,c,mod.FFTW_REAL_TO_COMPLEX, mod.FFTW_MEASURE|mod.FFTW_USE_WISDOM)
				else:
					mod.plans[shape] = mod.rfftw2d_create_plan(r,c,mod.FFTW_REAL_TO_COMPLEX, mod.FFTW_ESTIMATE|mod.FFTW_USE_WISDOM)

			return mod.plans[shape]

		def iplan(self, shape, mod):
			if shape not in mod.iplans:
				print 'creating %s iplan for %s' % (mod.__name__, shape)
				r,c = shape
				if self.measure:
					mod.iplans[shape] = mod.rfftw2d_create_plan(r,c,mod.FFTW_COMPLEX_TO_REAL, mod.FFTW_MEASURE|mod.FFTW_USE_WISDOM)
				else:
					mod.iplans[shape] = mod.rfftw2d_create_plan(r,c,mod.FFTW_COMPLEX_TO_REAL, mod.FFTW_ESTIMATE|mod.FFTW_USE_WISDOM)
			return mod.iplans[shape]

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
	print 'IM TYPE', im.typecode()
	stats(im)
	ffteng = fftEngine()
	fft = ffteng.transform(im)
	print 'FFT TYPE', fft.typecode()
	ifft = ffteng.itransform(fft)
	print 'IFFT TYPE', ifft.typecode()
	stats(ifft)
