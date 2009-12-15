#!/usr/bin/env python

### python
import os
import sys
import time
import threading
import numpy
### appion
import particleLoop2
import apFindEM
import apParam
import appiondata
import apDatabase
import apDisplay
import apParticle
import apPeaks
import apImage
from apTilt import apTiltTransform, apTiltPair, autotilt, tiltfile

##################################
##
##################################

class tiltAligner(particleLoop2.ParticleLoop):
	#####################################################
	##### START PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	#####################################################

	#---------------------------------------
	#---------------------------------------
	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	#---------------------------------------
	#---------------------------------------
	def preLoopFunctions(self):
		self.data = {}
		#if self.params['sessionname'] is not None:
		#	self.processAndSaveAllImages()
		self.params['pickdatadir'] = os.path.join(self.params['rundir'], "outfiles")
		apParam.createDirectory(self.params['pickdatadir'], warning=False)

	#---------------------------------------
	#---------------------------------------
	def setupParserOptions(self):
		### Input value options
		self.outtypes = ['text','xml','spider','pickle']
		self.parser.add_option("--outtype", dest="outtype", default="spider",
			help="file output type: "+str(self.outtypes), metavar="TYPE")
		self.parser.add_option("--pickrunids", dest="pickrunids",
			help="selection run ids for previous automated picking run", metavar="#,#,#")
		self.parser.add_option("--pickrunname", dest="pickrunname", type="int",
			help="previous selection run name, e.g. --pickrunname=dogrun1", metavar="NAME")

	#---------------------------------------
	#---------------------------------------
	def getExtension(self):
		if self.params['outtype'] == "text":
			return "txt"
		elif self.params['outtype'] == "xml":
			return "xml"
		elif self.params['outtype'] == "pickle":
			return "pickle"
		else:
			return "spi"

	#---------------------------------------
	#---------------------------------------
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(self.outtypes):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: "+str(self.outtypes)+"; NOT "+str(self.params['outtype']))
		if self.params['pickrunids'] is None:
			apDisplay.printError("you must select a previous particle picking run to use auto tilt picker")
		return

	#---------------------------------------
	#---------------------------------------
	def getParticleParamsData(self):
		tiltparamsq = appiondata.ApTiltAlignParamsData()
		tiltparamsq['output_type'] = self.params['outtype']
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			tiltparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunidlist'][0])
		return tiltparamsq

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	#---------------------------------------
	#---------------------------------------
	def loopProcessImage(self, imgdata):
		"""
		Over-writes the particleLoop processImage and uses the appionLoop processImage
		"""
		#GET THE TILT PAIR
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			return

		### process images
		procimgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
		if not os.path.isfile(procimgpath):
			apDisplay.printMsg("processing mrc for first image")
			apFindEM.processAndSaveImage(imgdata, params=self.params)
		procimg1 = apImage.mrcToArray(procimgpath, msg=False)

		procimgpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
		if not os.path.isfile(procimgpath):
			apDisplay.printMsg("processing mrc for second image")
			apFindEM.processAndSaveImage(tiltdata, params=self.params)
		procimg2 = apImage.mrcToArray(procimgpath, msg=False)

		#RUN THE ALIGNER GUI
		result = self.runTiltAligner(imgdata, tiltdata)
		if self.badprocess is True:
			return
		numpeaks = len(self.peaktree1)
		#apDisplay.printMsg("Found "+str(numpeaks)+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = numpeaks

		### mask the images
		procimg1, procimg2 = apTiltTransform.maskOverlapRegion(procimg1, procimg2, self.data)

		#CREATE PEAK JPEG
		if self.threadJpeg is True:
			threading.Thread(target=apPeaks.createTiltedPeakJpeg, args=(imgdata, tiltdata, self.peaktree1,
				self.peaktree2, self.params, procimg1, procimg2)).start()
		else:
			apPeaks.createTiltedPeakJpeg(imgdata, tiltdata, self.peaktree1, self.peaktree2, self.params,
				procimg1, procimg2)

		#EXTRA DONE DICT CALL
		self._writeDoneDict(tiltdata['filename'])

	#---------------------------------------
	#---------------------------------------
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

		if len(self.peaktree1) < 3 or len(self.peaktree2) < 3:
			apDisplay.printWarning("Not enough particle picks; not commiting transform or particle data")
			return False

		### insert the transform
		transdata = apTiltPair.insertTiltTransform(imgdata, tiltdata, self.data, self.params)
		### insert the particles

		self.insertParticlePeakPairs(imgdata, tiltdata, transdata)
		### insert image assessment


	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

	#---------------------------------------
	#---------------------------------------
	def insertParticlePeakPairs(self, imgdata, tiltdata, transdata):
		if transdata is not None:
			apDisplay.printMsg("insertParticlePeakPairs")
			apParticle.insertParticlePeakPairs(self.peaktree1, self.peaktree2, self.peakerrors,
				imgdata, tiltdata, transdata, self.params['runname'])
			apDisplay.printMsg("done")

	#---------------------------------------
	#---------------------------------------
	def getParticlePicks(self, imgdata):
		particles = []
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			for pickrunid in self.params['pickrunidlist']:
				newparticles = apParticle.getParticles(imgdata, pickrunid)
				particles.extend(newparticles)
		targets = self.particlesToTargets(particles)
		#apDisplay.printMsg("Found "+str(len(targets))+" particles for image "+apDisplay.short(imgdata['filename']))
		return targets

	#---------------------------------------
	#---------------------------------------
	def particlesToTargets(self, particles):
		targets = []
		for p in particles:
			targets.append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
		ntargets = numpy.array(targets, dtype=numpy.int32)
		return ntargets

	#---------------------------------------
	#---------------------------------------
	def parseTiltParams(self):
		theta = self.tiltparams['theta']
		gamma = self.tiltparams['gamma']
		phi   = self.tiltparams['phi']

	#---------------------------------------
	#---------------------------------------
	def getTiltAssess(self, imgdata, tiltdata):
		ass1 = apDatabase.getImgCompleteStatus(imgdata)
		ass2 = apDatabase.getImgCompleteStatus(tiltdata)
		if ass1 is False or ass2 is False:
			return False
		if ass1 is True and ass2 is True:
			return True
		return None

	#---------------------------------------
	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		if filename[-4:] == '.spi':
			array = apImage.spiderToArray(filename, msg=False)
			return array
		elif filename[-4:] == '.mrc':
			array = apImage.mrcToArray(filename, msg=False)
			return array
		else:
			image = Image.open(filename)
			array = apImage.imageToArray(image, msg=False)
			array = array.astype(numpy.float32)
			return array
		return None

	#---------------------------------------
	#---------------------------------------
	def getOverlap(self, imgfile1, imgfile2, msg=True):
		t0 = time.time()
		image1 = self.openImageFile(imgfile1)
		image2 = self.openImageFile(imgfile2)
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		if msg is True:
			apDisplay.printMsg("Found overlaps of "+overlapStr+" in "+apDisplay.timeString(time.time()-t0))
		self.data['overlap'] = bestOverlap
		return

	#---------------------------------------
	#---------------------------------------
	def getRmsdArray(self):
		targets1 = self.currentpicks1
		aligned1 = self.getAlignedArray2()
		if len(targets1) != len(aligned1):
			targets1 = numpy.vstack((targets1, aligned1[len(targets1):]))
			aligned1 = numpy.vstack((aligned1, targets1[len(aligned1):]))
		diffmat1 = (targets1 - aligned1)
		sqsum1 = diffmat1[:,0]**2 + diffmat1[:,1]**2
		rmsd1 = numpy.sqrt(sqsum1)
		self.data['rmsd'] = rmsd1.mean()
		return rmsd1

	#---------------------------------------
	#---------------------------------------
	def getAlignedArray2(self):
		apTiltTransform.setPointsFromArrays(self.currentpicks1, self.currentpicks2, self.data)
		a2b = apTiltTransform.a2Toa1Data(self.currentpicks2, self.data)
		return a2b

	#---------------------------------------
	#---------------------------------------
	def runTiltAligner(self, imgdata, tiltdata):
		### set tilt
		tilt1 = apDatabase.getTiltAngleDeg(imgdata)
		tilt2 = apDatabase.getTiltAngleDeg(tiltdata)
		theta = abs(tilt2) - abs(tilt1)

		### pre-load particle picks
		picks1 = self.getParticlePicks(imgdata)
		picks2 = self.getParticlePicks(tiltdata)
		if len(picks1) < 10 or len(picks2) < 10:
			apDisplay.printWarning("Not enough particles ot run program on image pair")
			self.badprocess = True
			return

		### set image file 1
		imgname  = imgdata['filename']+".dwn.mrc"
		imgpath  = os.path.join(self.params['rundir'], imgname)

		### set tilt file 2
		tiltname = tiltdata['filename']+".dwn.mrc"
		tiltpath = os.path.join(self.params['rundir'], tiltname)

		### set out file
		outname1 = os.path.basename(imgdata['filename'])+"."+self.getExtension()
		outfile1 = os.path.join(self.params['pickdatadir'], outname1)
		outname2 = os.path.basename(tiltdata['filename'])+"."+self.getExtension()
		outfile2 = os.path.join(self.params['pickdatadir'], outname1)

		pixdiam = self.params['diam']/self.params['apix']/self.params['bin']

		### run tilt automation
		autotilter = autotilt.autoTilt()
		result = autotilter.processTiltPair(imgpath, tiltpath, picks1, picks2, theta, outfile1, pixdiam)
		if result is None:
			apDisplay.printWarning("Image processing failed")
			self.badprocess = True
			return

		if os.path.isfile(outfile1) and outfile1 != outfile2:
			if os.path.exists(outfile2):
				os.remove(outfile2)
			os.symlink(os.path.basename(outfile1), outfile2)

		### read alignment results
		if not os.path.isfile(outfile1):
			apDisplay.printWarning("Image processing failed")
			self.badprocess = True
			return
		self.data = tiltfile.readData(outfile1)
		self.currentpicks1 = numpy.asarray(self.data['picks1'])
		self.currentpicks2 = numpy.asarray(self.data['picks2'])

		#print self.data
		# 1. tilt data are copied to self.tiltparams by app
		# 2. particles picks are copied to self.peaks1 and self.peaks2 by app
		# 3. particle errors are copied to self.peakerrors by app
		# 4. assessment status is  copied to self.assess
		self.peaktree1 = apPeaks.convertListToPeaks(self.currentpicks1, self.params)
		self.peaktree2 = apPeaks.convertListToPeaks(self.currentpicks2, self.params)
		self.peakerrors = self.getRmsdArray()
		self.getOverlap(imgpath, tiltpath)

#---------------------------------------
#---------------------------------------
#---------------------------------------
#---------------------------------------
if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()




