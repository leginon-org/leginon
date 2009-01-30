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
		apDisplay.printError("Outdata conversion did not work, data file smaller than docfile, %d < %d bytes"%(outfilesize, partfilesize))

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
		filesperdir = int(math.ceil(numpart/float(numdir)+2))
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
	stackimages = apImagicFile.readImagic(stackfile)

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







