#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import math, string
import numpy
import shelve

class GonData:
	"""
	A GonData instance holds the data from a goniometer calibration.
	It is only meant to handle one axis.
	"""
	def __init__(self, infile=None):
		self.gonpos = None
		self.othergonpos = None
		self.pixpertick = None
		self.datavg = None
		self.angle = None
		self.maginfo = {}
		if infile is not None:
			self.read_data(infile)

	def dict(self):
		return self.maginfo

	def import_data(self, mag, axis, datapoints):
		'''
		data is a sequence of data points.  each data point is a 5-tuple of floats.
		'''
		self.mag = mag
		self.axis = axis
		self.process_data(datapoints)

	def datalines2floats(self, datalines):
		floats = []
		for dataline in datalines:
			floatdata = string.split(dataline)
			if len(floatdata) != 5:
				continue
			floatdata = map(float, floatdata)
			floats.append(floatdata)

		return floats

	def read_data(self,filename):
		datafile = open(filename, 'r')
		lines = datafile.readlines()
		datafile.close()

		headlines = lines[:2]
		headlines = map(string.split,headlines)
		self.mag = float(headlines[0][0])
		self.axis = headlines[1][0]

		datalines = lines[2:]
		datapoints = self.datalines2floats(datalines)
		self.process_data(datapoints)

	def process_data(self, datapoints):
		datalen = len(datapoints)
		self.gonpos = numpy.zeros(datalen, numpy.float32)
		self.othergonpos = numpy.zeros(datalen, numpy.float32)
		self.pixpertick = numpy.zeros(datalen, numpy.float32)

		#self.angle = float(headlines[3][0])

		if self.axis == 'x':
			gonposcol = 0
			othergonposcol = 1
		else:
			gonposcol = 1
			othergonposcol = 0

		n = 0
		self.angle = 0.0
		self.avg = 0.0
		for point in datapoints:
			self.gonpos[n] = point[gonposcol]
			self.othergonpos[n] = point[othergonposcol]
			self.pixpertick[n] = math.hypot(point[3], point[4]) /  abs(point[2])
			self.avg += self.pixpertick[n]
			self.angle += math.atan2(point[4],point[3])
			n += 1

		self.ndata = n
		self.avg /= n
		self.avg = 1.0 / self.avg
		self.angle /= n

		if 'data angle' not in self.maginfo:
			self.maginfo['data angle'] = {}
		if 'data mean' not in self.maginfo:
			self.maginfo['data mean'] = {}
		self.maginfo['data angle'][self.axis] = self.angle
		self.maginfo['data mean'][self.axis] = self.avg

		print "maginfo set:"
		print "   angle:", self.angle
		print "   datavg:", self.avg

class GonModel:
	def __init__(self):
		self.period = None
		self.a = []
		self.b = []
		self.magcal = None


	## evaluate the model at a given position
	def eval(self, pos):
		k = 2.0 * math.pi / self.period
		k2 = k * pos
		result = 1.0
		for i in range(len(self.a)):
			q = (i + 1) * k2
			result += self.a[i] * math.cos(q)
			result += self.b[i] * math.sin(q)
		return result

	## evaluate the model at a given position
	def eval_intOLD(self, pos):
		k = 2.0 * math.pi / self.period
		k2 = k * pos
		result = pos
		for i in range(len(self.a)):
			q = (i + 1) * k2
			result += self.a[i] / k / (i+1) * math.sin(q)
			result -= self.b[i] / k / (i+1) * math.cos(q)
		return result

	def eval_int(self, pos):
		a = self.ai * numpy.sin(self.xia * pos)
		b = self.bi * numpy.cos(self.xib * pos)
		result = pos + a.sum() - b.sum()
		return result

	def integrate(self, pos0, pos1):
		return self.eval_int(pos1) - self.eval_int(pos0)

	## return a goniometer delta based on an image delta
	## this is a rotation, not scaled to the model
	## this only calculates the gon delta for one axis
	def rotate(self, angle, ximg, yimg):
		gon = ximg * math.cos(angle) + yimg * math.sin(angle)
		return gon

	## calculate a delta ticks from current position and delta nm
	def predict(self, pos, delta):
		intposdel = self.eval_int(pos) + delta
		# initial guess
		k = pos + delta

		# first iteration
		f = self.eval_int(k) - intposdel
		df = self.eval(k)
		correction = f / df
		kplus = k - correction
		
		# iterate to machine precision
		while k != kplus:
			k = kplus
			f = self.eval_int(k) - intposdel
			df = self.eval(k)
			correction = f / df
			kplus = k - correction

			# check if damping is necessary
			while self.eval_int(kplus) - intposdel > f:
				correction = 0.5 * correction
				kplus = k - correction

		ticks = kplus - pos
		return ticks

	def read_gonshelve(self,filename):
		ss = shelve.open(filename)
		self.axis = ss['axis']
		self.period = ss['period']
		self.a = ss['a']
		self.b = ss['b']
		ss.close()

	def write_gonshelve(self,filename):
		ss = shelve.open(filename)
		ss['axis'] = self.axis
		ss['period'] = self.period
		ss['a'] = self.a
		ss['b'] = self.b
		ss.close()

	def toDict(self):
		ss = {}
		ss['axis'] = self.axis
		ss['period'] = self.period
		ss['a'] = self.a
		ss['b'] = self.b
		return ss

	def removeTrailingZeros(self, seq):
		n = len(seq)
		for i in range(n-1,-1,-1):
			if not numpy.isnan(seq[i]) and seq[i]:
				break
		return seq[:i+1]

	def fromDict(self, d):
		self.axis = d['axis']
		self.period = d['period']

		a = self.removeTrailingZeros(d['a'])
		self.a = numpy.array(a, numpy.float32)
		self.a = self.a.ravel()

		b = self.removeTrailingZeros(d['b'])
		self.b = numpy.array(b, numpy.float32)
		self.b = self.b.ravel()

		k = 2.0 * numpy.pi / self.period

		i = numpy.arange(1,len(self.a)+1, 1, numpy.float32)
		self.ai = self.a / k / i
		self.xia = i * k

		i = numpy.arange(1,len(self.b)+1, 1, numpy.float32)
		self.bi = self.b / k / i
		self.xib = i * k

	def design_matrix(self, gondata, terms, period):
		ma = 2 * terms + 1
		a = numpy.zeros((gondata.ndata, ma), numpy.float32)

		k = 2.0 * math.pi / period
		
		g = 0
		for x in gondata.gonpos:
			a[g,0] = 1.0
			for i in range(1,terms+1):
				p = i * 2
				a[g,p-1] = math.cos( i * k * x )
				a[g,p] = math.sin( i * k * x )
			g += 1

		return a

	def fit_data(self, gondata, terms):
		b = gondata.pixpertick

		## converge the period of the solution to this precision.
		## smaller precision means longer execution time.
		precision = 1e-10

		## resolution of search within each search range
		## From my experience, this does not seem to affect execution too much
		## it just balances between the inner and outer loop below.
		search_periods = 10.0

		## Define the search range for the period of the fit function.
		## Right now, we know that the FEI Tecnai and CM goniometers have
		## the following theoretical periods (in meters):
		##     x:  6.24e-5,  y:  4.19e-5
		## Experimentally, we have found them to be closer to:
		##     x:  6.19e-5,  y:  ???
		## Here we use a search range that should include the solution for 
		## these goniometers.
		minp = 3.9e-5
		maxp = 6.5e-5

		## this loop begins a course search and narrows to a fine search which 
		## terminates when precision is reached.
		# Make sure incp is initially > precision, so loop goes at least once.
		incp = precision + 1
		best_resids = None
		best_period = minp
		while incp > precision:
			incp = (maxp - minp) / search_periods
			print 'current precision:', incp
			## this loop searches for the best period in the current range
			for period in numpy.arange(minp, maxp+incp, incp):
				a = self.design_matrix(gondata,terms,period)
				x,resids,rank,s = numpy.linalg.lstsq(a,b)
				try:
					resids0 = resids[0]
				except IndexError:
					raise RuntimeError('Not enough data for %d terms' % (terms,))
				if best_resids is None or resids[0] < best_resids:
					best_resids = resids[0]
					best_period = period
					best_x = x
			minp = best_period - incp
			maxp = best_period + incp

		self.period = best_period
		self.a0 = 1.0 / best_x[0]

		if 'model mean' not in gondata.maginfo:
			gondata.maginfo['model mean'] = {}
		gondata.maginfo['model mean'][gondata.axis] = self.a0
		print 'maginfo set:'
		print '  modavg:  ' + gondata.axis, self.a0
		print '  period:  ', self.period
		print '  resids:  ', best_resids

		if terms:
			self.a = numpy.zeros(terms)
			self.b = numpy.zeros(terms)
		else:
			self.a = numpy.zeros(1)
			self.b = numpy.zeros(1)
		for i in range(terms):
			self.a[i] = best_x[2*i+1]
			self.b[i] = best_x[2*i+2]
		print 'A', self.a
		print 'B', self.b

		## normalize
		self.a = self.a0 * self.a
		self.b = self.a0 * self.b
		self.axis = gondata.axis

	def fitInto(self, gondata):
		# calculate scale for each data point
		avg = 0.0
		for pos,pix in zip(gondata.gonpos, gondata.pixpertick):
			modval = self.eval(pos)
			scale = modval / pix
			avg += scale
		avg /= len(gondata.gonpos)
		return avg


if __name__ == '__main__':
	mymod = GonModel()
	import numpy.random as rand
	a = rand.random((1,12))
	b = rand.random((1,12))
	d = {
		'axis': 'x',
		'period': 5.6e-5,
		'a': a,
		'b': b,
	}
	mymod.fromDict(d)

	import profile
	xs =  rand.random(10000)
	def test1():
		for x in xs:
			mymod.eval_int(x)
	def test2():
		for x in xs:
			mymod.eval_int2(x)

	profile.run('test2()')
	profile.run('test1()')
