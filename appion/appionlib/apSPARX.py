#!/usr/bin/env python

import os
import sys
import glob
import time
import EMAN2
import sparx
import numpy
import random

#========================
#========================
def generationFromFile(stackfile):
	root = os.path.splitext(stackfile)[0]
	genStr = root[26:]
	genId = int(genStr)
	return genId

#========================
#========================
def readAndMergeStacks():
	files = glob.glob("class_averages_generation_*.hdf")
	files = sorted(files, key=lambda a: generationFromFile(a))
	classToGenerationDict = {}
	imageList = []
	for stackfile in files:
		print "reading images from %s"%(stackfile)
		d = EMAN2.EMData.read_images(stackfile)
		genId = generationFromFile(stackfile)
		for i in range(len(d)):
			classToGenerationDict[i] = (genId, i)
		imageList.extend(d)
	return imageList, classToGenerationDict

#========================
#========================
def listToString(myList):
	myStr = ""
	for item in myList:
		myStr += "%d,"%(item)
	return myStr

#========================
#========================
def readGenerationFile(genFile):
	t0 = time.time()
	if not os.path.isfile(genFile):
		print "File not found", genFile
		return numpy.array([])
	f = open(genFile, "r")
	mylist = []
	for line in f:
		sint = int(line.lstrip())
		mylist.append(sint)
	f.close()
	array = numpy.array(mylist)
	#print "read file", time.time() -t0
	return array

#========================
#========================
def trackParticlesInISAC():
	### input: number of generations & lists with particle numbers to exclude in each generation
	
	### read generation files
	genParamsAcct = {}
	genParamsUnacct = {}
	exdict = {}
	eman2func = EMAN2.EMData()
	numberOfGenerations = 19
	bigClassDict = {}
	f = open("generationClassMembers.csv", "w")
	f.write("generation\tclassNum\tnumMembers\tmember\n")
	t1 = time.time()
	for i in range(numberOfGenerations):
		t0 = time.time()
		generation = i+1
		genfileAcct = "generation_%d_accounted.txt" % (generation)
		if not os.path.isfile(genfileAcct):
			continue
		genParamsAcct[generation] = readGenerationFile(genfileAcct)
		genfileUnacct = "generation_%d_unaccounted.txt" % (generation)
		genParamsUnacct[generation] = readGenerationFile(genfileUnacct)
		print ( "Gen %d: Acct: %d / Unacct: %d = Total %d"
			%(generation, len(genParamsAcct[generation]), len(genParamsUnacct[generation]),
			len(genParamsAcct[generation])+ len(genParamsUnacct[generation])))

		### read HDF file to get class members
		headerOnly = True
		classFile = "class_averages_generation_%d.hdf"%(generation)
		classInfoList = eman2func.read_images(classFile, [], headerOnly)
		bigClassDict[generation] = []
		classNum = 0
		for classInfo in classInfoList:
			members = classInfo.get_attr('members')
			members.sort()
			adjGeneration = generation
			while adjGeneration > 1:
				### loop through accounted generations & find, for each particle, the corresponding match in 
				### previous unaccounted stack; also takes into account discounted members
				adjGeneration -= 1
				try:
					members = genParamsUnacct[adjGeneration][members]
				except KeyError:
					pass
			bigClassDict[generation].append(members)
			classNum += 1
			myStr = listToString(members)
			f.write("%d\t%d\t%d\t%s\n"%(generation, classNum, len(members), myStr))
	f.close()
	print "Finished tracking particles in %s"%(apDisplay.timeString(time.time() - t1))

#========================
#========================
def alignClassAverages(outputStack, xrange=5, yrange=5, transStep=1, fr=1, ringStep=1, radius=26):
	#output stack that will be sorted and aligned relative to the input
	outlist = "alignClassAverages.csv" 
	#output of the alignment program: new class number, original number, peak
	imageList, classToGenerationDict = readAndMergeStacks()
	print "done"

	mode = "F"
	numClassPerIter = int(0.1*len(imageList))+1
	
	# randomly select an initial class
	init = int(random.random()*len(imageList))
	print "initial align class %d of %d / num classes per iter %d"%(init, len(imageList)-1, numClassPerIter)
	temp = imageList[init].copy()
	temp.write_image(outputStack,0)
	
	#setup list of classes
	unusedClasses = range(0, len(imageList))
	unusedClasses.remove(init)

	#print unusedClasses
	f = open(outlist, "w")
	acceptedClass = []
	newClassNumber = 1
	while(len(unusedClasses) > 0):
		peakList = []
		alignDict = {}
		indexList = []
		## go through classes and assign data
		print "aligning %d particles"%(len(unusedClasses))
		for classNum in unusedClasses:
			indexList.append(classNum)
			alignData = sparx.align2d(imageList[classNum], temp, xrange, yrange, transStep, fr, radius, ringStep, mode) 
			alpha, x, y, mirror, peak = alignData
			peakList.append(peak)
			alignDict[classNum] = alignData
			
		peakArray = numpy.array(peakList)
		## fancy numpy thing to get the indices of top N values from an array
		peakSelect = peakArray.argsort()[-numClassPerIter:][::-1]
		print peakSelect

		#print unusedClasses
		for index in peakSelect:
			classNum = indexList[index]
			alignData = alignDict[classNum]
			alpha, x, y, mirror, peak = alignData
			#print newClassNumber,classNum,peak
			genId,origClass = classToGenerationDict[newClassNumber]
			f.write("%d\t%d\t%d\t%d\t%8.3f\n" % (genId, origClass, newClassNumber, index, peak))
			temp = imageList[classNum].copy()
			
			temp = sparx.rot_shift2D(temp, alpha, x, y, mirror)
			temp.write_image(outputStack, newClassNumber)
			newClassNumber += 1
			unusedClasses.remove(classNum)
	f.close()
	return 

#========================
#========================
def alignParticles(xrange=5, yrange=5, transStep=1, fr=1, ringStep=1, radius=26):
	return


if __name__ == "__main__"
	trackParticlesInISAC()
	alignClassAverages()
	alignParticles()
