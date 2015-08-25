#python
import os
import math
import numpy
import shutil
#pyami
from pyami import mrc
#appionlib
from appionlib.apCtf import ctfdb
from appionlib import apDisplay
from appionlib import apParam
from appionlib import starFile

def readStarFileDataBlock(starfile, datablock):
	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()
	return loopDict


def writeLoopDictToStarFile(loopDict, datablockname, starfilename):

	labels = loopDict[0].keys()
	valueSets = []
	for line in loopDict:
		params = ""
		for p in line.values():
			params += " %s" % p
		valueSets.append(params)
	star = starFile.StarFile(starfilename)
	star.buildLoopFile(datablockname, labels, valueSets)
	star.write()


def excludeClassesFromRelionDataFile(instarfile, datablock, outlist, outstarfile, *classlist):
	### input is Relion data star file, e.g. run1_it025_data.star
	### datablock: The start of a data block is defined by the keyword "data_" followed by an optional string for identification (e.g., "data_images")
	### outputs a list without the particles belonging to excluded classes
	### list is EMAN-style, particle numbering starts with 0 (note that in Relion particle numbering starts with 1)
	### outstarfile is the output star file
	### *classlist can be as many classes as you wish separated by comma, e.g. 1 or 1,3,6; classes are numbered Relion format, starting with 1

	star = starFile.StarFile(instarfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()

	badparts = []
	goodparts = []
	loopDictNew = []
	for i in range(len(loopDict)):
		rlnpart = float(loopDict[i]['_rlnImageName'].split("@")[0]) # starts with 1
		rlnclass = float(loopDict[i]['_rlnClassNumber'])
		bad = False
		badpart = 0
		for c in classlist:
			if float(c) == rlnclass:
				badpart = int(rlnpart)
				bad = True
		if bad is True:
			badparts.append(badpart)
		else:
			goodparts.append(int(rlnpart))
			loopDictNew.append(loopDict[i])
	badparts.sort()
	goodparts.sort()
	f = open(outlist, "w")
	for gp in goodparts:
		f.write("%d\n" % (gp-1)) # EMAN-style numbering, starts with 0
	f.close()
	
	# selected star file parameters, write star file with excluded images
	writeLoopDictToStarFile(loopDictNew, datablock, outstarfile)

def excludeClassesFromRelionDataFile2(starfile, outlist, *classlist):
	### input is Relion data star file, e.g. run1_it025_data.star
	### outputs a list without the particles belonging to excluded classes
	### list is EMAN-style, particle numbering starts with 0 (note that in Relion particle numbering starts with 1)
	### *classlist can be as many classes as you wish separated by comma, e.g. 1 or 1,3,6; classes are numbered Relion format, starting with 1

	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock("data_images")
	loopDict = dataBlock.getLoopDict()

	badparts = []
	goodparts = []
	for i in range(len(loopDict)):
		rlnpart = float(loopDict[i]['_rlnImageName'].split("@")[0]) # starts with 1
		rlnclass = float(loopDict[i]['_rlnClassNumber'])
		bad = False
		badpart = 0
		for c in classlist:
			if float(c) == rlnclass:
				badpart = int(rlnpart)
				bad = True
		if bad is True:
			badparts.append(badpart)
	for i in range(len(loopDict)):
		if (i+1) not in badparts:
			goodparts.append(i+1)
	f = open(outlist, "w")
	for gp in goodparts:
		f.write("%d\n" % (gp-1)) # EMAN-style numbering, starts with 0
	f.close()
	loopDictNew = starFile.LoopBlock
#	loopDictNew = []
	print dir(loopDict), "loop Dict"
	print dir(loopDictNew), "loop Dict New"
	print len(loopDict), "length of loop Dict"
	print loopDict[0]
	for gp in goodparts:
		loopDictNew.append(loopDict[gp-1])
	print len(loopDictNew), "length of loop Dict New"
	dataBlockNew = starFile.DataBlock("data_images")
	dataBlockNew.setLoopBlocks([loopDictNew])
	print dir(dataBlockNew)
	print len(dataBlockNew.loopBlocks)
	star.setDataBlock(dataBlockNew,"data_images")
	dbnew = star.getDataBlock("data_images")
	print dbnew.name, "****"
	print dir(dbnew)
	print len(dbnew.loopBlocks)
	loopDict = dbnew.getLoopDict()
	print len(loopDict)
	star.write("destination.star")

def listFileFromRelionStarFile(starfile, outlist, datablock="data_images"):
	### write out an EMAN-style list file (numbering starts with 0) based on a relion star file with images and image numbers

 	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()

	allparts = []
	for i in range(len(loopDict)):
		allparts.append(int(loopDict[i]['_rlnImageName'].split("@")[0])) # starts with 1
	allparts.sort()

	f = open(outlist, "w")
	for p in allparts:
		f.write("%d\n" % (p-1)) # EMAN-style numbering, starts with 0
	f.close()

def sortRelionStarFileByParticleNumber(instarfile, outstarfile, datablock="data_images"):
	star = starFile.StarFile(instarfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()
	
	partdict = {}
	for i in range(len(loopDict)):
		rlnpart = (int(loopDict[i]['_rlnImageName'].split("@")[0])) # starts with 1
		partdict[rlnpart] = loopDict[i]
	l = sorted(partdict, key=lambda key: partdict[key])
	l.sort()

	# write sorted star file
        loopDictNew = []
        for val in l:
                loopDictNew.append(partdict[val])
        writeLoopDictToStarFile(loopDictNew, datablock, outstarfile)
