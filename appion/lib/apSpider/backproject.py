
## python
import time
import os
import subprocess
import cPickle
import sys
import math
import numpy
import random
## PIL
#import Image
## spider
import spyder
## appion
import apImage
import apEMAN
import apParam
import apDisplay
import apFile
from apSpider import operations
from pyami import peakfinder, spider, correlator

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
image stack file: 
	*****stack.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def reconstructRct(stackfile, eulerdocfile, volfile, numpart, pixrad, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	if dataext in eulerdocfile:
		eulerdocfile = eulerdocfile[:-4]
	if dataext in volfile:
		volfile = volfile[:-4]
	apFile.removeFile(volfile+".spi")

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("BP CG", 
		stackfile+"@*****", #stack file
		"1-%d"%(numpart), #number of particles
		str(pixrad), #particle radius
		eulerdocfile, #angle doc file
		"N", #has symmetry?, does not work
		volfile, #filename for volume
 		"%.1e,%.1f" % (1.0e-5, 0.0), #error, chi^2 limits
 		"%d,%d" % (25,1), #iterations, 1st derivative mode
 		"2000", #lambda - higher=less sensitive to noise
	)
	mySpider.close()
	apDisplay.printColor("finished backprojection in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return

#===============================
def projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext=".spi"):
	"""
	project 3D volumes using given Euler angles
	"""
	starttime = time.time()
	if dataext in volfile:
		volfile = volfile[:-4]
	if dataext in eulerdocfile:
		eulerdocfile = eulerdocfile[:-4]
	if dataext in projstackfile:
		projstackfile = projstackfile[:-4]

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("PJ 3Q", 
		volfile, #input vol file
		str(pixrad), #pixel radius
		"1-%d"%(numpart), #number of particles		
		eulerdocfile, #Euler DOC file
		projstackfile+"@*****", #output projections
	)
	mySpider.close()
	apDisplay.printColor("finished projections in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return

#===============================
def crossCorrelateAndShift(infile, reffile, alignfile, ccdocfile, partnum, dataext=".spi"):
	if dataext in infile:
		infile = infile[:-4]
	if dataext in reffile:
		reffile = reffile[:-4]
	if dataext in alignfile:
		alignfile = alignfile[:-4]
	tempccfile = "tempccfile"
	### cross correlate images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet("CC N", 
		infile+("@%05d"%(partnum)), #picture
		reffile+("@%05d"%(partnum)), #reference
		tempccfile, #output file
	)
	mySpider.close()

	### find pixel peak from cc map
	if not os.path.isfile(tempccfile+dataext):
		mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
		mySpider.toSpiderQuiet("CP", 
			infile+("@%05d"%(partnum)), #old stack
			alignfile+("@%05d"%(partnum)), #new stack
		)
		mySpider.close()
		return
	ccmap = spider.read(tempccfile+dataext)
	peak = peakfinder.findSubpixelPeak(ccmap, lpf=1.5)
	subpixpeak = numpy.asarray(peak['subpixel peak'], dtype=numpy.float32)
	shift = subpixpeak - numpy.asarray(ccmap.shape, dtype=numpy.float32)/2.0
	### cannot shift more the 1/4 size of the image
	if abs(shift[0]) > ccmap.shape[0]/4.0:
		shift[0] = ccmap.shape[0]/4.0*shift[0]/abs(shift[0])
	if abs(shift[1]) > ccmap.shape[1]/4.0:
		shift[1] = ccmap.shape[1]/4.0*shift[1]/abs(shift[1])
	apFile.removeFile(tempccfile+dataext)
	f = open(ccdocfile, "a")
	spiline = operations.spiderOutputLine3(partnum, shift[0], shift[1], 0.0)
	f.write(spiline)
	f.close()

	### shift the images images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet("SH", 
		infile+("@%05d"%(partnum)), #old stack
		alignfile+("@%05d"%(partnum)), #new stack
		"%.3f,%.3f"%(shift[0], shift[1]), #output file
	)
	mySpider.close()
	return

#===============================
def rctParticleShift(volfile, origstackfile, eulerdocfile, iternum, numpart, pixrad, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### create corresponding projections
	projstackfile = "projstack%03d.spi"%(iternum)
	projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext)

	### align particles to projection
	ccdocfile = "ccdocfile%03d.spi"%(iternum)
	apFile.removeFile(ccdocfile)
	alignstackfile = "alignstack%03d.spi"%(iternum)
	apFile.removeFile(alignstackfile)
	apDisplay.printMsg("Shifting particles")
	starttime = time.time()
	partnum = 0
	while partnum <= numpart:
		partnum+=1
		if partnum%50 == 0:
			print "partnum=", partnum
		crossCorrelateAndShift(origstackfile, projstackfile, alignstackfile, ccdocfile, partnum)
	apDisplay.printColor("finished correlations in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return alignstackfile



