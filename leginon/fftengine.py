
import Numeric
import FFT
import sfftw
import time


class fftEngine(object):
	'''base class for a FFT engine'''
	def __init__(self):
		self.showtime = 1

	def transform(self, image):
		transimage = self.timer(self._transform, (image,))
		return transimage

	def itransform(self, image):
		itransimage = self.timer(self._itransform, (image,))
		return itransimage

	def timer(self, func, args=()):
		t0 = time.clock()
		ret = apply(func, args)
		t1 = time.clock()
		total = t1 - t0
		if self.showtime:
			print '%s %.5f' % (func.__name__, total)

		return ret

	def _transform(self, image):
		raise NotImplementedError()

	def _itransform(self, image):
		raise NotImplementedError()


class fftNumeric(fftEngine):
	'''subclass of fftEngine which uses FFT from Numeric module'''
	def __init__(self):
		fftEngine.__init__(self)

	def _transform(self, im):
		fftim = FFT.real_fft2d(im)
		return fftim

	def _itransform(self, fftim):
		im = FFT.inverse_real_fft2d(fftim)
		return im


### for managing fftFFTW plans
plans = {}
iplans = {}

class fftFFTW(fftEngine):
	'''
	Subclass of fftEngine which uses FFTW
	This can be initialized with a sequence of plan shapes
	that should be initialized to start with.  Plans are also created
	as needed.  Plans are stored at the module level, so many fftFFTW
	objects will share plans.
	'''
	def __init__(self, planshapes=(), estimate=0):
		fftEngine.__init__(self)
		self.estimate = estimate
		for shape in planshapes:
			self.plan(shape)
			self.iplan(shape)

	def _transform(self, im):
		if im.typecode() != Numeric.Float32:
			print 'warning: casting image to Float32'
			im = im.astype(Numeric.Float32)
		fftshape = (im.shape[0] / 2 + 1, im.shape[1])
		imfft = Numeric.zeros(fftshape, Numeric.Complex32)
		plan = self.timer(self.plan, (im.shape,))
		sfftw.rfftwnd_one_real_to_complex(plan, im, imfft)
		return imfft

	def _itransform(self, fftim, normalize=0):
		if fftim.typecode() != Numeric.Complex32:
			raise TypeError('input must be Numeric.Complex32')
		im = Numeric.zeros(fftim.shape, Numeric.Float32)
		im.savespace(1)  #prevent upcasting from float32 to float64
		plan = self.timer(self.iplan, (fftim.shape,))
		sfftw.rfftwnd_one_complex_to_real(plan, fftim, im)
		if normalize:
			norm = im.shape[0] * im.shape[1]
			im = Numeric.divide(im, norm)
		return im

	def plan(self, shape):
		if shape not in plans:
			r,c = shape
			if self.estimate:
				plans[shape] = sfftw.rfftw2d_create_plan(r,c,sfftw.FFTW_REAL_TO_COMPLEX, sfftw.FFTW_ESTIMATE|sfftw.FFTW_USE_WISDOM)
			else:
				plans[shape] = sfftw.rfftw2d_create_plan(r,c,sfftw.FFTW_REAL_TO_COMPLEX, sfftw.FFTW_MEASURE|sfftw.FFTW_USE_WISDOM)

		return plans[shape]

	def iplan(self, shape):
		if shape not in iplans:
			r,c = shape
			if self.estimate:
				iplans[shape] = sfftw.rfftw2d_create_plan(r,c,sfftw.FFTW_COMPLEX_TO_REAL, sfftw.FFTW_ESTIMATE|sfftw.FFTW_USE_WISDOM)
			else:
				iplans[shape] = sfftw.rfftw2d_create_plan(r,c,sfftw.FFTW_COMPLEX_TO_REAL, sfftw.FFTW_MEASURE|sfftw.FFTW_USE_WISDOM)
		return iplans[shape]
