# 3rd party
import scipy.stats
import numpy

# myami
import pyami.imagefun
import pyami.weakattr
import pyami.arraystats

# local
from redux.pipe import Pipe

class Scale(Pipe):
	required_args = {'scaletype': str, 'scalemin': float, 'scalemax': float}
	def run(self, input, scaletype, scalemin, scalemax):
		if scaletype == 'minmax':
			result = self.scale_minmax(input, scalemin, scalemax)
		elif scaletype == 'stdev':
			result = self.scale_stdev(input, scalemin, scalemax)
		elif scaletype == 'cdf':
			result = self.scale_cdf(input, scalemin, scalemax)
		else:
			raise ValueError('bad scaletype: %s' % (scaletype,))
		return result

	def linearscale(self, input, min, max):
		image_array = pyami.imagefun.linearscale(input, (min, max), (0,255))
		image_array = numpy.clip(image_array, 0, 255)
		return image_array

	def scale_minmax(self, input, min, max):
		return self.linearscale(input, min, max)

	def scale_stdev(self, input, min, max):
		mean = pyami.arraystats.mean(input)
		std = pyami.arraystats.std(input)
		scalemin = mean + min * std
		scalemax = mean + max * std
		return self.linearscale(input, scalemin, scalemax)

	def scale_cdf(self, input, min, max):
		bins = 1000
		try:
			cumfreq, lower, width, x = pyami.weakattr.get(input, 'cumfreq')
		except:
			cumfreq, lower, width, x = scipy.stats.cumfreq(input, bins)
			pyami.weakattr.set(input, 'cumfreq', (cumfreq, lower, width, x))
		cumfreq = cumfreq / input.size
		pmin = True
		for j in range(bins):
			if pmin and cumfreq[j] >= min:
				pmin = False
				minval = j
			elif cumfreq[j] >= max:
				maxval = j
				break
		scalemin = lower + (minval+0.5) * width
		scalemax = lower + (maxval+0.5) * width
		return self.linearscale(input, scalemin, scalemax)

