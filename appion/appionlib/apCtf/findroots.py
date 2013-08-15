#!/usr/bin/env python

import sys
import time
import math
import numpy
import random
from scipy import stats
from scipy import ndimage
from appionlib import apDisplay
from appionlib.apCtf import genctf

class FindRoots(object):
	#==================
	#==================
	def __init__(self, cs=2e-3, wavelength=3.35e-12, amp_con=0.07, 
			mindef=0.2e-6, maxdef=20e-6, volts=None):
		self.debug = False
		self.cs = cs
		self.wavelength = wavelength
		self.amp_con = amp_con
		self.mindef = mindef
		self.maxdef = maxdef
		self.volts = volts

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
	def removeFalsePostives(self, xsq, types):
		"""
		false positives that are too close together

		should incorporate information on type
		could choose n or n+1 to see which is better to remove or average them
		"""
		d = numpy.diff(xsq)
		lastdstd = 8*d.std()
		count = 0
		while lastdstd > 3*d.std():
			print lastdstd, d.std(), types
			lastdstd = d.std()
			lastxsq = xsq
			lasttypes = types
			n = numpy.argmin(d)
			xsq1 = numpy.delete(xsq, n)
			types1 = numpy.delete(types, n)
			d1 = numpy.diff(xsq1)
			xsq2 = numpy.delete(xsq, n+1)
			types2 = numpy.delete(types, n+1)
			d2 = numpy.diff(xsq2)
			if d1.std() < d2.std():
				xsq = xsq1
				types = types1
			else:
				xsq = xsq2
				types = types2
			d = numpy.diff(xsq)
			count += 1
		xsq = lastxsq
		types = lasttypes
		apDisplay.printMsg("removed %d false positive to find roots"%(count-1))
		return xsq, types

	#==================
	#==================
	def findPath(self, x, types):
		#print ""

		xsq = x**2
		xsq, types = self.removeFalsePostives(xsq, types)

		## group peaks together
		for i in range(len(types)-1):
			if types[i] > types[i+1]:
				types[i+1:] += 4

		rho = 2
		count = 0
		lasttypes = types
		while abs(rho) > 0.7 and count < 10:
			count += 1
			zvalues = self.getDefocus(xsq*1e20, types)
			if zvalues is None:
				types = lasttypes
				zvalues = self.getDefocus(xsq*1e20, types)
				break

			apDisplay.printColor("defocus estimate %d: %.3f um +/- %.3f"
				%(count, zvalues.mean()*1e6, zvalues.std()*1e6), "magenta")

			xtemp = numpy.arange(zvalues.shape[0])
			rho = self.getLinearRho(xtemp, zvalues)
			lasttypes = types
			if rho > 0.7:
				types += 4
			elif rho < -0.7:
				types -= 4

		bestdef = numpy.median(zvalues)
		print "best defocus=", bestdef
		return bestdef

	#==================
	#==================
	def findPathDiffs(self, x, types):
		#print ""

		xsq = x**2 * 1e10**2
		xsq, types = self.removeFalsePostives(xsq, types)
		newx = numpy.sqrt(xsq)

		## group peaks together
		for i in range(len(types)-1):
			if types[i] > types[i+1]:
				types[i+1:] += 4
		cs = self.cs
		wv = self.wavelength
		phi = math.asin(self.amp_con)

		defocii = []
		for i in range(len(xsq)-1):
			# case 1: consecutive peaks
			if types[i+1] - types[i] < 5:
				xsq1 = xsq[i+1]
				xsq2 = xsq[i]
				ndiff = types[i+1] - types[i]
				defocus = self.getDiffDefocus(ndiff, xsq1, xsq2)
				if defocus > self.mindef and defocus < self.maxdef:
					defocii.append(defocus)

			# case 2: alternate peaks
			if i+3 > len(types):
				continue
			if types[i+2] - types[i] < 5:
				xsq1 = xsq[i+2]
				xsq2 = xsq[i]
				ndiff = types[i+2] - types[i]
				defocus = self.getDiffDefocus(ndiff, xsq1, xsq2)
				if defocus > self.mindef and defocus < self.maxdef:
					defocii.append(defocus)

			# case 3: triplet peaks
			if i+4 > len(types):
				continue
			if types[i+3] - types[i] < 5:
				xsq1 = xsq[i+3]
				xsq2 = xsq[i]
				ndiff = types[i+3] - types[i]
				defocus = self.getDiffDefocus(ndiff, xsq1, xsq2)
				if defocus > self.mindef and defocus < self.maxdef:
					defocii.append(defocus)

			# case 4: full cycle peaks
			if i+5 > len(types):
				continue
			if types[i+4] - types[i] < 5:
				xsq1 = xsq[i+4]
				xsq2 = xsq[i]
				ndiff = types[i+4] - types[i]
				defocus = self.getDiffDefocus(ndiff, xsq1, xsq2)
				if defocus > self.mindef and defocus < self.maxdef:
					defocii.append(defocus)

		defocii.sort()
		#print defocii

		defocii = numpy.array(defocii)

		#print types
		#print numpy.mod(types,4)
		approxctf = numpy.where(numpy.mod(types,4) == 1, 0, types)
		approxctf = numpy.where(numpy.mod(types,4) == 2, 1, approxctf)
		approxctf = numpy.where(numpy.mod(types,4) == 3, 0, approxctf)
		approxctf = numpy.where(numpy.mod(types,4) == 0, -1, approxctf)

		counts = []
		for defocus in defocii:
			count = self.numMatchingPoints(newx, approxctf, defocus)
			counts.append(count)
		counts = numpy.array(counts)
		weightedmean = numpy.sum(defocii*counts)/numpy.sum(counts)
		#print "weightedmean", weightedmean

		index = numpy.argmax(counts)
		idealdef = defocii[index]

		"""
		bestdef = numpy.median(defocii)
		#print "best defocus= %.3e +- %.1e"%(bestdef, defocii.std())
		## filter outliers:
		defocii = defocii[numpy.where(defocii > bestdef - 2*defocii.std())]
		defocii = defocii[numpy.where(defocii < bestdef + 2*defocii.std())]
		bestdef = numpy.median(defocii)
		#print "best defocus= %.3e +- %.1e"%(bestdef, defocii.std())
		defocii = defocii[numpy.where(defocii > bestdef - 2*defocii.std())]
		defocii = defocii[numpy.where(defocii < bestdef + 2*defocii.std())]
		bestdef = numpy.median(defocii)
		#print "best defocus= %.3e +- %.1e"%(bestdef, defocii.std())
		"""

		self.numMatchingPoints(newx, approxctf, idealdef, show=True)

		#sys.exit(1)
		return idealdef

	#==================
	#==================
	def numMatchingPoints(self, x, approxctf, defocus, show=False):
		ctfvals = genctf.generateCTF1d(radii=x, focus=defocus, cs=self.cs, 
			volts=self.volts, ampconst=self.amp_con)
		#print x, types, ctfvals
		#print approxctf 

		countarray = numpy.where(numpy.abs(ctfvals - approxctf) < 0.2, 0.5, 0)
		count = countarray.sum()

		countarray = numpy.where(numpy.abs(ctfvals - approxctf) < 0.35, 0.5, 0)
		count += countarray.sum()

		countarray = numpy.where(numpy.abs(ctfvals - approxctf) < 0.5, 0.1, -0.1)
		count += countarray.sum()

		if show is True:
			from matplotlib import pyplot
			pyplot.clf()
			pyplot.plot(x, 2*ctfvals-1, linestyle='-', marker='o', color="black")
			pyplot.plot(x, approxctf, linestyle='-', marker='.', color="blue")
			pyplot.show()
		
		#print defocus, count

		return count


	#==================
	#==================
	def getDiffDefocus(self, ndiff, xsq1, xsq2):
		numer = ndiff + 2 * self.cs * self.wavelength**3 * ( xsq1**2 - xsq2**2 )
		denom = 4 * self.wavelength * ( xsq1 - xsq2 )
		defocus = numer/denom
		return defocus
	

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
	def getDefocus(self, xsq, nvalues):

		cs = self.cs
		wv = self.wavelength
		phi = math.asin(self.amp_con)

		numer = nvalues * math.pi + 2 * math.pi * cs * wv**3 * xsq**2 - 4 * phi
		denom = 4 * math.pi * wv * xsq
		zvalues = numer/denom
		zvalues = zvalues[numpy.where(zvalues > self.mindef)]
		zvalues = zvalues[numpy.where(zvalues < self.maxdef)]
		if len(zvalues) == 0:
			return None
		return zvalues

	#==================
	#==================
	def getZeros(self, a, b):
		#print a.shape
		#print b.shape
		signs = numpy.sign(a)
		diff = numpy.ediff1d(signs, to_end=0)
		b = numpy.where(numpy.logical_and(diff > 0, b < 0))
		c = numpy.where(numpy.logical_and(diff < 0, b > 0))
		#print b, c
		return b, c

#==================
#==================
def estimateDefocus(xdata, ydata, cs=2e-3, wavelength=3.35e-12, 
		amp_con=0.07, mindef=0.2e-6, maxdef=20e-6, volts=None):
	"""
	xdata in inverse Angstroms
	"""
	fcls = FindRoots(cs, wavelength, amp_con, mindef, maxdef, volts)
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

	if True: #fcls.debug is True:
		from matplotlib import pyplot	
		pyplot.plot (xdatasq,ydata, color="darkgreen", linewidth=2)
		pyplot.hlines(0, 0, xdatasq[-1], color="black")
		if len(xups) > 0:
			pyplot.vlines(xups**2, -1, 1, color="red")
		if len(xmaxs) > 0:
			pyplot.vlines(xmaxs**2, -1, 1, color="blue")
		if len(xdowns) > 0:
			pyplot.vlines(xdowns**2, -1, 1, color="orange")
		if len(xmins) > 0:
			pyplot.vlines(xmins**2, -1, 1, color="violet")
		pyplot.show()

	xzeros = numpy.hstack([xups, xmaxs, xdowns, xmins])
	xzerostype = numpy.hstack([
		numpy.ones(xups.shape), 
		numpy.ones(xmaxs.shape)*2, 
		numpy.ones(xdowns.shape)*3, 
		numpy.ones(xmins.shape)*4])
		
	args = numpy.argsort(xzeros)

	#print "find path diffs"
	defocus = fcls.findPathDiffs(xzeros[args], xzerostype[args])
	#print "find path"
	#defocus = fcls.findPath(xzeros[args], xzerostype[args])

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
	pyplot.plot (xdatasq,cumsumy, color="darkblue", linewidth=2)
	pyplot.plot (xdatasq,diffy, color="darkred", linewidth=2)

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

	pyplot.plot (xzeros**2, xzerostype, "x", color="darkgreen")
	pyplot.plot (ac, "x", color="darkgreen")
	pyplot.show()

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
	


	


