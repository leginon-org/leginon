#!/usr/bin/env python
#
import os
import sys
import time
import math
import subprocess
#appion
import apDisplay
import apEMAN
import apFile
import apParam
import apImagicFile
from pyami import spider, mrc, mem
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
def breakupStackIntoSingleFiles(stackfile, partdir="partfiles", numpart=None, filetype="spider"):
	"""
	takes the stack file and creates single spider files ready for processing
	"""
	apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")
	apDisplay.printMsg("stack: "+stackfile)

	starttime = time.time()
	boxsize = apFile.getBoxSize(stackfile)
	filesperdir = int(1e9/(boxsize[0]**2)/8.)
	if filesperdir > 4096:
		filesperdir = 4096
	if numpart is None:
		numpart = apFile.numImagesInStack(stackfile)
		apDisplay.printMsg("Found "+str(numpart)+" particles in stack")
	apParam.createDirectory(partdir)
	if numpart > filesperdir:
		numdir = createSubFolders(partdir, numpart, filesperdir)
		filesperdir = int(math.ceil(numpart/float(numdir)))
		apDisplay.printMsg("Splitting "+str(numpart)+" particles into "+str(numdir)+" folders with "
			+str(filesperdir)+" particles per folder")
		last = filesperdir
		subdir = 1
	else:
		filesperdir = numpart+1
		apDisplay.printMsg("Splitting "+str(numpart)+" particles into 1 folder with "
			+str(filesperdir)+" particles per folder")
		apParam.createDirectory(os.path.join(partdir, "1"))
		last = numpart
		subdir = 1

	if not os.path.isfile(stackfile):
		apDisplay.printError("stackfile does not exist: "+stackfile)

	### make particle files
	partlistdocfile = "partlist.doc"
	f = open(partlistdocfile, "w")
	first = 1
	index = 0
	t0 = time.time()
	while index < numpart and first < numpart:
		### read images
		if index > 10:
			esttime = (time.time()-t0)/float(index+1)*float(numpart-index)
			apDisplay.printMsg("dirnum %d at partnum %d to %d of %d, %s remain"
				%(subdir, first, last, numpart, apDisplay.timeString(esttime)))
		else:
			apDisplay.printMsg("dirnum %d at partnum %d to %d of %d"
				%(subdir, first, last, numpart))
		#print first, last, numpart, index
		stackimages = apImagicFile.readImagic(stackfile, first=first, last=last, msg=False)
		#print stackimages['images'].shape

		### write images
		for partimg in stackimages['images']:
			if filetype == "mrc":
				partfile = os.path.join(partdir, str(subdir), "part%06d.mrc"%(index))
				mrc.write(partimg, partfile)
			else:
				partfile = os.path.join(partdir, str(subdir), "part%06d.spi"%(index))
				spider.write(partimg, partfile)
			f.write(os.path.abspath(partfile)+" 1\n")
			index += 1

		### setup for next subdir
		first = last+1
		last += filesperdir
		if last > numpart:
			last = numpart
		subdir += 1
	f.close()
	if index < numpart:
		apDisplay.printError("Did not write all particles out, the stack header does not match the stack data")

	apDisplay.printColor("finished breaking stack in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return partlistdocfile

#======================
#======================
def gatherSingleFilesIntoStack(selfile, stackfile, filetype="spider"):
	"""
	takes a selfile and creates an EMAN stack
	"""
	selfile = os.path.abspath(selfile)
	stackfile = os.path.abspath(stackfile)
	if stackfile[-4:] != ".hed":
		apDisplay.printWarning("Stack file does not end in .hed")
		stackfile = stackfile[:-4]+".hed"

	apDisplay.printColor("Merging files into a stack, this can take a while", "cyan")

	starttime = time.time()

	if not os.path.isfile(selfile):
		apDisplay.printError("selfile does not exist: "+selfile)

	### Process selfile
	fh = open(selfile, 'r')
	filelist = []
	for line in fh:
		sline = line.strip()
		if sline:
			args=sline.split()
			if (len(args)>1):
				filename = args[0].strip()
				filelist.append(filename)
	fh.close()

	### Set variables
	boxsize = apFile.getBoxSize(filelist[0])
	partperiter = int(1e9/(boxsize[0]**2)/16.)
	if partperiter > 4096:
		partperiter = 4096
	apDisplay.printMsg("Using %d particle per iteration"%(partperiter))
	numpart = len(filelist)
	if numpart < partperiter:
		partperiter = numpart

	### Process images
	imgnum = 0
	stacklist = []
	stackroot = stackfile[:-4]
	### get memory in kB
	startmem = mem.active()
	while imgnum < len(filelist):
		filename = filelist[imgnum]
		index = imgnum % partperiter
		if imgnum % 100 == 0:
			sys.stderr.write(".")
			#sys.stderr.write("%03.1fM %d\n"%((mem.active()-startmem)/1024., index))
			if mem.active()-startmem > 2e6:
				apDisplay.printWarning("Out of memory")
		if index < 1:
			#print "img num", imgnum
			### deal with large stacks, reset loop
			if imgnum > 0:
				sys.stderr.write("\n")
				stackname = "%s-%d.hed"%(stackroot, imgnum)
				apDisplay.printMsg("writing single particles to file "+stackname)
				stacklist.append(stackname)
				apFile.removeStack(stackname, warn=False)
				apImagicFile.writeImagic(stackarray, stackname, msg=False)
				perpart = (time.time()-starttime)/imgnum
				apDisplay.printColor("part %d of %d :: %.1fM mem :: %s/part :: %s remain"%
					(imgnum+1, numpart, (mem.active()-startmem)/1024. , apDisplay.timeString(perpart), 
					apDisplay.timeString(perpart*(numpart-imgnum))), "blue")
			stackarray = []
		### merge particles
		if filetype == "mrc":
			partimg = mrc.read(filename)
		else:
			partimg = spider.read(filename)
		stackarray.append(partimg)
		imgnum += 1

	### write remaining particles to file
	sys.stderr.write("\n")
	stackname = "%s-%d.hed"%(stackroot, imgnum)
	apDisplay.printMsg("writing particles to file "+stackname)
	stacklist.append(stackname)
	apImagicFile.writeImagic(stackarray, stackname, msg=False)

	### merge stacks
	apFile.removeStack(stackfile, warn=False)
	apImagicFile.mergeStacks(stacklist, stackfile)
	print stackfile
	filepart = apFile.numImagesInStack(stackfile)
	if filepart != numpart:
		apDisplay.printError("number merged particles (%d) not equal number expected particles (%d)"%
			(filepart, numpart))
	for stackname in stacklist:
		apFile.removeStack(stackname, warn=False)

	### summarize
	apDisplay.printColor("merged %d particles in %s"%(imgnum, apDisplay.timeString(time.time()-starttime)), "cyan")

#======================
#======================
def createSubFolders(partdir, numpart, filesperdir):
	i = 0
	dirnum = 0
	while i < numpart:
		dirnum += 1
		apParam.createDirectory(os.path.join(partdir, str(dirnum)), warning=False)
		i += filesperdir
	return dirnum

