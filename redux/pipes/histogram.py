import numpy
import redux.pipe

class Histogram(redux.pipe.Pipe):
	'''
	returns result of numpy.histogram
	'''
	required_args = {'histbins': redux.pipe.int_converter}
	optional_args = {'histmin': float, 'histmax': float}
	def run(self, input, histbins, histmin=None, histmax=None):
		if None in (histmin, histmax):
			histrange = None
		else:
			histrange = histmin,histmax
		return numpy.histogram(input, histbins, histrange)
