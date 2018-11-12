#!/usr/bin/env python
import sys
import time

from appionlib import apImagicFile
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apImage

####
# This is file function file with no database connection
# Please keep it this way
####

#=====================
def createAlignedStack(partlist, origstackfile, outputfile='alignstack'):
	partperiter = min(4096,apImagicFile.getPartSegmentLimit(origstackfile))
	numpart = len(partlist)
	if numpart < partperiter:
		partperiter = numpart

	t0 = time.time()
	imgnum = 0
	stacklist = []
	apDisplay.printMsg("rotating and shifting particles at "+time.asctime())
	while imgnum < len(partlist):
		index = imgnum % partperiter
		if imgnum % 100 == 0:
			sys.stderr.write(".")
		if index == 0:
			### deal with large stacks
			if imgnum > 0:
				sys.stderr.write("\n")
				stackname = "%s%d.hed"%(outputfile,imgnum)
				apDisplay.printMsg("writing aligned particles to file "+stackname)
				stacklist.append(stackname)
				apFile.removeStack(stackname, warn=False)
				apImagicFile.writeImagic(alignstack, stackname, msg=False)
				perpart = (time.time()-t0)/imgnum
				apDisplay.printColor("particle %d of %d :: %s per part :: %s remain"%
					(imgnum+1, numpart, apDisplay.timeString(perpart),
					apDisplay.timeString(perpart*(numpart-imgnum))), "blue")
			alignstack = []
			imagesdict = apImagicFile.readImagic(origstackfile, first=imgnum+1,
				last=imgnum+partperiter, msg=False)

		### align particles
		partimg = imagesdict['images'][index]
		partdict = partlist[imgnum]
		partnum = imgnum+1
		if partdict['partnum'] != partnum:
			apDisplay.printError("particle shifting "+str(partnum)+" != "+str(partdict['partnum']))
		xyshift = (partdict['xshift'], partdict['yshift'])
		alignpartimg = apImage.xmippTransform(partimg, rot=partdict['inplane'],
			shift=xyshift, mirror=partdict['mirror'])
		alignstack.append(alignpartimg)
		imgnum += 1

	### write remaining particle to file
	sys.stderr.write("\n")
	stackname = "%s%d.hed"%(outputfile,imgnum)
	apDisplay.printMsg("writing aligned particles to file "+stackname)
	stacklist.append(stackname)
	apImagicFile.writeImagic(alignstack, stackname, msg=False)

	### merge stacks
	alignimagicfile = "%s.hed" % (outputfile,)
	apFile.removeStack(alignimagicfile, warn=False)
	apImagicFile.mergeStacks(stacklist, alignimagicfile)
	#for stackname in stacklist:
	#	emancmd = "proc2d %s %s"%(stackname, alignimagicfile)
	#	apEMAN.executeEmanCmd(emancmd, verbose=False)
	filepart = apFile.numImagesInStack(alignimagicfile)
	if filepart != numpart:
		apDisplay.printError("number aligned particles (%d) not equal number expected particles (%d)"%
			(filepart, numpart))
	for stackname in stacklist:
		apFile.removeStack(stackname, warn=False)

	### summarize
	apDisplay.printMsg("rotated and shifted %d particles in %s"
		%(imgnum, apDisplay.timeString(time.time()-t0)))

	return alignimagicfile


