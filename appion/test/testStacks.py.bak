#!/usr/bin/env python

import os
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
	mincc = 1.1
	for i in range(len(partlist1)):
		part1 = partlist1[i]
		part2 = partlist2[i]
		#print part1[0:2,0:2]
		#print part2[0:2,0:2]
		cc = getCCValue(part1, part2)
		#print "CC %.8f"%(cc)
		### cross-correlation must be better than 0.999, i.e., 0.001%
		### typically is it better than 0.999999
		if cc < mincc:
			mincc = cc
		if cc < 0.999:
			#print "failed CC %.6f"%(cc)
			#return False
			pass
	print "minimum CC %.10f"%(mincc)
	if mincc < 0.999:
		return False
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

def stackToEmanMrc(stackfile):
	numpart = apFile.numImagesInStack(stackfile)
	partlist = []
	for i in range(numpart):
		mrcfile = "eman%02d.mrc"%(i)
		emancmd = "proc2d %s %s first=%d last=%d"%(stackfile, mrcfile, i, i)
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		if not os.path.isfile(mrcfile):
			print "Failed to create MRC"
			sys.exit(1)
		part = mrc.read(mrcfile)
		apFile.removeFile(mrcfile)
		partlist.append(part)
	return partlist

def stackToEmanSpi(stackfile, swap=False):
	numpart = apFile.numImagesInStack(stackfile)
	partlist = []
	for i in range(numpart):
		spifile = "eman%d.spi"%(i)
		emanspifile = spifile
		if i > 0:
			### hack for eman auto-naming
			emanspifile = "eman"
		emancmd = "proc2d %s %s first=%d last=%d"%(stackfile, emanspifile, i, i)
		if swap is True:
			emancmd += " spiderswap-single"
		else:
			emancmd += " spider-single"
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		if not os.path.isfile(spifile):
			print "Failed to create SPIDER file"
			sys.exit(1)
		part = spider.read(spifile)
		apFile.removeFile(spifile)
		partlist.append(part)
	return partlist

if __name__ == "__main__":
	### generate random image data
	shape = (128,128)
	partlist = []
	for i in range(16):
		part = numpy.random.random(shape)
		part = ndimage.gaussian_filter(part, sigma=shape[0]/16)
		partlist.append(part)

	### save original data
	apFile.removeStack("original.hed", warn=False)
	apImagicFile.writeImagic(partlist, "original.hed", msg=False)

	### read and write with Appion
	apFile.removeStack("resave.hed", warn=False)
	imagic = apImagicFile.readImagic("original.hed", msg=False)
	partlist2 = imagic['images']
	apImagicFile.writeImagic(partlist2, "resave.hed", msg=False)
	print "============\nCompare APPION IMAGIC"
	if not isSameStack(partlist, partlist2):
		print "Stacks are different"
		#sys.exit(1)
	
	### read and write with EMAN mrc
	emanMrcToStack(partlist)
	imagic = apImagicFile.readImagic("emanmrc.hed", msg=False)
	partlist3 = imagic['images']
	print "============\nCompare EMAN MRC"
	if not isSameStack(partlist, partlist3):
		print "Stacks are different"
		#sys.exit(1)

	### read and write with EMAN spider
	emanSpiderToStack(partlist)
	imagic = apImagicFile.readImagic("emanspi.hed", msg=False)
	partlist4 = imagic['images']
	print "============\nCompare EMAN SPIDER"
	if not isSameStack(partlist, partlist4):
		print "Stacks are different"

	### convert imagic to MRC with EMAN and read
	partlist5 = stackToEmanMrc("original.hed")
	print "============\nCompare IMAGIC to EMAN MRC"
	if not isSameStack(partlist, partlist5):
		print "Stacks are different"

	### convert imagic to SPIDER with EMAN and read
	partlist6 = stackToEmanSpi("original.hed")
	print "============\nCompare IMAGIC to EMAN SPIDER"
	if not isSameStack(partlist, partlist6):
		print "Stacks are different"

	### convert imagic to SPIDER SWAP with EMAN and read
	partlist7 = stackToEmanSpi("original.hed")
	print "============\nCompare IMAGIC to EMAN SPIDER SWAP"
	if not isSameStack(partlist, partlist7):
		print "Stacks are different"

