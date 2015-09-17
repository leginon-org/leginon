#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import time
import copy
import numpy
import subprocess
from scipy import stats
from scipy import ndimage

#appion
from pyami import mrc
from pyami import imagic
from pyami import imagefun
from pyami import primefactor
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apStack
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apParam
from appionlib import apBoxer
from appionlib import apImagicFile
from appionlib import apStackMeanPlot
from appionlib import apParticleExtractor
from appionlib.apCtf import ctfdb
from appionlib.apSpider import filters
from appionlib.apImage import imagenorm
from appionlib.apImage import imagefilter


class Makestack2Loop(apParticleExtractor.ParticleBoxLoop):
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
			apDisplay.printError("database and file have different number of particles, \n"+
				"create a new stack this one is corrupt")

		return numfilepart

	#=======================
	def processParticles(self, imgdata, partdatas, shiftdata):
		self.shortname = apDisplay.short(imgdata['filename'])

		### if only selected points along helix,
		### fill in points with helical step
		if self.params['helicalstep']:
			apix = apDatabase.getPixelSize(imgdata)
			partdatas = self.fillWithHelicalStep(partdatas, apix)

		### run batchboxer
		self.boxedpartdatas, self.imgstackfile, self.partmeantree = self.boxParticlesFromImage(imgdata, partdatas, shiftdata)
		if self.boxedpartdatas is None:
			self.stats['lastpeaks'] = 0
			apDisplay.printWarning("no particles were boxed from "+self.shortname+"\n")
			self.badprocess = True
			return None

		self.stats['lastpeaks'] = len(self.boxedpartdatas)

		apDisplay.printMsg("do not break function now otherwise it will corrupt stack")
		#time.sleep(1.0)

		### merge image particles into big stack
		totalpart = self.mergeImageStackIntoBigStack(self.imgstackfile, imgdata)

		### create a stack average every so often
		if self.stats['lastpeaks'] > 0:
			totalPartices = self.existingParticleNumber+self.stats['peaksum']+self.stats['lastpeaks']
			logpeaks = math.log(totalPartices)
			if logpeaks > self.logpeaks:
				self.logpeaks = math.ceil(logpeaks)
				numpeaks = math.ceil(math.exp(self.logpeaks))
				apDisplay.printMsg("writing averaging stack, next average at %d particles"%(numpeaks))
				mrc.write(self.summedParticles/float(totalPartices), "average.mrc")
		return totalpart

	#=======================
	def removeBoxOutOfImage(self, imgdata, partdatas, shiftdata):
		# if using a helical step, particles will be filled between picks,
		# so don't want to throw picks out right now
		if self.params['helicalstep'] is not None:
			return partdatas
		else:
			return super(Makestack2Loop, self).removeBoxOutOfImage(imgdata, partdatas, shiftdata)

	#=======================
	def fillWithHelicalStep(self, partdatas, apix):
		"""
		each helix should be distinguished by a different angle number,
		fill in particles along the helices using the specified step size
		return a new copy of the partdatas
		"""
		newpartdatas = []
		## convert helicalstep to pixels
		steppix=self.params['helicalstep']/apix
		try:
			lasthelix=partdatas[0]['helixnum']
			lastx=partdatas[0]['xcoord']
			lasty=partdatas[0]['ycoord']
			leftover = 0
		except:
			return
		numhelices = 1
		for part in partdatas:
			currenthelix=part['helixnum']
			currentx=part['xcoord']
			currenty=part['ycoord']
			if currentx==lastx and currenty==lasty:
				continue
			### only fill in within the same helix
			if currenthelix==lasthelix:
				angle = math.atan2((currentx-lastx),(currenty-lasty))
				### in order for helix to be continuous, we can't simply
				### start exactly from the current point
				### we have to figure out what was leftover from the last
				### portion of the helix, and redefine the starting point
				if leftover > 0:
					d = steppix-leftover
					lastx = (d*math.sin(angle))+lastx
					lasty = (d*math.cos(angle))+lasty
				pixdistance = math.hypot(lastx-currentx, lasty-currenty)
				# get number of particles between the two points
				numsteps = int(math.floor(pixdistance/steppix))
				# keep remainder to continue the helix
				leftover = pixdistance-(numsteps*steppix)
				#print "should take %i steps at %i pixels per step, (leftover:%i)"%(numsteps,steppix,leftover)
				for step in range(numsteps+1):
					pointx = lastx+(step*(steppix*math.sin(angle)))
					pointy = lasty+(step*(steppix*math.cos(angle)))
					newpartinfo = copy.copy(part)
					newpartinfo['xcoord']=int(pointx)
					newpartinfo['ycoord']=int(pointy)
					# convert angle for appion database
					newpartinfo['angle']=math.degrees(-angle)-90
					newpartinfo['label']='helical'
					newpartinfo['selectionrun']=self.newselectiondata
					newpartdatas.append(newpartinfo)
			else:
				numhelices += 1
				leftover = 0
			lastx = currentx
			lasty = currenty
			lasthelix = currenthelix
		apDisplay.printMsg("Filled %i helices with %i helical segments"%(numhelices,len(newpartdatas)))
		return newpartdatas

	#=======================
	def getDDImageArray(self, imgdata):
		'''
		Returns integrated and gain/dark corrected image according to framelist
		'''
		framelist = self.dd.getFrameList(self.params)
		# FIXME handle empty framelist caused by driftlimit
		if self.is_dd_frame:
			return self.dd.correctFrameImage(framelist)
		if self.is_dd_stack:
			return self.dd.getDDStackFrameSumImage(framelist)

	#=======================
	def getOriginalImagePath(self, imgdata):
		'''
		This function gives back the image path to be used for boxing.
		Three possible results:
		1. image from the leginon/session/rawdata as recorded in imgdata (typical)
		2. -darknorm.dwn.mrc previously created
		3. -darknorm.dwn.mrc made from dd frames.
		'''
		# default path
		imgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
		if self.is_dd:
			### dark/bright correct image
			tmpname = self.shortname+"-darknorm.dwn.mrc"
			imgpath = os.path.join(self.params['rundir'], tmpname)
			if not self.params['usedownmrc'] or not os.path.isfile(imgpath):
				# make downmrc
				imgarray = self.getDDImageArray(imgdata)
				apImage.arrayToMrc(imgarray, imgpath)
		apDisplay.printMsg('Boxing is done on %s' % (imgpath,))
		return imgpath

	#=======================
	def boxParticlesFromImage(self, imgdata, partdatas, shiftdata):

		### convert database particle data to coordinates and write boxfile
		boxfile = os.path.join(self.params['rundir'], imgdata['filename']+".box")
		parttree, boxedpartdatas = apBoxer.processParticleData(imgdata, self.boxsize,
			partdatas, shiftdata, boxfile, rotate=self.params['rotate'])

		if self.params['boxfiles']:
			### quit and return, boxfile created, now process next image
			return None, None, None

		### check if we have particles again
		if len(partdatas) == 0 or len(parttree) == 0:
			apDisplay.printColor(self.shortname+" has no remaining particles and has been rejected\n","cyan")
			return None, None, None

		### set up output file path
		imgstackfile = os.path.join(self.params['rundir'], self.shortname+".hed")

		if (self.is_dd_stack and (self.params['nframe'] or self.params['driftlimit'])
			and not self.params['phaseflipped'] and not self.params['rotate']):
			# If processing on whole image is not needed, it is more efficient to use mmap to box frame stack
			apDisplay.printMsg("boxing "+str(len(parttree))+" particles into temp file: "+imgstackfile)
			framelist = self.dd.getFrameList(self.params)
			apBoxer.boxerFrameStack(self.dd.framestackpath, parttree, imgstackfile, self.boxsize, framelist)
		else:
			self._boxParticlesFromImage(imgdata, parttree, imgstackfile)
		partmeantree = self.calculateParticleStackStats(imgstackfile, boxedpartdatas)
		imgstackfile = self.postProcessParticleStack(imgdata, imgstackfile, boxedpartdatas, len(parttree))
		return boxedpartdatas, imgstackfile, partmeantree

	#=======================
	def _boxParticlesFromImage(self, imgdata, parttree, imgstackfile):
		'''
		Box Particles From the manipulated full size image file on disk
		'''
		### make corrected integrated frame image
		imgpath = self.getOriginalImagePath(imgdata)

		t0 = time.time()
		if self.params['phaseflipped'] is True:
			if self.params['fliptype'] == 'emanimage':
				### ctf correct whole image using EMAN
				imgpath = self.phaseFlipWholeImage(imgpath, imgdata)
			elif self.params['fliptype'] == "spiderimage":
				imgpath = self.phaseFlipSpider(imgpath, imgdata)
			elif self.params['fliptype'][:9] == "ace2image":
				### ctf correct whole image using Ace 2
				imgpath = self.phaseFlipAceTwo(imgpath, imgdata)
			self.ctftimes.append(time.time()-t0)
		if imgpath is None:
			return None, None, None

		### run apBoxer
		apDisplay.printMsg("boxing "+str(len(parttree))+" particles into temp file: "+imgstackfile)

		### method to align helices
		t0 = time.time()
		if self.params['rotate'] is True:
			apBoxer.boxerRotate(imgpath, parttree, imgstackfile, self.boxsize)
			if self.params['finealign'] is True:
				from appionlib import apXmipp
				apXmipp.breakupStackIntoSingleFiles(imgstackfile, filetype="mrc")
				rotcmd = "s_finealign %s %i" %(self.params['rundir'], self.boxsize)
				apParam.runCmd(rotcmd, "HIP", verbose=True)
				# read in text file containing refined angles
				anglepath = os.path.join(self.params['rundir'], 'angles.out')
				f = open(anglepath, 'r')
				angles = f.readlines()
				# loop through parttree and add refined angle to rough angle
				for i in range(len(parttree)):
					partdict = parttree[i]
					fineangle = float(angles[i])
					newangle = float(partdict['angle'])-fineangle
					partdict['angle'] = newangle
				# rerun apBoxer.boxerRotate with the new parttree containing final angles
				apBoxer.boxerRotate(imgpath, parttree, imgstackfile, self.boxsize, pixlimit=self.params['pixlimit'])
		else:
			apBoxer.boxer(imgpath, parttree, imgstackfile, self.boxsize, pixlimit=self.params['pixlimit'])
		self.batchboxertimes.append(time.time()-t0)

	#=======================
	def calculateParticleStackStats(self, imgstackfile, boxedpartdatas):
		### read mean and stdev
		partmeantree = []
		t0 = time.time()
		imagicdata = apImagicFile.readImagic(imgstackfile)
		apDisplay.printMsg("gathering mean and stdev data")
		### loop over the particles and read data
		for i in range(len(boxedpartdatas)):
			partdata = boxedpartdatas[i]
			partarray = imagicdata['images'][i]

			### if particle stdev == 0, then it is all constant, i.e., a bad particle
			stdev = float(partarray.std())
			if stdev < 1.0e-6:
				apDisplay.printError("Standard deviation == 0 for particle %d in image %s"%(i,self.shortname))

			### skew and kurtosis
			partravel = numpy.ravel(partarray)
			skew = float(stats.skew(partravel))
			kurtosis = float(stats.kurtosis(partravel))

			### edge and center stats
			edgemean = float(ndimage.mean(partarray, self.edgemap, 1.0))
			edgestdev = float(ndimage.standard_deviation(partarray, self.edgemap, 1.0))
			centermean = float(ndimage.mean(partarray, self.edgemap, 0.0))
			centerstdev = float(ndimage.standard_deviation(partarray, self.edgemap, 0.0))
			self.summedParticles += partarray

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
		return partmeantree

	#=======================
	def postProcessParticleStack(self, imgdata, imgstackfile, boxedpartdatas, parttree_length):
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
		apDisplay.printMsg(str(numpart)+" particles were boxed out from "+self.shortname)

		if parttree_length != numpart:
			apDisplay.printError("There is a mismatch in the number of particles expected and that were boxed")

		### rectangular box masking
		if self.params['boxmask'] is not None:
			# create a stack of rectangular masks, which will be applied to
			# the particles as they are added to the final stack
			pixsz = apDatabase.getPixelSize(imgdata)*self.params['bin']
			boxsz = self.boxsize/self.params['bin']

			bxmask = int(self.params['bxmask']/pixsz)
			bymask = int(self.params['bymask']/pixsz)
			if self.params['bimask'] > 0:
				bimask = int(self.params['bimask']/pixsz)
			else: bimask = None
			falloff = self.params['falloff']/pixsz
			# adjust masks for falloff
			bxmask -= falloff/2
			bymask = (bymask/2)-(falloff/2)

			self.params['boxmaskf'] = os.path.splitext(imgstackfile)[0]+"-mask.hed"
			apBoxer.boxMaskStack(self.params['boxmaskf'], boxedpartdatas, boxsz,
				bxmask, bymask, falloff, bimask, norotate=self.params['rotate'])

		return imgstackfile

	############################################################
	############################################################
	## CTF correction functions
	############################################################
	############################################################

	#=======================
	def getCS(self, ctfvalue):
		cs = None
		if ctfvalue['cs']:
			cs = ctfvalue['cs']
		elif ctfvalue['acerun']['ace2_params']:
			cs=ctfvalue['acerun']['ace2_params']['cs']
		elif ctfvalue['acerun']['ctftilt_params']:
			cs=ctfvalue['acerun']['ctftilt_params']['cs']
		if cs is None:
			### apply hard coded value, in case of missing cs value
			apDisplay.printWarning("No CS value found in database, setting to 2.0")
			cs = 2.0
		return cs

	#=======================
	def tiltPhaseFlipParticles(self, imgdata, imgstackfile, partdatas):
		apDisplay.printMsg("Applying per-particle CTF")
		ctfvalue = ctfdb.getBestTiltCtfValueForImage(imgdata)
		if ctfvalue is None:
			apDisplay.printError("Failed to get ctf parameters")
		apix = apDatabase.getPixelSize(imgdata)
		ctfimgstackfile = os.path.join(self.params['rundir'], apDisplay.short(imgdata['filename'])+"-ctf.hed")
		ampconst = ctfvalue['amplitude_contrast']

		### calculate defocus at given position
		dimx = imgdata['camera']['dimension']['x']
		dimy = imgdata['camera']['dimension']['y']
		CX = dimx/2
		CY = dimy/2

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
		cs = self.getCS(ctfvalue)

		imagicdata = apImagicFile.readImagic(imgstackfile, msg=False)
		ctfpartstack = []
		for i in range(len(partdatas)):
			partdata = partdatas[i]
			prepartarray = imagicdata['images'][i]
			prepartmrc = "rawpart.dwn.mrc"
			postpartmrc = "ctfpart.dwn.mrc"
			apImage.arrayToMrc(prepartarray, prepartmrc, msg = False)

			### calculate ctf based on position
			NX = partdata['xcoord']
			NY = dimy-partdata['ycoord'] # reverse due to boxer flip

			DX = CX - NX
			DY = CY - NY
			DF = (N1*DX + N2*DY) * PSIZE * math.tan( math.radians(ctfvalue['tilt_angle']) )
			### defocus is in Angstroms
			DFL1 = abs(ctfvalue['defocus1'])*1.0e10 + DF
			DFL2 = abs(ctfvalue['defocus2'])*1.0e10 + DF
			DF_final = (DFL1+DFL2)/2.0

			### convert defocus to microns
			defocus = DF_final*-1.0e-4

			### check to make sure defocus is a reasonable value for applyctf
			self.checkDefocus(defocus, apDisplay.short(imgdata['filename']))

			parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f"
				%(defocus, ampconst, voltage, cs, apix))
			emancmd = ("applyctf %s %s %s setparm flipphase" % (prepartmrc, postpartmrc, parmstr))
			apEMAN.executeEmanCmd(emancmd, showcmd = False)

			ctfpartarray = apImage.mrcToArray(postpartmrc, msg=False)
			ctfpartstack.append(ctfpartarray)

		apImagicFile.writeImagic(ctfpartstack, ctfimgstackfile)
		return ctfimgstackfile

	#=======================
	def phaseFlipParticles(self, imgdata, imgstackfile):
		apDisplay.printMsg("Applying CTF to particles")
		ctfimgstackfile = os.path.join(self.params['rundir'], self.shortname+"-ctf.hed")

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		apix = apDatabase.getPixelSize(imgdata)
		### get the adjusted defocus value for no astigmatism
		defocus, ampconst = self.getDefocusAmpConstForImage(imgdata, True)
		defocus *= 1.0e6
		### check to make sure defocus is a reasonable value for applyctf
		self.checkDefocus(defocus, self.shortname)
		### get all CTF parameters, we also need to get the CS value from the database
		ctfdata = self.getBestCtfValue(imgdata, False)
		#ampconst = ctfdata['amplitude_contrast'] ### we could use this too

		# find cs
		cs = self.getCS(ctfdata)

		"""
		// from EMAN1 source code: EMAN/src/eman/libEM/EMTypes.h
			and EMAN/src/eman/libEM/EMDataA.C
		struct CTFParam {
			 float defocus;	// in microns, negative underfocus
			 float bfactor;	// not needed for phaseflip, envelope function width (Pi/2 * Wg)^2
			 float amplitude; // not needed for phaseflip,
										ctf amplitude, mutliplied times the entire equation
			 float ampcont;	// number from 0 to 1, sqrt(1 - a^2) format
			 float noise1/exps4;	// not needed for phaseflip, noise exponential decay amplitude
			 float noise2;		// not needed for phaseflip, width
			 float noise3;		// not needed for phaseflip, noise gaussian amplitude
			 float noise4;		// not needed for phaseflip, noide gaussian width
			 float voltage;	// in kilovolts
			 float cs;			// in millimeters
			 float apix;		// in Angstroms per pixel
		};

		noise follows noise3*exp[ -1*(pi/2*noise4*x0)^2 - x0*noise2 - sqrt(fabs(x0))*noise1]
		"""
		parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f"
			%(defocus, ampconst, voltage, cs, apix))

		emancmd = ("applyctf %s %s %s setparm flipphase"
			%(imgstackfile, ctfimgstackfile, parmstr))

		apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(emancmd, showcmd = True)
		return ctfimgstackfile

	#=======================
	def phaseFlipWholeImage(self, inimgpath, imgdata):
		outimgpath = os.path.join(self.params['rundir'], self.shortname+"-ctfcorrect.dwn.mrc")

		### High tension on CM is given in kv instead of v so do not divide by 1000 in that case
		if imgdata['scope']['tem']['name'] == "CM":
			voltage = imgdata['scope']['high tension']
		else:
			voltage = (imgdata['scope']['high tension'])/1000

		apix = apDatabase.getPixelSize(imgdata)
		defocus, ampconst = self.getDefocusAmpConstForImage(imgdata, True)
		defocus *= 1.0e6
		self.checkDefocus(defocus, self.shortname)
		### get all CTF parameters, we also need to get the CS value from the database
		ctfdata = self.getBestCtfValue(imgdata, False)
		#ampconst = ctfdata['amplitude_contrast'] ### we could use this too

		# find cs
		cs = self.getCS(ctfdata)

		parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f" %(defocus, ampconst, voltage, cs, apix))
		emancmd = ("applyctf %s %s %s setparm flipphase" % (inimgpath, outimgpath, parmstr))

		apDisplay.printMsg("phaseflipping entire micrograph with defocus "+str(round(defocus,3))+" microns")
		apEMAN.executeEmanCmd(emancmd, showcmd = True)
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
		bestctfvalue = self.getBestCtfValue(imgdata, True)

		if bestctfvalue is None:
			apDisplay.printWarning("No ctf estimation for current image")
			self.badprocess = True
			return None

		if bestctfvalue['acerun'] is None:
			apDisplay.printWarning("No ctf runid for current image")
			self.badprocess = True
			return None

		if bestctfvalue['ctfvalues_file'] is None:
			# Since method = ace2 requires a ctfvalues_file,
			# create file from database values

			### cannot use ACE2 correction without CS value in database
			if not 'cs' in bestctfvalue:
				apDisplay.printMsg('No spherical abberation value in database, skipping image')
				self.badprocess = True
				return None

			# create ctfvalues_file from ctf run
			ctfvaluesfile = "tmp_ctfvaluesfile.txt"

			if abs(bestctfvalue['defocus1']) < abs(bestctfvalue['defocus2']):
				## this is the canonical form
				df1 = abs(bestctfvalue['defocus1'])
				df2 = abs(bestctfvalue['defocus2'])
				angast = bestctfvalue['angle_astigmatism']
			else:
				apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
				df1 = abs(bestctfvalue['defocus2'])
				df2 = abs(bestctfvalue['defocus1'])
				angast = bestctfvalue['angle_astigmatism'] + 90
			amp = bestctfvalue['amplitude_contrast']
			kv = imgdata['scope']['high tension']/1000
			cs = self.getCS(bestctfvalue)/1000
			conf = ctfdb.calculateConfidenceScore(bestctfvalue)

			if os.path.isfile(ctfvaluesfile):
				os.remove(ctfvaluesfile)
			f = open(ctfvaluesfile,'w')
			f.write("\tFinal Params for image: %s.mrc\n"%imgdata['filename'])
			# acecorrect definition is opposite to database
			f.write("\tFinal Defocus (m,m,deg): %.6e %.6e %.6f\n"%(df1,df2,-angast))
			f.write("\tAmplitude Contrast: %.6f\n"%amp)
			f.write("\tVoltage (kV): %.6f\n"%kv)
			f.write("\tSpherical Aberration (mm): %.6e\n"%cs)
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

		#apEMAN.executeEmanCmd(ace2cmd, showcmd = True)
		if self.params['verbose'] is True:
			ace2proc = subprocess.Popen(ace2cmd, shell=True)
		else:
			aceoutf = open("ace2.out", "a")
			aceerrf = open("ace2.err", "a")
			ace2proc = subprocess.Popen(ace2cmd, shell=True, stderr=aceerrf, stdout=aceoutf)
		ace2proc.wait()
		if self.stats['count'] <= 1:
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(0.1)
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

		bestctfvalue = self.getBestCtfValue(imgdata, True)

		if bestctfvalue is None:
			apDisplay.printWarning("No ctf estimation for current image")
			self.badprocess = True
			return None

		spi_imgpath = os.path.join(self.params['rundir'], self.shortname+".spi")

		df1 = abs(bestctfvalue['defocus1'])
		df2 = abs(bestctfvalue['defocus2'])
		defocus = (df1+df2)/2*1.0e6

		apix = apDatabase.getPixelSize(imgdata)
		voltage = imgdata['scope']['high tension']
		imgsize=imgdata['camera']['dimension']['y']

		# find cs
		cs = self.getCS(bestctfvalue)

		# convert image to spider ###proc2d
		emancmd="proc2d %s %s spidersingle"%(inimgpath,spi_imgpath)
		apEMAN.executeEmanCmd(emancmd, showcmd = True)
		apDisplay.printMsg("phaseflipping entire micrograph with defocus "+str(round(defocus,3))+" microns")
		# spider defocus is in Angstroms
		defocus *= 10000
		outimgpath = filters.phaseFlipImage(spi_imgpath, cs, defocus, voltage, imgsize, apix)

		# convert image back to mrc ###proc2d
		mrcname = os.path.join(self.params['rundir'], self.shortname+".mrc.corrected.mrc")
		emancmd="proc2d %s %s"%(outimgpath,mrcname)
		apEMAN.executeEmanCmd(emancmd, showcmd = True)
		# remove original spider image
		os.remove(spi_imgpath)

		return mrcname

	############################################################
	## General functions
	############################################################
	#=======================
	def mergeImageStackIntoBigStack(self, imgstackfile, imgdata):
		t0 = time.time()
		apDisplay.printMsg("filtering particles and adding to stack")
		# if applying a boxmask, write to a temporary file before adding to main stack
		bigimgstack = os.path.join(self.params['rundir'], self.params['single'])
		if self.params['boxmask'] is not None:
			bigimgstack = os.path.splitext(imgstackfile)[0]+"-premask.hed"
		### here is the craziness
		### step 1: read imgstackfile into memory
		imgstackmemmap = imagic.read(imgstackfile)
		### when only particle is read it defaults to a 2D array instead of 3D array
		if len(imgstackmemmap.shape) < 3:
			imgstackmemmap = imgstackmemmap.reshape(1, imgstackmemmap.shape[0], imgstackmemmap.shape[1])
		if self.params['debug'] is True:
			print "imgstackmemmap.shape", imgstackmemmap.shape
		apix = self.params['apix'] #apDatabase.getPixelSize(imgdata)

		boxshape = (self.boxsize, self.boxsize)
		processedParticles = []
		for particle in imgstackmemmap:

			### step 2: filter particles
			### high / low pass filtering
			#if self.params['pixlimit']:
			#	particle = imagefilter.pixelLimitFilter(particle, self.params['pixlimit'])
			if self.params['lowpass']:
				particle = imagefilter.lowPassFilter(particle, apix=apix, radius=self.params['lowpass'])
			if self.params['highpass']:
				particle = imagefilter.highPassFilter2(particle, self.params['highpass'], apix=apix)
			### unless specified, invert the images
			if self.params['inverted'] is True:
				particle = -1.0 * particle
			if particle.shape != boxshape:
				if self.boxsize <= particle.shape[0] and self.boxsize <= particle.shape[1]:
					particle = imagefilter.frame_cut(particle, boxshape)
				else:
					apDisplay.printError("particle shape (%dx%d) is smaller than boxsize (%d)"
						%(particle.shape[0], particle.shape[1], self.boxsize))

			### step 3: normalize particles
			#self.normoptions = ('none', 'boxnorm', 'edgenorm', 'rampnorm', 'parabolic') #normalizemethod
			if self.params['normalizemethod'] == 'boxnorm':
				particle = imagenorm.normStdev(particle)
			elif self.params['normalizemethod'] == 'edgenorm':
				particle = imagenorm.edgeNorm(particle)
			elif self.params['normalizemethod'] == 'rampnorm':
				particle = imagenorm.rampNorm(particle)
			elif self.params['normalizemethod'] == 'parabolic':
				particle = imagenorm.parabolicNorm(particle)

			### step 4: decimate/bin particles if specified
			### binning is last, so we maintain most detail and do not have to deal with binned apix
			if self.params['bin'] > 1:
				particle = imagefun.bin2(particle, self.params['bin'])

			#from scipy.misc import toimage
			#toimage(particle).show()

			processedParticles.append(particle)

		### step 5: merge particle list with larger stack
		apImagicFile.appendParticleListToStackFile(processedParticles, bigimgstack,
			msg=self.params['debug'])

		#remove original image stack from memory
		del imgstackmemmap
		del processedParticles

		t0 = time.time()
		# if applying boxmask, now mask the particles & append to stack
		if self.params['boxmask'] is not None:
			# normalize particles before boxing, since zeros in mask
			# can affect subsequent processing if not properly normalized
			apEMAN.executeEmanCmd("proc2d %s %s edgenorm inplace"%(bigimgstack,bigimgstack),showcmd=False)
			imgstack = apImagicFile.readImagic(bigimgstack, msg=False)
			maskstack = apImagicFile.readImagic(self.params['boxmaskf'],msg=False)
			for i in range(len(imgstack['images'])):
				imgstack['images'][i]*=maskstack['images'][i]
			maskedpartstack = os.path.splitext(imgstackfile)[0]+"-aftermask.hed"
			apImagicFile.writeImagic(imgstack['images'], maskedpartstack)
			bigimgstack = os.path.join(self.params['rundir'], self.params['single'])
			apEMAN.executeEmanCmd("proc2d %s %s flip"%(maskedpartstack,bigimgstack))

		### count particles
		bigcount = apFile.numImagesInStack(bigimgstack, self.boxsize/self.params['bin'])
		imgcount = apFile.numImagesInStack(imgstackfile, self.boxsize)

		### append to particle log file
		partlogfile = os.path.join(self.params['rundir'], self.timestamp+"-particles.info")
		f = open(partlogfile, 'a')
		for i in range(imgcount):
			partnum = self.particleNumber + i + 1
			line = str(partnum)+'\t'+os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
			f.write(line+"\n")
		f.close()

		self.mergestacktimes.append(time.time()-t0)

		return bigcount

############################################################
## Insert and Committing
############################################################

	#=======================
	def insertStackRun(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])

		stparamq = appiondata.ApStackParamsData()
		paramlist = ('boxSize','bin','aceCutoff','correlationMin','correlationMax',
			'checkMask','minDefocus','maxDefocus','fileType','inverted', 'defocpair', 'normalizemethod',
			'lowpass','highpass','pixlimit','norejects', 'tiltangle','startframe','nframe','driftlimit')

		### fill stack parameters
		for p in paramlist:
			if p.lower() in self.params:
				stparamq[p] = self.params[p.lower()]
			elif p=='aceCutoff' and self.params['ctfcutoff']:
				stparamq[p] = self.params['ctfcutoff']
			else:
				apDisplay.printMsg("missing "+p.lower())
		if self.params['phaseflipped'] is True:
			stparamq['phaseFlipped'] = True
			stparamq['fliptype'] = self.params['fliptype']
		if self.params['rotate'] is True:
			stparamq['rotate'] = True
		if self.params['normalizemethod'] == 'none':
			stparamq['normalized'] = False
		else:
			stparamq['normalized'] = True

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

		if self.params['helicalstep']:
			runq['selectionrun'] = self.newselectiondata
		else:
			runq['selectionrun'] = self.selectiondata

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
				rinstackq.insert(force=self.params['forceInsert'])
			return
		elif uniqrundatas and not uniqstackdatas:
			apDisplay.printError("Weird, run data without stack already in the database")
		elif not uniqrundatas and uniqstackdatas:
			apDisplay.printError("Weird, stack data without run already in the database")
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
						print i, uniqrundatas[0][i], runq[i]
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
						print i, uniqstackdatas[0][i], stackq[i]
				for i in prevrinstack[0]:
					if i=='stack' or i=='stackRun':
						continue
					print "rin =======",i,"========"
					if prevrinstack[0][i] != rinstackq[i]:
						print i, prevrinstack[0][i], rinstackq[i]
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i, prevrinstack[0][i], rinstackq[i]
				#apDisplay.printError("All parameters for a particular stack must be identical! \n"+\
				#			     "please check your parameter settings.")
			apDisplay.printWarning("Stack already exists in database! Will try and appending new particles to stack")
		return

	############################################################
	## Common parameters
	############################################################

	#=======================
	def setupParserOptions(self):
		super(Makestack2Loop, self).setupParserOptions()

		self.flipoptions = ('emanimage', 'emanpart', 'emantilt', 'spiderimage', 'ace2image', 'ace2imagephase')
		self.sortoptions = ('res80', 'res50', 'resplus', 'maxconf', 'conf3010', 'conf5peak', 'crosscorr')
		self.normoptions = ('none', 'boxnorm', 'edgenorm', 'rampnorm', 'parabolic') #normalizemethod

		### values
		self.parser.add_option("--single", dest="single", default="start.hed",
			help="create a single stack")
		self.parser.add_option("--filetype", dest="filetype", default='imagic',
			help="filetype, default=imagic")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="float",
			help="low pass filter")
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="float",
			help="high pass filter")
		self.parser.add_option("--pixlimit", dest="pixlimit", type="float",
			help="Limit pixel values to within <pixlimit> standard deviations", metavar="FLOAT")
		self.parser.add_option("--helicalstep", dest="helicalstep", type="float",
			help="helical step, in Angstroms")
		self.parser.add_option("--boxmask", dest="boxmask",
			help="box mask parameters: xmask,ymask,imask,falloff (in Angstroms)")

		### true/false
		self.parser.add_option("--phaseflip", dest="phaseflipped", default=False,
			action="store_true", help="perform CTF correction on the boxed images")
		self.parser.add_option("--invert", dest="inverted", default=False,
			action="store_true", help="contrast of the micrographs")
		self.parser.add_option("--no-invert", dest="inverted", default=False,
			action="store_false", help="contrast of the micrographs")
		self.parser.add_option("--spider", dest="spider", default=False,
			action="store_true", help="create a spider stack")
		self.parser.add_option("--forceInsert", dest="forceInsert", default=True,
			action="store_true", help="insert new entries without checking if corresponding data already exists")
		self.parser.add_option("--no-forceInsert", dest="forceInsert", action="store_false",
			help="check for duplicates before inserting new particles")

		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="do not make stack mean plot")

		self.parser.add_option("--boxfiles", dest="boxfiles", default=False,
			action="store_true", help="create only boxfiles, no stack")
		self.parser.add_option("--verbose", dest="verbose", default=False,
			action="store_true", help="Show extra ace2 information while running")
		self.parser.add_option("--finealign", dest="finealign", default=False,
			action="store_true", help="Align filaments vertically in a single interpolation")
		self.parser.add_option("--debug", dest="debug", default=False,
			action="store_true", help="Debug mode, print more to command line")

		### choice
		self.parser.add_option("--flip-type", dest="fliptype",
			help="CTF correction method", metavar="TYPE",
			type="choice", choices=self.flipoptions, default="ace2image" )
		self.parser.add_option("--sort-type", dest="ctfsorttype",
			help="CTF sorting method", metavar="TYPE",
			type="choice", choices=self.sortoptions, default="res80" )
		self.parser.add_option("--normalize-method", dest="normalizemethod",
			help="Normalization method", metavar="TYPE",
			type="choice", choices=self.normoptions, default="edgenorm" )

	#=======================
	def checkConflicts(self):
		super(Makestack2Loop, self).checkConflicts()
		if not primefactor.isGoodStack(self.params['boxsize']):
			apDisplay.printWarning("Boxsize does not contain recommended prime numbers")
			smallbox,bigbox = primefactor.getPrimeLimits(self.params['boxsize'])
			apDisplay.printWarning("You should use %d or %d for a boxsize instead"%(smallbox,bigbox))
		else:
			primes = primefactor.prime_factors(self.params['boxsize'])
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
		if self.params['fromstackid'] is not None and self.params['helicalstep'] is not None:
			apDisplay.printWarning("Helicalstep option cannot be used with --fromstackid, ignoring")
			self.params['helicalstep'] = None
		if self.params['fromstackid'] is None and self.params['selectionid'] is None:
			apDisplay.printError("please specify one of either --selectionid or --fromstackid")
		if self.params['maskassess'] is None and self.params['checkmask']:
			apDisplay.printError("particle mask assessment run need to be defined to check mask")
		if self.params['maskassess'] is not None and not self.params['checkmask']:
			apDisplay.printMsg("running mask assess")
			self.params['checkmask'] = True
		if self.params['particlelabel'] == 'user' and self.params['rotate'] is True:
			apDisplay.printError("User selected targets do not have rotation angles")
		if self.params['particlelabel'] == 'helical' and self.params['rotate'] is False:
			apDisplay.printWarning("Rotate parameter is not set, helical filaments will not be aligned")
		if self.params['boxmask'] is not None:
			bxlist=self.params['boxmask'].split(',')
			if len(bxlist) < 4:
				apDisplay.printError("boxmask requires 4 values separated by commas")
			self.params['bxmask']=int(float(bxlist[0]))
			self.params['bymask']=int(float(bxlist[1]))
			self.params['bimask']=int(float(bxlist[2]))
			self.params['falloff']=int(float(bxlist[3]))

	#=======================
	def resetStack(self):
		if self.params['helicalstep'] is not None:
			### a new set of ApParticleData are stored, in case
			### the inserted particles will be used to create future stacks
			### So new selection run name has the helical step size
			oldsrn = self.selectiondata['name']
			newsrn = "%s_%i"%(oldsrn,self.params['helicalstep'])
			self.newselectiondata = copy.copy(self.selectiondata)
			self.newselectiondata['name'] = newsrn

		if self.params['commit'] is True:
			self.insertStackRun()
		else:
			stackfile=os.path.join(self.params['rundir'], self.params['single'])
			apFile.removeStack(stackfile)

	#=======================
	def setStartingParticleNumber(self):
		self.resetStack()
		if self.params['commit'] is True:
			self.particleNumber = self.getExistingStackInfo()
			self.existingParticleNumber = self.particleNumber
		else:
			self.particleNumber = 0

	#=======================
	def checkRequireCtf(self):
		return super(Makestack2Loop,self).checkRequireCtf() or self.params['phaseflipped']

	#=======================
	def preLoopFunctions(self):
		super(Makestack2Loop, self).preLoopFunctions()
		### create an edge map for edge statistics
		box = self.boxsize
		self.boxedpartdatas = None
		### use a radius one pixel less than the boxsize
		self.edgemap = imagefun.filled_circle((box, box), box/2.0-1.0)
		self.summedParticles = numpy.zeros((box, box))

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

		stackpath = os.path.join(self.params['rundir'], self.params['single'])
		### delete this after testing
		apStack.averageStack(stack = stackpath)
		### Create Stack Mean Plot
		if self.params['commit'] is True and self.params['meanplot'] is True:
			stackid = apStack.getStackIdFromPath(stackpath)
			if stackid is not None:
				apStackMeanPlot.makeStackMeanPlot(stackid)

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
		### first check if there are any particles to commit
		if not isinstance(self.boxedpartdatas, list) or len(self.boxedpartdatas) == 0:
			return

		if self.framelist and self.params['commit'] is True:
			# insert framelist
			q = appiondata.ApStackImageFrameListData(stack=self.stackdata, image=imgdata, frames=self.framelist)
			q.insert(force=self.params['forceInsert'])
		#t0 = time.time()
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
			if not self.params['forceInsert']:
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
				stpartq.insert(force=self.params['forceInsert'])
		#self.insertdbtimes.append(time.time()-t0)

	#=======================
	def loopCleanUp(self, imgdata):
		super(Makestack2Loop, self).loopCleanUp(imgdata)
		### last remove any existing boxed files
		self.imgstackfile = None
		self.boxedpartdatas = []

if __name__ == '__main__':
	makeStack = Makestack2Loop()
	makeStack.run()
