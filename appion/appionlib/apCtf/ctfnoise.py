#!/usr/bin/env python

import sys
import math
import time
import numpy
import scipy.optimize
import scipy.ndimage
import scipy.interpolate
from appionlib import apDisplay

### remove warning about polyfit
import warnings
warnings.simplefilter('ignore', numpy.RankWarning)

class CtfNoise(object):

	#============
	def __init__(self):
		self.debug = False

	#============
	def runMinimization(self, xdata, ctfdata, initfitparams, noiseModel, contraintFunction, maxfun=1e4):
		"""
		run a minimization
		"""

		refinefitparams = scipy.optimize.fmin_cobyla( self.modelFitFun, initfitparams, 
			args=(xdata, ctfdata, noiseModel), cons=[contraintFunction,],
			consargs=(xdata, ctfdata, noiseModel), iprint=0, maxfun=maxfun)

		return refinefitparams


	#============
	def writeDatFile(self, filename, fitparams, xdata, ctfdata):
		return
		fitx = self.noiseModel(fitparams, xdata)
		f = open(filename, "w")
		for i in range(len(xdata)):
			f.write("%.3f\t%.8f\t%.8f\n"%(xdata[i], fitx[i], ctfdata[i]))
		f.close()

	#============
	def noiseModelBFactor(self, fitparams, xdata=None):
		"""
		Function to model ctf noise using: A + B*x^2
		"""
		fitx = ( fitparams[0] 
			+ fitparams[1]*numpy.power(xdata, 2.0)
		)
		return fitx

	#============
	def noiseModelOnlyLinear(self, fitparams, xdata=None):
		"""
		Function to model ctf noise using: A + B*x
		"""
		fitx = ( fitparams[0] 
			+ fitparams[1]*xdata 
		)
		return fitx

	#============
	def noiseModelOnlySqrt(self, fitparams, xdata=None):
		"""
		Function to model ctf noise using: A + B*sqrt(x)
		"""
		fitx = ( fitparams[0] 
			+ fitparams[1]*numpy.sqrt(xdata) 
		)
		return fitx

	#============
	def noiseModelNoSquare(self, fitparams, xdata=None):
		"""
		Function to model ctf noise using: A + B*sqrt(x) + C*x
		"""
		fitx = ( fitparams[0] 
			+ fitparams[1]*numpy.sqrt(xdata) 
			+ fitparams[2]*xdata 
		)
		return fitx

	#============
	def noiseModel(self, fitparams, xdata=None):
		"""
		Function to model ctf noise
		"""
		fitx = ( fitparams[0] 
			+ fitparams[1]*numpy.sqrt(xdata) 
			+ fitparams[2]*xdata 
			+ fitparams[3]*numpy.power(xdata, 2.0)
			+ fitparams[4]*numpy.power(xdata, 3.0)
		)
		return fitx

	#============
	def modelConstFunAbove(self, fitparams, xdata=None, ctfdata=None, model=None):
		"""
		constraint: f(x) - fit(x) < 0
			     OR: fit(x) - f(x) > 0  -- forces to fit above function

		if returns value of constraint, such that any thing below zero is bad
		"""
		if model is None:
			model = self.noiseModel
		fitx = model(fitparams, xdata)
		meanval = (fitx - ctfdata).mean()
		minval = (fitx - ctfdata).min()
		### allow the function to go below the maximum by 5% of the mean
		fitval = minval #+ (meanval - minval)*0.15
		return fitval

	#============
	def modelConstFunBelow(self, fitparams, xdata=None, ctfdata=None, model=None):
		"""
		constraint: f(x) - fit(x) > 0  -- forces to fit below function

		if returns value of constraint, such that any thing below zero is bad
		"""
		if model is None:
			model = self.noiseModel
		fitx = model(fitparams, xdata)
		meanval = (ctfdata - fitx).mean()
		minval = (ctfdata - fitx).min()
		### allow the function to go above the minimum by 15% of the mean
		fitval = minval #+ (meanval - minval)*0.15
		return fitval

	#============
	def modelFitFun(self, fitparams, xdata=None, ctfdata=None, model=None, trimdata=True):
		"""
		calculate sum of square difference to fit function
		"""
		if model is None:
			model = self.noiseModel
		fitx = model(fitparams, xdata)
		#fitness = ((ctfdata - fitx)**2).mean()
		#fitness = numpy.abs(ctfdata - fitx).mean()
		#fitness = ((ctfdata - fitx)**2).sum()
		#fitness = numpy.abs(ctfdata - fitx).sum()

		### BEST MODEL
		fitfunc = numpy.abs(ctfdata - fitx)
		if trimdata is True:
			mean = fitfunc.mean()
			fitfunc = numpy.where(fitfunc > mean, mean, fitfunc)
		fitness = fitfunc.sum()
		### END BEST MODEL

		#fitness = 1.0 - scipy.stats.pearsonr(fitx, ctfdata)[0]
		return fitness

	#============
	def fitNoSquare(self, xdata, ctfdata, contraintFunction, maxfun=1e4):
		"""
		model the noise using: A + B*sqrt(x) + C*x
		"""
		try:
			z = numpy.polyfit(numpy.sqrt(xdata), ctfdata, 2)
		except:
			return None, None
		if self.debug is True:
			print "poly fit: sqrt(x),y = ", z

		initfitparams = [z[2], z[1], z[0]]

		nosqfitparams = self.runMinimization(xdata, ctfdata, initfitparams, 
			self.noiseModelNoSquare, contraintFunction, maxfun)

		### add square term back in
		fitparams = [nosqfitparams[0], nosqfitparams[1], nosqfitparams[2], 0.0, 0.0]
		nosqvalue = self.modelFitFun(fitparams, xdata, ctfdata)
		#writeDatFile("nosqvalue.dat", fitparams, xdata, ctfdata)
		return fitparams, nosqvalue

	#============
	def fitLinear(self, xdata, ctfdata, contraintFunction, maxfun=1e4):
		"""
		model the noise using: A + B*x
		"""
		z = numpy.polyfit(xdata, ctfdata, 1)
		if self.debug is True:
			print "poly fit: x,y = ", z

		initfitparams = [z[1], z[0]]

		linearfitparams = self.runMinimization(xdata, ctfdata, initfitparams, 
			self.noiseModelOnlyLinear, contraintFunction, maxfun)

		### add square root and square terms back in
		fitparams = [linearfitparams[0], 0.0, linearfitparams[1], 0.0, 0.0]
		linearvalue = self.modelFitFun(fitparams, xdata, ctfdata)
		#writeDatFile("linearvalue.dat", fitparams, xdata, ctfdata)
		return fitparams, linearvalue

	#============
	def fitOnlySqrt(self, xdata, ctfdata, contraintFunction, maxfun=1e4):
		"""
		model the noise using: A + B*sqrt(x)
		"""
		z = numpy.polyfit(numpy.sqrt(xdata), ctfdata, 1)
		if self.debug is True:
			print "poly fit: sqrt(x),y = ", z
		initfitparams = [z[1], z[0]]

		sqrtfitparams = self.runMinimization(xdata, ctfdata, initfitparams, 
			self.noiseModelOnlySqrt, contraintFunction, maxfun)

		### add linear and square terms back in
		fitparams = [sqrtfitparams[0], sqrtfitparams[1], 0.0, 0.0, 0.0]
		sqrtvalue = self.modelFitFun(fitparams, xdata, ctfdata)
		#writeDatFile("sqrtvalue.dat", fitparams, xdata, ctfdata)
		return fitparams, sqrtvalue

	#============
	def fitBFactor(self, xdata, ctfdata, contraintFunction, maxfun=1e4):
		"""
		model the noise using: A + B*sqrt(x)
		"""
		z = numpy.polyfit(numpy.power(xdata, 2), ctfdata, 1)
		if self.debug is True:
			print "poly fit: x**2,y = ", z
		initfitparams = [z[1], z[0]]

		bfactfitparams = self.runMinimization(xdata, ctfdata, initfitparams, 
			self.noiseModelBFactor, contraintFunction, maxfun)

		### add linear and square terms back in
		fitparams = [bfactfitparams[0], 0.0, 0.0, bfactfitparams[1], 0.0]
		bfactvalue = self.modelFitFun(fitparams, xdata, ctfdata)
		#writeDatFile("bfactvalue.dat", fitparams, xdata, ctfdata)
		return fitparams, bfactvalue

	#============
	def fitFullFunction(self, xdata, ctfdata, contraintFunction, maxfun=1e4):
		"""
		model the noise using full function
		"""
		z = numpy.polyfit(xdata, ctfdata, 3)
		if self.debug is True:
			print "poly fit: sqrt(x),y = ", z
		initfitparams = [z[3], 0.0, z[2], z[1], z[0]]

		fullfitparams = self.runMinimization(xdata, ctfdata, initfitparams, 
			self.noiseModel, contraintFunction, maxfun)

		### check the fit
		fullvalue = self.modelFitFun(fullfitparams, xdata, ctfdata)
		#writeDatFile("fullvalue.dat", fullfitparams, xdata, ctfdata)
		return fullfitparams, fullvalue


	#============
	def fitTwoSlopeFunction(self, xdata, ctfdata, contraintFunction, maxfun=1e4, cutoffper=2/5.):
		"""
		model the noise using: A + B*sqrt(x)
		"""
		## divide points into fifths
		numpoints = xdata.shape[0]
		cutoff = int(math.floor(cutoffper*numpoints))
		if self.debug is True:
			print "CUT: totalpoints=%d: fit1points=%d / fit2points=%d"%(numpoints, cutoff, (numpoints - cutoff))
		if cutoff < 3 or abs(numpoints - cutoff) < 3:
			return None, None
		if self.debug: print "cutoff percent %.3f (%d points)"%(cutoffper, cutoff)
		### fit first two fifths
		if self.debug is True: print "fit1"
		firstlinearfitparams, firstlinearvalue = self.fitLinear(
			xdata[:cutoff], ctfdata[:cutoff], contraintFunction, maxfun)
		### fit last two fifths
		if self.debug is True: print "fit2"		
		lastlinearfitparams, lastlinearvalue = self.fitLinear(
			xdata[-cutoff:], ctfdata[-cutoff:], contraintFunction, maxfun)

		xmin = xdata[0]
		xmax = xdata[len(xdata)-1]
		xfull = xmax - xmin
		m1 = firstlinearfitparams[2]
		b1 = firstlinearfitparams[0]
		m2 = lastlinearfitparams[2]
		b2 = lastlinearfitparams[0]
		xsquare = (m2 - m1)/xfull # m2*x^2 - m1*x^2
		xlinear = (m1*xmax - m2*xmin + b2 - b1)/xfull #m1*xmax - m2*xmin + b2 - b1
		xconst =  (b1*xmax - b2*xmin)/xfull #b1*xmax - b2*xmin

		initfitparams = numpy.array([xconst, 0, xlinear, xsquare, 0.0])
		if self.debug is True: print "modelFitFun"
		fullvalue = self.modelFitFun(initfitparams, xdata, ctfdata)
		return initfitparams, fullvalue

	#============
	def fitTwoSlopeSquareFunction(self, xdata, ctfdata, contraintFunction, maxfun=1e4, cutoffper=2/5.):
		"""
		model the noise using: A + B*sqrt(x)
		"""
		## divide points into fifths
		numpoints = xdata.shape[0]
		cutoff = int(math.floor(cutoffper*numpoints))
		if cutoff < 3 or (numpoints - cutoff) < 3:
			return None, None
		if self.debug: print "cutoff percent %.3f (%d points)"%(cutoffper, cutoff)
		### fit first two fifths
		firstlinearfitparams, firstlinearvalue = self.fitLinear(
			xdata[:cutoff], ctfdata[:cutoff], contraintFunction, maxfun)
		### fit last two fifths
		lastlinearfitparams, lastlinearvalue = self.fitLinear(
			xdata[-cutoff:], ctfdata[-cutoff:], contraintFunction, maxfun)

		## maxima: f[x] := (x-xmin)^2*(m1*x+b1) + (x-xmax)^2*(m2*x+b2);
		## expand(f[x]);

		## const: b1*xmin^2 + b2*xmax^2
		## linear: m1*x*xmin^2 -2*b1*x*xmin + m2*x*xmax^2 -2*b2*x*xmax
		## square: b2*x^2+b1*x^2 - 2*m1*x^2*xmin -2*m2*x^2*xmax
		## cube: m2*x^3+m1*x^3
		## Note: divide all by xfull^2

		xmin = xdata[0]
		xmax = xdata[len(xdata)-1]
		xfull = xmax - xmin
		xfullsq = xfull**2
		m1 = firstlinearfitparams[2]
		b1 = firstlinearfitparams[0]
		m2 = lastlinearfitparams[2]
		b2 = lastlinearfitparams[0]
		xconst = (b1*xmin**2 + b2*xmax**2)/xfullsq
		xlinear = (m1*xmin**2 + m2*xmax**2 - 2*(b1*xmin + b2*xmax))/xfullsq
		xsquare = (b2 + b1 - 2*(m1*xmin + m2*xmax))/xfullsq
		xcube = (m1 + m2)/xfullsq

		initfitparams = numpy.array([xconst, 0, xlinear, xsquare, 0.0])
		fullvalue = self.modelFitFun(initfitparams, xdata, ctfdata)
		return initfitparams, fullvalue

	#============
	def fitThreeSlopeSquareFunction(self, xdata, ctfdata, contraintFunction, maxfun=1e4, cutoffper=2/5.):
		"""
		model the noise using: A + B*sqrt(x)
		"""
		## divide points into fifths
		numpoints = xdata.shape[0]
		cutoff = int(math.floor(cutoffper*numpoints/2))*2
		if cutoff < 3 or (numpoints - cutoff) < 3:
			return None, None
		if self.debug: print "cutoff percent %.3f (%d points)"%(cutoffper, cutoff)
		### fit first two fifths
		firstlinearfitparams, firstlinearvalue = self.fitLinear(
			xdata[:cutoff], ctfdata[:cutoff], contraintFunction, maxfun)
		### fit middle three fifths
		midlinearfitparams, midlinearvalue = self.fitLinear(
			xdata[cutoff/2:-cutoff/2], ctfdata[cutoff/2:-cutoff/2], contraintFunction, maxfun)
		### fit last two fifths
		lastlinearfitparams, lastlinearvalue = self.fitLinear(
			xdata[-cutoff:], ctfdata[-cutoff:], contraintFunction, maxfun)

		## maxima: f[x] := (x-xmin)^2*(m1*x+b1) + (x-xmid)^2*(m2*x+b2) + (x-xmax)^2*(m3*x+b3);
		## expand(f[x]);

		## const: b1*xmin^2 + b2*xmid^2 + b3*xmax^2
		## linear: m1*xmin^2 + m2*xmid^2 + m3*xmax^2 - 2*(b1*xmin + b2*xmid + b3*xmax)
		## square: b3 + b2 + b1 - 2*(m1*xmin + m2*xmid + m3*xmax)
		## cube: m3 + m2 + m1
		## Note: divide all by xfull^2

		xmin = xdata[0]
		xmax = xdata[len(xdata)-1]
		midpoint = int((len(xdata)-1)/2)
		xmid = xdata[midpoint]
		xfull = xmax - xmin
		xfullsq = xfull**2
		m1 = firstlinearfitparams[2]
		b1 = firstlinearfitparams[0]
		m2 = midlinearfitparams[2]
		b2 = midlinearfitparams[0]
		m3 = lastlinearfitparams[2]
		b3 = lastlinearfitparams[0]
		xconst = (b1*xmin**2 + b2*xmid**2 + b3*xmax**2)/xfullsq
		xlinear = (m1*xmin**2 + m2*xmid**2 + m3*xmax**2 - 2*(b1*xmin + b2*xmid + b3*xmax))/xfullsq
		xsquare = (b3 + b2 + b1 - 2*(m1*xmin + m2*xmid + m3*xmax))/xfullsq
		xcube = (m1 + m2 + m3)/xfullsq

		initfitparams = numpy.array([xconst, 0, xlinear, xsquare, xcube])
		fullvalue = self.modelFitFun(initfitparams, xdata, ctfdata)
		return initfitparams, fullvalue

	#============
	def getAllInitialParameters(self, xdata, ctfdata, contraintFunction):
		namelist = [] #list of fit names
		valuelist = [] #list of fit square error values
		fitparamslist = [] #list of numpy array corresponding to param values

		fitparams, value = self.fitNoSquare(xdata, ctfdata, contraintFunction)
		namelist.append("no square")
		valuelist.append(value)
		fitparamslist.append(fitparams)

		fitparams, value = self.fitLinear(xdata, ctfdata, contraintFunction)
		namelist.append("linear")
		valuelist.append(value)
		fitparamslist.append(fitparams)

		fitparams, value = self.fitOnlySqrt(xdata, ctfdata, contraintFunction)
		namelist.append("only sqrt")
		valuelist.append(value)
		fitparamslist.append(fitparams)

		fitparams, value = self.fitBFactor(xdata, ctfdata, contraintFunction)
		namelist.append("b factor")
		valuelist.append(value)
		fitparamslist.append(fitparams)

		for cutoffper in numpy.arange(0.1, 0.99, 0.1):
			fitparams, value = self.fitTwoSlopeFunction(xdata, ctfdata, 
				contraintFunction, cutoffper=cutoffper)
			if fitparams is None:
				continue
			namelist.append("two slope %d"%(cutoffper*100))
			valuelist.append(value)
			fitparamslist.append(fitparams)		

		## does a bad job
		fitparams, value = self.fitTwoSlopeSquareFunction(xdata, ctfdata, contraintFunction, cutoffper=1/5.)
		if fitparams is not None:
			namelist.append("two slope sq 2/5")
			valuelist.append(value)
			fitparamslist.append(fitparams)

		## does a bad job
		fitparams, value = self.fitFullFunction(xdata, ctfdata, contraintFunction)
		namelist.append("full function")
		valuelist.append(value)
		fitparamslist.append(fitparams)

		return namelist, valuelist, fitparamslist

	#============
	def upwardLeftMonotonicFilter(self, data, windowsize=3):
		"""
		filters a 1D array such that it is alway increasing

		this could be more clever
		"""
		data = numpy.array(data)
		monotonicdata = data.copy()
		indices = range(data.shape[0]-windowsize)
		indices.reverse()
		monoval = data[indices[0]]
		startmonoindex = 0
		firstmono = None
		lastmono = None
		for i in indices:
			if data[i-windowsize:i].mean() < monoval:
				### fails monotonic condition
				if startmonoindex == 0:
					startmonoindex = i
					if lastmono is None:
						lastmono = i
					firstmono = i
				monotonicdata[i] = monoval
			else:
				if startmonoindex != 0:
					#slope = (data[i] - monoval)/(i - startmonoindex)
					#for j in range(startmonoindex-1, i):
					#	 monotonicdata[j] = slope*(j-startmonoindex) + monoval
					startmonoindex = 0
				monoval = data[i]
		print "monotonic", firstmono, lastmono
		monotonicdata[:firstmono] = monotonicdata[firstmono]
		monotonicdata[lastmono:] = monotonicdata[lastmono]
		return monotonicdata

	#============
	def downwardRightMonotonicFilter(self, data, windowsize=3):
		"""
		filters a 1D array such that it is alway increasing

		this could be more clever
		"""
		datadiff1  = scipy.ndimage.gaussian_filter(numpy.diff(data), windowsize)
		datadiff2  = scipy.ndimage.gaussian_filter(numpy.diff(datadiff1), windowsize**3)
		monotonicdata = data.copy()
		monoval = data[0]
		startmonoindex = 0
		firstmono = None
		lastmono = None
		for i in range(data.shape[0]-windowsize):
			if data[i:i+windowsize].mean() > monoval:
				### fails monotonic condition
				if startmonoindex == 0:
					startmonoindex = i
					if firstmono is None and datadiff1[i] < datadiff1.std() and datadiff2[i] > 0:
						firstmono = i
					lastmono = i
				monotonicdata[i] = monoval
			else:
				if startmonoindex != 0:
					#slope = (data[i] - monoval)/(i - startmonoindex)
					#for j in range(startmonoindex-1, i):
					#	 monotonicdata[j] = slope*(j-startmonoindex) + monoval
					startmonoindex = 0
				monoval = data[i]
		print "monotonic", firstmono, lastmono
		monotonicdata[:firstmono] = monotonicdata[firstmono]
		monotonicdata[lastmono:] = monotonicdata[lastmono]
		return monotonicdata

	#============
	def modelCTFNoise(self, xdata, ctfdata, contraint="below"):
		"""
		Master control function to fit the CTF noise function

		xdata - should be in inverse Angstroms
		"""
		t0 = time.time()
		### need to reduce precision of the xdata
		### otherwise it takes too long, with no better of a fit
		xdata = xdata.astype(numpy.float32)

		if self.debug is True:
			apDisplay.printColor("CTF limits %.1f A -->> %.1fA"
				%(1./xdata.min(), 1./xdata.max()), "cyan")

		if contraint == "above":
			if self.debug is True:
				print "constrained above function"
			contraintFunction = self.modelConstFunAbove
			#filterctfdata = scipy.ndimage.maximum_filter(ctfdata, size=2)
			#for i in range(1):
			#	filterctfdata = (filterctfdata + scipy.ndimage.maximum_filter(filterctfdata, size=2))/2.0
			#firstmax = filterctfdata[0:250].max()
			#filterctfdata = numpy.where(filterctfdata>firstmax, firstmax, filterctfdata)
			#filterctfdata = self.upwardLeftMonotonicFilter(ctfdata)
			filterctfdata = ctfdata
		else:
			if self.debug is True:
				print "constrained below function"
			contraintFunction = self.modelConstFunBelow
			#filterctfdata = scipy.ndimage.minimum_filter(ctfdata, size=2)
			#for i in range(1):
			#	filterctfdata = (filterctfdata + scipy.ndimage.minimum_filter(filterctfdata, size=2))/2.0
			#firstmin = filterctfdata[0:250].min()
			#filterctfdata = numpy.where(filterctfdata>firstmin, firstmin, filterctfdata)
			#filterctfdata = self.downwardRightMonotonicFilter(ctfdata)
			filterctfdata = ctfdata

		### run the initial minimizations
		namelist, valuelist, fitparamslist = self.getAllInitialParameters(xdata, 
			filterctfdata, contraintFunction)

		### figure out which initial fit was best
		if self.debug is True:
			namestr = "|"
			valstr = "|"
			conststr = "|"
			for i in range(len(valuelist)):
				constrainval = contraintFunction(fitparamslist[i], xdata, filterctfdata)
				namestr += apDisplay.rightPadString("%s"%(namelist[i][:15]), 15)+"|"
				valstr += apDisplay.leftPadString("%.4f"%(valuelist[i]), 15)+"|"
				conststr += apDisplay.leftPadString("%.4e"%(constrainval), 15)+"|"
			print namestr
			print valstr
			print conststr

		### lowest is best
		minvalindex = numpy.argmin(valuelist)
		constrainval = contraintFunction(fitparamslist[minvalindex], xdata, filterctfdata)
		valuelist = numpy.array(valuelist)
		if contraint == "below":
			minconval = -1e-2
		elif contraint == "above":
			minconval = -1e-2
		else:
			minconval = -1e-3
		while constrainval < minconval and valuelist.min() < 1e6:
			if constrainval < 0.1 and self.debug is True:
				apDisplay.printMsg("Constraint violation: %.3e < %.3e"%(constrainval, minconval))
			valuelist[minvalindex] *= 1e10
			minvalindex = numpy.argmin(valuelist)
			constrainval = contraintFunction(fitparamslist[minvalindex], xdata, filterctfdata)
		if self.debug is True:
			apDisplay.printColor( namelist[minvalindex]+" is best" , "cyan")
		midfitparams = fitparamslist[minvalindex]

		if self.debug is True:
			print ( "middle parameters (%.5e, %.5e, %.5e, %.5e, %.5e)"
				%(midfitparams[0], midfitparams[1], midfitparams[2], midfitparams[3], midfitparams[4]))
		midvalue = self.modelFitFun(midfitparams, xdata, ctfdata)
		if self.debug is True:
			print "middle function value %.10f"%(midvalue)
			constrainval = contraintFunction(midfitparams, xdata, ctfdata)
			print "constrained value %.10e"%(constrainval)

		### run the full minimization
		rhobeg = (numpy.where(numpy.abs(midfitparams)<1e-20, 1e20, numpy.abs(midfitparams))).min()/1e7
		if self.debug: print "RHO begin", rhobeg
		fitparams = scipy.optimize.fmin_cobyla( self.modelFitFun, midfitparams, 
			args=(xdata, ctfdata), cons=[contraintFunction,],
			consargs=(xdata, ctfdata), rhobeg=rhobeg, rhoend=rhobeg/1e4, iprint=0, maxfun=1e8)
		if self.debug is True: 
			print ( "final parameters (%.4e, %.4e, %.4e, %.4e, %.4e)"
				%(fitparams[0], fitparams[1], fitparams[2], fitparams[3], fitparams[4]))
		finalvalue = self.modelFitFun(fitparams, xdata, ctfdata)
		if self.debug is True: 
			print "final function value %.10f"%(finalvalue)
		#writeDatFile("finalvalue.dat", fitparams, xdata, ctfdata)
		
		if finalvalue <= midvalue:
			if self.debug is True:
				apDisplay.printColor("Final value is better", "green")
			bestfitparams = fitparams
		else:
			if self.debug is True:
				apDisplay.printColor("Final value is worse", "red")
			bestfitparams = midfitparams

		z = numpy.polyfit(xdata, filterctfdata, 3)
		polyfitparams = [z[3], 0.0, z[2], z[1], z[0]]

		if self.debug is True:
			xdatasq = xdata**2
			xdatasq = numpy.arange(0, len(xdata), 1)

			from matplotlib import pyplot
			pyplot.plot(xdatasq, ctfdata, 'r-', )
			pyplot.plot(xdatasq, filterctfdata, 'b-', )
			midfitdata = self.noiseModel(midfitparams, xdata)
			pyplot.plot(xdatasq, midfitdata, 'm:', )
			polyfitdata = self.noiseModel(polyfitparams, xdata)
			pyplot.plot(xdatasq, polyfitdata, 'y-', )
			finalfitdata = self.noiseModel(fitparams, xdata)
			pyplot.plot(xdatasq, finalfitdata, 'k-', )
			pyplot.show()
			pyplot.clf()

			"""
			datadiff1  = scipy.ndimage.median_filter(numpy.diff(ctfdata), 3)
			datadiff2  = scipy.ndimage.median_filter(numpy.diff(datadiff1), 27)
			pyplot.plot(xdatasq[:500], (datadiff2/datadiff2.std())[:500], 'y-', )
			pyplot.plot(xdatasq[:500], (ctfdata - ctfdata.mean())[:500], 'r-', )
			pyplot.plot(xdatasq[:500], (datadiff1/datadiff1.std())[:500], 'c-', )
			pyplot.show()
			pyplot.clf()
			"""

		if self.debug is True:
			apDisplay.printColor("Noise Model Complete in %s"
				%(apDisplay.timeString(time.time()-t0)), "cyan")

		return bestfitparams

#================================================
#================================================
#================================================
def peakExtender(raddata, rotdata, extrema, extrematype="below"):
	"""
	raddata - x data in inverse Angstroms
	rotdata - powerspectra data, almost normalized to 0 and 1
	extrema - numpy array of peak or valley locations in inverse Angstroms
	extrematype - type of extrema, must be either below or above

	this program looks at the CTF data using the "known" location of the extrema
	extracts their extreme values 
	and does a linear interpolation between the extreme points
	"""
	t0 = time.time()
	apDisplay.printMsg("starting peak extension")
	extremeindices = numpy.searchsorted(raddata, extrema)

	raddatasq = raddata**2

	xdata = []
	ydata = []
	minx = extremeindices[0]
	for i in range(extremeindices.shape[0]-1):
		if extremeindices[i] > raddata.shape[0]-2:
			break
		if extremeindices[i+1] > raddata.shape[0]-1:
			extremeindices[i+1] = raddata.shape[0]-1
		eindex = extremeindices[i]
		if i == 0:
			preveindex = int(eindex/2)
		else:
			preveindex = extremeindices[i-1]
		nexteindex = extremeindices[i+1]
		eindex1 = int(round(eindex - abs(preveindex-eindex)/2.0))
		eindex2 = int(round(eindex + abs(nexteindex-eindex)/2.0))

		values = rotdata[eindex1:eindex2]
		if extrematype is "below":
			value = values.min()
		elif extrematype is "above":
			value = values.max()

		maxx = eindex
		xdata.append(raddatasq[eindex])
		ydata.append(value)

	if len(xdata) < 2:
		#not enough indices
		if extrematype is "below":
			return numpy.zeros(raddata.shape)
		elif extrematype is "above":		
			return numpy.ones(raddata.shape)

	func = scipy.interpolate.interp1d(xdata, ydata, kind='linear')
	extremedata = func(raddatasq[minx:maxx])
	if extrematype is "below":
		if minx < 3:
			startvalue = 0.0
		else:
			startvalue = rotdata[int(minx*0.5):minx].min()
		endvalue = rotdata[maxx:].min()
	elif extrematype is "above":
		if minx < 3:
			startvalue = 1.0
		else:
			startvalue = rotdata[int(minx*0.5):minx].max()
		endvalue = rotdata[maxx:].max()

	#print startvalue, endvalue

	startdata = numpy.ones((minx)) * startvalue
	enddata = numpy.ones((raddata.shape[0]-maxx)) * endvalue

	extremedata = numpy.hstack( (startdata, extremedata, enddata) )

	apDisplay.printColor("Peak Extension Complete in %s"
		%(apDisplay.timeString(time.time()-t0)), "cyan")

	return extremedata

