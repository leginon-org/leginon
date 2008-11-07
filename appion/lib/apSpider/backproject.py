
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
def backprojectCG(stackfile, eulerdocfile, volfile, numpart, pixrad, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	stackfile = spyder.fileFilter(stackfile)
	eulerdocfile = spyder.fileFilter(eulerdocfile)
	volfile = spyder.fileFilter(volfile)
	if not os.path.isfile(stackfile+dataext):
		apDisplay.printError("stack file not found: "+stackfile+dataext)
	if not os.path.isfile(eulerdocfile+dataext):
		apDisplay.printError("euler doc file not found: "+eulerdocfile+dataext)
	apFile.removeFile(volfile+dataext)

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
def backproject3F(stackfile, eulerdocfile, volfile, numpart, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	stackfile = spyder.fileFilter(stackfile)
	eulerdocfile = spyder.fileFilter(eulerdocfile)
	volfile = spyder.fileFilter(volfile)
	if not os.path.isfile(stackfile+dataext):
		apDisplay.printError("stack file not found: "+stackfile+dataext)
	if not os.path.isfile(eulerdocfile+dataext):
		apDisplay.printError("euler doc file not found: "+eulerdocfile+dataext)
	apFile.removeFile(volfile+dataext)

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("BP 3F", 
		stackfile+"@*****", #stack file
		"1-%d"%(numpart), #number of particles
		eulerdocfile, #angle doc file
		"*", #input symmetry file, '*' for skip
		volfile, #filename for volume
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
	volfile = spyder.fileFilter(volfile)
	eulerdocfile = spyder.fileFilter(eulerdocfile)
	projstackfile = spyder.fileFilter(projstackfile)
	if not os.path.isfile(volfile+dataext):
		apDisplay.printError("volume file not found: "+volfile+dataext)
	if not os.path.isfile(eulerdocfile+dataext):
		apDisplay.printError("euler doc file not found: "+eulerdocfile+dataext)

	apFile.removeFile(projstackfile)
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
	### rewriten to do the whole thing in memory in SPIDER, it should be faster
	infile = spyder.fileFilter(infile)
	reffile = spyder.fileFilter(reffile)
	alignfile = spyder.fileFilter(alignfile)
	ccmap = "_5"
	windccmap = "_6"
	if not os.path.isfile(infile+dataext):
		apDisplay.printError("input stack file not found: "+infile+dataext)
	if not os.path.isfile(reffile+dataext):
		apDisplay.printError("reference stack file not found: "+reffile+dataext)


	### cross correlate images; reversed order to avoid -1*shift
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet("CC N", 
		reffile+("@%05d"%(partnum)), #reference
		infile+("@%05d"%(partnum)), #picture
		ccmap, #output file
	)

	### cannot shift more the 1/4 size of the image
	mySpider.toSpiderQuiet("FI x52", infile+("@%05d"%(partnum)), "12" )
	mySpider.toSpiderQuiet("x54=int(x52/2)") #window size
	mySpider.toSpiderQuiet("x55=int(x52/4)") #window topleft
	mySpider.toSpiderQuiet("WI", 
		ccmap, #input file
		windccmap, #output file
		"x54,x54", #window size
		"x55,x55", #window origin
	)

	### find the cross-correlation peak
	mySpider.toSpiderQuiet("x56=int(x52/4)+1") #center of window
	mySpider.toSpiderQuiet("PK M x11,x12,x13,x14", 
		windccmap, #input ccmap file
		"x56,x56", #origin coordinates
	)

	### save info to doc file
	mySpider.toSpiderQuiet("SD %d,x13,x14"%(partnum), 
		ccdocfile, #input ccmap file
	)

	### shift the images images
	mySpider.toSpiderQuiet("SH", 
		infile+("@%05d"%(partnum)), #old stack
		alignfile+("@%05d"%(partnum)), #new stack
		"x13,x14", #shift value file
	)
	mySpider.close()
	return

#===============================
def rctParticleShift(volfile, origstackfile, eulerdocfile, iternum, numpart, pixrad, timestamp, dataext=".spi"):
	"""
	inputs:
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### create corresponding projections
	projstackfile = "projstack%s-%03d.spi"%(timestamp, iternum)
	projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext)

	### clean up files
	ccdocfile = "ccdocfile%s-%03d.spi"%(timestamp, iternum)
	apFile.removeFile(ccdocfile)
	alignstackfile = "alignstack%s-%03d.spi"%(timestamp, iternum)
	apFile.removeFile(alignstackfile)

	### align particles to projection
	apDisplay.printMsg("Shifting particles")
	starttime = time.time()
	partnum = 0
	while partnum < numpart:
		partnum+=1
		if partnum%25 == 0:
			esttime = float(time.time()-starttime)/float(partnum)*float(numpart-partnum)
			print "partnum=", partnum, "--", apDisplay.timeString(esttime), "remain"
		crossCorrelateAndShift(origstackfile, projstackfile, alignstackfile, ccdocfile, partnum)

	if not os.path.isfile(alignstackfile):
		apDisplay.printError("aligned stack file not found: "+alignstackfile)
	apDisplay.printColor("finished correlations in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return alignstackfile



