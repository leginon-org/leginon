from redux.pipe import Pipe
import pyami.fft

class Power(Pipe):
	switch_arg = 'power'
	def run(self, input):
		output = pyami.fft.calculator.power(input, full=True, centered=True)
		return output

