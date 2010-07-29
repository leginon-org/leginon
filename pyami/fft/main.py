#!/usr/bin/env python
'''
This module selects the FFT Calculator class and creates an instance of it.
It exposes public methods of the Calculator as module functions.
'''

#force_calculator = 'fftpack'
force_calculator = None

import registry
if not registry.calculators:
	raise ImportError('You need to install one of the fft calculators: %s' % (registry.attempted,))

## check for forced calculator, otherwise registry order defines preference
if force_calculator is not None:
	if force_calculator in registry.calculators:
		calc_name = force_calculator
	else:
		raise RuntimeError('Forced calculator not imported: %s' % (force_calculator,))
else:
	calc_name = registry.priority[0]
calc_class = registry.calculators[calc_name]
calculator = calc_class()

def test1():
	import pyami.mrc
	import time
	import sys
	import numpy
	filename = sys.argv[1]
	a = pyami.mrc.read(filename)
	a = numpy.asarray(a, numpy.float64)
	for i in range(5):
		t0 = time.time()
		calculator.forward(a)
		print 'time', time.time()-t0

def test2():
	import fftw3
	import numpy
	input = numpy.zeros((4,4), dtype=float)
	output = numpy.zeros((4,3), dtype=complex)
	#plan = fftw3.Plan(input, output, direction='forward', flags=['measure'])
	plan = fftw3.Plan(output, input, direction='forward', flags=['measure'])

	a = numpy.random.normal(100, 10, (4,4))

if __name__ == '__main__':
	test1()
	#test2()
