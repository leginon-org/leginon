#!/usr/bin/env python

import sys
import math
import numpy
import scipy.optimize
from appionlib import apDisplay

### remove warning about polyfit
import warnings
warnings.simplefilter('ignore', numpy.RankWarning)

debug = True

#============
def writeDatFile(filename, fitparams, xdata, ctfdata):
	fitx = noiseModel(fitparams, xdata)
	f = open(filename, "w")
	for i in range(len(xdata)):
		f.write("%.3f\t%.8f\t%.8f\n"%(xdata[i], fitx[i], ctfdata[i]))
	f.close()

#============
def noiseModelBFactor(fitparams, xdata=None):
	"""
	Function to model ctf noise using: A + B*x^2
	"""
	fitx = ( fitparams[0] 
		+ fitparams[1]*numpy.power(xdata, 2.0)
	)
	return fitx

#============
def noiseModelOnlyLinear(fitparams, xdata=None):
	"""
	Function to model ctf noise using: A + B*x
	"""
	fitx = ( fitparams[0] 
		+ fitparams[1]*xdata 
	)
	return fitx

#============
def noiseModelOnlySqrt(fitparams, xdata=None):
	"""
	Function to model ctf noise using: A + B*sqrt(x)
	"""
	fitx = ( fitparams[0] 
		+ fitparams[1]*numpy.sqrt(xdata) 
	)
	return fitx

#============
def noiseModelNoSquare(fitparams, xdata=None):
	"""
	Function to model ctf noise using: A + B*sqrt(x) + C*x
	"""
	fitx = ( fitparams[0] 
		+ fitparams[1]*numpy.sqrt(xdata) 
		+ fitparams[2]*xdata 
	)
	return fitx

#============
def noiseModel(fitparams, xdata=None):
	"""
	Function to model ctf noise
	"""
	fitx = ( fitparams[0] 
		+ fitparams[1]*numpy.sqrt(xdata) 
		+ fitparams[2]*xdata 
		+ fitparams[3]*numpy.power(xdata, 2.0)
	)
	return fitx

#============
def modelConstFunAbove(fitparams, xdata=None, ctfdata=None, model=noiseModel):
	"""
	constraint: f(x) - fit(x) < 0
	        OR: fit(x) - f(x) > 0  -- forces to fit above function
	"""
	fitx = model(fitparams, xdata)
	meanval = (fitx - ctfdata).mean()
	minval = (fitx - ctfdata).min()
	### allow the function to go below the maximum by 5% of the mean
	fitval = minval + (meanval - minval)*0.05
	return fitval

#============
def modelConstFunBelow(fitparams, xdata=None, ctfdata=None, model=noiseModel):
	"""
	constraint: f(x) - fit(x) > 0  -- forces to fit below function
	"""
	fitx = model(fitparams, xdata)
	meanval = (ctfdata - fitx).mean()
	minval = (ctfdata - fitx).min()
	### allow the function to go above the minimum by 15% of the mean
	fitval = minval + (meanval - minval)*0.05
	return fitval

#============
def modelFitFun(fitparams, xdata=None, ctfdata=None, model=noiseModel):
	"""
	calculate sum of square difference to fit function
	"""
	fitx = model(fitparams, xdata)
	#fitness = ((ctfdata - fitx)**2).mean()
	#fitness = numpy.abs(ctfdata - fitx).mean()
	#fitness = ((ctfdata - fitx)**2).sum()
	#fitness = numpy.abs(ctfdata - fitx).sum()

	### BEST MODEL
	fitfunc = numpy.abs(ctfdata - fitx)
	mean = fitfunc.mean()
	fitfunc = numpy.where(fitfunc > mean, mean, fitfunc)
	fitness = fitfunc.sum()
	### END BEST MODEL

	#fitness = 1.0 - scipy.stats.pearsonr(fitx, ctfdata)[0]
	return fitness

#============
def fitNoSquare(xdata, ctfdata, contraintFunction, maxfun=1e4):
	"""
	model the noise using: A + B*sqrt(x) + C*x
	"""
	z = numpy.polyfit(numpy.sqrt(xdata), ctfdata, 2)
	if debug is True:
		print "poly fit: sqrt(x),y = ", z
	initfitparams = [z[2], z[1], z[0]]

	nosqfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata, noiseModelNoSquare), cons=[contraintFunction,],
		consargs=(xdata, ctfdata, noiseModelNoSquare), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### add square term back in
	fitparams = [nosqfitparams[0], nosqfitparams[1], nosqfitparams[2], 0.0]
	nosqvalue = modelFitFun(fitparams, xdata, ctfdata)
	#writeDatFile("nosqvalue.dat", fitparams, xdata, ctfdata)
	return fitparams, nosqvalue

#============
def fitLinear(xdata, ctfdata, contraintFunction, maxfun=1e4):
	"""
	model the noise using: A + B*x
	"""
	z = numpy.polyfit(xdata, ctfdata, 1)
	if debug is True:
		print "poly fit: x,y = ", z
	initfitparams = [z[1], z[0]]

	linearfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata, noiseModelOnlyLinear), cons=[contraintFunction,],
		consargs=(xdata, ctfdata, noiseModelOnlyLinear), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### add square root and square terms back in
	fitparams = [linearfitparams[0], 0.0, linearfitparams[1], 0.0]
	linearvalue = modelFitFun(fitparams, xdata, ctfdata)
	#writeDatFile("linearvalue.dat", fitparams, xdata, ctfdata)
	return fitparams, linearvalue

#============
def fitOnlySqrt(xdata, ctfdata, contraintFunction, maxfun=1e4):
	"""
	model the noise using: A + B*sqrt(x)
	"""
	z = numpy.polyfit(numpy.sqrt(xdata), ctfdata, 1)
	if debug is True:
		print "poly fit: sqrt(x),y = ", z
	initfitparams = [z[1], z[0]]

	sqrtfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata, noiseModelOnlySqrt), cons=[contraintFunction,],
		consargs=(xdata, ctfdata, noiseModelOnlySqrt), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### add linear and square terms back in
	fitparams = [sqrtfitparams[0], sqrtfitparams[1], 0.0, 0.0]
	sqrtvalue = modelFitFun(fitparams, xdata, ctfdata)
	#writeDatFile("sqrtvalue.dat", fitparams, xdata, ctfdata)
	return fitparams, sqrtvalue

#============
def fitBFactor(xdata, ctfdata, contraintFunction, maxfun=1e4):
	"""
	model the noise using: A + B*sqrt(x)
	"""
	z = numpy.polyfit(numpy.power(xdata, 2), ctfdata, 1)
	if debug is True:
		print "poly fit: x**2,y = ", z
	initfitparams = [z[1], z[0]]

	bfactfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata, noiseModelBFactor), cons=[contraintFunction,],
		consargs=(xdata, ctfdata, noiseModelBFactor), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### add linear and square terms back in
	fitparams = [bfactfitparams[0], 0.0, 0.0, bfactfitparams[1]]
	bfactvalue = modelFitFun(fitparams, xdata, ctfdata)
	#writeDatFile("bfactvalue.dat", fitparams, xdata, ctfdata)
	return fitparams, bfactvalue

#============
def fitFullFunction(xdata, ctfdata, contraintFunction, maxfun=1e4):
	"""
	model the noise using: A + B*sqrt(x)
	"""
	z = numpy.polyfit(numpy.sqrt(xdata), ctfdata, 4)
	if debug is True:
		print "poly fit: sqrt(x),y = ", z
	initfitparams = [z[4], z[3]+z[2], z[1], z[0]]

	fullfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata), cons=[contraintFunction,],
		consargs=(xdata, ctfdata), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### check the fit
	fullvalue = modelFitFun(fullfitparams, xdata, ctfdata)
	#writeDatFile("fullvalue.dat", fullfitparams, xdata, ctfdata)
	return fullfitparams, fullvalue


#============
def fitTwoSlopeFullFunction(xdata, ctfdata, contraintFunction, maxfun=1e4, cutoffper=2/5.):
	"""
	model the noise using: A + B*sqrt(x)
	"""
	## divide points into fifths
	numpoints = xdata.shape[0]
	cutoff = int(math.floor(cutoffper*numpoints))
	if debug: print "cutoff percent %.3f (%d points)"%(cutoffper, cutoff)
	### fit first two fifths
	firstlinearfitparams, firstlinearvalue = fitLinear(
		xdata[:cutoff], ctfdata[:cutoff], contraintFunction, maxfun)
	### fit last two fifths
	lastlinearfitparams, lastlinearvalue = fitLinear(
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

	initfitparams = numpy.array([xconst, 0, xlinear, xsquare])
	fullvalue = modelFitFun(initfitparams, xdata, ctfdata)
	return initfitparams, fullvalue


	fullfitparams = scipy.optimize.fmin_cobyla( modelFitFun, initfitparams, 
		args=(xdata, ctfdata), cons=[contraintFunction,],
		consargs=(xdata, ctfdata), rhoend=1e-10, iprint=0, maxfun=maxfun)
	### check the fit
	fullvalue = modelFitFun(fullfitparams, xdata, ctfdata)
	#writeDatFile("fullvalue.dat", fullfitparams, xdata, ctfdata)

	return fullfitparams, fullvalue

#============
def modelCTFNoise(xdata, ctfdata, contraint="below"):
	"""
	Master control function to fit the CTF noise function
	"""

	if contraint == "above":
		if debug is True:
			print "constrained above function"
		contraintFunction = modelConstFunAbove
	else:
		if debug is True:
			print "constrained below function"
		contraintFunction = modelConstFunBelow

	### run the initial minimizations
	
	nosqfitparams, nosqvalue = fitNoSquare(xdata, ctfdata, contraintFunction)
	linearfitparams, linearvalue = fitLinear(xdata, ctfdata, contraintFunction)
	sqrtfitparams, sqrtvalue = fitOnlySqrt(xdata, ctfdata, contraintFunction)
	bfactfitparams, bfactvalue = fitBFactor(xdata, ctfdata, contraintFunction)
	twoslopefitparams, twoslopevalue = fitTwoSlopeFullFunction(xdata, ctfdata, contraintFunction)
	fullfitparams, fullvalue = fitTwoSlopeFullFunction(xdata, ctfdata, contraintFunction, cutoffper=2/3.)
	#fullfitparams, fullvalue = fitFullFunction(xdata, ctfdata, contraintFunction)

	### figure out which initial fit was best
	if debug is True:
		print sqrtvalue, linearvalue, nosqvalue, bfactvalue, twoslopevalue, fullvalue
	### lowest is best
	if sqrtvalue < min(linearvalue, nosqvalue, bfactvalue, fullvalue, twoslopevalue):
		if debug is True: apDisplay.printColor( "Sqrt Only is best" , "blue")
		midfitparams = sqrtfitparams
	elif linearvalue < min(nosqvalue, bfactvalue, fullvalue, twoslopevalue):
		if debug is True: apDisplay.printColor( "Linear is best" , "blue")
		midfitparams = linearfitparams
	elif nosqvalue < min(bfactvalue, fullvalue, twoslopevalue):
		if debug is True: apDisplay.printColor( "No Square is best" , "blue")
		midfitparams = nosqfitparams
	elif bfactvalue < min(fullvalue, twoslopevalue):
		if debug is True: apDisplay.printColor( "B-Factor is best" , "blue")
		midfitparams = bfactfitparams
	elif twoslopevalue < fullvalue:
		if debug is True: apDisplay.printColor( "Two Slopes is best" , "blue")
		midfitparams = twoslopefitparams
	else:
		if debug is True: apDisplay.printColor( "Full is best" , "blue")
		midfitparams = fullfitparams

	if debug is True:
		print ( "middle parameters (%.3e, %.3e, %.3e, %.3e)"
			%(midfitparams[0], midfitparams[1], midfitparams[2], midfitparams[3]))
	midvalue = modelFitFun(midfitparams, xdata, ctfdata)
	if debug is True: print "middle function value %.10f"%(midvalue)

	### run the full minimization
	rhobeg = (numpy.where(numpy.abs(midfitparams)<1e-20, 1e20, numpy.abs(midfitparams))).min()/1e7
	print "RHO begin", rhobeg
	fitparams = scipy.optimize.fmin_cobyla( modelFitFun, midfitparams, 
		args=(xdata, ctfdata), cons=[contraintFunction,],
		consargs=(xdata, ctfdata), rhobeg=rhobeg, rhoend=rhobeg/1e4, iprint=2, maxfun=1e8)
	if debug is True: 
		print ( "final parameters (%.4e, %.4e, %.4e, %.4e)"
			%(fitparams[0], fitparams[1], fitparams[2], fitparams[3]))
	finalvalue = modelFitFun(fitparams, xdata, ctfdata)
	if debug is True: 
		print "final function value %.10f"%(finalvalue)
	#writeDatFile("finalvalue.dat", fitparams, xdata, ctfdata)
	if debug is True:
		if finalvalue < midvalue:
			apDisplay.printColor("Final value is better", "green")
		elif finalvalue > midvalue:
			apDisplay.printColor("Final value is worse", "red")

	return fitparams










