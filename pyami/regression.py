#!/usr/bin/env python
import math
from scipy.odr import Model, Data, ODR
from scipy.stats import linregress
import numpy

def orthoganalDistanceRegression(x, y):
	'''
	Orthoganal Distance Regression
	'''
	beta, res_var, is_successful = _orthoganalDistanceRegression(x, y)
	if not is_successful:
		# Regression fails if slope is too high
		beta, res_var, is_successful = _orthoganalDistanceRegression(y, x)
		slope = 1/beta[0]
	else:
		slope = beta[0]
	intercept = beta[1]
	return slope, intercept, res_var, is_successful

def _orthoganalDistanceRegression(x, y):
	# default
	is_successful = True
	# function to fit
	def f(p, x):
		return (p[0]*x) + p[1]
	# use simple linear regression result as guess
	linreg = linregress(x, y)
	mod = Model(f)
	dat = Data(x, y)
	od = ODR(dat, mod, beta0=linreg[0:2])
	out = od.run()
	res_var = out.res_var
	stopreason = out.stopreason
	if "Sum of squares convergence" not in stopreason:
		is_successful = False
	#out.pprint()
	return list(out.beta), res_var, is_successful

if __name__=='__main__':
	import numpy.random
	for i in range(10):
		rs = numpy.random.random_sample(20) - 0.5
		xs = numpy.array(list(range(10)))*0.5 + i*rs[:10]*0.1
		ys = numpy.array(list(range(10)))*2.0 + 2 + i*rs[10:]*0.1
		a, b, r, is_successful =  orthoganalDistanceRegression(xs, ys)
		length = math.hypot(xs.min()-xs.max(), a*xs.min()-a*xs.max())
		print(a, b, r, is_successful)
		print(r*100/length)
		print('............')
