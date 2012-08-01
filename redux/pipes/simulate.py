# standard lib
import os

# 3rd party
import numpy

# local
import redux.pipe

class Simulate(redux.pipe.Pipe):
	cache_file = False
	required_args = {'simshape': redux.pipe.shape_converter}

	def make_dirname(self):
		shape_strs = map(str, self.kwargs['simshape'])
		self._dirname = 'sim_'+'x'.join(shape_strs)

	def run(self, input, simshape):
		## input ignored
		
		result = numpy.random.normal(20000, 200, simshape)

		return result

