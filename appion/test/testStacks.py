#!/usr/bin/env python

import sys
import numpy
from appionlib import apFile
from appionlib import apEMAN
from appionlib import apImagicFile
from pyami import mrc, spider
from scipy import stats, ndimage

def getCCValue(imgarray1, imgarray2):
	### faster cc, thanks Jim
	ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
	return ccs[0]

def isSameStack(partlist1, partlist2):
	if len(partlist1) != len(partlist2):
		print "failed length %d vs. %d"%(len(partlist1),len(partlist2))
		return False
	for i in range(len(partlist1)):
		part1 = partlist1[i]
		part2 = partlist2[i]
		print part1[0:2,0:2]
		print part2[0:2,0:2]
		cc = getCCValue(part1, part2)
		### cross-correlation must be better than 0.99
		print "CC %.3f"%(cc)
		if cc < 0.99:
			print "failed CC %.3f"%(cc)
			#return False
	return True

def emanMrcToStack(partlist):
	apFile.removeStack("emanmrc.hed", warn=False)
	for part in partlist:
		mrc.write(part, "temp.mrc")
		emancmd = "proc2d temp.mrc emanmrc.hed"
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		apFile.removeFile("temp.mrc")
	return

def emanSpiderToStack(partlist):
	apFile.removeStack("emanspi.hed", warn=False)
	for part in partlist:
		spider.write(part, "temp.spi")
		emancmd = "proc2d temp.spi emanspi.hed"
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		apFile.removeFile("temp.spi")
	return

if __name__ == "__main__":
	### generate random image data
	shape = (128,128)
	partlist = []
	for i in range(8):
		part = numpy.random.random(shape)
		part = ndimage.gaussian_filter(part, sigma=shape[0]/16)
		partlist.append(part)

	### save original data
	apFile.removeStack("original.hed", warn=False)
	apImagicFile.writeImagic(partlist, "original.hed")

	### read and write with Appion
	apFile.removeStack("resave.hed", warn=False)
	imagic = apImagicFile.readImagic("original.hed")
	partlist2 = imagic['images']
	apImagicFile.writeImagic(partlist2, "resave.hed")
	if not isSameStack(partlist, partlist2):
		print "Stacks are different"
		sys.exit(1)
	
	### read and write with EMAN mrc
	emanMrcToStack(partlist)

	### read and write with EMAN mrc
	emanSpiderToStack(partlist)

