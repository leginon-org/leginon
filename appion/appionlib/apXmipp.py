#!/usr/bin/env python
#
import os
import sys
import time
import math
import subprocess
#appion
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apParam
from appionlib import apImagicFile
from pyami import spider, mrc, mem
from appionlib.apSpider import operations

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
#======================
#======================
class breakUpStack(apImagicFile.processStack):
	#===============
	def preLoop(self):
		self.dirnum = 0
		if self.stepsize > 4096:
			numchucks = math.ceil(self.numpart/4096.0)
			self.stepsize = int(self.numpart/numchucks)
		self.numdir = math.ceil(self.numpart/float(self.stepsize))
		self.message("Splitting %d particles into %d folders with %d particles per folder"
			%(self.numpart, self.numdir, self.stepsize))
		self.partdocf = open(self.partdocfile, "w")

	#===============
	def processStack(self, stackarray):
		self.dirnum += 1
		self.partdir = os.path.join(self.rootdir, "%03d"%(self.dirnum))
		apParam.createDirectory(self.partdir, warning=False)
		for partarray in stackarray:
			self.processParticle(partarray)
			self.index += 1 #you must have this line in your loop

	#===============
	def processParticle(self, partarray):
		if self.filetype == "mrc":
			partfile = os.path.join(self.partdir, "part%06d.mrc"%(self.index))
			mrc.write(partarray, partfile)
		else:
			partfile = os.path.join(self.partdir, "part%06d.spi"%(self.index))
			try:
				spider.write(partarray, partfile)
			except:
				print partarray
				apDisplay.printWarning("failed to write spider file for part index %d"%(self.index))
				print partarray.shape
				spider.write(partarray, partfile)
		self.partdocf.write(os.path.abspath(partfile)+" 1\n")

	#===============
	def postLoop(self):
		self.partdocf.close()

#======================
#======================
def breakupStackIntoSingleFiles(stackfile, partdir="partfiles", numpart=None, filetype="spider"):
	"""
	takes the stack file and creates single spider files ready for processing
	"""
	apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")
	apParam.createDirectory(partdir)
	partdocfile = "partlist.doc"

	### setup
	breaker = breakUpStack()
	breaker.rootdir = partdir
	breaker.filetype = filetype
	breaker.partdocfile = partdocfile

	### make particle files
	breaker.start(stackfile)

	return partdocfile

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

