#!/usr/bin/env python
#
import os
import time
import sys
import random
import math
import shutil
#appion
import apDisplay
import apFile
import apParam
import apEMAN
import apTemplate
import apStack
from pyami import spider

def breakupStackIntoSingleFiles(stackfile, partdir="partfiles"):
	"""
	takes the stack file and creates single spider files ready for processing
	"""
	apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")

	starttime = time.time()
	filesperdir = 4096
	numpart = apFile.numImagesInStack(stackfile)
	apParam.createDirectory(partdir)
	if numpart > filesperdir:
		numdir = createSubFolders(partdir, numpart, filesperdir)
		filesperdir = int(math.ceil(numpart/float(numdir)))
		apDisplay.printMsg("Splitting "+str(numpart)+" particles into "+str(numdir)+" folders with "
			+str(filesperdir)+" particles per folder")
		subdir = 1
	else:
		subdir = "."

	if not os.path.isfile(stackfile):
		apDisplay.printError("stackfile does not exist: "+stackfile)

	### make particle files
	partlistdocfile = "partlist.doc"
	f = open(partlistdocfile, "w")
	i = 0

	curdir = os.path.join(partdir,str(subdir))
	stackimages = apStack.readImagic(stackfile)

	t0 = time.time()
	while i < numpart:
		### messaging
		if (i+1) % filesperdir == 0:
			subdir += 1
			curdir = os.path.join(partdir,str(subdir))
			esttime = (time.time()-t0)/float(i+1)*float(numpart-i)
			apDisplay.printMsg("new directory: '"+curdir+"' at particle "+str(i)+" of "+str(numpart)
				+", "+apDisplay.timeString(esttime)+" remain")

		### Scott's imagic reader and Neil's spidersingle writer, 38 sec for 9000 particles
		partfile = os.path.join(partdir,str(subdir),"part%06d.spi"%(i))
		partimg = stackimages['images'][i]
		spider.write(partimg, partfile)
		f.write(os.path.abspath(partfile)+" 1\n")

		i += 1
	f.close()

	apDisplay.printColor("finished breaking stack in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return partlistdocfile


def createSubFolders(partdir, numpart, filesperdir):
	i = 0
	dirnum = 0
	while i < numpart:
		dirnum += 1
		apParam.createDirectory(os.path.join(partdir, str(dirnum)))
		i += filesperdir
	return dirnum







