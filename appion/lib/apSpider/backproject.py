
## python
import time
import os
import subprocess
import cPickle
import sys
import math
from string import lowercase
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
from pyami import peakfinder, spider

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
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	if dataext in eulerdocfile:
		eulerdocfile = eulerdocfile[:-4]
	if dataext in volfile:
		volfile = volfile[:-4]
	apFile.removeFile(volfile+".spi")
	t0 = time.time()
	rundir = "volumes"
	apParam.createDirectory(rundir)

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
	return

#===============================
def projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext=".spi"):
	"""
	project 3D volumes using given Euler angles
	"""
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
	return

#===============================
def crossCorrelateAndShift(infile, reffile, alignfile, ccdocfile, partnum, dataext=".spi"):
	if dataext in infile:
		infile = infile[:-4]
	if dataext in reffile:
		reffile = reffile[:-4]
	if dataext in ccdocfile:
		ccdocfile = ccdocfile[:-4]
	tempccfile = "tempccfile"
	### cross correlate images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("CC N", 
		infile+("@%05d"%(partnum)), #picture
		reffile+("@%05d"%(partnum)), #reference
		tempccfile, #output file
	)
	mySpider.close()

	### find pixel peak from cc map
	ccmap = spider.read(tempccfile+dataext)
	pf = peakfinder.PeakFinder()
	peak = pf.subpixelPeak(newimage=ccmap, npix=5)
	apFile.removeFile(tempccfile+dataext)
	f = open(ccdocfile, "a")
	spiline = operations.spiderOutputLine3(partnum, peak[0], peak[1], 0.0)
	f.write(spiline)
	f.close()

	### shift the images images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("SH", 
		infile+("@%05d"%(partnum)), #old stack
		alignfile+("@%05d"%(partnum)), #new stack
		"%.3f,%.3f"%(peak[0],peak[1]), #output file
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
	projstackfile = "projstack%03d.spi"%(iternum)
	projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext)

	partnum = 1
	ccdocfile = "ccdocfile%03d.spi"%(iternum)
	alignstackfile = "alignstack%03d.spi"%(iternum)
	while partnum <= numpart:
		partnum+=1
		crossCorrelateAndShift(origstackfile, projstackfile, alignstackfile, ccdocfile, partnum)

	return alignstackfile



