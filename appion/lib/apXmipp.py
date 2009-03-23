#!/usr/bin/env python
#
import os
import time
import math
import subprocess
#appion
import apDisplay
import apFile
import apParam
import apImagicFile
from pyami import spider
from apSpider import operations

#======================
#======================
def convertStackToXmippData(instack, outdata, maskpixrad, boxsize, numpart=None):
	"""
	From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Img2Data

	This program applies a mask to a set of images. 
	This set is given by a selfile. 
	After applying the mask the result is storaged as a vector in the following format:
		The first line indicates the dimension of the vectors and the number of vectors.
		The rest of the lines are the feature vectors. 
		Each line is a vector and each column is a vectors' component (pixels values inside the mask). 
	"""
	apDisplay.printMsg("Convert stack file to Xmipp data file")
	maskfile = "circlemask.spi"
	operations.createMask(maskfile, maskpixrad, boxsize)
	partlistdocfile = breakupStackIntoSingleFiles(instack, numpart=numpart)
	convertcmd = "xmipp_convert_img2data -i %s -mask %s -o %s"%(partlistdocfile, maskfile, outdata)
	proc = subprocess.Popen(convertcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
	proc.wait()
	outfilesize = apFile.fileSize(outdata)
	partfilesize = apFile.fileSize(partlistdocfile)
	if outfilesize < 2*partfilesize:
		apDisplay.printError("Outdata conversion did not work, data file smaller than docfile, %s < %s"
			%(apDisplay.bytes(outfilesize), apDisplay.bytes(partfilesize)))
	apFile.removeFilePattern("partfiles/*")

	return outdata

#======================
#======================
def convertXmippDataToStack(indata, outstack, maskpixrad):
	"""
	From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Img2Data

	This program applies a mask to a set of images. 
	This set is given by a selfile. 
	After applying the mask the result is storaged as a vector in the following format:
		The first line indicates the dimension of the vectors and the number of vectors.
		The rest of the lines are the feature vectors. 
		Each line is a vector and each column is a vectors' component (pixels values inside the mask). 
	"""
	convertcmd = "xmipp_convert_data2img "

#======================
#======================
def breakupStackIntoSingleFiles(stackfile, partdir="partfiles", numpart=None):
	"""
	takes the stack file and creates single spider files ready for processing
	"""
	apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")

	starttime = time.time()
	filesperdir = 4096
	if numpart is None:
		numpart = apFile.numImagesInStack(stackfile)
	apParam.createDirectory(partdir)
	if numpart > filesperdir:
		numdir = createSubFolders(partdir, numpart, filesperdir)
		filesperdir = int(math.ceil(numpart/float(numdir)))
		apDisplay.printMsg("Splitting "+str(numpart)+" particles into "+str(numdir)+" folders with "
			+str(filesperdir)+" particles per folder")
		last = filesperdir
		subdir = 1
	else:
		apParam.createDirectory(os.path.join(partdir, "1"))
		last = numpart
		subdir = 1

	if not os.path.isfile(stackfile):
		apDisplay.printError("stackfile does not exist: "+stackfile)

	### make particle files
	partlistdocfile = "partlist.doc"
	f = open(partlistdocfile, "w")
	i = 0
	first = 1
	i = 0
	t0 = time.time()
	while i < numpart:
		### read images
		stackimages = apImagicFile.readImagic(stackfile, first=first, last=last, msg=False)
		esttime = (time.time()-t0)/float(i+1)*float(numpart-i)
		apDisplay.printMsg("dirnum %d at partnum %d to %d of %d, %s remain"
			%(subdir, first, last, numpart, apDisplay.timeString(esttime)))

		### write images
		for partimg in stackimages['images']:
			partfile = os.path.join(partdir, str(subdir), "part%06d.spi"%(i))
			spider.write(partimg, partfile)
			f.write(os.path.abspath(partfile)+" 1\n")
			i += 1

		### setup for next subdir
		first = last+1
		last += filesperdir
		if last > numpart:
			last = numpart
		subdir += 1
	f.close()

	apDisplay.printColor("finished breaking stack in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return partlistdocfile

#======================
#======================
def createSubFolders(partdir, numpart, filesperdir):
	i = 0
	dirnum = 0
	while i < numpart:
		dirnum += 1
		apParam.createDirectory(os.path.join(partdir, str(dirnum)))
		i += filesperdir
	return dirnum







