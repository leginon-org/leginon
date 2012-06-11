#!/usr/bin/env python


import os
import math
import numpy
from appionlib import apDisplay
from appionlib.apImage import imagestat

#=============================
#=============================
#=============================
class ImproveIEEEfit(object):
	def __init__(self, k, xdata, ydata):
		"""
		xdata is linear from the CTF
		ydata is the normalized CTF with range 0 -> 1 and mean 0.5
		k is the shift as published in:
			Park et al., IEEE Trans on Instr. and Meas. v 60#8, Aug 2011
		DOI: 10.1109/TIM.2011.2121231

		ydata ~= sin ( xdata^2 * freq + phi)
		"""
		self.k = k
		self.xdata = xdata
		self.ydata = ydata
		self.xdatasq = self.xdata**2
		xfull = self.xdatasq.max() - self.xdatasq.min()
		self.sampling = xfull/float(len(self.xdata))

		self.xmax = self.sampling * len(self.xdata)**2
		print "Max X", self.xmax
		print "X sampling", self.sampling
		print "X data", len(self.xdata)
		imagestat.printImageInfo(self.xdata)
		print "X data^2", len(self.xdatasq)
		imagestat.printImageInfo(self.xdatasq)
		print "Y data", len(self.ydata)
		imagestat.printImageInfo(self.ydata)

	#================
	def a(self, n):
		return self.getY(n**2) - self.getY(n**2-self.k)

	#================
	def b(self, n):
		firstterm =  self.getY(n**2+self.k) - self.getY(n**2)
		secondterm = self.getY(n**2-self.k) - self.getY(n**2-2*self.k)
		return (firstterm + secondterm)/2.

	#================
	def getY(self, xval):
		#print xval, "-->", xval*self.sampling
		if xval < 0:
			apDisplay.printError("Negative X value: %d -> %.3f"%(xval, xval*self.sampling))
		xsampl = xval*self.sampling
		if xsampl > self.xmax:
			apDisplay.printError("X value out of bounds: %d -> %.3f > %.2f"%(xval, xsampl, self.xmax))
		yinterp = numpy.interp(xsampl, self.xdatasq, self.ydata)
		#print xval, xsampl, yinterp
		return yinterp

	#================
	def fit(self):
		# n^2 - 2k > 0 => n^2 > 2k => n > sqrt(2k)
		nmin = int(math.ceil(math.sqrt(2*self.k)))+2
		# n^2 + k < N - 1 => n^2 < N - k - 1 => n < sqrt(N - k - 1)
		nmax = int(math.floor(math.sqrt(len(self.xdata) - self.k - 1)))
		#print "min,max", nmin, nmax
		print "k,min,max", self.k, nmin, nmax
		if nmin >= nmax:
			# 2k > N - k - 1 =>  3k > N-1 => k > (N-1)/3
			return None
		nvalues = range(nmin, nmax)
		sumab = 0
		sumaa = 0
		for n in nvalues:
			a = self.a(n)
			b = self.b(n)
			#print a,b
			sumab += a*b
			sumaa += a**2
		print "sumab/sumaa", sumab, sumaa, len(nvalues)
		ratio = sumab/sumaa
		acos = math.acos(ratio)
		# k w T = acos => w = acos/k/T
		frequency = acos/self.k

		fitdata = numpy.zeros(ydata.shape)
		sqmax = int(math.floor(math.sqrt(len(self.xdata))))
		for i in range(sqmax):
			fitdata[i] = math.sin(frequency * self.xdata[i] *self.sampling)

		"""
		from matplotlib import pyplot
		print len(self.xdata), len(self.ydata), len(fitdata)
		pyplot.plot(self.xdata, self.ydata, 'r-', )
		pyplot.plot(self.xdata, fitdata, 'k-', )
		pyplot.show()
		"""

		return frequency

if __name__ == "__main__":
	xdata = numpy.load("xdata.npz", "r")['arr_0']
	ydata = numpy.load("ydata.npz", "r")['arr_0']
	N = len(xdata)
	maxk = int(math.floor((N-1)/6))
	print "maxk=", maxk
	#k = 10
	#for k in range(100,maxk):
	k=100
	freqs = []
	for k in range(100,200):
		print "k=", k
		a = ImproveIEEEfit(k, xdata, ydata)
		freq = a.fit()
		freqs.append(freq)
	print freqs

