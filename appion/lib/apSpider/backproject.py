
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
	nproc = apParam.getNumProcessors()
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
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
def backprojectRP(stackfile, eulerdocfile, volfile, pixrad, classnum, lambDa, numpart=None, selfile=None, dataext=".spi"):
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
	if selfile is not None:
		selfile = spyder.fileFilter(selfile)
	volfile = spyder.fileFilter(volfile)
	counter = spyder.fileFilter("numiter")
	if not os.path.isfile(stackfile+dataext):
		apDisplay.printError("stack file not found: "+stackfile+dataext)
	if not os.path.isfile(eulerdocfile+dataext):
		apDisplay.printError("euler doc file not found: "+eulerdocfile+dataext)
	apFile.removeFile(volfile+dataext)

	if (numpart is not None):
		selection = "1-"+str(numpart)
	elif (selfile is not None):
		selection = selfile
	else:
		apDisplay.printError("Partilce selection is invalid for BP RP. Please make sure either numpart or selfile is specified in the function backprojectRP!")
	nproc = apParam.getNumProcessors()
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
	mySpider.toSpider("BP RP x11", 
		stackfile+"@*****", #stack file
		selection, #selection file or particle range 
		str(pixrad), #particle radius
		eulerdocfile, #angle doc file
		"*", #has symmetry?, does not work
		volfile, #filename for volume
 		"%.1e,%.1f" % (lambDa, 0.0), #lambda, correction
 		"%d,%d" % (50,1), #iteration limit, mode
 		"%d,%d" % (0,0), #minimum, maximum
 		"%.5f" % ((1/(1+6*lambDa))*0.999), #smoothing constant = (1/(1+6*lambda))*0.999
	)
	mySpider.toSpider("SD 1,x11", str(classnum)+"/"+str(counter)) 
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
	nproc = apParam.getNumProcessors()
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
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
	nproc = apParam.getNumProcessors()
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
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
def crossCorrelateAndShift(infile, reffile, alignfile, ccdocfile, numpart, dataext=".spi"):
	### rewriten to do the whole thing in memory in SPIDER, it should be faster
	starttime = time.time()
	infile = spyder.fileFilter(infile)
	reffile = spyder.fileFilter(reffile)
	alignfile = spyder.fileFilter(alignfile)
	partimg = "_4"
	ccmap = "_5"
	windccmap = "_6"

	boxsize = apFile.getBoxSize(infile+dataext)

	if not os.path.isfile(infile+dataext):
		apDisplay.printError("input stack file not found: "+infile+dataext)
	if not os.path.isfile(reffile+dataext):
		apDisplay.printError("reference stack file not found: "+reffile+dataext)
	nproc = apParam.getNumProcessors()
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)

	### Allocate empty stack
	mySpider.toSpiderQuiet(
		"MS I", #command
		"_2@", #name
		"%d,%d,%d"%(boxsize), #boxsize
		str(numpart+1), #num part to create in memory
		str(numpart+1), #max particle number
	)

	partnum = 0
	while partnum < numpart:
		partnum+=1

		mySpider.toSpiderQuiet("CP", 
			infile+("@%05d"%(partnum)), #picture
			partimg,
		)

		### cross correlate images; reversed order to avoid -1*shift

		mySpider.toSpiderQuiet("CC N", 
			reffile+("@%05d"%(partnum)), #reference
			partimg, #picture
			ccmap, #output file
		)

		### cannot shift more the 1/4 size of the image
		mySpider.toSpiderQuiet("FI x52", partimg, "12" )
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
			partimg, #old stack
			("_2@%05d"%(partnum)), #new stack
			"x13,x14", #shift value file
		)
	### finish up
	#save stack to file
	mySpider.toSpiderQuiet(
		"CP", "_2@",
		alignfile+"@",	
	)
	#delete stack
	mySpider.toSpiderQuiet(
		"DE", "_2",
	)
	mySpider.close()

	apDisplay.printColor("finished shifting particles in "+apDisplay.timeString(time.time()-starttime), "cyan")

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
	starttime = time.time()
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
	crossCorrelateAndShift(origstackfile, projstackfile, alignstackfile, ccdocfile, numpart)

	if not os.path.isfile(alignstackfile):
		apDisplay.printError("aligned stack file not found: "+alignstackfile)
	apDisplay.printColor("finished correlations in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return alignstackfile

###########################################
#														#
#	OTR functions									#
#														#
###########################################
#===============================
def otrParticleShift(volfile, origstackfile, eulerdocfile, iternum, numpart, pixrad, timestamp, dataext=".spi", classnum=None):
	"""
	inputs:
		volume
		stack, in spider format
		eulerdocfile
	outputs:
		volume
	"""
	### create corresponding projections
	if classnum is not None:
		projstackfile = str(classnum)+"/"+"projstack-%03d.spi"%(iternum)
	else:
		projstackfile = "projstack-%03d.spi"%(iternum)
	projectVolume(volfile, eulerdocfile, projstackfile, numpart, pixrad, dataext)

	### clean up files
	if classnum is not None:
		ccdocfile = str(classnum)+"/"+"ccdocfile-%03d.spi"%(iternum)
	else:
		ccdocfile = "ccdocfile-%03d.spi"%(iternum)
	apFile.removeFile(ccdocfile)
	
	if classnum is not None:
		alignstackfile = str(classnum)+"/"+"alignstack-%03d.spi"%(iternum)
	else:
		alignstackfile = "alignstack-%03d.spi"%(iternum)
	apFile.removeFile(alignstackfile)

	### align particles to projection
	starttime = time.time()
	apDisplay.printMsg("Shifting particles")
	crossCorrelateAndShift(origstackfile, projstackfile, alignstackfile, ccdocfile, numpart)

	if not os.path.isfile(alignstackfile):
		apDisplay.printError("aligned stack file not found: "+alignstackfile)
	apDisplay.printColor("finished correlations in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return alignstackfile

#===============================
def alignAPSH(volfile, origstackfile, eulerdocfile, classnum, boxsize, numpart, pixrad, timestamp, iternum, dataext=".spi"):
	
	apshAngularFile = str(classnum)+"/"+"apshAngularFile-%03d.spi"%(iternum)
	if os.path.isfile(apshAngularFile):
		os.remove(apshAngularFile)
		apDisplay.printColor("File exist! Removing file "+apshAngularFile, "cyan")
	apshAngularFile = spyder.fileFilter(apshAngularFile)
	
	apshListFile = str(classnum)+"/"+"apshListFile-%03d.spi"%(iternum)
	if os.path.isfile(apshListFile):
		os.remove(apshListFile)
		apDisplay.printColor("File exist! Removing file "+apshListFile, "cyan")
	apshListFile = spyder.fileFilter(apshListFile)
	
	apshOutFile = str(classnum)+"/"+"apshOut-%03d.spi"%(iternum)
	if os.path.isfile(apshOutFile):
		os.remove(apshOutFile)
		apDisplay.printColor("File exist! Removing file "+apshOutFile, "cyan")
	apshOut = spyder.fileFilter(apshOutFile)
	
	apshProjStack = str(classnum)+"/"+"apshProjStack-%03d.spi"%(iternum)
	if os.path.isfile(apshProjStack):
		os.remove(apshProjStack)
		apDisplay.printColor("File exist! Removing file "+apshProjStack, "cyan")
	apshProjStack = spyder.fileFilter(apshProjStack)
	
	origstackfile = spyder.fileFilter(origstackfile)
	volfile = spyder.fileFilter(volfile)
	origeulerdocfile = spyder.fileFilter(eulerdocfile)
	
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	mySpider.toSpider("VO EA,x53",
		"10", #angular increment
		"0,90.0", #Range of Theta
		"0,359.9", #Range of Phi
		apshAngularFile, #Angular file name
	)
	mySpider.toSpider("DOC CREATE",
		apshListFile, #List file name
		"1",
		"1-x53"
	)
	#mySpider.toSpider("MS",
	#	"_9@", #reference projections
	#	str(boxsize),str(boxsize),"1", #boxsize
	#	"x53",
	#)
	mySpider.toSpider("PJ 3Q", 
		volfile, #input vol file
		str(pixrad), #pixel radius
		apshListFile, #number of particles		
		apshAngularFile, #Euler DOC file
		apshProjStack+"@*****", #output projections
	)
	mySpider.toSpider("AP SH",
		apshProjStack+"@*****", #reference projections
		"1-x53", #reference numbers
		"6,2", #translational search range, step size
		"1,%d"%(boxsize/3), #first and last ring
		apshAngularFile,
		origstackfile+"@*****",
		"1-%d"%(numpart),
		origeulerdocfile,
		"20", #"(0.0)", # no restrictions for alignment
		"1", # mirror check?
		apshOut, # output 
	)
	
	mySpider.close()
	return apshOutFile

#===============================
def centerVolume(volfile, outvolfile, dataext=".spi"):
	volfile = spyder.fileFilter(volfile)
	outvolfile = spyder.fileFilter(outvolfile)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("CG PH x11,x12,x13,x21,x22,x23", 
		volfile, #volume
	)
	mySpider.toSpider("SH F", 
		volfile, #volume
		outvolfile, #output volume
		"-x21,-x22,-x23", #shifts in x y z
	)
	mySpider.close()
	return
	
#===============================
def calcFSC(volfile1, volfile2, fscout, dataext=".spi"):
	volfile1 = spyder.fileFilter(volfile1)
	volfile2 = spyder.fileFilter(volfile2)
	fscout = spyder.fileFilter(fscout)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("RF 3", 
		volfile1, #volume 1
		volfile2, #volume 2
		"0.5", # ring width for RF 3
		"0.5,1.5", # scale factor - lower
		#"1.5", # scale factor - upper
		"C", # use 'C' for missing cone and 'W' for missing wedge
		"90", # maximum tilt angle in data for OTR
		"3", # factor for noise comparison ("sigma")
		fscout, # fsc curve output
	)
	mySpider.close()
	return

#===============================
def rotshiftParticle(origstackfile, partnum, rotation, Xshift, Yshift, iternum, timestamp, classnum=None, dataext=".spi"):

	origstack = spyder.fileFilter(origstackfile)
	
	if classnum is not None:
		apshstackfile = str(classnum)+"/"+"apshStack-%03d.spi"%(iternum)
	else:
		apshstackfile = "apshStack-%03d.spi"%(iternum)
	
	apshstack = spyder.fileFilter(apshstackfile)
	
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	mySpider.toSpiderQuiet("RT SQ",
		origstack+"@"+str(partnum), #stack and particle number
		apshstack+"@"+str(partnum), #output stack and particle
		"("+str(rotation)+")", #rotation
		"("+str(Xshift)+","+str(Yshift)+")", #shift parameters
	)
	mySpider.close()
		
	return apshstackfile

#=============================== NOT WORKING CORRECTLY
def rotshiftStack(origstackfile, rotShiftFile, timestamp, iternum, classnum=None, dataext=".spi"):

	origstackfile = spyder.fileFilter(origstackfile)
	
	if classnum is not None:
		apshstackfile = str(classnum)+"/"+"apshstack%s.spi"%(timestamp)
	else:
		apshstackfile = "apshstack%s.spi"%(timestamp)
	
	apshstackfile = spyder.fileFilter(apshstackfile)
		
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	mySpider.toSpider("RT SQ",
		origstackfile+"@*****", #stack and particle number
		apshstackfile+"@*****", #output stack and particle
		"("+str(rotation)+")", #rotation
		"("+str(Xshift)+","+str(Yshift)+")", #shift parameters
	)
	mySpider.close()
	return

###########################################
#														#
#	Spider filtering functions					#
#														#
###########################################
		
#===============================
def butterworthLP(volfile, pixelsize, dataext=".spi"):
	"""
	inputs:
		volume
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	volfile = spyder.fileFilter(volfile)
	if not os.path.isfile(volfile+dataext):
		apDisplay.printError("volume file not found: "+volfile+dataext)
		
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("FQ", 
		volfile, #filename for volume
		"_1",
#		volfile+"_filtered", #filename for output volume
		"(7)",
		"(%.5f,%.5f)" % (pixelsize/25,pixelsize/15), #pass-band and stop-band
	)
	mySpider.close()
	apDisplay.printColor("finished filtering the volume "+apDisplay.timeString(time.time()-starttime), "cyan")
	return
	
#===============================
def butterworthFscLP(volfile, fscout, dataext=".spi"):
	"""
	inputs:
		volume
		fsc output file
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	volfile = spyder.fileFilter(volfile)
	if not os.path.isfile(volfile+dataext):
		apDisplay.printError("volume file not found: "+volfile+dataext)
	
	if not os.path.isfile(fscout):
		apDisplay.printError("fsc output file not found: "+fscout+dataext)
		
	fscfile = open(fscout, "r")
	prevValue = None
	for line in fscfile.readlines():
		value = line.split() 
		try:
			int(value[0])
		except:
			#apDisplay.printMsg(line)
			continue
		
		if float(value[4]) < 0.5:
			if prevValue is None:
				passband = float(value[2])
				stopband = float(value[2])+0.1
			else:
				passband = prevValue
				stopband = prevValue + 0.1
			break
		prevValue = float(value[2])
		
	fscfile.close()

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("FQ", 
		volfile, #filename for volume
		volfile+"_filtered", #filename for output volume
		"(7)",
		"(%.5f,%.5f)" % (passband, stopband), #pass-band and stop-band
	)
	mySpider.close()
	apDisplay.printColor("finished filtering the volume "+apDisplay.timeString(time.time()-starttime), "cyan")
	return

#===============================
def normalizeVol(volfile, dataext=".spi"):
	"""
	inputs:
		volume
	outputs:
		volume
	"""
	### setup
	starttime = time.time()
	volfile = spyder.fileFilter(volfile)
	if not os.path.isfile(volfile+dataext):
		apDisplay.printError("volume file not found: "+volfile+dataext)
		
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	### read out the statistics of the volume
	mySpider.toSpider("FS x11,x12", 
		volfile, #filename for volume
	)
	mySpider.toSpider("IF(x12.LT.0.0)x12=-x12")
	### set all values to positive
	mySpider.toSpider("AR",
		volfile, #filename for volume
		"_1",
		"(P1+x12)",
	)
	### save file
	mySpider.toSpider("CP",
		"_1",
		volfile, #filename for volume
	)
	
	mySpider.close()
	apDisplay.printColor("finished normalizing the volume to set all values to be positive"+apDisplay.timeString(time.time()-starttime), "cyan")
	return	
	 
	
	

