#!/usr/bin/env python
import math, string
import Numeric
import LinearAlgebra
import shelve

class OLDMagInfo:
	def __init__(self, magfile):
		self.magfile = magfile
	def open_shelve(self):
		self.shelve = shelve.open(self.magfile)
	def close_shelve(self):
		self.shelve.close()

	def get(self, key):
		self.open_shelve()
		ret = self.shelve[key] 
		self.close_shelve()
		return ret

	def set(self, key, value):
		self.open_shelve()
		self.shelve[key] = value
		self.close_shelve()

class GonData:
	"""
	A GonData instance holds the data from a goniometer calibration.
	It is only meant to handle one axis.
	"""
	def __init__(self, infile):
		self.gonpos = None
		self.othergonpos = None
		self.pixpertick = None
		self.datavg = None
		self.angle = None
		self.maginfo = {}
		self.read_data(infile)

	def dict(self):
		return self.maginfo

	def read_data(self,filename):
		datafile = open(filename, 'r')
		lines = datafile.readlines()
		datafile.close()

		headlines = lines[:2]
		headlines = map(string.split,headlines)
		self.mag = float(headlines[0][0])
		self.axis = headlines[1][0]

		print 'mag', self.mag
		print 'axis', self.axis

		datalines = lines[2:]
		datalen = len(datalines)

		self.gonpos = Numeric.zeros(datalen,Numeric.Float32)
		self.othergonpos = Numeric.zeros(datalen,Numeric.Float32)
		self.pixpertick = Numeric.zeros(datalen,Numeric.Float32)

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
		print 'len(datalines)', len(datalines)
		for line in datalines:
			sp = string.split(line)
			sp = map(float,sp)
			if len(sp) == 5:
				self.gonpos[n] = sp[gonposcol]
				self.othergonpos[n] = sp[othergonposcol]
				self.pixpertick[n] = math.sqrt(sp[3] * sp[3] + sp[4] * sp[4]) /  sp[2]
				self.avg += self.pixpertick[n]
				self.angle += math.atan2(sp[4],sp[3])
				n += 1
			else:
				print 'SP', sp

		self.ndata = n
		print 'NNN', n
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
	def eval_int(self, pos):
		k = 2.0 * math.pi / self.period
		k2 = k * pos
		result = pos
		for i in range(len(self.a)):
			q = (i + 1) * k2
			result += self.a[i] / k / (i+1) * math.sin(q)
			result -= self.b[i] / k / (i+1) * math.cos(q)
		return result

	## return a goniometer delta based on an image delta
	## this is a rotation, not scaled to the model
	## this only calculates the gon delta for one axis
	def rotate(self, angle, ximg, yimg):
		gon = ximg * math.cos(angle) + yimg * math.sin(angle)
		return gon

	## calculate a delta ticks from current position and delta nm
	def predict(self, pos, delta):

		# initial guess
		k = pos + delta

		# first iteration
		f = self.eval_int(k) - self.eval_int(pos) - delta
		df = self.eval(k)
		correction = f / df
		kplus = k - correction
		
		# iterate to machine precision
		while k != kplus:
			k = kplus
			f = self.eval_int(k) - self.eval_int(pos) - delta
			df = self.eval(k)
			correction = f / df
			kplus = k - correction

			# check if damping is necessary
			while self.eval_int(kplus) - self.eval_int(pos) - delta > f:
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

	def fromDict(self, d):
		self.axis = d['axis']
		self.period = d['period']
		self.a = d['a']
		self.b = d['b']

	def design_matrix(self, gondata, terms, period):
		ma = 2 * terms + 1
		a = Numeric.zeros((gondata.ndata, ma),Numeric.Float32)
		print 'gondata.gonpos', gondata.gonpos.shape
		print 'a.shape', a.shape

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
		search_periods = 20.0

		best_resids = 1e999
		precision = 0.1

		## minp,maxp work for the Philips CM/Tecnai
		## other goniometers may vary
		minp = 0.000035
		maxp = 0.000070
		incp = precision + 1
		while incp > precision:
			incp = (maxp - minp) / search_periods
			for period in Numeric.arrayrange(minp, maxp, incp):
				a = self.design_matrix(gondata,terms,period)
				x,resids,rank,s = LinearAlgebra.linear_least_squares(a,b)
				if resids < best_resids:
					best_resids = resids
					best_period = period
					best_x = x
			minp = best_period - incp
			maxp = best_period + incp

		self.period = best_period
		self.a0 = 1.0 / best_x[0]

		if 'model mean' not in gondata.maginfo:
			gondata.maginfo['model mean'] = {}
		gondata.maginfo['model mean'][gondata.axis] = self.a0
		print "maginfo set:"
		print "  modavg" + gondata.axis, self.a0

		self.a = Numeric.zeros(terms)
		self.b = Numeric.zeros(terms)
		for i in range(terms):
			self.a[i] = best_x[2*i+1]
			self.b[i] = best_x[2*i+2]

		## normalize
		self.a = self.a0 * self.a
		self.b = self.a0 * self.b
		self.axis = gondata.axis


if __name__ == '__main__':
	mymod = GonModel()
	mymod.read_model('1600.gonx')
	print mymod.eval(1234)
	print mymod.predict(12345, 1000)
	print mymod.rotate(123, 300)
	mymod.read_data('01sep24.x')
	mymod.fit_data(3,35000,70000)
	print "period", mymod.period
	print "rotation", mymod.rotation
	print "a0", mymod.a0
	print "a", mymod.a
	print "b", mymod.b
