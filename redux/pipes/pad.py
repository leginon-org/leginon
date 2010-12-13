# 3rd party
import numpy

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter, int_converter

class Pad(Pipe):
	cache_file = False
	required_args = {'padshape': shape_converter}
	optional_args = {'padpos': shape_converter, 'padvalue': float}
	optional_defaults = {'padpos': (0,0), 'padvalue': 0}
	def run(self, input, padshape, padpos, padvalue):
		# make sure shape is same dimensions as input image
		if len(padshape) != len(input.shape):
			raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, shape))
		if padvalue:
			output = padvalue * numpy.ones(padshape, dtype=input.dtype)
		else:
			output = numpy.zeros(padshape, dtype=input.dtype)

		output[padpos[0]:padpos[0]+input.shape[0], padpos[1]:padpos[1]+input.shape[1]] = input

		return output
