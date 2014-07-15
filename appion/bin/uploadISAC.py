#!/usr/bin/env python

import os
import sys
import glob
import time
import sparx
import numpy
import pprint
import random
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack

#========================
#========================
class parseISAC(object):
	def __init__(self):
		self.files = None

	#========================
	#========================
	def generationFromFile(self, stackfile):
		root = os.path.splitext(stackfile)[0]
		genStr = root[26:]
		genId = int(genStr)
		return genId

	#========================
	#========================
	def getGenerationFiles(self):
		if self.files is None:
			files = glob.glob("class_averages_generation_*.hdf")
			self.files = sorted(files, key=lambda a: self.generationFromFile(a))
		return self.files

	#========================
	#========================
	def readAndMergeStacks(self):
		files = self.getGenerationFiles()
		self.classToGenerationDict = {}
		imageList = []
		count = 0
		for stackfile in files:
			apDisplay.printMsg( "reading images from %s"%(stackfile))
			d = sparx.EMData.read_images(stackfile)
			genId = self.generationFromFile(stackfile)
			for i in range(len(d)):
				self.classToGenerationDict[count] = (genId, i)
				count += 1
			imageList.extend(d)
		return imageList, self.classToGenerationDict

	#========================
	#========================
	def listToString(self, myList):
		myStr = ""
		for item in myList:
			myStr += "%d,"%(item)
		return myStr

	#========================
	#========================
	def readGenerationFile(self, genFile):
		t0 = time.time()
		if not os.path.isfile(genFile):
			apDisplay.printWarning( "File not found %s"%(genFile))
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
	def trackParticlesInISAC(self):
		t1 = time.time()

		genParamsAcct = {}
		genParamsUnacct = {}
		exdict = {}
		self.classMembersDict = {}
		f = open("generationClassMembers.csv", "w")
		f.write("generation\tclassNum\tnumMembers\tmember\n")
		t1 = time.time()
		files = self.getGenerationFiles()	
		for genFile in files:
			t0 = time.time()
			generation = self.generationFromFile(genFile)
			genfileAcct = "generation_%d_accounted.txt" % (generation)
			if not os.path.isfile(genfileAcct):
				continue
			genParamsAcct[generation] = self.readGenerationFile(genfileAcct)
			genfileUnacct = "generation_%d_unaccounted.txt" % (generation)
			genParamsUnacct[generation] = self.readGenerationFile(genfileUnacct)
			apDisplay.printMsg ( "Gen %d: Acct: %d / Unacct: %d = Total %d"
				%(generation, len(genParamsAcct[generation]), len(genParamsUnacct[generation]),
				len(genParamsAcct[generation])+ len(genParamsUnacct[generation])))

			### read HDF file to get class members
			headerOnly = True
			classFile = "class_averages_generation_%d.hdf"%(generation)
			classInfoList = sparx.EMData.read_images(classFile, [], headerOnly)
			self.classMembersDict[generation] = []
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
				if isinstance(members, numpy.ndarray):
					members = members.tolist()
				self.classMembersDict[generation].append(members)
				classNum += 1
				myStr = self.listToString(members)
				f.write("%d\t%d\t%d\t%s\n"%(generation, classNum, len(members), myStr))
		f.close()
		apDisplay.printColor("Finished tracking particles in %s"
			%(apDisplay.timeString(time.time() - t1)), "cyan")	
		return 

	#========================
	#========================
	def alignClassAverages(self, outputStack, numClassPerIter=None, xrange=5, yrange=5, 
			transStep=1, firstRing=1, lastRing=26, ringStep=1):
		t1 = time.time()
		outlist = "alignClassAverages.csv" 
		#output of the alignment program: new class number, original number, peak
		imageList, self.classToGenerationDict = self.readAndMergeStacks()

		mode = "F"
		if numClassPerIter is None:
			numClassPerIter = int(0.25*len(imageList))+1
	
		# randomly select an initial class
		init = int(random.random()*len(imageList))
		apDisplay.printMsg( "initial align class %d of %d / num classes per iter %d"
			%(init, len(imageList)-1, numClassPerIter))
		temp = imageList[init].copy()
		temp.write_image(outputStack,0)
	
		#setup list of classes
		unusedClasses = range(0, len(imageList))
		unusedClasses.remove(init)

		#print unusedClasses
		f = open(outlist, "w")
		f.write("genId\tgenClass\tcombineClass\torigClass\talpha\tx\ty\tmirror\tpeak\n")
		acceptedClass = []
		newClassNumber = 0
		self.newClassToGenClass = {}
		while(len(unusedClasses) > 0):
			t0 = time.time()
			peakList = []
			alignDict = {}
			indexList = []
			## go through classes and assign data
			apDisplay.printMsg("aligning %d remaining class averages"%(len(unusedClasses)))
			for classNum in unusedClasses:
				indexList.append(classNum)
				alignData = sparx.align2d(imageList[classNum], temp, xrange, yrange, 
					transStep, firstRing, lastRing, ringStep, mode) 
				alpha, x, y, mirror, peak = alignData
				peakList.append(peak)
				alignDict[classNum] = alignData
			
			peakArray = numpy.array(peakList)
			## fancy numpy thing to get the indices of top N values from an array
			peakSelect = peakArray.argsort()[-numClassPerIter:][::-1]
			#print peakSelect
			
			#print unusedClasses
			for index in peakSelect:
				classNum = indexList[index]
				alignData = alignDict[classNum]
				alpha, x, y, mirror, peak = alignData
				#print newClassNumber,classNum,peak
				genId,origClass = self.classToGenerationDict[index]
				self.newClassToGenClass[newClassNumber] = genId,origClass
				f.write("%d\t%d\t%d\t%d\t%.3f\t%.3f\t%.3f\t%d\t%.3f\n" 
					% (genId, origClass, newClassNumber, index, alpha, x, y, mirror, peak))
				temp = imageList[classNum].copy()
				temp = sparx.rot_shift2D(temp, alpha, x, y, mirror)
				temp.write_image(outputStack, newClassNumber)
				newClassNumber += 1
				unusedClasses.remove(classNum)
			apDisplay.printMsg("done in %s"%(apDisplay.timeString(time.time()-t0)))	
		f.close()
		apDisplay.printColor("Finished aligning classes in %s"
			%(apDisplay.timeString(time.time() - t1)), "cyan")	
		return 

	#========================
	#========================
	def getParticlesForClass(newClassNum):
		genId, genClassNum = self.newClassToGenClass[newClassNum]
		particleList = self.classMembersDict[genId][genClassNum]
		return particleList

	#========================
	#========================
	def alignParticlesToClasses(self, partStack, alignedClassStack, alignedPartStack, 
			xrange=5, yrange=5, transStep=1, firstRing=1, lastRing=26, ringStep=1):
		t1 = time.time()
		numPart = sparx.EMUtil.get_image_count(partStack)
		# for some reason this reports more classes than exist		
		numClasses = sparx.EMUtil.get_image_count(alignedClassStack)
		apDisplay.printMsg("aligning %d particles to %d classes"%(numPart, numClasses))		
		headerOnly = True
		mode = "F"
		combinePartList = []
		self.particleAlignData = {}
		for newClassNum in range(numClasses):
			genId, genClassNum = self.newClassToGenClass[newClassNum]
			particleList = self.classMembersDict[genId][genClassNum]
			apDisplay.printMsg("aligning %d particles to class %d of %d (gen %d, num %d)"
				%(len(particleList), newClassNum, numClasses, genId, genClassNum))
			partEMDataList = sparx.EMData.read_images(partStack, particleList, not headerOnly)
			classEMData = sparx.get_im(alignedClassStack, newClassNum)

			for i in range(len(particleList)):
				partEMData = partEMDataList[i]
				partId = particleList[i]
				alignData = sparx.align2d(partEMData, classEMData, 
					xrange, yrange, transStep, firstRing, lastRing, ringStep, mode)
				self.particleAlignData[partId] = alignData
				combinePartList.append(partId)
		apDisplay.printColor("Finished aligning particles in %s"
			%(apDisplay.timeString(time.time() - t1)), "cyan")
		
		t1 = time.time()
		### write out complete alignment parameters for all generations & aligned stack
		f = open("alignParticles.csv", "w")
		count = 0
		for partId in combinePartList:
			# write alignments to file
			alignData = self.particleAlignData[partId]
			alpha, x, y, mirror, peak = alignData

			f.write("%.3f\t%.3f\t%.3f\t%d\t%d\n" % (alpha, x, y, mirror, peak))
			partEMData = sparx.EMData.read_images(partStack, [partId], not headerOnly)[0]
			alignPartEMData = sparx.rot_shift2D(partEMData, alpha, x, y, mirror)
			#we have to use count instead of partId, because not all images were aligned
			alignPartEMData.write_image(alignedPartStack, count)
			count += 1
		f.close()
		apDisplay.printColor("Finished creating aligned stack in %s"
			%(apDisplay.timeString(time.time() - t1)), "cyan")	
		return



#=====================
#=====================
class UploadISAC(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --jobid=ID [ --commit ]")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="ISAC jobid", metavar="#")

	#=====================
	def checkConflicts(self):
		return

	#=====================
	def setRunDir(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApMaxLikeJobData.direct_query(self.params["jobid"])
			self.params['rundir'] = jobdata['path']['path']
		else:
			self.params['rundir'] = os.path.abspath(".")

	#=====================
	def getMaxLikeJob(self, runparams):
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = runparams['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(runparams['rundir']))
		maxjobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])
		maxjobq['timestamp'] = self.params['timestamp']
		maxjobdata = maxjobq.query(results=1)
		if not maxjobdata:
			return None
		return maxjobdata[0]

	#=====================
	def insertRunIntoDatabase(self, alignimagicfile, runparams):
		apDisplay.printMsg("Inserting MaxLike Run into DB")

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = runparams['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup max like run
		maxlikeq = appiondata.ApMaxLikeRunData()
		maxlikeq['runname'] = runparams['runname']
		maxlikeq['run_seconds'] = runparams['runtime']
		#maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['fastmode'] = runparams['fastmode']
		maxlikeq['mirror'] = runparams['mirror']
		maxlikeq['student'] = bool(runparams['student'])
		maxlikeq['init_method'] = "xmipp default"
		maxlikeq['job'] = self.getMaxLikeJob(runparams)

		### finish alignment run
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] = False
		alignrunq['runname'] = runparams['runname']
		alignrunq['description'] = runparams['description']
		alignrunq['lp_filt'] = runparams['lowpass']
		alignrunq['hp_filt'] = runparams['highpass']
		alignrunq['bin'] = runparams['bin']

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = alignimagicfile
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = "part"+self.params['timestamp']+"_average.hed"
		alignstackq['iteration'] = self.lastiter
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		alignimagicfilepath = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(alignimagicfilepath):
			apDisplay.printError("could not find stack file: "+alignimagicfilepath)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		alignstackq['boxsize'] = apFile.getBoxSize(alignimagicfilepath)[0]
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		alignstackq['description'] = runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  runparams['numpart']

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertParticlesIntoDatabase(self, stackid, partlist):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = partdict['refnum']
			refq['iteration'] = self.lastiter
			refsearch = "part"+self.params['timestamp']+"_ref*"+str(partdict['refnum'])+"*"
			refbase = os.path.splitext(glob.glob(refsearch)[0])[0]
			refq['mrcfile'] = refbase+".mrc"
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			if partdict['refnum']  in self.resdict:
				refq['ssnr_resolution'] = self.resdict[partdict['refnum']]
			reffile = os.path.join(self.params['rundir'], refq['mrcfile'])
			if not os.path.isfile(reffile):
				emancmd = "proc2d "+refbase+".xmp "+refbase+".mrc"
				apEMAN.executeEmanCmd(emancmd, verbose=False)
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### setup particle
			alignpartq = appiondata.ApAlignParticleData()
			alignpartq['partnum'] = partdict['partnum']
			alignpartq['alignstack'] = self.alignstackdata
			stackpartdata = apStack.getStackParticle(stackid, partdict['partnum'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['inplane']
			alignpartq['mirror'] = partdict['mirror']
			alignpartq['ref'] = refq
			alignpartq['spread'] = partdict['spread']

			### insert
			if self.params['commit'] is True:
				inserted += 1
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def calcResolution(self, partlist, alignimagicfile, apix):
		### group particles by refnum
		reflistsdict = {}
		for partdict in partlist:
			refnum = partdict['refnum']
			partnum = partdict['partnum']
			if not refnum in reflistsdict:
					reflistsdict[refnum] = []
			reflistsdict[refnum].append(partnum)

		### get resolution
		self.resdict = {}
		boxsizetuple = apFile.getBoxSize(alignimagicfile)
		boxsize = boxsizetuple[0]
		for refnum in reflistsdict.keys():
			partlist = reflistsdict[refnum]
			esttime = 3e-6 * len(partlist) * boxsize**2
			apDisplay.printMsg("Ref num %d; %d parts; est time %s"
				%(refnum, len(partlist), apDisplay.timeString(esttime)))

			frcdata = apFourier.spectralSNRStack(alignimagicfile, apix, partlist, msg=False)
			frcfile = "frcplot-%03d.dat"%(refnum)
			apFourier.writeFrcPlot(frcfile, frcdata, apix, boxsize)
			res = apFourier.getResolution(frcdata, apix, boxsize)

			self.resdict[refnum] = res

		return

	#=====================
	#=====================
	def start(self):
		### load parameters
		runparams = self.readRunParameters()

		### align references
		self.alignReferences(runparams)

		### create an aligned stack
		self.createAlignedReferenceStack()

		### read particles
		self.lastiter = self.findLastIterNumber()
		if self.params['sort'] is True:
			self.sortFolder()
		reflist = self.readRefDocFile()
		partlist = self.readPartDocFile(reflist)
		self.writePartDocFile(partlist)

		### create aligned stacks
		alignimagicfile = self.createAlignedStacks(partlist, runparams['localstack'])
		apStack.averageStack(alignimagicfile)

		### calculate resolution for each reference
		apix = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		self.calcResolution(partlist, alignimagicfile, apix)

		### insert into databse
		self.insertRunIntoDatabase(alignimagicfile, runparams)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist)

		apFile.removeStack(runparams['localstack'], warn=False)
		rmcmd = "/bin/rm -fr partfiles/*"
		apEMAN.executeEmanCmd(rmcmd, verbose=False, showcmd=False)
		apFile.removeFilePattern("partfiles/*")

#=====================
#=====================
if __name__ == '__main__':
	runner = UploadISAC()
	runner.start()
	runner.close()

