#!/usr/bin/env python

import os
import sys
import time
import math
import multiprocessing
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apParam
from appionlib import appiondata
from appionlib import starFile
from appionlib import apFile
from appionlib import apStackMeanPlot
from appionlib.StackClass import stackTools
from appionlib.apCtf import ctfdb
import sinedon.directq

#================================
def makeStack(starfile):
	star = starFile.StarFile(starfile)
	star.read()

	imDataBlock = star.getDataBlock("data_image")
	imDict = imDataBlock.getLoopDict()[0]

	partDataBlock = star.getDataBlock("data_particles")
	loopDict = partDataBlock.getLoopDict()

	print "Found %d particles"%(len(loopDict))
	if len(loopDict) == 0:
		return

	micrograph = imDict['_micrographName']
	stackfile = imDict['_stackFile']
	initboxsize = int(imDict['_initBoxSize'])
	finalboxsize = int(imDict['_finalBoxSize'])
	invert = bool(imDict['_invert'])

	coordinates = []
	partnum = 0
	for partdict in loopDict:
		partnum += 1
		x = int(partdict['_coordinateX'])
		y = int(partdict['_coordinateY'])
		partid = int(partdict['_appionParticleDBID'])
		coordinates.append((x, y, partid))
	if len(coordinates) == 0:
		return
	#this creates a new file
	usedparticles = stackTools.boxParticlesFromFile(micrograph, stackfile,
			initboxsize, finalboxsize, coordinates, invert)
	if usedparticles is None:
		return

	numpart = stackTools.getNumberOfParticles(stackfile)
	if numpart != len(usedparticles):
		apDisplay.printError("number of particles does not match %d != %d"
			%(numpart, len(usedparticles)))
	#for ituple in usedparticles:
	statsstarfile = starfile.replace("picks", "stats")
	writeUsedParticleStackStats(statsstarfile, stackfile, usedparticles)
	return

#================================
def writeUsedParticleStackStats(starfile, stackfile, usedparticles):
	meanlist, stdevlist = stackTools.stackStatistics(stackfile)
	if len(usedparticles) != len(meanlist):
		apDisplay.printError("particle number mismatch %d, %d"
			%(len(usedparticles),len(meanlist)))

	looplabels = [ "_particleid", "_mean", "_stdev", ]
	valueSets = []
	for i in range(len(usedparticles)):
		valueString = ("%d %.8f %.8f"
			%(usedparticles[i], abs(meanlist[i]), stdevlist[i]))
		valueSets.append(valueString)

	star = starFile.StarFile(starfile)
	star.buildLoopFile("data_particles", looplabels, valueSets )
	star.write()

#================================
def start_process():
	print 'Starting', multiprocessing.current_process().name

#=====================
#=====================
class QuickStack(appionScript.AppionScript):
	#================================
	def setupParserOptions(self):
		self.parser.add_option("--selectid", "--selectionid", dest="selectid", type="int",
			help="Particle Selction ID", metavar="#")
		self.parser.add_option("--preset", dest="preset",
			help="Preset Name", metavar="#")
		self.parser.add_option("--init-boxsize", dest="initboxsize", type="int",
			help="Initial Micrograph Boxsize", metavar="#")
		self.parser.add_option("--final-boxsize", dest="finalboxsize", type="int",
			help="Final Reduced Particle Boxsize", metavar="#")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert particle density")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--mode", dest="mode", default="both",
			type="choice", choices=('relion', 'appion', 'both'),
			help="Processing modes (1) 'relion'=just a stack, faster; "
			+"(2) 'appion'=upload to database; or (3) 'both'", metavar="..")

	#================================
	def checkConflicts(self):
		if self.params['expid'] is None:
			apDisplay.printError("Please provide a session id, e.g. --expid=15")
		if self.params['selectid'] is None:
			apDisplay.printError("Please provide a Particle Selction id, e.g. --selectid=15")
		if self.params['initboxsize'] is None:
			apDisplay.printError("Please provide an Initial Box size id, e.g. --init-boxsize=256")
		if self.params['finalboxsize'] is None:
			apDisplay.printError("Please provide an Final Box size id, e.g. --final-boxsize=128")
		if self.params['nproc'] is None:
			self.params['nproc'] = apParam.getNumProcessors()

	#================================
	def writeParticleStarFile(self, imgdata):
		starfile = "picks/"+apDisplay.short(imgdata['filename'])+".picks.star"
		stackfile = "mrcs/"+apDisplay.short(imgdata['filename'])+".picks.mrcs"
		micrograph = os.path.join(imgdata['session']['image path'], imgdata['filename']+'.mrc')

		particles = apParticle.getParticles(imgdata, self.params['selectid'])
		if len(particles) == 0:
			return
		
		looplabels = ["_coordinateX", "_coordinateY", "_particleCount", "_appionParticleDBID",  ]
		count = 0
		valueSets = []
		imgdbid = int(imgdata.dbid)
		for part in particles:
			count += 1
			valueString = ("%d %d %d %d"
				%(part['xcoord'], part['ycoord'], count, part.dbid))
			valueSets.append(valueString)
		if count == 0:
			return None
		star = starFile.StarFile(starfile)

		imlabels = ["_stackFile", "_micrographName", "_appionImageId",
			"_initBoxSize", "_finalBoxSize", "_invert",]
		imvaluestring = ("%s %s %d %d %d %d"
			%(stackfile, micrograph, imgdbid, self.params['initboxsize'],
			self.params['finalboxsize'], self.params['invert']))

		star.buildLoopFile("data_image", imlabels, [imvaluestring,])
		star.buildLoopFile("data_particles", looplabels, valueSets )

		star.write()
		return starfile

	#================================
	def writeStackStarFile(self, pickstarfilelist):
		"""
		https://www2.mrc-lmb.cam.ac.uk/relion/index.php/This_equivalent_STAR_file
		"""
		valueSets = []
		for pickstarfile in pickstarfilelist:
			star = starFile.StarFile(pickstarfile)
			star.read()
			dataBlock = star.getDataBlock("data_image")
			loopDict  = dataBlock.getLoopDict()
			if len(loopDict) == 0:
				apDisplay.printWarning("star file read error")
				continue

			imageid = int(loopDict[0]['_appionImageId'])
			imgdata = apDatabase.getImageDataFromSpecificImageId(imageid)
			voltage = (imgdata['scope']['high tension'])/1000

			stackfile = loopDict[0]['_stackFile']
			numpart = stackTools.getNumberOfParticles(stackfile)
			if numpart == 0:
				continue

			ctfdata = ctfdb.getBestCtfValue(imgdata)
			if ctfdata is None:
				defU = 0
				defV = 0
				defAngle = 0
				amp_contrast = 0
				extra_phase_shift = 0
				spherical_aberration = 0
			else:
				defU = ctfdata['defocus1']*1.0e10
				defV = ctfdata['defocus2']*1.0e10
				defAngle = ctfdata['angle_astigmatism']
				amp_contrast = ctfdata['amplitude_contrast']
				extra_phase_shift = ctfdata['extra_phase_shift']
				spherical_aberration = ctfdata['cs']

			for i in range(numpart):
				partcount = i+1
				#basics
				valueString = ("%06d@%s %s "%(partcount, stackfile, imgdata['filename']))

				#ctf in Angstroms and degrees
				valueString += ("%d %d %.3f "%(defU, defV, defAngle))

				#microscope
				valueString += ("%d %.3f %.3f"%(voltage, spherical_aberration, amp_contrast))

				valueSets.append(valueString)

		outputstarfile = "%s-complete_relion_stack.star"%(self.params['runname'])
		labels = ["_rlnImageName", "_rlnMicrographName",
			"_rlnDefocusU", "_rlnDefocusV", "_rlnDefocusAngle",
			"_rlnVoltage", '_rlnSphericalAberration', '_rlnAmplitudeContrast',]

		star = starFile.StarFile(outputstarfile)
		star.buildLoopFile( "data_", labels, valueSets )
		star.write()

		return outputstarfile

	#================================
	def mergeStacksIntoOneImagicFile(self, mergestack, starlist):
		for pickstarfile in starlist:
			star = starFile.StarFile(pickstarfile)
			star.read()
			dataBlock = star.getDataBlock("data_image")
			loopDict  = dataBlock.getLoopDict()

			if len(loopDict) == 0:
				apDisplay.printWarning("star file read error")
				continue

			stackfile = loopDict[0]['_stackFile']
			if os.path.isfile(stackfile):
				stackTools.mergeStacks(stackfile, mergestack, msg=False)
		return

	#================================
	def commitStackToDatabase(self, starlist):
		partNum = 0
		self.insertStackRun()
		stackid = int(self.stackdata.dbid)
		stackrunid = int(self.stackrundata.dbid)
		for pickstarfile in starlist:
			stackpartlist = []
			statsstarfile = pickstarfile.replace("picks", "stats")
			star = starFile.StarFile(statsstarfile)
			star.read()
			dataBlock = star.getDataBlock("data_particles")
			loopDict  = dataBlock.getLoopDict()
			#looplabels = [ "_particleid", "_mean", "_stdev", ]
			for partdict in loopDict:
				partNum += 1
				stackpartval = {
					'particleid': int(partdict['_particleid']),
					'particlenum': partNum,
					'mean': float(partdict['_mean']),
					'stdev': float(partdict['_stdev']),
				}
				stackpartlist.append(stackpartval)
			sqlcmd = apStack.stackPartListToSQLInsertString(stackpartlist, stackid, stackrunid)
			sinedon.directq.complexMysqlQuery('appiondata', sqlcmd)

		return

	#=======================
	def insertStackRun(self):
		downscalefactor = self.params['initboxsize']/float(self.params['finalboxsize'])

		### create a stack object
		stackq = appiondata.ApStackData()
		stackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))

		### create a stackRun object
		runq = appiondata.ApStackRunData()
		runq['stackRunName'] = self.params['runname']
		runq['session'] = self.getSessionData()

		### finish stack object
		stackq['name'] = "start.hed"
		if self.params['description'] is not None:
			stackq['description'] = self.params['description']
		else:
			stackq['description'] = "quick stack completed on "+time.asctime()
		stackq['hidden'] = False
		stackq['pixelsize'] = round(self.apix*downscalefactor, 4)*1e-10

		stackq['boxsize'] = self.params['finalboxsize']

		self.stackdata = stackq

		stparamq = appiondata.ApStackParamsData()
		stparamq['boxSize'] = self.params['finalboxsize']
		stparamq['bin'] = int(math.ceil(downscalefactor))
		stparamq['fileType'] = "imagic"
		stparamq['inverted'] = self.params['invert']
		stparamq['phaseFlipped'] = False

		### finish stackRun object
		runq['stackParams'] = stparamq
		self.stackrundata = runq

		### create runinstack object
		rinstackq = appiondata.ApRunsInStackData()
		rinstackq['stackRun'] = runq
		rinstackq['stack'] = stackq

		### if not in the database, make sure run doesn't already exist
		apDisplay.printColor("Inserting stack parameters into database", "cyan")
		rinstackq.insert()
		return

	#================================
	def deleteMrcsFiles(self, starlist):
		for pickstarfile in starlist:
			star = starFile.StarFile(pickstarfile)
			star.read()
			dataBlock = star.getDataBlock("data_image")
			loopDict  = dataBlock.getLoopDict()

			stackfile = loopDict[0]['_stackFile']
			if os.path.isfile(stackfile):
				apFile.removeFile(stackfile, warn=False)
		return

	#================================
	def checkIfStackAlreadyExists(self):
		if self.params['mode'] == 'relion':
			return

		### create a stack object
		stackq = appiondata.ApStackData()
		stackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		### see if stack already exists in the database (just checking path & name)
		uniqstackdatas = stackq.query(results=1)

		### create a stackRun object
		runq = appiondata.ApStackRunData()
		runq['stackRunName'] = self.params['runname']
		runq['session'] = self.getSessionData()
		### see if stack run already exists in the database (just checking runname & session)
		uniqrundatas = runq.query(results=1)

		if uniqrundatas and not uniqstackdatas:
			apDisplay.printError("Weird, run data without stack already in the database")
		elif not uniqrundatas and uniqstackdatas:
			apDisplay.printError("Weird, stack data without run already in the database")
		elif uniqrundatas and uniqstackdatas:
			apDisplay.printError("Stack already created")
		return

	#================================
	def start(self):
		sessiondata = self.getSessionData()
		self.checkIfStackAlreadyExists()
		if self.params['preset'] is not None:
			self.imgtree = apDatabase.getImagesFromDB(sessiondata['name'], self.params['preset'])
		else:
			self.imgtree = apDatabase.getAllImagesFromDB(sessiondata['name'])
		apParam.createDirectory("mrcs")
		apParam.createDirectory("stats")
		apParam.createDirectory("picks")

		starlist = []
		apDisplay.printMsg("Writing particle pick star files")
		self.apix = apDatabase.getPixelSize(self.imgtree[0])
		for imgdata in self.imgtree:
			sys.stderr.write(".")
			starfile = self.writeParticleStarFile(imgdata)
			if starfile is None:
				continue
			starlist.append(starfile)
		del self.imgtree
		#FIXME: the next line is for testing only
		#makeStack(starlist[0])

		t0 = time.time()
		p = multiprocessing.Pool(processes=self.params['nproc'], initializer=start_process)
		p.map(makeStack, starlist)
		p.close()
		p.join()
		p.terminate()
		print "Image Processing Finished in %.3f seconds"%((time.time()-t0)*1)

		if self.params['mode'] == 'appion' or self.params['mode'] == 'both':
			mergestack = "start.hed"
			self.mergeStacksIntoOneImagicFile(mergestack, starlist)
			stackTools.averageStack(mergestack)

		if self.params['mode'] == 'relion' or self.params['mode'] == 'both':
			outputstarfile = self.writeStackStarFile(starlist)
			fullstarpath = os.path.join(self.params['rundir'], outputstarfile)
			apDisplay.printColor("RELION Stack saved to %s"%(fullstarpath), "green")
		else:
			self.deleteMrcsFiles(starlist)

		if self.params['mode'] == 'appion' or self.params['mode'] == 'both':
			self.commitStackToDatabase(starlist)
			stackid = int(self.stackdata.dbid)
			apStackMeanPlot.makeStackMeanPlot(stackid)

#=====================
#=====================
if __name__ == '__main__':
	quickstack = QuickStack()
	quickstack.start()
	quickstack.close()

