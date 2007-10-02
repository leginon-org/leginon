#!/usr/bin/python -O

import os
import sys
import time
import wx
import numpy
import threading
import appionLoop
import particleLoop
import apFindEM
import appionData
import apDatabase
import apDisplay
import apParticle
import apPeaks
import ApTiltPicker
from apTilt import apTiltTransform
from apTilt import apTiltPair

##################################
##
##################################

class tiltAligner(particleLoop.ParticleLoop):
	#####################################################
	##### START PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	#####################################################

	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	def preLoopFunctions(self):
		if self.params['dbimages'] or self.params['alldbimages']:
			self.processAndSaveAllImages()
		self.app = ApTiltPicker.PickerApp(mode='loop')
		self.app.appionloop = self

	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	def particleDefaultParams(self):
		"""
		put in any additional default parameters
		"""
		self.params['mapdir']="tiltalignmaps"
		self.params['outtype'] = 'pickle'
		self.params['outtypeindex'] = None
		self.params['pickrunname'] = None
		self.params['pickrunid'] = None
		self.params['bin'] = 2
		self.assess = None

	def particleParseParams(self, args):
		"""
		put in any additional parameters to parse
		"""
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			if elements[0] == 'outtype':
				self.params['outtype'] = elements[1]
			elif (elements[0]=='pickrunid'):
				self.params['pickrunid']=int(elements[1])
			elif (elements[0]=='pickrunname'):
				self.params['pickrunname']=str(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def particleParamConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(('text','xml','spider','pickle')):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: text, xml, pickle or spider; NOT "+str(self.params['outtype']))
		return

	def particleCreateOutputDirs(self):
		"""
		put in any additional directories to create
		"""
		self.params['pickdatadir'] = os.path.join(self.params['rundir'],"pickdata")
		self._createDirectory(self.params['pickdatadir'], warning=False)
	
		return

	def getParticleParamsData(self):
		tiltparamsq = appionData.ApTiltAlignParamsData()
		tiltparamsq['output_type'] = self.params['outtype']
		if self.params['pickrunid'] is not None:
			tiltparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunid'])
		return tiltparamsq

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	def processImage(self, imgdata):
		#GET THE TILT PAIR
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			return

		if not self.params['dbimages'] and not self.params['alldbimages']:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
			apFindEM.processAndSaveImage(tiltdata, params=self.params)

		#RUN THE ALIGNER GUI
		self.runTiltAligner(imgdata, tiltdata)
		numpeaks = len(self.peaktree1)
		apDisplay.printMsg("Found "+str(numpeaks)+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = numpeaks

		#CREATE PEAK JPEG
		if self.threadJpeg is True:
			threading.Thread(target=apPeaks.createTiltedPeakJpeg, args=(imgdata, tiltdata, self.peaktree1, self.peaktree2, self.params)).start()
		else:
			apPeaks.createTiltedPeakJpeg(imgdata, tiltdata, self.peaktree1, self.peaktree2, self.params)

		#EXTRA DONE DICT CALL
	 	self._writeDoneDict(tiltdata['filename'])

	def commitToDatabase(self, imgdata):
		"""
		Over-writes the particleLoop commit and uses the appionLoop commit
		"""
		if len(self.peaktree1) == 0:
			apDisplay.printWarning("No particle picks; not commiting data")
			return False
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			apDisplay.printWarning("Tilt data not found; not commiting data")
			return False
		### insert the runid
		expid = int(imgdata['session'].dbid)
		self.commitRunToDatabase(expid, True)
		### insert the transform
		transdata = apTiltPair.insertTiltTransform(imgdata, tiltdata, self.tiltparams, self.params)
		### insert the particles
		self.insertParticlePeakPairs(imgdata, tiltdata, transdata)
		### insert image assessment
		if self.assess != self.assessold and self.assess is not None:
			#note runid is overrided to be 'run1'
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runid'], self.assess)
			apDatabase.insertImgAssessmentStatus(tiltdata, self.params['runid'], self.assess)

	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

	def insertParticlePeakPairs(self, imgdata, tiltdata, transdata):
		if transdata is not None:
			apParticle.insertParticlePeakPairs(self.peaktree1, self.peaktree2, self.peakerrors, imgdata, tiltdata, transdata, self.params)

	def getParticlePicks(self, imgdata):
		if not self.params['pickrunid']:
			if not self.params['pickrunname']:
				return []
			self.params['pickrunid'] = apParticle.getSelectionRun(imgdata, self.params['pickrunname'])
			#particles = apParticle.getParticlesForImageFromRunName(imgdata, self.params['pickrunname'])
		particles = apParticle.getParticles(imgdata, self.params['pickrunid'])
		targets = self.particlesToTargets(particles)
		apDisplay.printMsg("Found "+str(len(targets))+" particles for image "+apDisplay.short(imgdata['filename']))
		return targets

	def particlesToTargets(self, particles):
		targets = []
		for p in particles:
			targets.append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
		ntargets = numpy.array(targets, dtype=numpy.int32)
		return ntargets

	def parseTiltParams(self):
		theta = self.tiltparams['theta']
		gamma = self.tiltparams['gamma']
		phi   = self.tiltparams['phi']

	def processAndSaveAllImages(self):
		print "Pre-processing images before picking"
		for imgdata in self.imgtree:
			tiltdata = apTiltPair.getTiltPair(imgdata)
			if tiltdata is None:
				#reject it
				apDatabase.insertImgAssessmentStatus(imgdata, "notiltpair", False)
				continue

			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				print "processing: ",apDisplay.short(imgdata['filename'])
				apFindEM.processAndSaveImage(imgdata, params=self.params)
			tiltpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
			if os.path.isfile(tiltpath):
				print "already processed: ",apDisplay.short(tiltdata['filename'])
			else:
				print "processing: ",apDisplay.short(tiltdata['filename'])
				apFindEM.processAndSaveImage(tiltdata, params=self.params)

	def getTiltAssess(self, imgdata, tiltdata):
		ass1 = apDatabase.getImgAssessmentStatus(imgdata)
		ass2 = apDatabase.getImgAssessmentStatus(tiltdata)
		if ass1 is False or ass2 is False:
			return False
		if ass1 is True and ass2 is True:
			return True
		return None

	def runTiltAligner(self, imgdata, tiltdata):
		#reset targets
		self.app.onClearPicks(None)
		self.app.onResetParams(None)
		self.tiltparams = {}

		#set tilt
		tilt1 = apDatabase.getTiltAngleDeg(imgdata)
		tilt2 = apDatabase.getTiltAngleDeg(tiltdata)
		self.app.data['theta'] = tilt1 - tilt2
		#print "theta=",self.app.data['theta']

		#pre-load particle picks
		self.app.picks1 = self.getParticlePicks(imgdata)
		self.app.picks2 = self.getParticlePicks(tiltdata)

		#get image assessment
		self.assess = self.getTiltAssess(imgdata, tiltdata)
		self.assessold = self.assess
		self.app.setAssessStatus()

		#open new file
		imgname = imgdata['filename']+".dwn.mrc"
		imgpath = os.path.join(self.params['rundir'],imgname)
		self.app.panel1.openImageFile(imgpath)

		#open tilt file
		tiltname = tiltdata['filename']+".dwn.mrc"
		tiltpath = os.path.join(self.params['rundir'],tiltname)
		self.app.panel2.openImageFile(tiltpath)

		#run the picker
		self.app.MainLoop()
		self.app.panel1.openImageFile(None)
		self.app.panel2.openImageFile(None)
		# 1. tilt data are copied to self.tiltparams by app
		# 2. particles picks are copied to self.peaks1 and self.peaks2 by app
		# 3. particle errors are copied to self.peakerrors by app
		self.peaktree1 = apPeaks.convertListToPeaks(self.peaks1, self.params)
		self.peaktree2 = apPeaks.convertListToPeaks(self.peaks2, self.params)

if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()



