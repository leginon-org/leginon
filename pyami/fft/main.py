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
	for i in range(5):
		t0 = time.time()
		calculator.forward(a)
		print 'time', time.time()-t0
	return a

def test2():
	import pyami.mrc
	import time
	import sys
	import numpy
	filename = sys.argv[1]
	a = pyami.mrc.read(filename)
	for i in range(5):
		t0 = time.time()
		calculator.power(a)
		print 'time', time.time()-t0




if __name__ == '__main__':
	a = test1()
	test2()
