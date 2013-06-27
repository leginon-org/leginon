#!/usr/bin/env python

import time
import math
import numpy
import random
from scipy import stats
from scipy import ndimage

class FindRoots(object):
	#==================
	#==================
	def __init__(self, cs=2e-3, wavelength=3.35e-12, amp_con=0.07, mindef=0.2e-6, maxdef=20e-6):
		self.debug = False
		self.cs = cs
		self.wavelength = wavelength
		self.amp_con = amp_con
		self.mindef = mindef
		self.maxdef = maxdef

		if self.debug is True:
			from matplotlib import pyplot	

	#==================
	#==================
	def autocorr(self, x):
		 result = numpy.correlate(x, x, mode='full')
		 return result[result.size/2:]

	#==================
	#==================
	def choice(self, a):
		try:
			linDecay = numpy.arange(1.0, 0.0, 1.0/len(a))
			c = numpy.random.choice(a, 1, p=linDecay)
		except:
			i = int(random.random()*len(a))
			c = a[i]
		return c

	#==================
	#==================
	def findPath(self, x, types):
		#print ""
		xsq = x**2
		d = numpy.diff(xsq)
		#print xsq
		#print d.std()
		lastdstd = 2*d.std()
		while lastdstd > d.std():
			lastdstd = d.std()
			lastxsq = xsq
			lasttypes = types
			n = numpy.argmin(d)
			xsq = numpy.delete(xsq, n)
			types = numpy.delete(types, n)
			#xsq = numpy.concatenate([xsq[:n], xsq[n+1:]])
			#types = numpy.concatenate([types[:n], types[n+1:]])
			d = numpy.diff(xsq)
			#print xsq
			#print d.std()
		xsq = lastxsq
		types = lasttypes
		#print xsq
		#print types
		#newtypes = []
		for i in range(len(types)-1):
			if types[i] > types[i+1]:
				types[i+1:] += 4
		#print types

		"""
		d = numpy.diff(xsq)/(numpy.diff(types) + 0.1)
		lastdstd = 2*d.std()
		while lastdstd > d.std():
			lastdstd = d.std()
			lastxsq = xsq
			lasttypes = types
			n = numpy.argmin(d)
			xsq = numpy.concatenate([xsq[:n], xsq[n+1:]])
			types = numpy.concatenate([types[:n], types[n+1:]])
			d = numpy.diff(xsq)/numpy.diff(types)
			print xsq
			print d.std()
		"""

		newx = numpy.sqrt(xsq)
		zvalues = []
		for i in range(len(newx)):
			zs = self.getDefocus(newx[i]*1e10, types[i])
			if isinstance(zs, int):
				continue
			zvalues.append(zs[0])
			print zs[0]

		zvalues = numpy.array(zvalues)
		xtemp = numpy.arange(zvalues.shape[0])
		rho = self.getLinearRho(xtemp, zvalues)
		if rho > 0.5:
			types += 4
		elif rho < -0.5:
			types -= 4

		zvalues = []
		for i in range(len(newx)):
			zs = self.getDefocus(newx[i]*1e10, types[i])
			if isinstance(zs, int):
				continue
			zvalues.append(zs[0])
			print zs[0]

		zvalues = numpy.array(zvalues)
		xtemp = numpy.arange(zvalues.shape[0])
		rho = self.getLinearRho(xtemp, zvalues)

		bestdef = numpy.median(zvalues)
		print "bestDef=", bestdef
		return bestdef

	#==================
	#==================
	def getLinearRho(self, x, y):
		slope, intercept, rho, _, _ = stats.linregress(x,y)
		print "slope=", slope, "rho=", rho
		return rho

	#==================
	#==================
	def getNormRunningSum(self, x, y):
		cumsumy = numpy.cumsum(y)
		slope, intercept, _, _, _ = stats.linregress(x,cumsumy)
		fity = slope*x + intercept
		cumsumy = cumsumy-fity
		cumsumy /= numpy.abs(cumsumy).max()
		return cumsumy

	#==================
	#==================
	def getDefocus(self, s, n=1, num=0):
		nvalues = numpy.arange(n-4*num, n+4*num+1, 4)
		nvalues = nvalues[numpy.where(nvalues > 0)]

		cs = self.cs
		wv = self.wavelength
		phi = math.asin(self.amp_con)

		numer = nvalues * math.pi + 2 * math.pi * cs * wv**3 * s**4 - 4 * phi
		denom = 4 * math.pi * wv * s**2
		zvalues = numer/denom
		zvalues = zvalues[numpy.where(zvalues > self.mindef)]
		if len(zvalues) == 0:
			return +1
		zvalues = zvalues[numpy.where(zvalues < self.maxdef)]
		if len(zvalues) == 0:
			return -1
		return zvalues

	#==================
	#==================
	def getZeros(self, a, b):
		print a.shape
		print b.shape
		signs = numpy.sign(a)
		diff = numpy.ediff1d(signs, to_end=0)
		b = numpy.where(numpy.logical_and(diff > 0, b < 0))
		c = numpy.where(numpy.logical_and(diff < 0, b > 0))
		print b, c
		return b, c

#==================
#==================
def estimateDefocus(xdata, ydata, cs=2e-3, wavelength=3.35e-12, 
		amp_con=0.07, mindef=0.2e-6, maxdef=20e-6):
	"""
	xdata in inverse Angstroms
	"""
	fcls = FindRoots(cs, wavelength, amp_con, mindef, maxdef)
	xdatasq = xdata**2

	cumsumy = fcls.getNormRunningSum(xdatasq, ydata)
	ups,downs = fcls.getZeros(ydata, cumsumy)
	diffy = numpy.ediff1d(ydata, to_begin=0)
	diffy = ndimage.filters.gaussian_filter(diffy, sigma=1)
	diffy /= numpy.abs(diffy).max()
	mins,maxs = fcls.getZeros(diffy, ydata)

	xups = xdata[ups]
	xmaxs = xdata[maxs]
	xdowns = xdata[downs]
	xmins = xdata[mins]

	if fcls.debug is True:
		pyplot.plot (xdatasq,ydata, color="darkgreen", linewidth=2)
		pyplot.hlines(0, 0, xdatasq[-1], color="black")
		pyplot.vlines(xups**2, -1, 1, color="red")
		pyplot.vlines(xmaxs**2, -1, 1, color="blue")
		pyplot.vlines(xdowns**2, -1, 1, color="orange")
		pyplot.vlines(xmins**2, -1, 1, color="violet")
		pyplot.show()

	xzeros = numpy.hstack([xups, xmaxs, xdowns, xmins])
	xzerostype = numpy.hstack([
		numpy.ones(xups.shape), 
		numpy.ones(xmaxs.shape)*2, 
		numpy.ones(xdowns.shape)*3, 
		numpy.ones(xmins.shape)*4])
		
	args = numpy.argsort(xzeros)
	
	defocus = fcls.findPath(xzeros[args], xzerostype[args])


	return defocus

#==================
#==================	
if __name__ == "__main__" :
	from matplotlib import pyplot
	filename = "ctfroots.dat"
	#filename = "interact1-profile.dat"
	f = open (filename, "r")
	xdata = []
	ydata = []
	count = 0
	for line in f:
		sline = line.strip()
		bits = sline.split()
		if len(bits)<2:
			continue
		count += 1
		if count < 50:
			continue
		x = float(bits[0])
		xdata.append(x)
		y = float(bits[1])
		ydata.append(y)

		#if count >200:
		#	break
		if x > 0.125e10:
			break
	#print xdata
	f.close()
	xdata = numpy.array(xdata) #/1e10
	ydata = numpy.array(ydata)
	if ydata.min() > -0.1:
		ydata = ydata - 0.5
	ydata /= numpy.abs(ydata).max()
	xdatasq = xdata**2

	t0=time.time()

	fcls = FindRoots()

	zvalues = []
	cumsumy = fcls.getNormRunningSum(xdatasq, ydata)
	ups,downs = fcls.getZeros(ydata, cumsumy)
	diffy = numpy.ediff1d(ydata, to_begin=0)
	diffy = ndimage.filters.gaussian_filter(diffy, sigma=1)
	diffy /= numpy.abs(diffy).max()
	mins,maxs = fcls.getZeros(diffy, ydata)

	xups = xdata[ups]
	xmaxs = xdata[maxs]
	xdowns = xdata[downs]
	xmins = xdata[mins]

	pyplot.plot (xdatasq,ydata, color="darkgreen", linewidth=2)
	#pyplot.plot (xdatasq,cumsumy, color="darkblue", linewidth=2)
	#pyplot.plot (xdatasq,diffy, color="darkred", linewidth=2)

	pyplot.hlines(0, 0, xdatasq[-1], color="black")
	if len(xups) > 0:
		pyplot.vlines(xups**2, -1, 1, color="red")
		pyplot.vlines(xmaxs**2, -1, 1, color="blue")
		pyplot.vlines(xdowns**2, -1, 1, color="orange")
		pyplot.vlines(xmins**2, -1, 1, color="violet")
	pyplot.show()

	xzeros = numpy.hstack([xups, xmaxs, xdowns, xmins])
	xzerostype = numpy.hstack([
		numpy.ones(xups.shape), 
		numpy.ones(xmaxs.shape)*2, 
		numpy.ones(xdowns.shape)*3, 
		numpy.ones(xmins.shape)*4])
		
	args = numpy.argsort(xzeros)
	print args
	
	combine = numpy.vstack([xzeros[args], xzerostype[args]])
	
	for i in range(combine.shape[1]):
		print "%.6f\t%d"%(combine[0,i]**2, int(combine[1,i]))

	ac = fcls.autocorr(xzeros**2)

	#pyplot.plot (xzeros**2, xzerostype, "x", color="darkgreen")
	#pyplot.plot (ac, "x", color="darkgreen")
	#pyplot.show()

	fcls.findPath(xzeros[args], xzerostype[args])


	"""
	for i, s in enumerate(xups):
		zvalues.extend(getDefocus(s*1e10, 1+4*i))

	for i, s in enumerate(xmaxs):
		zvalues.extend(getDefocus(s*1e10, 2+4*i))
		
	for i, s in enumerate(xdowns):
		zvalues.extend(getDefocus(s*1e10, 3+4*i))

	for i, s in enumerate(xmins):
		zvalues.extend(getDefocus(s*1e10, 4+4*i))

	zarray = numpy.array(zvalues, dtype=numpy.float64)

	print len(zvalues)

	gridres = 0.2e-6
	zints = numpy.array(zarray/gridres, dtype=numpy.uint32)
	counts = numpy.bincount(zints)
	counts = numpy.array(counts, dtype= numpy.float64)
	counts = ndimage.gaussian_filter(counts, 1)
	print numpy.round(counts, 1)
	print numpy.argmax(counts)*gridres
	"""
	


	


