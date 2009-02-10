#!/usr/bin/env python

import os
import sys
import time
import wx
import numpy
import threading
import particleLoop2
import apFindEM
import appionData
import apDatabase
import apDisplay
import apParticle
import apPeaks
import apImage
import apParam
import ApTiltPicker
from apTilt import apTiltTransform, apTiltPair, autotilt

##################################
##
##################################

class tiltAligner(particleLoop2.ParticleLoop):
	#####################################################
	##### START PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	#####################################################

	#=======================================
	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	#=======================================
	def preLoopFunctions(self):
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()
		self.app = ApTiltPicker.PickerApp(mode='loop')
		self.app.appionloop = self
		self.theta = 0.0
		self.params['pickdatadir'] = os.path.join(self.params['rundir'],"pickdata")
		apParam.createDirectory(self.params['pickdatadir'], warning=False)

	#=======================================
	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	#=======================================
	def setupParserOptions(self):
		### Input value options
		self.outtypes = ('spider','text','pickle','xml')
		self.parser.add_option("--outtype", dest="outtype",
			default="spider", type="choice", choices=self.outtypes,
			help="file output type: "+str(self.outtypes), metavar="TYPE")
		self.parser.add_option("--pickrunids", dest="pickrunids",
			help="selection run ids for previous automated picking run", metavar="#,#,#")
		self.parser.add_option("--no-autopick", dest="autopick", default=True,
			action="store_false", help="Do NOT auto pick images")

	#=======================================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(self.outtypes):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: "+str(self.outtypes)+"; NOT "+str(self.params['outtype']))
		return

	#=======================================
	def getParticleParamsData(self):
		tiltparamsq = appionData.ApTiltAlignParamsData()
		tiltparamsq['output_type'] = self.params['outtype']
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			tiltparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunidlist'][0])
		return tiltparamsq

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	#=======================================
	def loopProcessImage(self, imgdata):
		"""
		Over-writes the particleLoop processImage and uses the appionLoop processImage
		"""
		#GET THE TILT PAIR
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			return

		if self.params['sessionname'] is None:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
			apFindEM.processAndSaveImage(tiltdata, params=self.params)

		#RUN THE ALIGNER GUI
		self.runTiltAligner(imgdata, tiltdata)
		numpeaks = len(self.peaktree1)
		#apDisplay.printMsg("Found "+str(numpeaks)+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = numpeaks

		procimgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
		if os.path.isfile(procimgpath):
			#apDisplay.printMsg("reading processing mrc for reg")
			procimg1 = apImage.mrcToArray(procimgpath, msg=False)
		procimgpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
		if os.path.isfile(procimgpath):
			#apDisplay.printMsg("reading processing mrc for tilt")
			procimg2 = apImage.mrcToArray(procimgpath, msg=False)
		procimg1, procimg2 = apTiltTransform.maskOverlapRegion(procimg1, procimg2, self.appdata)

		#CREATE PEAK JPEG
		if self.threadJpeg is True:
			threading.Thread(target=apPeaks.createTiltedPeakJpeg, args=(imgdata, tiltdata, self.peaktree1,
				self.peaktree2, self.params, procimg1, procimg2)).start()
		else:
			apPeaks.createTiltedPeakJpeg(imgdata, tiltdata, self.peaktree1, self.peaktree2, self.params,
				procimg1, procimg2)

		#EXTRA DONE DICT CALL
		self._writeDoneDict(tiltdata['filename'])

	#=======================================
	def loopCommitToDatabase(self, imgdata):
		"""
		Over-writes the particleLoop commit and uses the appionLoop commit
		"""
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			apDisplay.printWarning("Tilt data not found; not commiting data")
			return False

		### insert the runid
		self.commitRunToDatabase(imgdata['session'], True)

		if self.assess is not None:
			#note runid is overrided to be 'run1'
			apDatabase.insertImgAssessmentStatus(imgdata, self.params['runname'], self.assess)
			apDatabase.insertImgAssessmentStatus(tiltdata, self.params['runname'], self.assess)

		if len(self.peaktree1) < 3 or len(self.peaktree1) < 3:
			apDisplay.printWarning("Not enough particle picks; not commiting transform or particle data")
			return False

		### insert the transform
		transdata = apTiltPair.insertTiltTransform(imgdata, tiltdata, self.tiltparams, self.params)
		### insert the particles
		self.insertParticlePeakPairs(imgdata, tiltdata, transdata)
		### insert image assessment


	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

	#=======================================
	def insertParticlePeakPairs(self, imgdata, tiltdata, transdata):
		if transdata is not None:
			apParticle.insertParticlePeakPairs(self.peaktree1, self.peaktree2, self.peakerrors, imgdata, tiltdata, transdata, self.params)

	#=======================================
	def getParticlePicks(self, imgdata, msg=True):
		particles = []
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			for pickrunid in self.params['pickrunidlist']:
				#print pickrunid
				newparticles = apParticle.getParticles(imgdata, pickrunid)
				#apDisplay.printMsg("Found "+str(len(newparticles))+" particles for image "+apDisplay.short(imgdata['filename']))
				particles.extend(newparticles)
		targets = self.particlesToTargets(particles)
		if msg is True:
			apDisplay.printMsg("Found "+str(len(targets))+" particles for image "+apDisplay.short(imgdata['filename']))
		return targets

	#=======================================
	def particlesToTargets(self, particles):
		targets = []
		for p in particles:
			targets.append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
		ntargets = numpy.array(targets, dtype=numpy.int32)
		return ntargets

	#=======================================
	def parseTiltParams(self):
		theta = self.tiltparams['theta']
		gamma = self.tiltparams['gamma']
		phi   = self.tiltparams['phi']

	#=======================================
	def getExtension(self):
		if self.params['outtype'] == "text":
			return "txt"
		elif self.params['outtype'] == "xml":
			return "xml"
		elif self.params['outtype'] == "pickle":
			return "pickle"
		else:
			return "spi"

	#=======================================
	def processAndSaveAllImages(self):
		print "Pre-processing images before picking\nNow is a good time to go get a candy bar"
		count = 0
		total = len(self.imgtree)
		for imgdata in self.imgtree:
			count += 1
			tiltdata = apTiltPair.getTiltPair(imgdata)
			if tiltdata is None:
				#reject it
				apDatabase.insertImgAssessmentStatus(imgdata, "notiltpair", False)
				continue

			#First the image
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				sys.stderr.write("#")
				#print "processing: ",apDisplay.short(imgdata['filename'])
				apFindEM.processAndSaveImage(imgdata, params=self.params)

			#Now for its tilt pair
			tiltpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
			if os.path.isfile(tiltpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(tiltdata['filename'])
			else:
				sys.stderr.write("#")
				#print "processing: ",apDisplay.short(tiltdata['filename'])
				apFindEM.processAndSaveImage(tiltdata, params=self.params)

			if count % 30 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

			### check if automation was already run
			outfile = os.path.basename(imgdata['filename'])+".dwn.mrc"+"."+self.getExtension()
			if os.path.isfile(outfile):
				sys.stderr.write(",")
			else:
				### set important parameters
				picks1 =  self.getParticlePicks(imgdata, False)
				picks2 =  self.getParticlePicks(tiltdata, False)
				pixdiam = self.params['diam']/self.params['apix']/self.params['bin']
				tilt1 = apDatabase.getTiltAngleDeg(imgdata)
				tilt2 = apDatabase.getTiltAngleDeg(tiltdata)
				tiltdiff = abs(tilt2) - abs(tilt1)
				tiltaxis = -7.2
				### run tilt automation
				if len(picks1) > 0 and len(picks2) > 0 and self.params['autopick'] is True:
					autotilter = autotilt.autoTilt()
					result = autotilter.processTiltPair(imgpath, tiltpath, picks1, picks2, tiltdiff, outfile, pixdiam, tiltaxis, msg=False)
				sys.stderr.write("%")
			apDisplay.printMsg("done") 
		return

	#=======================================
	def getTiltAssess(self, imgdata, tiltdata):
		ass1 = apDatabase.getImgCompleteStatus(imgdata)
		ass2 = apDatabase.getImgCompleteStatus(tiltdata)
		if ass1 is False or ass2 is False:
			return False
		if ass1 is True and ass2 is True:
			return True
		return None

	#=======================================
	def runTiltAligner(self, imgdata, tiltdata):
		#reset targets
		self.app.onClearPicks(None)
		self.app.onResetParams(None)
		self.tiltparams = {}

		#set tilt
		tilt1 = apDatabase.getTiltAngleDeg(imgdata)
		tilt2 = apDatabase.getTiltAngleDeg(tiltdata)
		self.theta = abs(tilt2) - abs(tilt1)
		self.app.data['theta'] = self.theta
		self.app.data['filetypeindex'] = self.params['outtypeindex']
		self.app.data['outfile'] = os.path.basename(imgdata['filename'])+".dwn.mrc"+"."+self.app.getExtension()
		self.app.data['dirname'] = self.params['pickdatadir']
		self.app.data['image1file'] = apDisplay.short(imgdata['filename'])
		self.app.data['image2file'] = apDisplay.short(tiltdata['filename'])
		self.app.data['pixdiam'] = self.params['diam']/self.params['apix']/self.params['bin']
		print "pixdiam=", self.app.data['pixdiam']
		#print "theta=",self.app.data['theta']

		#pre-load particle picks
		self.app.picks1 = self.getParticlePicks(imgdata)
		self.app.picks2 = self.getParticlePicks(tiltdata)

		#set image assessment
		self.assess = self.getTiltAssess(imgdata, tiltdata)
		self.assessold = self.assess
		self.app.setAssessStatus()

		#open image file 1
		imgname = imgdata['filename']+".dwn.mrc"
		imgpath = os.path.join(self.params['rundir'],imgname)
		self.app.panel1.openImageFile(imgpath)

		#open tilt file 2
		tiltname = tiltdata['filename']+".dwn.mrc"
		tiltpath = os.path.join(self.params['rundir'],tiltname)
		self.app.panel2.openImageFile(tiltpath)

		#guess the shift
		outfile = self.app.data['outfile']
		if not os.path.isfile(outfile):
			if len(self.app.picks1) > 0 and len(self.app.picks2) > 0 and self.params['autopick'] is True:
				self.app.onGuessShift(None)
		else:
			self.app.readData(outfile)
			self.app.onAutoOptim(None)
		time.sleep(0.1)

		#run the picker
		self.app.MainLoop()

		#########################################
		# RESULTS
		#########################################

		self.app.panel1.openImageFile(None)
		self.app.panel2.openImageFile(None)

		# 1. tilt data are copied to self.tiltparams by app
		# 2. particles picks are copied to self.peaks1 and self.peaks2 by app
		# 3. particle errors are copied to self.peakerrors by app
		# 4. assessment status is  copied to self.assess
		self.appdata = self.app.data
		self.peaktree1 = apPeaks.convertListToPeaks(self.peaks1, self.params)
		self.peaktree2 = apPeaks.convertListToPeaks(self.peaks2, self.params)

if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()



