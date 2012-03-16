#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import re
import time
import glob
import numpy
#appion
from pyami import imagefun
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apDefocalPairs
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apFile
from appionlib import apMask
from appionlib import apBoxer
from appionlib import apSizing

class ParticleExtractLoop(appionLoop2.AppionLoop):
	############################################################
	## Check pixel size
	############################################################
	def checkPixelSize(self):
		# make sure that images all have same pixel size:
		# first get pixel size of first image:
		self.params['apix'] = None
		for imgdata in self.imgtree:
			# get pixel size
			imgname = imgdata['filename']
			if imgname in self.donedict:
				continue
			if self.params['apix'] is None:
				self.params['apix'] = apDatabase.getPixelSize(imgdata)
				apDisplay.printMsg("Stack pixelsize = %.3f A"%(self.params['apix']))
			if apDatabase.getPixelSize(imgdata) != self.params['apix']:
				apDisplay.printMsg("Image pixelsize %.3f A != Stack pixelsize %.3f A"%(apDatabase.getPixelSize(imgdata), self.params['apix']))
				apDisplay.printMsg("Problem image name: %s"%(apDisplay.short(imgdata['filename'])))
				apDisplay.printError("This particle selection run contains images of varying pixelsizes, a stack cannot be created")

	#=======================
	def getParticlesFromStack(self, stackdata,imgdata,is_defocpair=False):
		"""
		For image (or defocal pair), imgdata get particles in corresponding stack
		"""
		if is_defocpair is True:
			sibling, shiftpeak = apDefocalPairs.getShiftFromImage(imgdata, self.params['sessionname'])
			if shiftpeak is None:
				return []
			shiftdata = {'shiftx':shiftpeak['shift'][0], 'shifty':shiftpeak['shift'][1], 'scale':shiftpeak['scalefactor']}
			searchimgdata = sibling
		else:
			searchimgdata = imgdata
			shiftdata = {'shiftx':0, 'shifty':0, 'scale':1}

		partq = appiondata.ApParticleData()
		partq['image'] = searchimgdata

		stackpartq = appiondata.ApStackParticleData()
		stackpartq['stack'] = stackdata
		stackpartq['particle'] = partq
		
		stackpartdatas = stackpartq.query()

		partdatas = []
		for stackpartdata in stackpartdatas:
			partdata = stackpartdata['particle']
			partdatas.append(partdata)
		partdatas.reverse()
		return partdatas, shiftdata

	def getParticlesInImage(self,imgdata):
		if self.params['defocpair'] is True and self.params['selectionid'] is not None:
			# using defocal pairs and particle picks
			partdatas, shiftdata = apParticle.getDefocPairParticles(imgdata, self.params['selectionid'], self.params['particlelabel'])
		elif self.params['fromstackid'] is not None:
			# using previous stack to make a new stack
			fromstackdata = appiondata.ApStackData.direct_query(self.params['fromstackid'])
			partdatas, shiftdata = self.getParticlesFromStack(fromstackdata,imgdata,self.params['defocpair'],)
		else:
			# using particle picks
			partdatas = apParticle.getParticles(imgdata, self.params['selectionid'], self.params['particlelabel'])
			shiftdata = {'shiftx':0, 'shifty':0, 'scale':1}

		apDisplay.printMsg("Found %d particles"%(len(partdatas)))

		### apply correlation limits
		if self.params['correlationmin'] or self.params['correlationmax']:
			partdatas = self.eliminateMinMaxCCParticles(partdatas)

		### apply masks
		if self.params['checkmask']:
			partdatas = self.eliminateMaskedParticles(partdatas, imgdata)
		return partdatas,shiftdata

############################################################
## Rejection Criteria
############################################################

	############################################################
	##  skip image if additional criteria is not met
	############################################################
	def rejectImage(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])

		if self.params['mag']:
			if not apDatabase.checkMag(imgdata, self.params['mag']):
				apDisplay.printColor(shortname+" was not at the specific magnification","cyan")
				return False

		return True

	############################################################
	## get CTF parameters and skip image if criteria is not met
	############################################################

	def checkRequireCtf(self):
			return self.params['ctfcutoff'] or self.params['mindefocus'] or self.params['maxdefocus']

	def checkCtfParams(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata,msg=False,method=self.params['ctfmethod'])

		### check if we have values and if we care
		if ctfvalue is None:
			return not self.checkRequireCtf()

		### check that CTF estimation is above confidence threshold
		if self.params['ctfcutoff'] and conf < self.params['ctfcutoff']:
			#apDisplay.printColor(shortname+" is below CTF threshold (conf="+str(round(conf,3))+")\n","cyan")
			return False

		### get best defocus value
		### defocus should be in negative meters
		if ctfvalue['defocus2'] is not None and ctfvalue['defocus1'] != ctfvalue['defocus2']:
			defocus = (ctfvalue['defocus1'] + ctfvalue['defocus2'])/2.0
		else:
			defocus = ctfvalue['defocus1']
		defocus = -1.0*abs(defocus)	

		### assume defocus values are ALWAYS negative but mindefocus is greater than maxdefocus
		if self.params['mindefocus']:
			self.params['mindefocus'] = -abs( self.params['mindefocus'] )
		if self.params['maxdefocus']:
			self.params['maxdefocus'] = -abs( self.params['maxdefocus'] )
		if self.params['mindefocus'] and self.params['maxdefocus']:
			if self.params['maxdefocus'] > self.params['mindefocus']:
				mindef = self.params['mindefocus']
				maxdef = self.params['maxdefocus']
				self.params['mindefocus'] = maxdef
				self.params['maxdefocus'] = mindef
		### skip micrograph that have defocus above or below min & max defocus levels
		if self.params['mindefocus'] and defocus > self.params['mindefocus']:
			#apDisplay.printColor(shortname+" defocus ("+str(round(defocus*1e6,2))+\
			#	" um) is less than mindefocus ("+str(self.params['mindefocus']*1e6)+" um)\n","cyan")
			return False
		if self.params['maxdefocus'] and defocus < self.params['maxdefocus']:
			#apDisplay.printColor(shortname+" defocus ("+str(round(defocus*1e6,2))+\
			#	" um) is greater than maxdefocus ("+str(self.params['maxdefocus']*1e6)+" um)\n","cyan")
			return False

		return True

	#=======================
	
	#=======================
	def checkDefocus(self, defocus, shortname):
		if defocus > 0:
			apDisplay.printError("defocus is positive "+str(defocus)+" for image "+shortname)
		elif defocus < -1.0e3:
			apDisplay.printError("defocus is very big "+str(defocus)+" for image "+shortname)
		elif defocus > -1.0e-3:
			apDisplay.printError("defocus is very small "+str(defocus)+" for image "+shortname)

	#=======================
	def eliminateMinMaxCCParticles(self, particles):
		newparticles = []
		eliminated = 0
		for prtl in particles:
			if self.params['correlationmin'] and prtl['correlation'] < self.params['correlationmin']:
				eliminated += 1
			elif self.params['correlationmax'] and prtl['correlation'] > self.params['correlationmax']:
				eliminated += 1
			else:
				newparticles.append(prtl)
		if eliminated > 0:
			apDisplay.printMsg(str(eliminated)+" particle(s) eliminated due to min or max correlation cutoff")
		return newparticles

	#=======================
	def eliminateMaskedParticles(self, particles, imgdata):
		newparticles = []
		eliminated = 0
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if self.params['defocpair']:
			imgdata = apDefocalPairs.getTransformedDefocPair(imgdata,2)
		maskimg,maskbin = apMask.makeInspectedMask(sessiondata,self.params['maskassess'],imgdata)
		if maskimg is not None:
			for prtl in particles:
				binnedcoord = (int(prtl['ycoord']/maskbin),int(prtl['xcoord']/maskbin))
				if maskimg[binnedcoord] != 0:
					eliminated += 1
				else:
					newparticles.append(prtl)
			apDisplay.printMsg("%i particle(s) eliminated due to masking"%eliminated)
		else:
			apDisplay.printMsg("no masking")
			newparticles = particles
		return newparticles

	############################################################
	## Common parameters
	############################################################

	#=======================
	def setupParserOptions(self):
		self.ctfestopts = ('ace2', 'ctffind')

		### values
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin the particles after extracting", metavar="#")
		self.parser.add_option("--ctfcutoff", dest="ctfcutoff", type="float",
			help="CTF cut off")
		self.parser.add_option("--mincc", dest="correlationmin", type="float",
			help="particle correlation mininum")
		self.parser.add_option("--maxcc", dest="correlationmax", type="float",
			help="particle correlation maximum")
		self.parser.add_option("--mindef", dest="mindefocus", type="float",
			help="minimum defocus")
		self.parser.add_option("--maxdef", dest="maxdefocus", type="float",
			help="maximum defocus")
		self.parser.add_option("--selectionid", dest="selectionid", type="int",
			help="particle picking runid")
		self.parser.add_option("--fromstackid", dest="fromstackid", type="int",
			help="redo a stack from a previous stack")
		self.parser.add_option("--partlimit", dest="partlimit", type="int",
			help="particle limit")
		self.parser.add_option("--mag", dest="mag", type="int",
			help="process only images of magification, mag")
		self.parser.add_option("--maskassess", dest="maskassess",
			help="Assessed mask run name")
		self.parser.add_option("--label", dest="particlelabel", type="str", default=None,
			help="select particles by label within the same run name")
		self.parser.add_option("--ddstartframe", dest="startframe", type="int", default=1,
			help="starting frame for direct detector raw frame processing")
		self.parser.add_option("--ddnframe", dest="nframe", type="int", default=0,
			help="total frames to sum up for direct detector raw frame processing")

		### true/false
		self.parser.add_option("--defocpair", dest="defocpair", default=False,
			action="store_true", help="select defocal pair")

		self.parser.add_option("--checkmask", dest="checkmask", default=False,
			action="store_true", help="Check masks")
		self.parser.add_option("--keepall", dest="keepall", default=False,
			action="store_true", help="Do not delete CTF corrected MRC files when finishing")

		### option based
		self.parser.add_option("--ctfmethod", dest="ctfmethod",
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)

	#=======================
	def checkConflicts(self):
		if self.params['description'] is None:
			apDisplay.printError("A description has to be specified")
		if (self.params['mindefocus'] is not None and
				(self.params['mindefocus'] < -1e-3 or self.params['mindefocus'] > -1e-9)):
			apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=-1.5e-6")
		if (self.params['maxdefocus'] is not None and
				(self.params['maxdefocus'] < -1e-3 or self.params['maxdefocus'] > -1e-9)):
			apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=-1.5e-6")
		if self.params['fromstackid'] is not None and self.params['selectionid'] is not None:
			apDisplay.printError("please only specify one of either --selectionid or --fromstackid")
		if self.params['fromstackid'] is None and self.params['selectionid'] is None:
			apDisplay.printError("please specify one of either --selectionid or --fromstackid")
		if self.params['maskassess'] is None and self.params['checkmask']:
			apDisplay.printError("particle mask assessment run need to be defined to check mask")
		if self.params['maskassess'] is not None and not self.params['checkmask']:
			apDisplay.printMsg("running mask assess")
			self.params['checkmask'] = True

	#=======================
	def preLoopFunctions(self):
		self.batchboxertimes = []
		self.ctftimes = []
		self.mergestacktimes = []
		self.meanreadtimes = []
		self.insertdbtimes = []
		self.noimages = False
		self.totalpart = 0
		if len(self.imgtree) == 0:
			apDisplay.printWarning("No images were found to process")
			self.noimages = True
			return
		self.selectiondata = None
		if self.params['selectionid'] is not None:
			self.selectiondata = apParticle.getSelectionRunDataFromID(self.params['selectionid'])
			if self.params['particlelabel'] == 'fromtrace':
				if (not self.selectiondata['manparams'] or not self.selectiondata['manparams']['trace']):
				apDisplay.printError("Can not use traced object center to extract boxed area without tracing")
				else:
					self.params['particlelabel'] = '_trace'
		self.checkPixelSize()
		self.existingParticleNumber=0
		self.setStartingParticleNumber()
		apDisplay.printMsg("Starting at particle number: "+str(self.particleNumber))

		if self.params['partlimit'] is not None and self.particleNumber > self.params['partlimit']:
			apDisplay.printError("Number of particles in existing stack already exceeds limit!")
		self.logpeaks = 2

	def setStartingParticleNumber(self):
		self.particleNumber = self.existingParticleNumber

	def convertTraceToParticlePeaks(self,imgdata):
		apSizing.makeParticleFromContour(imgdata,self.selectiondata,'_trace')
		
	#=====================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		# check to see if image is rejected by other criteria
		if self.rejectImage(imgdata) is False:
			return False
		# check CTF parameters for image and skip if criteria is not met
		if self.checkCtfParams(imgdata) is False:
			return False
		return None


	#=======================
	def processImage(self, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgdata['filename'])


		### first remove any existing boxed files
		shortfileroot = os.path.join(self.params['rundir'], shortname)
		rmfiles = glob.glob(shortfileroot+"*")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

		### convert contours to particles
		print self.params['particlelabel']
		if self.selectiondata and self.params['particlelabel'] == '_trace':
			self.convertTraceToParticlePeaks(imgdata)

		### get particles
		partdatas,shiftdata = self.getParticlesInImage(imgdata)

		### check if we have particles
		if len(partdatas) == 0:
			apDisplay.printColor(shortname+" has no remaining particles and has been rejected\n","cyan")
			total_processed_particles = None
		else:
			### process partdatas
			total_processed_particles = self.processParticles(imgdata,partdatas,shiftdata)

		if total_processed_particles is None:
			self.totalpart = len(partdatas)+self.totalpart
		else:
			self.totalpart = total_processed_particles
		### check if particle limit is met
		if self.params['partlimit'] is not None and self.totalpart > self.params['partlimit']:
			apDisplay.printWarning("reached particle number limit of "+str(self.params['partlimit'])+" now stopping")
			self.imgtree = []
			self.notdone = False


	def processParticles(self,imgdata,partdatas,shiftdata):
		"""
		this is the main component
		it should return the total number of processed particles if available otherwise, it returns None
		"""
		raise NotImplementedError()

	#=======================
	def loopCleanUp(self,imgdata):
		### last remove any existing boxed files, reset global params
		shortname = apDisplay.short(imgdata['filename'])
		shortfileroot = os.path.join(self.params['rundir'], shortname)
		rmfiles = glob.glob(shortfileroot+"*")
		if not self.params['keepall']:
			for rmfile in rmfiles:
				apFile.removeFile(rmfile)

############################################################################
# PaeticleExtract with Elimination of boxed particle cropped by the image
############################################################################
class ParticleBoxLoop(ParticleExtractLoop):
	def setupParserOptions(self):
		super(ParticleBoxLoop,self).setupParserOptions()
		self.parser.add_option("--boxsize", dest="boxsize", type="int",
			help="particle box size in pixel")
		self.parser.add_option("--rotate", dest="rotate", default=False,
			action="store_true", help="Apply rotation angles of ,for example, helix")

	def checkConflicts(self):
		super(ParticleBoxLoop,self).checkConflicts()
		if self.params['boxsize'] is None:
			apDisplay.printError("A boxsize has to be specified")

	def preLoopFunctions(self):
		super(ParticleBoxLoop,self).preLoopFunctions()
		self.boxsize = int(self.params['boxsize'])
		if self.params['rotate'] is True:
			### with rotate we use a bigger boxsize
			self.half_box = int(1.5*self.boxsize/2)
		else:
			self.half_box = int(math.floor(self.boxsize / 2.0))

	def getParticlesInImage(self,imgdata):
		partdatas,shiftdata = super(ParticleBoxLoop,self).getParticlesInImage(imgdata)
		imgdims = imgdata['camera']['dimension']
		newpartdatas = []
		for partdata in partdatas:
			start_x,start_y = apBoxer.getBoxStartPosition(imgdata,self.half_box,partdata, shiftdata)
			if apBoxer.checkBoxInImage(imgdims,start_x,start_y,self.boxsize):
				newpartdatas.append(partdata)
		return newpartdatas,shiftdata

class Test(ParticleExtractLoop):
	def processParticles(self,imgdata,partdatas,shiftdata):
		for partdata in partdatas:
			print partdata['xcoord'],partdata['ycoord']
		return None

	def commitToDatabase(self,imgdata):
		pass

if __name__ == '__main__':
	makeStack = Test()
	makeStack.run()



