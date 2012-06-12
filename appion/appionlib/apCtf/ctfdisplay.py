#!/usr/bin/env python

debug = True
import sys
import math
import numpy
import time
from pyami import imagefun
from pyami import ellipse
from appionlib.apCtf import ctfdb
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import lowess
from appionlib.apImage import imagefile

from matplotlib import pyplot
from matplotlib import mlab

from appionlib.apCtf import ctfnoise
from appionlib.apCtf import ctftools
from appionlib.apCtf import genctf
from PIL import Image
from PIL import ImageDraw
from scipy import ndimage

class CtfDisplay(object):
	#====================
	#====================
	def __init__(self):
		### global params that do NOT change with image
		self.ringwidth = 0.5
		return

	#====================
	#====================
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#====================
	#====================
	def normalizeCtf(self, zdata2d, innercutradius, angle, ratio):
		"""
		inner cut radius - radius for number of pixels to clip in the center of image
		"""

		print "Step0", zdata2d.shape, innercutradius
		rdata, zdata = ctftools.rotationalAverage(zdata2d, self.ringwidth, innercutradius, full=False)
		rdatae, zdatae = ctftools.ellipticalAverage(zdata2d, ratio, angle, self.ringwidth, 
			innercutradius, full=False, filename=self.powerspecfile)
		xfreq = 1.0/( (zdata2d.shape[0]-1)*2.0*self.pixelsize )
		rdata = rdata*xfreq
		rdatae = rdatae*xfreq
		print "Rdata", rdata.min(), rdata.max()
		print type(rdata), type(zdata)

		if rdata.shape[0] < 2 or zdata.shape[0] < 2:
			apDisplay.printWarning("rotational Average failed")
			return zdata2d

		smooth = 0.67
		numiter = 10

		#lowessnoisedata = lowess.lowess(rdata**2, zdata, smooth, numiter)
		#lowessnoisedatae = lowess.lowess(rdatae**2, zdatae, smooth, numiter)

		CtfNoise = ctfnoise.CtfNoise()

		noisefitparams = CtfNoise.modelCTFNoise(rdata, zdata, "below")
		noisedata = CtfNoise.noiseModel(noisefitparams, rdata)
		noisefitparamse = CtfNoise.modelCTFNoise(rdatae, zdatae, "below")
		noisedatae = CtfNoise.noiseModel(noisefitparamse, rdatae)

		rdatasq = rdata**2
		rdatasqe = rdatae**2
		rdatasqe /= rdatasq.min()
		rdatasq /= rdatasq.min()

		normzdata = numpy.exp(zdata) - numpy.exp(noisedata)
		lognormzdata = numpy.log( numpy.abs( normzdata ) )

		normzdatae = numpy.exp(zdatae) - numpy.exp(noisedatae)
		lognormzdatae = numpy.log( numpy.abs( normzdatae ) )

		envelopfitparams = CtfNoise.modelCTFNoise(rdata, lognormzdata, "above")
		envelopdata = CtfNoise.noiseModel(envelopfitparams, rdata)

		envelopfitparamse = CtfNoise.modelCTFNoise(rdatae, lognormzdatae, "above")
		envelopdatae = CtfNoise.noiseModel(envelopfitparamse, rdatae)

		normnormzdata = normzdata / numpy.exp(envelopdata)
		normnormzdatae = normzdatae / numpy.exp(envelopdatae)

		#=====================
		# Make Figure
		#=====================
		pyplot.subplot(3,2,1) # 3 rows, 2 columns, plot 1
		pyplot.plot(rdatasq, zdata, 'b-', )
		#pyplot.plot(rdatasq, lowessnoisedata, 'g-', )
		pyplot.plot(rdatasq, noisedata, 'k-', )

		pyplot.subplot(3,2,2) # 3 rows, 2 columns, plot 2
		pyplot.plot(rdatasqe, zdatae, 'r-', )
		#pyplot.plot(rdatasqe, lowessnoisedatae, 'g-', )
		pyplot.plot(rdatasqe, noisedatae, 'k-', )

		pyplot.subplot(3,2,3) # 3 rows, 2 columns, plot 3
		pyplot.plot(rdatasq, numpy.log(numpy.abs(normzdata)), 'b.', )
		pyplot.plot(rdatasq, envelopdata, 'k-', )
		pyplot.ylim(ymin=0)

		pyplot.subplot(3,2,4) # 3 rows, 2 columns, plot 4
		pyplot.plot(rdatasqe, numpy.log(numpy.abs(normzdatae)), 'r.', )
		pyplot.plot(rdatasqe, envelopdatae, 'k-', )
		pyplot.ylim(ymin=0)

		pyplot.subplot(3,2,5) # 3 rows, 2 columns, plot 5
		pyplot.plot(rdatasq, normnormzdata, 'b.', )
		pyplot.plot(rdatasqe, normnormzdatae, 'r-', )
		pyplot.ylim(-0.1, 1.1)

		pyplot.subplot(3,2,6) # 3 rows, 2 columns, plot 6
		pyplot.plot(rdatasqe, normnormzdatae, 'r.', )
		pyplot.ylim(-0.1, 1.1)

		pyplot.savefig("plots.png", format="png", dpi=200)
		pyplot.show()
		#sys.exit(1)
		#=====================
		# End Figure
		#=====================

		#numpy.savez("xdata.npz", rdatasqe)
		#numpy.savez("ydata.npz", normnormzdatae)
		#print "saved files"
		#sys.exit(1)

		fitdata = imagefun.fromRadialFunction(self.funcrad, zdata2d.shape, rdata=rdata, zdata=noisedata)
		#imagefile.arrayToJpeg(fitdata, "fitdata.jpg")
		normalized = zdata2d-fitdata

		mincut = normalized.std()
		print "Minimum cut...", mincut
		return numpy.where(normalized < -1*mincut, 0.0, normalized+mincut)

	#====================
	#====================
	def convertDefociToConvention(ctfdata):
		self.defocus1 = ctfdata['defocus1'] #round(ctfdata['defocus1']*1e6,0)*1e-6
		self.defocus2 = ctfdata['defocus2'] #round(ctfdata['defocus2']*1e6,0)*1e-6

		if ctfdata['acerun']['ctftilt_params'] is not None:
			self.angle = ctfdata['angle_astigmatism']
		elif ctfdata['acerun']['ace2_params'] is not None:
			self.angle = ctfdata['angle_astigmatism']
		else:
			self.angle = ctfdata['angle_astigmatism']
		#angle = round(self.angle/2.5,0)*2.5
		self.ratio = self.defocus1/self.defocus2
		if self.ratio < 1:
			self.ratio = 1.0/self.ratio
			self.angle += 90
		elif self.ratio == 1:
			self.angle = 0
		while self.angle > 90:
			self.angle -= 180
		while self.angle < -90:
			self.angle += 180
		return

	#====================
	#====================
	def CTFpowerspec(self, imgdata, ctfdata, outerbound=6.5e-10):
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
		self.imgname = imgdata['filename']
		self.powerspecfile = apDisplay.short(imagename)+"-powerspec.jpg"

		### get correct data

		#print "%.3e / %.3e"%(ctfdata['defocus1'], ctfdata['defocus2'])

		#apDisplay.printColor("ratio=%.3f\tangle=%.2f\tfile=%s"%(ratio, angle, self.powerspecfile), "magenta")

		if debug is True:
			for key in ctfdata.keys():
				if ctfdata[key] is not None and not isinstance(ctfdata[key], dict):
					print "  ", key, "--", ctfdata[key]
		return

		### process power spectra
		self.pixelsize = apDatabase.getPixelSize(imgdata)
		print "Pixelsize", self.pixelsize

		prebin = 1 #ctftools.getPowerSpectraPreBin(outerbound*1e10, pixelsize)
		print "Reading image..."
		image = imgdata['image']
		print "Binning image by %d..."%(prebin)
		binimage = imagefun.bin2(image, prebin)
		binpixelsize = prebin * self.pixelsize
		print "Computing power spectra..."
		powerspec = ctftools.powerSpectraToOuterResolution(binimage, outerbound*1e10, binpixelsize)
		print "Median filter image..."
		powerspec = ndimage.median_filter(powerspec, 5)

		### get peaks of CTF
		cs = ctfdata['cs']*1e-3
		volts = imgdata['scope']['high tension']
		ampconst = ctfdata['amplitude_contrast']
		numzeros = 12
		numcols = image.shape[0]/(2*prebin)
		radii1 = ctftools.getCTFpeaks(self.defocus2, binpixelsize*1e-10, cs, volts, 
			ampconst, cols=numcols, numzeros=numzeros)
		radii2 = ctftools.getCTFpeaks(self.defocus1, binpixelsize*1e-10, cs, volts, 
			ampconst, cols=numcols, numzeros=numzeros)

		print radii1[0]," > ",radii2[0], radii1[0] > radii2[0]
		innercutradius = min(radii2[0],radii1[0])

		### more processing
		print powerspec.shape
		print "Subtract noise model..."

		normpowerspec = self.normalizeCtf(powerspec, innercutradius, 
			angle=self.angle, ratio=self.ratio)
		#normpowerspec = self.subtractNoiseModel(powerspec, innercutradius, angle=angle, ratio=ratio)

		powerspec = normpowerspec

		center = numpy.array(powerspec.shape, dtype=numpy.float)/2.0
		color="#3d3df2"
		originalimage = imagefile.arrayToImage(powerspec)
		originalimage = originalimage.convert("RGB")
		pilimage = originalimage.copy()
		draw = ImageDraw.Draw(pilimage)

		## draw an axis line:
		perdiff = abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		print ("Defocus Astig Percent Diff %.2f -- %.3e, %.3e"
			%(perdiff*100,self.defocus1,self.defocus2))
		if perdiff > 0.01:
			print self.angle, radii2[0], center
			x = radii2[0]*math.sin(math.radians(self.angle))
			y = radii2[0]*math.cos(math.radians(self.angle))
			print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			print xy
			time.sleep(3)
			draw.line(xy, fill="#f23d3d", width=30)

		foundzeros = min(len(radii1), len(radii2))
		for i in range(foundzeros):
			major = radii1[i]
			minor = radii2[i]
			minradius = min(major,minor)
			maxradius = max(major,minor)
			if minradius > powerspec.shape[0]/math.sqrt(3):
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
			theta = 2.0 * math.asin (a/(2.0*maxradius))
			numpoints = int(2.0*math.pi/theta)
			#print "numpoints", numpoints

			points = ellipse.generate_ellipse(major, minor, math.radians(self.angle), center, numpoints, None, "step", True)
			x = points[:,0]
			y = points[:,1]

			## wrap around to end
			x = numpy.hstack((x, [x[0],]))
			y = numpy.hstack((y, [y[0],]))
			## convert image

			for j in range((len(x)-1)/2):
				k = j*2
				xy = (x[k], y[k], x[k+1], y[k+1])
				draw.line(xy, fill=color, width=width)

		## create an alpha blend effect
		originalimage = Image.blend(originalimage, pilimage, 0.7)
		print "savefile", self.powerspecfile
		originalimage.save(self.powerspecfile, "JPEG", quality=85)

		return							

#====================
#====================
#====================
#====================
if __name__ == "__main__":
	import os
	import re
	import glob
	import random
	### Pick-wei images with lots of rings
	#imagelist = glob.glob("/data01/leginon/09sep20a/rawdata/09*en.mrc")
	#imagelist = glob.glob("/data01/leginon/09feb20d/rawdata/09*en.mrc")
	#imagelist = glob.glob("/data01/leginon/12may21q50/rawdata/12may21q50_*.ctf_1.mrc")
	#imagelist = glob.glob("/data01/leginon/12may21q50/rawdata/12may21q50_2_1_0_0.ctf_1.mrc")
	### images of Hassan with 1.45/1.55 astig at various angles
	imagelist = glob.glob("/data01/leginon/12jun12a/rawdata/12jun12a_ctf_image_ang*.mrc")
	print "# of images", len(imagelist)
	imagelist.sort()
	#random.shuffle(imagelist)
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
		#print "\n\n\n\n"
		imagename = os.path.basename(imgfile)
		#print imagename
		imagename = re.sub(".mrc", "", imagename)
		imgdata = apDatabase.getImageData(imagename)
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata)
		ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ctffind")
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ace2")
		a = CtfDisplay()
		a.CTFpowerspec(imgdata, ctfdata)

		if count > 8:
			sys.exit(1)













