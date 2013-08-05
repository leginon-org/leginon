#!/usr/bin/env python

import pyami.fft.calc_fftw3
import fftw3
import numpy
import time
import os
import sys

timing = {'create':[], 'plan':[], 'init':[], 'run':[]}

def create(shape):
	global timing
	t0 = time.time()
	a = numpy.empty(shape, numpy.float)
	timing['create'].append(time.time() - t0)
	return a

def make_plan(image_array, rigor):
	global timing
	t0 = time.time()
	input_array = numpy.empty(image_array.shape, numpy.float)
	fftshape = image_array.shape[0], image_array.shape[1]/2+1
	fft_array = numpy.empty(fftshape, dtype=complex)
	plan_kwargs = dict(pyami.fft.calc_fftw3.global_plan_kwargs)
	plan_kwargs['flags'] = [rigor]
	p = fftw3.Plan(input_array, fft_array, direction='forward', **plan_kwargs)
	p.input_array = input_array
	p.fft_array = fft_array
	timing['plan'].append(time.time() - t0)
	return p

def init(image_array, plan):
	global timing
	t0 = time.time()
	plan.input_array[:] = image_array
	timing['init'].append(time.time() - t0)

def run(plan):
	global timing
	t0 = time.time()
	plan()
	timing['run'].append(time.time() - t0)

def run_timing():
	try:
		n = int(sys.argv[1])
		shape = int(sys.argv[2]), int(sys.argv[3])
		try:
			rigor = sys.argv[4]
		except:
			rigor = 'measure'
	except:
		print '''
  usage:   %s N shape0 shape1
    N - number of iterations to test
    shape0,shape1 - the shape of the array to test
		''' % (sys.argv[0],)
		sys.exit()
	pyami.fft.calc_fftw3.load_wisdom()

	for i in range(n):
		print i
		a = create(shape)
		plan = make_plan(a, rigor)
		init(a, plan)
		run(plan)

	pyami.fft.calc_fftw3.store_wisdom()

	for key in ['create','plan','init','run']:
		print key, timing[key]

def wisdom_test():
	pyami.fft.calc_fftw3.load_wisdom()
	pyami.fft.calc_fftw3.store_wisdom()

if __name__ == '__main__':
	run_timing()
