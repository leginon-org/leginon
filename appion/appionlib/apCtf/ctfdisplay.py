#!/usr/bin/env python

import sys
import math
import numpy
import time
import random
from pyami import imagefun
from pyami import ellipse
from appionlib.apCtf import ctfdb
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import lowess
from appionlib.apImage import imagefile
from appionlib.apImage import imagefilter

from matplotlib import pyplot
from matplotlib import mlab

from appionlib.apCtf import ctfnoise
from appionlib.apCtf import ctftools
from appionlib.apCtf import genctf
from PIL import Image
from PIL import ImageDraw
from scipy import ndimage
import scipy.stats

class CtfDisplay(object):
	#====================
	#====================
	def __init__(self):
		### global params that do NOT change with image
		self.ringwidth = 0.5
		self.debug = False
		return

	#====================
	#====================
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#====================
	#====================
	def Array1dintoArray2d(self, array1d, shape):
		array2d = imagefun.fromRadialFunction(self.funcrad, shape, rdata=rdata, zdata=array1d)
		return array2d

	#====================
	#====================
	def normalizeCtf(self, zdata2d):
		"""
		inner cut radius - radius for number of pixels to clip in the center of image
		"""
		numcols = (zdata2d.shape[0])/2 #column in radial sense
		radii2 = ctftools.getCtfExtrema(self.defocus2, self.trimapix*1e-10, self.cs, self.volts, 
			self.ampconst, cols=numcols, numzeros=3, zerotype="all")
		firstpeak = radii2[0]
		firstvalley = radii2[1]
		if self.debug is True:
			print "MIN/MAX peaks", 1./firstpeak, 1./firstvalley

		### get all peaks (not valleys)
		peaks = ctftools.getCtfExtrema(self.defocus2, self.trimapix*1e-10, self.cs, self.volts, 
			self.ampconst, cols=numcols, numzeros=12, zerotype="peak")
		peaksradii = self.freq*numpy.array(peaks, dtype=numpy.float32)
		peaksradiisq = peaksradii**2
		valleys = ctftools.getCtfExtrema(self.defocus2, self.trimapix*1e-10, self.cs, self.volts, 
			self.ampconst, cols=numcols, numzeros=12, zerotype="valley")
		valleysradii = self.freq*numpy.array(valleys, dtype=numpy.float32)
		valleysradiisq = valleysradii**2

		if self.debug is True:
			print "MIN/MAX peaks", 1./resradii.min(), 1./resradii.max()

		pixelrdata, zdata = ctftools.rotationalAverage(zdata2d, self.ringwidth, 
			firstpeak, full=False)
		pixelrdatae, zdatae = ctftools.ellipticalAverage(zdata2d, self.ratio, self.angle,
			self.ringwidth, firstpeak, full=False, filename=self.powerspecfile)
		if self.debug is True:
			print "  Pixel MIN/MAX:", pixelrdata.min(), pixelrdata.max()
			print "  Pixel # points", len(pixelrdata)
			print "  Pixel Size", self.trimapix
			print "  Orig Shape", zdata2d.shape[0]
			print "  Ring width", self.ringwidth
		rdata = pixelrdata*self.freq
		rdatae = pixelrdatae*self.freq
		if self.debug is True:
			print "Rotational CTF limits %.1f A -->> %.1fA"%(1./rdata.min(), 1./rdata.max())
			print "Elliptical CTF limits %.1f A -->> %.1fA"%(1./rdatae.min(), 1./rdatae.max())
		#print "Rdata", rdata.min(), rdata.max()

		if rdata.shape[0] < 2 or zdata.shape[0] < 2:
			apDisplay.printWarning("rotational Average failed")
			return zdata2d

		#smooth = 0.67
		#numiter = 10
		#lowessnoisedata = lowess.lowess(rdata**2, zdata, smooth, numiter)
		#lowessnoisedatae = lowess.lowess(rdatae**2, zdatae, smooth, numiter)

		print "Determine and subtract noise model..."
		CtfNoise = ctfnoise.CtfNoise()
		rdatasq = rdata**2
		rdatasqe = rdatae**2

		### fit function below log(CTF), i.e., noise model	
		firstvalleyindex = numpy.searchsorted(rdata, self.freq*firstvalley)
		firstvalleyindexe = numpy.searchsorted(rdatae, self.freq*firstvalley)
		noisefitparams = CtfNoise.modelCTFNoise(rdata[firstvalleyindex:], zdata[firstvalleyindex:], "below")
		noisefitparamse = CtfNoise.modelCTFNoise(rdatae[firstvalleyindexe:], zdatae[firstvalleyindexe:], "below")
		"""
		rdatavalley, zdatavalley = self.trimDataToExtrema(rdata, zdata, valleysradii)
		noisefitparams = CtfNoise.modelCTFNoise(rdatavalley, zdatavalley, "below")
		rdatavalleye, zdatavalleye = self.trimDataToExtrema(rdatae, zdatae, valleysradii)
		noisefitparamse = CtfNoise.modelCTFNoise(rdatavalleye, zdatavalleye, "below")
		"""
		noisedata = CtfNoise.noiseModel(noisefitparams, rdata)
		noisedatae = CtfNoise.noiseModel(noisefitparamse, rdatae)

		### subtract noise model
		normzdata = numpy.exp(zdata) - numpy.exp(noisedata)
		lognormzdata = numpy.log( numpy.abs( normzdata ) )
		normzdatae = numpy.exp(zdatae) - numpy.exp(noisedatae)
		lognormzdatae = numpy.log( numpy.abs( normzdatae ) )

		print "Determine and normalize envelope model..."
		### fit function above log(CTF), i.e., envelop model
		envelopfitparams = CtfNoise.modelCTFNoise(rdata, lognormzdata, "above")
		envelopdata = CtfNoise.noiseModel(envelopfitparams, rdata)
		envelopfitparamse = CtfNoise.modelCTFNoise(rdatae, lognormzdatae, "above")
		envelopdatae = CtfNoise.noiseModel(envelopfitparamse, rdatae)

		### divide by envelop (normalize)
		normnormzdata = normzdata / numpy.exp(envelopdata)
		normnormzdatae = normzdatae / numpy.exp(envelopdatae)

		print "Generating CTF fit..."
		### everything in mks units, because rdata is 1/A multiply be 1e10 to get 1/m
		ctfe = genctf.generateCTF1d(rdatae*1e10, focus=self.defavg, cs=self.cs,
			pixelsize=self.trimapix*1e-10, volts=self.volts, ampconst=self.ampconst)
		normctfe = ctfe**2 #(ctfe + 1.0)/2.0

		ctf = genctf.generateCTF1d(rdata*1e10, focus=self.defavg, cs=self.cs,
			pixelsize=self.trimapix*1e-10, volts=self.volts, ampconst=self.ampconst)
		normctf = ctf**2 #(ctf + 1.0)/2.0

		self.rotconf = scipy.stats.pearsonr(normnormzdata, normctf)[0]
		self.ellipconf = scipy.stats.pearsonr(normnormzdatae, normctfe)[0]
		print "Rotational confidence is %.3f"%(self.rotconf)
		print "Elliptical confidence is %.3f"%(self.ellipconf)

		#self.resolutionBins(rdatasq, normnormzdata, normctf)
		#self.resolutionBins(rdatasqe, normnormzdatae, normctfe)
		#sys.exit(1)

		#=====================
		# Make Figure
		#=====================
		titlefontsize=11
		axisfontsize=8

		pyplot.subplot(3,2,1) # 3 rows, 2 columns, plot 1
		pyplot.plot(rdatasq, zdata, 'b-', )
		#pyplot.plot(rdatasq, lowessnoisedata, 'g-', )
		pyplot.plot(rdatasq, noisedata, 'k-', )
		self.setPyPlotXLabels(rdatasq, valleysradiisq)
		pyplot.ylabel("Log(PSD)", fontsize=axisfontsize)
		pyplot.title("Noise Fit (Circular)", fontsize=titlefontsize)

		pyplot.subplot(3,2,2) # 3 rows, 2 columns, plot 2
		pyplot.plot(rdatasqe, zdatae, 'r-', )
		#pyplot.plot(rdatasqe, lowessnoisedatae, 'g-', )
		pyplot.plot(rdatasqe, noisedatae, 'k-', )
		self.setPyPlotXLabels(rdatasqe, valleysradiisq)
		pyplot.ylabel("Log(PSD)", fontsize=axisfontsize)
		pyplot.title("Noise Fit (Elliptical)", fontsize=titlefontsize)

		pyplot.subplot(3,2,3) # 3 rows, 2 columns, plot 3
		pyplot.plot(rdatasq, numpy.log(numpy.abs(normzdata)), 'b.', markersize=1,)
		pyplot.plot(rdatasq, envelopdata, 'k-', )
		self.setPyPlotXLabels(rdatasq, peaksradiisq)
		pyplot.ylabel("Log(PSD)-Log(Noise)", fontsize=axisfontsize)
		pyplot.title("Envelope Fit (Circular)", fontsize=titlefontsize)
		#pyplot.ylim(ymin=0)

		pyplot.subplot(3,2,4) # 3 rows, 2 columns, plot 4
		pyplot.plot(rdatasqe, numpy.log(numpy.abs(normzdatae)), 'r.', markersize=1,)
		pyplot.plot(rdatasqe, envelopdatae, 'k-', )
		#pyplot.ylim(ymin=0)
		self.setPyPlotXLabels(rdatasqe, peaksradiisq)
		pyplot.ylabel("Log(PSD)-Log(Noise)", fontsize=axisfontsize)
		pyplot.title("Envelope Fit (Elliptical)", fontsize=titlefontsize)

		pyplot.subplot(3,2,5) # 3 rows, 2 columns, plot 5
		#pyplot.plot(rdatasqe, normnormzdatae, 'r-', )
		pyplot.plot(rdatasq, normctf, '-', linewidth=1, color="#222222", alpha=0.5)
		pyplot.plot(rdatasq, normnormzdata, 'b.', markersize=1.5,)
		self.setPyPlotXLabels(rdatasq)
		pyplot.ylim(-0.1, 1.1)
		pyplot.yticks([0.0, 0.5, 1.0])
		pyplot.ylabel("Normalized PSD", fontsize=axisfontsize)
		pyplot.title("Normalized PowerSpec (Circular)", fontsize=titlefontsize)
		pyplot.grid(True, linestyle=':', )

		pyplot.subplot(3,2,6) # 3 rows, 2 columns, plot 6
		pyplot.plot(rdatasqe, normctfe, '-', linewidth=1, color="#222222", alpha=0.5)
		pyplot.plot(rdatasqe, normnormzdatae, 'r.', markersize=1.5,)
		self.setPyPlotXLabels(rdatasqe)
		pyplot.ylim(-0.1, 1.1)
		pyplot.yticks([0.0, 0.5, 1.0])
		pyplot.ylabel("Normalized PSD", fontsize=axisfontsize)
		pyplot.title("Normalized PowerSpec (Elliptical)", fontsize=titlefontsize)
		pyplot.grid(True, linestyle=':', )

		pyplot.subplots_adjust(wspace=0.22, hspace=0.55, 
			bottom=0.08, left=0.07, top=0.95, right=0.965, )
		self.plotsfile = apDisplay.short(self.imgname)+"-plots.png"
		print "Saving 1D graph to file", self.plotsfile
		pyplot.savefig(self.plotsfile, format="png", dpi=150)

		if self.debug is True:
			print "Showing results"
			#pyplot.show()
			plotspng = Image.open(self.plotsfile)
			plotspng.show()
		pyplot.clf()


		#=====================
		# End Figure
		#=====================

		#numpy.savez("xdata.npz", rdatasqe)
		#numpy.savez("ydata.npz", normnormzdatae)
		#print "saved files"
		#sys.exit(1)

		### 1D FINISHED, NOW PROCESS 2D IMAGE
		noise2d = imagefun.fromRadialFunction(self.funcrad, zdata2d.shape, 
			rdata=rdata/self.freq, zdata=noisedata)
		envelop2d = imagefun.fromRadialFunction(self.funcrad, zdata2d.shape, 
			rdata=rdata/self.freq, zdata=envelopdata)
		#imagefile.arrayToJpeg(fitdata, "fitdata.jpg")
		normal2d = numpy.exp(zdata2d) - numpy.exp(noise2d)
		#normnormal2d = normal2d / numpy.exp(envelop2d)
		envelop2d = numpy.exp(envelop2d)
		normnormal2d = numpy.where(normal2d > envelop2d, envelop2d, normal2d)
		mincut = normnormal2d.std()
		if self.debug is True:
			print "Minimum cut...", mincut
		cutnormal = numpy.where(normnormal2d < 0.0, 0.0, normnormal2d+mincut)
		return cutnormal

	#====================
	#====================
	def trimDataToExtrema(self, xdata, rawdata, extrema):
		trimxdata = []
		trimrawdata = []
		for i in range(len(extrema)):
			exvalue = extrema[i]
			index = numpy.searchsorted(xdata, exvalue)
			trimxdata.extend(xdata[index-10:index+10])
			trimrawdata.extend(rawdata[index-10:index+10])
			print len(trimxdata)
		return numpy.array(trimxdata), numpy.array(trimrawdata)

	#====================
	#====================
	def resolutionBins(self, xdatasq, rawdata, fitdata):
		"""
		break data into bins and calculate Pearson Correlation
		"""
		xmin = xdatasq.min()
		xmax = xdatasq.max()
		numbins = 10
		xstep = (xmax - xmin)/float(numbins)
		apDisplay.printColor("Resolution Bins", "purple")
		print " low  --  high  | #pts |  corr  | chi^2"
		indexmax = 0
		for i in range(numbins):
			binmin = xmin + i*xstep
			binmax = xmin + (i+1)*xstep
			indexmin = indexmax
			indexmax = numpy.searchsorted(xdatasq, binmax)
			binminlabel = apDisplay.leftPadString("%.1f"%(1/math.sqrt(binmin)), 4)
			binmaxlabel = apDisplay.leftPadString("%.1f"%(1/math.sqrt(binmax)), 4)
			numptslabel = apDisplay.leftPadString(str(indexmax-indexmin), 4)
			corr = scipy.stats.pearsonr(rawdata[indexmin:indexmax], fitdata[indexmin:indexmax])[0]
			corrlabel = apDisplay.leftPadString("%.3f"%(corr), 6)
			chisq = 0
			print (" %s -- %s A | %s | %s | %.3f"
				%(binminlabel, binmaxlabel, numptslabel, corrlabel, chisq))


	#====================
	#====================
	def setPyPlotXLabels(self, xdata, radiisq=None):
		"""
		assumes xdata is in units of 1/Angstroms
		"""
		minloc = xdata.min()
		maxloc = xdata.max()
		xstd = xdata.std()/2.
		pyplot.xlim(xmin=minloc, xmax=maxloc)
		#pyplot.xlim(xmax=maxloc)
		locs, labels = pyplot.xticks()

		### assumes that x values are 1/Angstroms^2, which give the best plot
		newlocs = []
		newlabels = []
		#print "maxloc=", maxloc
		for loc in locs:
			if loc < minloc + xstd/4:
				continue
			origres = 1.0/math.sqrt(loc)
			if origres > 50:
				trueres = round(origres/10.0)*10
			if origres > 25:
				trueres = round(origres/5.0)*5
			elif origres > 12:
				trueres = round(origres/2.0)*2
			elif origres > 7.5:
				trueres = round(origres)
			else:
				trueres = round(origres*2)/2.0

			trueloc = 1.0/trueres**2
			#print ("Loc=%.4f, Res=%.2f, TrueRes=%.1f, TrueLoc=%.4f"	
			#	%(loc, origres, trueres, trueloc))
			if trueloc > maxloc - xstd:
				continue
			if trueres < 10 and (trueres*2)%2 == 1:
				label = "1/%.1fA"%(trueres)
			else:
				label = "1/%dA"%(trueres)
			if not label in newlabels:
				newlabels.append(label)
				newlocs.append(trueloc)
		#add final value
		newlocs.append(minloc)
		label = "1/%dA"%(1.0/math.sqrt(minloc))
		newlabels.append(label)

		newlocs.append(maxloc)
		label = "1/%.1fA"%(1.0/math.sqrt(maxloc))
		newlabels.append(label)

		# set the labels
		pyplot.yticks(fontsize=8)
		pyplot.xticks(newlocs, newlabels, fontsize=8)

		pyplot.xlabel("Resolution (s^2)", fontsize=9)
		if radiisq is not None:
			for i, radsq in enumerate(radiisq):
				if radsq < minloc:
					continue
				elif radsq > maxloc:
					break
				elif i % 1 == 0:
					pyplot.axvline(x=radsq, linewidth=1, color="cyan", alpha=0.5)
				else:
					#pyplot.axvline(x=radsq, linewidth=1, color="yellow", alpha=0.5)
					pass

		return

	#====================
	#====================
	def drawPowerSpecImage(self, origpowerspec, maxsize=1500):
		if max(origpowerspec.shape) > maxsize:
			scale = maxsize/float(max(origpowerspec.shape))
			#scale = math.sqrt((random.random()+random.random()+random.random())/3.0)
			print "Scaling final powerspec image by %.3f"%(scale)
			powerspec = imagefilter.scaleImage(origpowerspec, scale)
		else:
			scale = 1.0
			powerspec = origpowerspec.copy()

		self.scaleapix = self.trimapix
		self.scalefreq = self.freq/scale
		if self.debug is True:
			print "orig pixel", self.apix
			print "bin pixel", self.binapix
			print "trim pixel", self.trimapix
			print "scale pixel", self.scaleapix

		numzeros = 10
		numcols = powerspec.shape[0]/2
		#numcols = self.origimageshape[0]/(2*self.prebin)*scale #**2
		#print "numcols=", numcols

		radii1 = ctftools.getCtfExtrema(self.defocus1, self.scaleapix*1e-10, 
			self.cs, self.volts, self.ampconst, cols=numcols, numzeros=numzeros)
		radii2 = ctftools.getCtfExtrema(self.defocus2, self.scaleapix*1e-10, 
			self.cs, self.volts, self.ampconst, cols=numcols, numzeros=numzeros)

		firstpeak = radii2[0]

		center = numpy.array(powerspec.shape, dtype=numpy.float)/2.0
		originalimage = imagefile.arrayToImage(powerspec)
		originalimage = originalimage.convert("RGB")
		pilimage = originalimage.copy()
		draw = ImageDraw.Draw(pilimage)

		## draw an axis line, if astig > 5%
		perdiff = 2*abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		if self.debug is True:
			print "Percent Difference %.1f"%(perdiff*100)
		if perdiff > 0.05:
			#print self.angle, radii2[0], center
			x = -1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=20)
		elif perdiff > 1e-6:
			#print self.angle, radii2[0], center
			x = -1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=2)

		foundzeros = min(len(radii1), len(radii2))
		color="#3d3dd2"
		for i in range(foundzeros):
			# because |def1| < |def2| ==> firstzero1 > firstzero2
			major = radii1[i]
			minor = radii2[i]
			if self.debug is True: 
				print "major=%.1f, minor=%.1f, angle=%.1f"%(major, minor, self.angle)
			if minor > powerspec.shape[0]/math.sqrt(3):
				continue
			width = int(math.ceil(2*math.sqrt(numzeros - i)))

			### determine number of points to use to draw ellipse, minimize distance btw points
			#isoceles triangle, b: radius ot CTF ring, a: distance btw points
			#a = 2 * b sin (theta/2)
			#a / 2b = sin(theta/2)
			#theta = 2 * asin (a/2b)
			#numpoints = 2 pi / theta
			## define a to be 5 pixels
			a = 15
			theta = 2.0 * math.asin (a/(2.0*major))
			skipfactor = 2
			numpoints = int(math.ceil(2.0*math.pi/theta/skipfactor))*skipfactor + 1
			#print "numpoints", numpoints


			### for some reason, we need to give a negative angle here
			points = ellipse.generate_ellipse(major, minor, 
				-math.radians(self.angle), center, numpoints, None, "step", True)
			x = points[:,0]
			y = points[:,1]

			## wrap around to end
			x = numpy.hstack((x, [x[0],]))
			y = numpy.hstack((y, [y[0],]))
			## convert image


			numsteps = int(math.floor((len(x)-2)/skipfactor))
			for j in range(numsteps):
				k = j*skipfactor
				xy = (x[k], y[k], x[k+1], y[k+1])
				draw.line(xy, fill=color, width=width)


		# 1/res = freq * pixrad => pixrad = 1/(res*freq)
		maxrad = (max(powerspec.shape)-1)/2.0 - 3
		maxres = 1.0/(self.scalefreq*maxrad)
		bestres = math.ceil(maxres)
		pixrad = 1.0/(self.scalefreq*bestres)
		if self.debug is True:
			print "bestres %d Angstroms (max: %.3f)"%(bestres, maxres)
			print "pixrad %d (max: %.3f)"%(pixrad, maxrad)
		if pixrad > maxrad:
			apDisplay.printError("Too big of outer radius to draw")
		outpixrad = math.ceil(pixrad)+1
		inpixrad = math.floor(pixrad)-1
		a = 15
		theta = 2.0 * math.asin (a/(2.0*outpixrad))
		numpoints = int(math.ceil(2.0*math.pi/theta))
		outpoints = ellipse.generate_ellipse(outpixrad, outpixrad, 
			0.0, center, numpoints, None, "step", True)
		outx = outpoints[:,0]
		outy = outpoints[:,1]
		inpoints = ellipse.generate_ellipse(inpixrad, inpixrad, 
			0.0, center, numpoints, None, "step", True)
		inx = inpoints[:,0]
		iny = inpoints[:,1]
		numsteps = len(inx)-1
		for k in range(numsteps):
			inxy = (inx[k], iny[k], inx[k+1], iny[k+1])
			draw.line(inxy, fill="black", width=2)
			outxy = (outx[k], outy[k], outx[k+1], outy[k+1])
			draw.line(outxy, fill="white", width=2)


		### add text
		fontpath = "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"
		from PIL import ImageFont
		if os.path.isfile(fontpath):
			fontsize = int(math.ceil( 48/2. * min(powerspec.shape)/float(maxsize))*2)
			font = ImageFont.truetype(fontpath, fontsize)
		else:
			font = ImageFont.load_default()
		angrad = maxrad/math.sqrt(2) + 10
		coord = (angrad+maxrad, angrad+maxrad)
		draw.text(coord, "%.1f A"%(bestres), font=font)

		## create an alpha blend effect
		originalimage = Image.blend(originalimage, pilimage, 0.95)
		print "Saving 2D powerspectra to file", self.powerspecfile
		#pilimage.save(self.powerspecfile, "JPEG", quality=85)
		originalimage.save(self.powerspecfile, "JPEG", quality=85)
		if self.debug is True:
			originalimage.show()
			time.sleep(3)
		return

	#====================
	#====================
	def convertDefociToConvention(self, ctfdata):
		initratio = ctfdata['defocus2']/ctfdata['defocus1']
		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f | ratio %.2f"%
			(ctfdata['defocus1'], ctfdata['defocus2'], ctfdata['angle_astigmatism'], 
			initratio), "cyan")

		# program specific corrections?
		self.angle = ctfdata['angle_astigmatism']
		#angle = round(self.angle/2.5,0)*2.5

		#by convention: abs(ctfdata['defocus1']) < abs(ctfdata['defocus2'])
		if abs(ctfdata['defocus1']) > abs(ctfdata['defocus2']):
			# incorrect, need to shift angle by 90 degrees
			apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
			self.defocus1 = ctfdata['defocus2']
			self.defocus2 = ctfdata['defocus1']
			self.angle += 90
		else:
			# correct, ratio > 1
			self.defocus1 = ctfdata['defocus1']
			self.defocus2 = ctfdata['defocus2']
		if self.defocus1 < 0 and self.defocus2 < 0:
			apDisplay.printWarning("Negative defocus values, taking absolute value")
			self.defocus1 = abs(self.defocus1)
			self.defocus2 = abs(self.defocus2)
		self.defavg = (self.defocus1 + self.defocus2)/2.0
		self.defdiff = self.defocus1 - self.defocus2
		self.ratio = self.defocus2/self.defocus1

		# get angle within range -90 < angle <= 90
		while self.angle > 90:
			self.angle -= 180
		while self.angle < -90:
			self.angle += 180

		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f | ratio %.2f"%
			(self.defocus1, self.defocus2, self.angle, self.ratio), "cyan")

		perdiff = abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		print ("Defocus Astig Percent Diff %.2f -- %.3e, %.3e"
				%(perdiff*100,self.defocus1,self.defocus2))

		return

	#====================
	#====================
	def CTFpowerspec(self, imgdata, ctfdata, outerbound=10e-10):
		"""
		Make a nice looking powerspectra with lines for location of Thon rings

		inputs:
			imgdata - sinedon AcquistionImage table row
			ctfdata - sinedon apCtfData table row
				amplitude constrast - ( a cos + sqrt(1-a^2) sin format)
				defocus1 > defocus2
				angle - in degrees, positive x-axis is zero
			outerbound = 5 #Angstrom resolution  (in meters)
				outside this radius is trimmed away
		"""
		### setup initial parameters for image
		#outerbound = outerbound * 2*math.sqrt(random.random())
		self.imgname = imgdata['filename']
		if self.debug is True:
			print apDisplay.short(self.imgname)
		self.powerspecfile = apDisplay.short(self.imgname)+"-powerspec.jpg"

		### get correct data
		self.convertDefociToConvention(ctfdata)

		if self.debug is True:
			for key in ctfdata.keys():
				if ctfdata[key] is not None and not isinstance(ctfdata[key], dict):
					print "  ", key, "--", ctfdata[key]

		### process power spectra
		self.apix = apDatabase.getPixelSize(imgdata)

		if self.debug is True:
			print "Pixelsize (A/pix)", self.apix

		self.prebin = ctftools.getPowerSpectraPreBin(outerbound*1e10, self.apix)
		print "Reading image..."
		image = imgdata['image']
		self.freq = 1./(self.apix * image.shape[0])
		self.origimageshape = image.shape
		print "Binning image by %d..."%(self.prebin)
		binimage = imagefun.bin2(image, self.prebin)
		self.binapix = self.prebin * self.apix
		self.binfreq = 1./(self.apix * binimage.shape[0] * self.prebin)
		self.binfreq2 = 1./(self.binapix * binimage.shape[0])
		print "Computing power spectra..."
		powerspec, self.trimapix = ctftools.powerSpectraToOuterResolution(binimage, 
			outerbound*1e10, self.binapix)
		self.trimfreq = 1./(self.trimapix * powerspec.shape[0])
		print "Median filter image..."
		powerspec = ndimage.median_filter(powerspec, 2)

		### get peaks of CTF
		self.cs = ctfdata['cs']*1e-3
		self.volts = imgdata['scope']['high tension']
		self.ampconst = ctfdata['amplitude_contrast']

		if self.debug is True:
			print "\torig pixel %.3f freq %.3e"%(self.apix, self.freq)
			print "\tbin  pixel %.3f freq %.3e"%(self.binapix, self.binfreq)
			print "\tbin  pixel %.3f freq %.3e"%(self.binapix, self.binfreq2)
			print "\ttrim pixel %.3f freq %.3e"%(self.trimapix, self.trimfreq)

		### more processing

		normpowerspec = self.normalizeCtf(powerspec)

		self.drawPowerSpecImage(normpowerspec)

		if self.debug is True:
			time.sleep(10)

		return self.powerspecfile, self.plotsfile, self.ellipconf

#====================
#====================
#====================
#====================
if __name__ == "__main__":
	import os
	import re
	import glob
	import random

	#=====================
	### CNV data
	#imagelist = glob.glob("/data01/leginon/10apr19a/rawdata/10apr19a_10apr19a_*en_1.mrc")
	### Pick-wei images with lots of rings
	#imagelist = glob.glob("/data01/leginon/09sep20a/rawdata/09*en.mrc")
	### Something else, ice data
	#imagelist = glob.glob("/data01/leginon/09feb20d/rawdata/09*en.mrc")
	### images of Hassan with 1.45/1.65 astig at various angles
	imagelist = glob.glob("/data01/leginon/12jun12a/rawdata/12jun12a_ctf_image_ang*.mrc")
	#=====================

	print "# of images", len(imagelist)
	#imagelist.sort()
	#imagelist.reverse()
	random.shuffle(imagelist)

	imageint = int(random.random()*len(imagelist))
	imagename = os.path.basename(imagelist[imageint])
	imagename = re.sub(".mrc", "", imagename)

	imgdata = apDatabase.getImageData(imagename)
	from appionlib import apProject
	projid = apProject.getProjectIdFromImageData(imgdata)
	print "Project ID: ", projid
	newdbname = apProject.getAppionDBFromProjectId(projid)
	import sinedon
	sinedon.setConfig('appiondata', db=newdbname)
	#from appionlib import appiondata
	#ctfq = appiondata.ApCtfData()
	#ctfq['image'] = imgdata
	#ctfdatas = ctfq.query(results=1)
	#ctfdata = ctfdatas[0]
	#ctfdata, bestconf = apCtf.getBestCtfValueForImage(imgdata, method="ace2")

	count = 0
	for imgfile in imagelist:
		count += 1
		imagename = os.path.basename(imgfile)
		imagename = re.sub(".mrc", "", imagename)
		imgdata = apDatabase.getImageData(imagename)
		print ""
		print "**********************************"
		print "IMAGE: ", apDisplay.short(imagename)
		print "**********************************"
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata)
		ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ctffind")
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ace2")
		if ctfdata is None:
			print "Skipping image, no CTF data"
			continue
		a = CtfDisplay()
		powerspecfile, plotsfile, conf = a.CTFpowerspec(imgdata, ctfdata)

		if count > 8:
			sys.exit(1)

#====================
#====================
#====================
def makeCtfImages(imgdata, ctfdata):
	a = CtfDisplay()
	powerspecfile, plotsfile, conf= a.CTFpowerspec(imgdata, ctfdata)
	return powerspecfile, plotsfile, conf


