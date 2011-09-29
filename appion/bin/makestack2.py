#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import re
import time
import glob
import socket
import numpy
import subprocess
from scipy import stats
from scipy import ndimage
#appion
from pyami import imagefun
from appionlib import appionLoop2
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apStack
from appionlib import apDefocalPairs
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apStackMeanPlot
from appionlib import apEMAN
from appionlib import apProject
from appionlib import apPrimeFactor
from appionlib import apFile
from appionlib import apParam
from appionlib import apImagicFile
from appionlib import apMask
from appionlib import apXmipp
from appionlib import apBoxer
from appionlib.apSpider import filters

class Makestack2Loop(appionLoop2.AppionLoop):
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

	############################################################
	## Retrive existing stack info
	############################################################
	def getExistingStackInfo(self):
		stackfile=os.path.join(self.params['rundir'], self.params['single'])
		stackid = apStack.getStackIdFromPath(stackfile)
		numdbpart = len(apStack.getStackParticlesFromId(stackid))

		if numdbpart == 0:
			self.params['continue'] = False
			apDisplay.printWarning("file exists but no particles in database, deleting stack file")
			apFile.removeStack(stackfile)
			return 0

		### we now have particles in the database
		if self.params['continue'] is False:
			apDisplay.printWarning("particles exist in database, must force continue")
			self.params['continue'] = True

		### we better have the same number of particles in the file and the database
		numfilepart = apFile.numImagesInStack(stackfile)
		if numfilepart != numdbpart:
			apDisplay.printError("database and file have different number of particles, create a new stack this one is corrupt")

		return numfilepart


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
	def checkCtfParams(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata,msg=False,method=self.params['ctfmethod'])

		### check if we have values and if we care
		if ctfvalue is None:
			if self.params['ctfcutoff'] or self.params['mindefocus'] or self.params['maxdefocus'] or self.params['phaseflipped']:
				#apDisplay.printColor(shortname+" was rejected because it has no CTF values\n","cyan")
				return False
			else:
				#apDisplay.printWarning(shortname+" has no CTF values")
				return True

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
	def getParticlesFromStack(self, imgdata):
		"""
		For image (or defocal pair), imgdata get particles in corresponding stack
		"""
		if self.params['defocpair'] is True:
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
		stackpartq['stack'] = appiondata.ApStackData.direct_query(self.params['fromstackid'])
		stackpartq['particle'] = partq
		
		stackpartdatas = stackpartq.query()

		partdatas = []
		for stackpartdata in stackpartdatas:
			partdata = stackpartdata['particle']
			partdatas.append(partdata)
		partdatas.reverse()
		return partdatas, shiftdata

	#=======================
	def boxParticlesFromImage(self, imgdata):
		shortname = apDisplay.short(imgdata['filename'])
		if self.params['nframe'] == 0:
			imgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
		else:
			self.params['uncorrected'] = True

		### get the particle before image filtering
		if self.params['defocpair'] is True and self.params['selectionid'] is not None:
			# using defocal pairs and particle picks
			partdatas, shiftdata = apParticle.getDefocPairParticles(imgdata, self.params['selectionid'], self.params['particlelabel'])
		elif self.params['fromstackid'] is not None:
			# using previous stack to make a new stack
			partdatas, shiftdata = self.getParticlesFromStack(imgdata)
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

		### check if we have particles
		if len(partdatas) == 0:
			apDisplay.printColor(shortname+" has no remaining particles and has been rejected\n","cyan")
			return None, None, None

		### convert database particle data to coordinates and write boxfile
		boxfile = os.path.join(self.params['rundir'], imgdata['filename']+".box")
		parttree, boxedpartdatas = apBoxer.processParticleData(imgdata, self.params['boxsize'], 
			partdatas, shiftdata, boxfile, rotate=self.params['rotate'])

		if self.params['boxfiles']:
			### quit and return, boxfile created, now process next image
			return None, None, None

		### check if we have particles again
		if len(partdatas) == 0 or len(parttree) == 0:
			apDisplay.printColor(shortname+" has no remaining particles and has been rejected\n","cyan")
			return None, None, None

		if self.params['uncorrected']:
			### dark/bright correct image
			tmpname = shortname+"-darknorm.dwn.mrc"
			imgarray = apImage.correctImage(imgdata, self.params['sessionname'],self.params['startframe'],self.params['nframe'])
			imgpath = os.path.join(self.params['rundir'], tmpname)
			apImage.arrayToMrc(imgarray,imgpath)
			print "processing", imgpath

		t0 = time.time()
		if self.params['phaseflipped'] is True:
			if self.params['fliptype'] == 'emanimage':
				### ctf correct whole image using EMAN
				imgpath = self.phaseFlipWholeImage(imgpath, imgdata)
				self.ctftimes.append(time.time()-t0)
			elif self.params['fliptype'] == "spiderimage":
				imgpath = self.phaseFlipSpider(imgpath,imgdata)
				self.ctftimes.append(time.time()-t0)
			elif self.params['fliptype'][:9] == "ace2image":
				### ctf correct whole image using Ace 2
				imgpath = self.phaseFlipAceTwo(imgpath, imgdata)
				self.ctftimes.append(time.time()-t0)
		if imgpath is None:
			return None, None, None

		### run batchboxer command
		imgstackfile = os.path.join(self.params['rundir'], shortname+".hed")
		#emancmd = ("batchboxer input=%s dbbox=%s output=%s newsize=%i" 
		#	%(imgpath, emanboxfile, imgstackfile, self.params['boxsize']))
		apDisplay.printMsg("boxing "+str(len(parttree))+" particles into temp file: "+imgstackfile)
		t0 = time.time()
		if self.params['rotate'] is True:
			apBoxer.boxerRotate(imgpath, parttree, imgstackfile, self.params['boxsize'])
		else:
			apBoxer.boxer(imgpath, parttree, imgstackfile, self.params['boxsize'])
		self.batchboxertimes.append(time.time()-t0)

		### read mean and stdev
		partmeantree = []
		t0 = time.time()
		imagicdata = apImagicFile.readImagic(imgstackfile)
		### loop over the particles and read data
		for i in range(len(boxedpartdatas)):
			partdata = boxedpartdatas[i]
			partarray = imagicdata['images'][i]
			
			### if particle stdev == 0, then it is all constant, i.e., a bad particle
			stdev = float(partarray.std())
			if stdev < 1.0e-6:
				apDisplay.printError("Standard deviation == 0 for particle %d in image %s"%(i,shortname))

			### skew and kurtosis
			partravel = numpy.ravel(partarray)
			skew = float(stats.skew(partravel))
			kurtosis = float(stats.kurtosis(partravel))

			### edge and center stats
			edgemean = float(ndimage.mean(partarray, self.edgemap, 1.0))
			edgestdev = float(ndimage.standard_deviation(partarray, self.edgemap, 1.0))
			centermean = float(ndimage.mean(partarray, self.edgemap, 0.0))
			centerstdev = float(ndimage.standard_deviation(partarray, self.edgemap, 0.0))

			### take abs of all means, because ctf whole image may become negative
			partmeandict = {
				'partdata': partdata,
				'mean': abs(float(partarray.mean())),
				'stdev': stdev,
				'min': float(partarray.min()),
				'max': float(partarray.max()),
				'skew': skew,
				'kurtosis': kurtosis,
				'edgemean': abs(edgemean),
				'edgestdev': edgestdev,
				'centermean': abs(centermean),
				'centerstdev': centerstdev,
			}
			### show stats for first particle
			"""
			if i == 0:
				keys = partmeandict.keys()
				keys.sort()
				mystr = "PART STATS: "
				for key in keys:
					if isinstance(partmeandict[key], float):
						mystr += "%s=%.3f :: "%(key, partmeandict[key])
				print mystr
			"""
			partmeantree.append(partmeandict)
		self.meanreadtimes.append(time.time()-t0)

		### phase flipping
		t0 = time.time()
		if self.params['phaseflipped'] is True:
			if self.params['fliptype'] == 'emantilt':
				### ctf correct individual particles with tilt using Eman
				imgstackfile = self.tiltPhaseFlipParticles(imgdata, imgstackfile, boxedpartdatas)
				self.ctftimes.append(time.time()-t0)
			elif self.params['fliptype'] == 'emanpart':
				### ctf correct individual particles using Eman
				imgstackfile = self.phaseFlipParticles(imgdata, imgstackfile)
				self.ctftimes.append(time.time()-t0)
			else:
				apDisplay.printMsg("phase flipped whole image already")
		else:
			apDisplay.printMsg("not phase flipping particles")

		numpart = apFile.numImagesInStack(imgstackfile)
		apDisplay.printMsg(str(numpart)+" particles were boxed out from "+shortname)

		if len(parttree) != numpart:
			apDisplay.printError("There is a mismatch in the number of particles expected and that were boxed")

		return boxedpartdatas, imgstackfile, partmeantree

	############################################################
	############################################################
	## CTF correction functions
	############################################################
	############################################################

	#=======================
	def tiltPhaseFlipParticles(self, imgdata, imgstackfile, partdatas):
		ctfvalue = apCtf.getBestTiltCtfValueForImage(imgdata)
		if ctfvalue is None:
			apDisplay.printError("Failed to get ctf parameters")
		apix = apDatabase.getPixelSize(imgdata)
		ctfimgstackfile = os.path.join(self.params['rundir'], apDisplay.short(imgdata['filename'])+"-ctf.hed")

		### calculate defocus at given position
		CX = imgdata['camera']['dimension']['x']
		CY = imgdata['camera']['dimension']['y']

		if ctfvalue['tilt_axis_angle'] is not None:
			N1 = -1.0 * math.sin( math.radians(ctfvalue['tilt_axis_angle']) )
			N2 = math.cos( math.radians(ctfvalue['tilt_axis_angle']) )
		else:
			N1 = 0.0
			N2 = 1.0
		PSIZE = apix

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		# find cs
		if ctfvalue['cs']:
			cs = ctfvalue['cs']
		elif ctfvalue['acerun']['ace2_params']:
			cs=ctfvalue['acerun']['ace2_params']['cs']
		elif ctfvalue['acerun']['ctftilt_params']:
			cs=ctfvalue['acerun']['ctftilt_params']['cs']
		if cs is None:
			### apply hard coded value, in case of missing cs value
			cs = 2.0

		imagicdata = apImagicFile.readImagic(imgstackfile)
		ctfpartstack = []
		for i in range(len(partdatas)):
			partdata = partdatas[i]
			prepartarray = imagicdata['images'][i]
			prepartmrc = "rawpart.dwn.mrc"
			postpartmrc = "ctfpart.dwn.mrc"
			apImage.arrayToMrc(partarray, prepartmrc, msg=False)

			### calculate ctf based on position
			DX = CX - partdata['xcoord']
			DY = CY - partdata['ycoord']
			DF = (N1*DX + N2*DY) * PSIZE * math.tan( math.radians(ctfvalue['tilt_angle']) )
			DFL1 = ctfvalue['defocus1']*-1.0e4 + DF
			DFL2 = ctfvalue['defocus2']*-1.0e4 + DF
			DF_final = (DFL1+DFL2)/2.0

			### convert defocus to meters
			defocus = DF_final*-1.0e-4

			self.checkDefocus(defocus, shortname)

			parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f" %(defocus, ampconst, voltage, cs, apix))
			emancmd = ("applyctf %s %s %s setparm flipphase" % (prepartmrc, postpartmrc, parmstr))
			apEMAN.executeEmanCmd(emancmd, showcmd=True)

			ctfpartarray = apImage.mrcToArray(postpartmrc)
			ctfpartstack.append(ctfpartarray)

		apImagicFile.writeImagic(ctfpartstack, ctfimgstackfile)

	#=======================
	def phaseFlipParticles(self, imgdata, imgstackfile):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		ctfimgstackfile = os.path.join(self.params['rundir'], apDisplay.short(imgdata['filename'])+"-ctf.hed")

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		apix = apDatabase.getPixelSize(imgdata)
		### get the adjusted defocus value for no astigmatism
		defocus, ampconst = apCtf.getBestDefocusAndAmpConstForImage(imgdata, msg=True, method=self.params['ctfmethod'])
		defocus *= 1.0e6
		### check to make sure defocus is a reasonable value for applyctf
		self.checkDefocus(defocus, shortname)
		### get all CTF parameters, we also need to get the CS value from the database
		ctfdata, score = apCtf.getBestCtfValueForImage(imgdata, msg=False, method=self.params['ctfmethod'])
		#ampconst = ctfdata['amplitude_contrast'] ### we could use this too
		# find cs
		if ctfdata['cs']:
			cs = ctfdata['cs']
		elif ctfdata['acerun']['ace2_params']:
			cs=ctfdata['acerun']['ace2_params']['cs']
		elif ctfdata['acerun']['ctftilt_params']:
			cs=ctfdata['acerun']['ctftilt_params']['cs']
		if cs is None:
			### apply hard coded value, in case of missing cs value
			cs = 2.0

		parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f" %(defocus, ampconst, voltage, cs, apix))
		emancmd = ("applyctf %s %s %s setparm flipphase" % (imgstackfile, ctfimgstackfile, parmstr))

		apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
		return ctfimgstackfile

	#=======================
	def phaseFlipWholeImage(self, inimgpath, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		outimgpath = os.path.join(self.params['rundir'], shortname+"-ctfcorrect.dwn.mrc")

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		apix = apDatabase.getPixelSize(imgdata)
		defocus, ampconst = apCtf.getBestDefocusAndAmpConstForImage(imgdata, msg=True, method=self.params['ctfmethod'])
		defocus *= 1.0e6
		self.checkDefocus(defocus, shortname)
		### get all CTF parameters, we also need to get the CS value from the database
		ctfdata, score = apCtf.getBestCtfValueForImage(imgdata, msg=False, method=self.params['ctfmethod'])
		#ampconst = ctfdata['amplitude_contrast'] ### we could use this too
		# find cs
		if ctfdata['cs']:
			cs = ctfdata['cs']
		elif ctfdata['acerun']['ace2_params']:
			cs=ctfdata['acerun']['ace2_params']['cs']
		elif ctfdata['acerun']['ctftilt_params']:
			cs=ctfdata['acerun']['ctftilt_params']['cs']
		if cs is None:
			### apply hard coded value, in case of missing cs value
			cs = 2.0
			
		parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f" %(defocus, ampconst, voltage, cs, apix))
		emancmd = ("applyctf %s %s %s setparm flipphase" % (inimgpath, outimgpath, parmstr))

		apDisplay.printMsg("phaseflipping entire micrograph with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
		return outimgpath

	#======================
	def getACE2Path(self):
		exename = 'ace2correct.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			ace2exe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ace2exe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ace2exe

	#=======================
	def phaseFlipAceTwo(self, inimgpath, imgdata):

		apix = apDatabase.getPixelSize(imgdata)
		bestctfvalue, bestconf = apCtf.getBestCtfValueForImage(imgdata, msg=True, method=self.params['ctfmethod'])

		if bestctfvalue is None:
			apDisplay.printWarning("No ctf estimation for current image")
			self.badprocess = True
			return None

		if bestctfvalue['acerun'] is None:
			apDisplay.printWarning("No ctf runid for current image")
			self.badprocess = True
			return None

		# method=ace2 requires a ctfvalues_file
		if bestctfvalue['ctfvalues_file'] is None:
			if self.params['ctfmethod']=="ace2":
				apDisplay.printWarning("No ctf file for current image")
				self.badprocess = True
				return None

			### cannot use ACE2 correction without CS value in database
			if not 'cs' in bestctfvalue:
				apDisplay.printMsg('No spherical abberation value in database, skipping image')
				self.badprocess = True
				return None

			# create ctfvalues_file from ctf run
			ctfvaluesfile = "tmp_ctfvaluesfile.txt"

			df1 = bestctfvalue['defocus1']
			df2 = bestctfvalue['defocus2']
			angast = bestctfvalue['angle_astigmatism']*math.pi/180.0
			amp = bestctfvalue['amplitude_contrast']
			kev = imgdata['scope']['high tension']/1000
			cs = bestctfvalue['cs']/1000
			conf = bestctfvalue['confidence_d']

			if os.path.isfile(ctfvaluesfile):
				os.remove(ctfvaluesfile)
			f = open(ctfvaluesfile,'w')
			f.write("\tFinal Params for image: %s.mrc\n"%imgdata['filename'])
			f.write("\tFinal Defocus: %.6e %.6e %.6e\n"%(df1,df2,angast))
			f.write("\tAmplitude Contrast: %.6e\n"%amp)
			f.write("\tVoltage: %.6e\n"%kev)
			f.write("\tSpherical Aberration: %.6e\n"%cs)
			f.write("\tAngstroms per pixel: %.6e\n"%apix)
			f.write("\tConfidence: %.6e\n"%conf)
			f.close()

		# use ace2 ctfvalues file
		else:
			ctfvaluesfile = os.path.join(bestctfvalue['acerun']['path']['path'], bestctfvalue['ctfvalues_file'])

			ctfvaluesfilesplit = os.path.splitext(ctfvaluesfile)
			while ctfvaluesfilesplit[1] != '.mrc':
				ctfvaluesfilesplit = os.path.splitext(ctfvaluesfilesplit[0])

			ctfvaluesfile = ctfvaluesfilesplit[0]+".mrc.ctf.txt"

		defocus1 = bestctfvalue['defocus1']
		defocus2 = bestctfvalue['defocus2']
		defocus = (defocus1+defocus2)/2.0*1.0e6

		apDisplay.printMsg("using ctfvaluesfile: "+ctfvaluesfile)

		if not os.path.isfile(ctfvaluesfile):
			apDisplay.printError("ctfvaluesfile does not exist")

		ace2exe = self.getACE2Path()
		outfile = os.path.join(os.getcwd(),imgdata['filename']+".mrc.corrected.mrc")

		ace2cmd = (ace2exe+" -ctf %s -apix %.3f -img %s -out %s" % (ctfvaluesfile, apix, inimgpath,outfile))
		if self.params['fliptype'] == "ace2image":
			ace2cmd += " -wiener 0.1"
		apDisplay.printMsg("ace2 command: "+ace2cmd)
		apDisplay.printMsg("phaseflipping entire micrograph with defocus "+str(round(defocus,3))+" microns")

		#apEMAN.executeEmanCmd(ace2cmd, showcmd=True)
		if self.params['verbose'] is True:
			ace2proc = subprocess.Popen(ace2cmd, shell=True)
		else:
			aceoutf = open("ace2.out", "a")
			aceerrf = open("ace2.err", "a")
			ace2proc = subprocess.Popen(ace2cmd, shell=True, stderr=aceerrf, stdout=aceoutf)
		ace2proc.wait()
		if self.stats['count'] <= 1:
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)
			if self.params['verbose'] is True:
				ace2proc = subprocess.Popen(ace2cmd, shell=True)
			else:
				aceoutf = open("ace2.out", "a")
				aceerrf = open("ace2.err", "a")
				ace2proc = subprocess.Popen(ace2cmd, shell=True, stderr=aceerrf, stdout=aceoutf)
			ace2proc.wait()

		if self.params['verbose'] is False:
			aceoutf.close()
			aceerrf.close()

		if not os.path.isfile(outfile):
			apDisplay.printError("ACE 2 failed to create image file:\n%s" % outfile)

		return outfile

	#=======================
	def phaseFlipSpider(self, inimgpath, imgdata):
		"""
		phaseflip whole image using spider
		"""

		bestctfvalue, bestconf = apCtf.getBestCtfValueForImage(imgdata,msg=True,method=self.params['ctfmethod'])

		if bestctfvalue is None:
			apDisplay.printWarning("No ctf estimation for current image")
			self.badprocess = True
			return None

		imgname = imgdata['filename']
		shortname = apDisplay.short(imgname)
		spi_imgpath = os.path.join(self.params['rundir'], shortname+".spi")

		
		df1 = bestctfvalue['defocus1']
		df2 = bestctfvalue['defocus2']
		defocus = (df1+df2)/2*1.0e6

		apix = apDatabase.getPixelSize(imgdata)
		voltage = imgdata['scope']['high tension']
		imgsize=imgdata['camera']['dimension']['y']
		# find cs
		if bestctfvalue['cs']:
			cs = bestctfvalue['cs']
		elif bestctfvalue['acerun']['ace2_params']:
			cs=bestctfvalue['acerun']['ace2_params']['cs']
		elif bestctfvalue['acerun']['ctftilt_params']:
			cs=bestctfvalue['acerun']['ctftilt_params']['cs']
		else:
			apDisplay.printError("No cs value found in database")

		# no astigmatism correction now
		#angast = bestctfvalue['angle_astigmatism']*math.pi/180
		#amp = bestctfvalue['amplitude_contrast']

		# convert image to spider
		emancmd="proc2d %s %s spidersingle"%(inimgpath,spi_imgpath)
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
		apDisplay.printMsg("phaseflipping entire micrograph with defocus "+str(round(defocus,3))+" microns")
		# spider defocus is +, and in Angstroms
		defocus *= -10000 
		outimgpath = filters.phaseFlipImage(spi_imgpath,cs,defocus,voltage,imgsize,apix)

		# convert image back to mrc
		mrcname = os.path.join(self.params['rundir'], shortname+".mrc.corrected.mrc")
		emancmd="proc2d %s %s"%(outimgpath,mrcname)
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
		# remove original spider image
		os.remove(spi_imgpath)

		return mrcname
		

############################################################
## General functions
############################################################

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

	#=======================
	def mergeImageStackIntoBigStack(self, imgstackfile, imgdata):
		bigimgstack = os.path.join(self.params['rundir'], self.params['single'])

		emancmd="proc2d %s %s" %(imgstackfile, bigimgstack)
		### normalization
		if self.params['normalized'] is True:
			emancmd += " norm=0.0,1.0"
			# edge normalization
			emancmd += " edgenorm"
		### high / low pass filtering
		if self.params['highpass'] or self.params['lowpass']:
			emancmd += " apix=%s" % apDatabase.getPixelSize(imgdata)
			if self.params['highpass']:
				emancmd += " hp=%.2f" % self.params['highpass']
			if self.params['lowpass']:
				emancmd += " lp=%.2f" % self.params['lowpass']
		### bin images if specified
		if self.params['bin'] > 1:
			emancmd += " shrink=%d"%(self.params['bin'])
		emancmd += " clip=%d,%d"%(self.params['boxsize'],self.params['boxsize'])
		### unless specified, invert the images
		if self.params['inverted'] is True:
			emancmd += " invert"
		### if specified, create spider stack
		if self.params['spider'] is True:
			emancmd += " spiderswap"

		apDisplay.printMsg("appending particles to stack: "+bigimgstack)
		t0 = time.time()
		apEMAN.executeEmanCmd(emancmd)
		self.mergestacktimes.append(time.time()-t0)

		### count particles
		bigcount = apFile.numImagesInStack(bigimgstack, self.params['boxsize']/self.params['bin'])
		imgcount = apFile.numImagesInStack(imgstackfile, self.params['boxsize'])

		### append to particle log file
		partlogfile = os.path.join(self.params['rundir'], self.timestamp+"-particles.info")
		f = open(partlogfile, 'a')
		for i in range(imgcount):
			partnum = self.particleNumber + i + 1
			line = str(partnum)+'\t'+os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
			f.write(line+"\n")
		f.close()

		return bigcount

############################################################
## Insert and Committing
############################################################

	#=======================
	def insertStackRun(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		projectnum = apProject.getProjectIdFromSessionName(self.params['sessionname'])

		stparamq=appiondata.ApStackParamsData()
		paramlist = ('boxSize','bin','aceCutoff','correlationMin','correlationMax',
			'checkMask','minDefocus','maxDefocus','fileType','inverted','normalized', 'xmipp-norm', 'defocpair',
			'lowpass','highpass','norejects', 'tiltangle')

		### fill stack parameters
		for p in paramlist:
			if p.lower() in self.params:
				stparamq[p] = self.params[p.lower()]
			elif p=='aceCutoff' and self.params['ctfcutoff']:
				stparamq[p] = self.params['ctfcutoff']	
			else:
				print "missing", p.lower()
		if self.params['phaseflipped'] is True:
			stparamq['phaseFlipped'] = True
			stparamq['fliptype'] = self.params['fliptype']
		if self.params['rotate'] is True:
			stparamq['rotate'] = True
		paramslist = stparamq.query()

		if not 'boxSize' in stparamq or stparamq['boxSize'] is None:
			print stparamq
			apDisplay.printError("problem in database insert")

		### create a stack object
		stackq = appiondata.ApStackData()
		stackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
      	### see if stack already exists in the database (just checking path & name)
		uniqstackdatas = stackq.query(results=1)

		### create a stackRun object
		runq = appiondata.ApStackRunData()
		runq['stackRunName'] = self.params['runname']
		runq['session'] = sessiondata
		if self.params['selectionid'] is not None:
			runq['selectionrun'] = appiondata.ApSelectionRunData.direct_query(self.params['selectionid'])
      	### see if stack run already exists in the database (just checking runname & session)
		uniqrundatas = runq.query(results=1)

      	### finish stack object
		stackq['name'] = self.params['single']
		stackq['description'] = self.params['description']
		stackq['hidden'] = False
		stackq['pixelsize'] = self.params['apix']*self.params['bin']*1e-10
		stackq['boxsize'] = self.params['boxsize']/self.params['bin']

		### add info for from stack ids
		if self.params['fromstackid'] is not None:
			#stackq['oldstack'] = appiondata.ApStackData.direct_query(self.params['fromstackid'])
			stackq['substackname'] = "restack%d"%(self.params['fromstackid'])
			stackq['description'] += " ... restack from stack id %d"%(self.params['fromstackid'])

		self.stackdata = stackq

      	### finish stackRun object
		runq['stackParams'] = stparamq
		self.stackrundata = runq

      	### create runinstack object
		rinstackq = appiondata.ApRunsInStackData()
		rinstackq['stackRun'] = runq
#		rinstackq['stack'] = stackq

      	### if not in the database, make sure run doesn't already exist
		if not uniqstackdatas and not uniqrundatas:
			apDisplay.printColor("Inserting stack parameters into database", "cyan")
			if self.params['commit'] is True:
				rinstackq['stack'] = stackq
				rinstackq.insert()
			return
		elif uniqrundatas and not uniqstackdatas:
			apDisplay.printError("Weird, run data without stack already in the database")
		else:
			rinstackq['stack'] = stackq
			rinstack = rinstackq.query(results=1)

			prevrinstackq = appiondata.ApRunsInStackData()
			prevrinstackq['stackRun'] = uniqrundatas[0]
			prevrinstackq['stack'] = uniqstackdatas[0]
			prevrinstack = prevrinstackq.query(results=1)

			## if no runinstack found, find out which parameters are wrong:
			if not rinstack:
				for i in uniqrundatas[0]:
					print "r =======",i,"========"
					if uniqrundatas[0][i] != runq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,uniqrundatas[0][i],runq[i]
				for i in uniqrundatas[0]['stackParams']:
					print "p =======",i,"========"
					if uniqrundatas[0]['stackParams'][i] != stparamq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i, uniqrundatas[0]['stackParams'][i], stparamq[i]
				for i in uniqstackdatas[0]:
					print "s =======",i,"========"
					if str(uniqstackdatas[0][i]) != str(stackq[i]):
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,uniqstackdatas[0][i],stackq[i]
				for i in prevrinstack[0]:
					if i=='stack' or i=='stackRun':
						continue
					print "rin =======",i,"========"
					if prevrinstack[0][i] != rinstackq[i]:
						print i,prevrinstack[0][i],rinstackq[i]
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,prevrinstack[0][i],rinstackq[i]
				#apDisplay.printError("All parameters for a particular stack must be identical! \n"+\
				#			     "please check your parameter settings.")
			apDisplay.printWarning("Stack already exists in database! Will try and appending new particles to stack")
		return

	############################################################
	## Common parameters
	############################################################

	#=======================
	def setupParserOptions(self):
		self.flipoptions = ('emanimage', 'emanpart', 'emantilt', 'spiderimage', 'ace2image','ace2imagephase')
		self.ctfestopts = ('ace2', 'ctffind')

		### values
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin the particles after boxing", metavar="#")
		self.parser.add_option("--single", dest="single", default="start.hed",
			help="create a single stack")
		self.parser.add_option("--ctfcutoff", dest="ctfcutoff", type="float",
			help="CTF cut off")
		self.parser.add_option("--boxsize", dest="boxsize", type="int",
			help="particle box size in pixel")
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
		self.parser.add_option("--filetype", dest="filetype", default='imagic',
			help="filetype, default=imagic")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="float",
			help="low pass filter")
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="float",
			help="high pass filter")
		self.parser.add_option("--mag", dest="mag", type="int",
			help="process only images of magification, mag")
		self.parser.add_option("--maskassess", dest="maskassess",
			help="Assessed mask run name")
		self.parser.add_option("--label", dest="particlelabel", type="str", default=None,
			help="select particles by label within the same run name")
		self.parser.add_option("--xmipp-normalize", dest="xmipp-norm", type="float",
			help="normalize the entire stack using xmipp")
		self.parser.add_option("--ddstartframe", dest="startframe", type="int", default=1,
			help="starting frame for direct detector raw frame processing")
		self.parser.add_option("--ddnframe", dest="nframe", type="int", default=0,
			help="total frames to sum up for direct detector raw frame processing")

		### true/false
		self.parser.add_option("--phaseflip", dest="phaseflipped", default=False,
			action="store_true", help="perform CTF correction on the boxed images")
		self.parser.add_option("--invert", dest="inverted", default=False,
			action="store_true", help="contrast of the micrographs")
		self.parser.add_option("--no-invert", dest="inverted", default=False,
			action="store_false", help="contrast of the micrographs")
		self.parser.add_option("--spider", dest="spider", default=False,
			action="store_true", help="create a spider stack")
		self.parser.add_option("--normalized", dest="normalized", default=False,
			action="store_true", help="normalize the entire stack")
		self.parser.add_option("--defocpair", dest="defocpair", default=False,
			action="store_true", help="select defocal pair")

		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="do not make stack mean plot")

		self.parser.add_option("--boxfiles", dest="boxfiles", default=False,
			action="store_true", help="create only boxfiles, no stack")
		self.parser.add_option("--checkmask", dest="checkmask", default=False,
			action="store_true", help="Check masks")
		self.parser.add_option("--keepall", dest="keepall", default=False,
			action="store_true", help="Do not delete CTF corrected MRC files when finishing")
		self.parser.add_option("--verbose", dest="verbose", default=False,
			action="store_true", help="Show extra ace2 information while running")
		self.parser.add_option("--rotate", dest="rotate", default=False,
			action="store_true", help="Apply helical rotation angles")

		### option based
		#self.parser.add_option("--whole-image", dest="wholeimage", default=False,
		#	action="store_true", help="whole image ctf correction with EMAN")
		#self.parser.add_option("--acetwo", dest="acetwo", default=False,
		#	action="store_true", help="whole image ctf correction with Ace 2")
		#self.parser.add_option("--tiltedflip", dest="tiltedflip", default=False,
		#	action="store_true", help="using tilted defocus estimation based on particle location")
		self.parser.add_option("--flip-type", dest="fliptype",
			help="CTF correction method", metavar="TYPE",
			type="choice", choices=self.flipoptions, default="emanpart" )
		self.parser.add_option("--ctfmethod", dest="ctfmethod",
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)

	#=======================
	def checkConflicts(self):
		if self.params['boxsize'] is None:
			apDisplay.printError("A boxsize has to be specified")
		if not apPrimeFactor.isGoodStack(self.params['boxsize']):
			apDisplay.printWarning("Boxsize does not contain recommended prime numbers")
			smallbox,bigbox = apPrimeFactor.getPrimeLimits(self.params['boxsize'])
			apDisplay.printWarning("You should use %d or %d for a boxsize instead"%(smallbox,bigbox))
		else:
			primes = apPrimeFactor.prime_factors(self.params['boxsize'])
			apDisplay.printMsg("Boxsize "+str(self.params['boxsize'])+" contains the primes: "+str(primes))
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
		if self.params['fliptype'] == 'ace2image' and self.params['ctfmethod'] is None:
			apDisplay.printMsg("setting ctf method to ace2")
			self.params['ctfmethod'] = 'ace2'
		if self.params['xmipp-norm'] is not None:
			self.xmippexe = apParam.getExecPath("xmipp_normalize", die=True)
		if self.params['particlelabel'] == 'user' and self.params['rotate'] is True:
			apDisplay.printError("User selected targets do not have rotation angles")
		if self.params['particlelabel'] == 'helical' and self.params['rotate'] is False:
			apDisplay.printWarning("Rotate parameter is not set, helical filaments will not be aligned")
			

	#=======================
	def preLoopFunctions(self):
		self.batchboxertimes = []
		self.ctftimes = []
		self.mergestacktimes = []
		self.meanreadtimes = []
		self.insertdbtimes = []
		self.noimages = False
		if len(self.imgtree) == 0:
			apDisplay.printWarning("No images were found to process")
			self.noimages = True
			return
		self.checkPixelSize()
		self.existingParticleNumber=0
		if self.params['commit'] is True:
			self.insertStackRun()
			self.particleNumber = self.getExistingStackInfo()
			self.existingParticleNumber=self.particleNumber
		else:
			self.particleNumber = 0
			stackfile=os.path.join(self.params['rundir'], self.params['single'])
			apFile.removeStack(stackfile)

		apDisplay.printMsg("Starting at particle number: "+str(self.particleNumber))

		if self.params['partlimit'] is not None and self.particleNumber > self.params['partlimit']:
			apDisplay.printError("Number of particles in existing stack already exceeds limit!")
		self.logpeaks = 2

		### create an edge map for edge statistics
		box = int(self.params['boxsize'])
		### use a radius one pixel less than the boxsize
		self.edgemap = imagefun.filled_circle((box,box), box/2.0-1.0)

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

		### run batchboxer
		self.boxedpartdatas, self.imgstackfile, self.partmeantree = self.boxParticlesFromImage(imgdata)
		if self.boxedpartdatas is None:
			apDisplay.printWarning("no particles were boxed from "+shortname+"\n")
			self.badprocess = True
			return

		self.stats['lastpeaks'] = len(self.boxedpartdatas)

		apDisplay.printMsg("do not break function now otherwise it will corrupt run")
		time.sleep(1.0)

		### merge image particles into big stack
		totalpart = self.mergeImageStackIntoBigStack(self.imgstackfile, imgdata)

		### check if particle limit is met
		if self.params['partlimit'] is not None and totalpart > self.params['partlimit']:
			apDisplay.printWarning("reached particle number limit of "+str(self.params['partlimit'])+" now stopping")
			self.imgtree = []
			self.notdone = False

		### create a stack average every so often
		if self.stats['lastpeaks'] > 0:
			logpeaks = math.log(self.existingParticleNumber+self.stats['peaksum']+self.stats['lastpeaks'])
			if logpeaks > self.logpeaks:
				self.logpeaks = math.ceil(logpeaks)
				numpeaks = math.ceil(math.exp(self.logpeaks))
				apDisplay.printMsg("averaging stack, next average at %d particles"%(numpeaks))
				stackpath = os.path.join(self.params['rundir'], "start.hed")
				apStack.averageStack(stack=stackpath)

	#=======================
	def postLoopFunctions(self):
		### Delete CTF corrected images
		if self.params['keepall'] is False:
			pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*.dwn.mrc')
			apFile.removeFilePattern(pattern)
			### remove Ace2 images
			pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*mrc.corrected.mrc')
			apFile.removeFilePattern(pattern)
			### remove Spider images
			if self.params['fliptype'] == 'spiderimage':
				pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*_out.spi')
				apFile.removeFilePattern(pattern)
				pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*_tf.spi')
				apFile.removeFilePattern(pattern)
		if self.noimages is True:
			return
		### Averaging completed stack
		stackpath = os.path.join(self.params['rundir'], "start.hed")
		apStack.averageStack(stack=stackpath)
		### Create Stack Mean Plot
		if self.params['commit'] is True and self.params['meanplot'] is True:
			stackid = apStack.getStackIdFromPath(stackpath)
			if stackid is not None:
				apStackMeanPlot.makeStackMeanPlot(stackid)
		### apply xmipp normalization
		if self.params['xmipp-norm'] is not None:
			### convert stack into single spider files
			selfile = apXmipp.breakupStackIntoSingleFiles(stackpath)	

			### setup Xmipp command
			apDisplay.printMsg("Using Xmipp to normalize particle stack")
			normtime = time.time()
			xmippopts = ( " "
				+" -i %s"%os.path.join(self.params['rundir'],selfile)
				+" -method Ramp "
				+" -background circle %i"%(int(self.params['boxsize']/self.params['bin']*0.4))
				+" -remove_black_dust"
				+" -remove_white_dust"
				+" -thr_black_dust -%.2f"%(self.params['xmipp-norm'])
				+" -thr_white_dust %.2f"%(self.params['xmipp-norm'])
			)
			xmippcmd = self.xmippexe+" "+xmippopts
			apParam.runCmd(xmippcmd, package="Xmipp", verbose=True, showcmd=True)
			normtime = time.time() - normtime
			apDisplay.printMsg("Xmipp normalization time: "+apDisplay.timeString(normtime))

			### recombine particles to a single imagic stack
			tmpstack = "tmp.xmippStack.hed"
			apXmipp.gatherSingleFilesIntoStack(selfile,tmpstack)
			apFile.moveStack(tmpstack,stackpath)

			### clean up directory
			apFile.removeFile(selfile)
			apFile.removeDir("partfiles")
			
		apDisplay.printColor("Timing stats", "blue")
		self.printTimeStats("Batch Boxer", self.batchboxertimes)
		self.printTimeStats("Ctf Correction", self.ctftimes)
		self.printTimeStats("Stack Merging", self.mergestacktimes)
		self.printTimeStats("Mean/Std Read", self.meanreadtimes)
		self.printTimeStats("DB Insertion", self.insertdbtimes)

	#=======================
	def printTimeStats(self, name, timelist):
		if len(timelist) < 2:
			return
		meantime = self.stats['timesum']/float(self.stats['count'])
		timearray = numpy.array(timelist, dtype=numpy.float64)
		apDisplay.printColor("%s: %s (%.2f percent)"%
			(name, apDisplay.timeString(timearray.mean(), timearray.std()), 100*timearray.mean()/meantime), "blue")

	#=======================
	def commitToDatabase(self, imgdata):
		t0 = time.time()
		### loop over the particles and insert
		for i in range(len(self.boxedpartdatas)):
			partdata = self.boxedpartdatas[i]
			partmeandict = self.partmeantree[i]

			self.particleNumber += 1
			stpartq = appiondata.ApStackParticleData()

			### check unique params
			stpartq['stack'] = self.stackdata
			stpartq['stackRun'] = self.stackrundata
			stpartq['particleNumber'] = self.particleNumber
			stpartdata = stpartq.query(results=1)
			if stpartdata:
				apDisplay.printError("trying to insert a duplicate particle")

			stpartq['particle'] = partdata
			stpartq['mean'] = round(partmeandict['mean'],8)
			stpartq['stdev'] = round(partmeandict['stdev'],8)
			stpartq['min'] = round(partmeandict['min'],4)
			stpartq['max'] = round(partmeandict['max'],4)
			stpartq['skew'] = round(partmeandict['skew'],4)
			stpartq['kurtosis'] = round(partmeandict['kurtosis'],4)
			stpartq['edgemean'] = round(partmeandict['edgemean'],4)
			stpartq['edgestdev'] = round(partmeandict['edgestdev'],4)
			stpartq['centermean'] = round(partmeandict['centermean'],4)
			stpartq['centerstdev'] = round(partmeandict['centerstdev'],4)
			if self.params['commit'] is True:
				stpartq.insert()
		self.insertdbtimes.append(time.time()-t0)

	#=======================
	def loopCleanUp(self,imgdata):
		### last remove any existing boxed files, reset global params
		shortname = apDisplay.short(imgdata['filename'])
		shortfileroot = os.path.join(self.params['rundir'], shortname)
		rmfiles = glob.glob(shortfileroot+"*")
		if not self.params['keepall']:
			for rmfile in rmfiles:
				apFile.removeFile(rmfile)
		self.imgstackfile = None
		self.boxedpartdatas = []

if __name__ == '__main__':
	makeStack = Makestack2Loop()
	makeStack.run()



