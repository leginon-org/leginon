# 3rd party
import scipy.stats
import numpy

# myami
import pyami.imagefun
import pyami.weakattr
import pyami.arraystats

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter
import redux.pipes.shape

class Scale(Pipe):
	required_args = {'scaletype': str, 'scalemin': float, 'scalemax': float}
	optional_args = {'scaleshape': shape_converter}
	options_defaults = {'scaleshape': None}
	def run(self, input, scaletype, scalemin, scalemax, scaleshape=None):
		if scaletype == 'minmax':
			result = self.scale_minmax(input, scalemin, scalemax)
		elif scaletype == 'stdev':
			result = self.scale_stdev(input, scalemin, scalemax, scaleshape)
		elif scaletype == 'cdf':
			result = self.scale_cdf(input, scalemin, scalemax,scaleshape)
		elif scaletype == 'pctminmax':
			result = self.scale_percentminmax(input, scalemin, scalemax,scaleshape)
		else:
			raise ValueError('bad scaletype: %s' % (scaletype,))
		return result

	## consider using scipy.misc.bytescale (is it faster?)
	def linearscale(self, input, min, max):
		image_array = pyami.imagefun.linearscale(input, (min, max), (0,255))
		image_array = numpy.clip(image_array, 0, 255)
		return image_array

	def scale_minmax(self, input, min, max):
		return self.linearscale(input, min, max)

	def scale_percentminmax(self, input, min, max, small):
		if small:
			tempinput = redux.pipes.shape.Shape.run(input, small)
		else:
			tempinput = input
		stats = pyami.arraystats.all(tempinput)
		minmaxrange = stats['max'] - stats['min']
		mn = stats['min'] + min / 100.0 * minmaxrange
		mx = stats['min'] + max / 100.0 * minmaxrange
		return self.scale_minmax(input, mn, mx)

	def scale_stdev(self, input, min, max, small):
		if small:
			tempinput = redux.pipes.shape.Shape.run(input, small)
		else:
			tempinput = input
		mean = pyami.arraystats.mean(tempinput)
		std = pyami.arraystats.std(tempinput)
		scalemin = mean + min * std
		scalemax = mean + max * std
		return self.linearscale(input, scalemin, scalemax)

	def scale_cdf(self, input, min, max, small):
		if small:
			tempinput = redux.pipes.shape.Shape.run(input, small)
		else:
			tempinput = input
		bins = 1000
		try:
			cumfreq, lower, width, x = pyami.weakattr.get(tempinput, 'cumfreq')
		except:
			cumfreq, lower, width, x = scipy.stats.cumfreq(tempinput, bins)
			pyami.weakattr.set(tempinput, 'cumfreq', (cumfreq, lower, width, x))
		cumfreq = cumfreq / tempinput.size
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

