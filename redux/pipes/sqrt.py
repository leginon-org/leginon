# local
from redux.pipe import Pipe
from redux.pipe import int_converter

# 3rd party
import numpy

class Sqrt(Pipe):
	required_args = {'sqrt': int_converter}
	def run(self, input, sqrt):
		for i in range(sqrt):
			input = numpy.sqrt(input)
		return input
