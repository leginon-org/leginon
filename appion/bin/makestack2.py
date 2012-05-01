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
from appionlib import apParticleExtractor
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apStack
from appionlib import apDefocalPairs
from appionlib import appiondata
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
			apDisplay.printError("database and file have different number of particles, create a new stack this one is corrupt")

		return numfilepart

	#=======================
	def processParticles(self,imgdata,partdatas,shiftdata):
		shortname = apDisplay.short(imgdata['filename'])
		### run batchboxer
		self.boxedpartdatas, self.imgstackfile, self.partmeantree = self.boxParticlesFromImage(imgdata,partdatas,shiftdata)
		if self.boxedpartdatas is None:
			apDisplay.printWarning("no particles were boxed from "+shortname+"\n")
			self.badprocess = True
			return None

		self.stats['lastpeaks'] = len(self.boxedpartdatas)

		apDisplay.printMsg("do not break function now otherwise it will corrupt run")
		time.sleep(1.0)

		### merge image particles into big stack
		totalpart = self.mergeImageStackIntoBigStack(self.imgstackfile, imgdata)

		### create a stack average every so often
		if self.stats['lastpeaks'] > 0:
			logpeaks = math.log(self.existingParticleNumber+self.stats['peaksum']+self.stats['lastpeaks'])
			if logpeaks > self.logpeaks:
				self.logpeaks = math.ceil(logpeaks)
				numpeaks = math.ceil(math.exp(self.logpeaks))
				apDisplay.printMsg("averaging stack, next average at %d particles"%(numpeaks))
				stackpath = os.path.join(self.params['rundir'], "start.hed")
				apStack.averageStack(stack=stackpath)
		return totalpart

	def getDDImageArray(self,imgdata):
		self.dd.setImageData(imgdata)
		return self.dd.correctFrameImage(self.params['startframe'],self.params['nframe'])

	def getOriginalImagePath(self, imgdata):
		imgname = imgdata['filename']
		shortname = apDisplay.short(imgdata['filename'])
		imgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
		if self.params['nframe'] != 0:
			self.params['uncorrected'] = True
			### dark/bright correct image
			tmpname = shortname+"-darknorm.dwn.mrc"
			imgpath = os.path.join(self.params['rundir'], tmpname)
			if not self.params['usedownmrc'] or not os.path.isfile(imgpath):
				imgarray = self.getDDImageArray(imgdata)
				apImage.arrayToMrc(imgarray,imgpath)
		return imgpath

	#=======================
	def boxParticlesFromImage(self, imgdata,partdatas,shiftdata):
		shortname = apDisplay.short(imgdata['filename'])

		### convert database particle data to coordinates and write boxfile
		boxfile = os.path.join(self.params['rundir'], imgdata['filename']+".box")
		parttree, boxedpartdatas = apBoxer.processParticleData(imgdata, self.boxsize, 
			partdatas, shiftdata, boxfile, rotate=self.params['rotate'])

		if self.params['boxfiles']:
			### quit and return, boxfile created, now process next image
			return None, None, None

		### check if we have particles again
		if len(partdatas) == 0 or len(parttree) == 0:
			apDisplay.printColor(shortname+" has no remaining particles and has been rejected\n","cyan")
			return None, None, None

		### get corrected leginon image path.  This will make corrected integrated frame image, too.
		imgpath = self.getOriginalImagePath(imgdata)

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

		### run apBoxer
		imgstackfile = os.path.join(self.params['rundir'], shortname+".hed")
		#emancmd = ("batchboxer input=%s dbbox=%s output=%s newsize=%i" 
		#	%(imgpath, emanboxfile, imgstackfile, self.params['boxsize']))
		apDisplay.printMsg("boxing "+str(len(parttree))+" particles into temp file: "+imgstackfile)
		t0 = time.time()
		if self.params['rotate'] is True:
			apBoxer.boxerRotate(imgpath, parttree, imgstackfile, self.boxsize)
			if self.params['finealign'] is True:
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
				apBoxer.boxerRotate(imgpath, parttree, imgstackfile, self.boxsize)
		else:
			apBoxer.boxer(imgpath, parttree, imgstackfile, self.boxsize)
		self.batchboxertimes.append(time.time()-t0)

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

		### if xmipp-norm before phaseflip:
		if self.params['xmipp-norm'] is not None and self.params['xmipp-norm-before'] is True:
			self.xmippNormStack(imgstackfile)

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
	def getCS(self, ctfvalue):
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
		ctfvalue = apCtf.getBestTiltCtfValueForImage(imgdata)
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

		imagicdata = apImagicFile.readImagic(imgstackfile)
		ctfpartstack = []
		for i in range(len(partdatas)):
			partdata = partdatas[i]
			prepartarray = imagicdata['images'][i]
			prepartmrc = "rawpart.dwn.mrc"
			postpartmrc = "ctfpart.dwn.mrc"
			apImage.arrayToMrc(prepartarray, prepartmrc, msg=False)

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

			parmstr = ("parm=%f,200,1,%.3f,0,17.4,9,1.53,%i,%.1f,%f" %(defocus, ampconst, voltage, cs, apix))
			emancmd = ("applyctf %s %s %s setparm flipphase" % (prepartmrc, postpartmrc, parmstr))
			apEMAN.executeEmanCmd(emancmd, showcmd=True)

			ctfpartarray = apImage.mrcToArray(postpartmrc)
			ctfpartstack.append(ctfpartarray)

		apImagicFile.writeImagic(ctfpartstack, ctfimgstackfile)
		return ctfimgstackfile

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
		cs = self.getCS(ctfdata)

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
		cs = self.getCS(ctfdata)

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

		if bestctfvalue['ctfvalues_file'] is None:
			# Since method=ace2 requires a ctfvalues_file,
			# create file from database values

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
		cs = self.getCS(bestctfvalue)

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
		emancmd += " clip=%d,%d"%(self.boxsize,self.boxsize)
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
				apDisplay.printMsg("missing "+p.lower())
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
		super(Makestack2Loop,self).setupParserOptions()

		self.flipoptions = ('emanimage', 'emanpart', 'emantilt', 'spiderimage', 'ace2image','ace2imagephase')
		### values
		self.parser.add_option("--single", dest="single", default="start.hed",
			help="create a single stack")
		self.parser.add_option("--filetype", dest="filetype", default='imagic',
			help="filetype, default=imagic")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="float",
			help="low pass filter")
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="float",
			help="high pass filter")
		self.parser.add_option("--xmipp-normalize", dest="xmipp-norm", type="float",
			help="normalize the entire stack using xmipp")

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
		self.parser.add_option("--xmipp-norm-before", dest="xmipp-norm-before", default=False,
			action="store_true", help="xmipp normalize before phaseflipping")

		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="do not make stack mean plot")

		self.parser.add_option("--boxfiles", dest="boxfiles", default=False,
			action="store_true", help="create only boxfiles, no stack")
		self.parser.add_option("--verbose", dest="verbose", default=False,
			action="store_true", help="Show extra ace2 information while running")
		self.parser.add_option("--finealign", dest="finealign", default=False,
			action="store_true", help="Align filaments vertically in a single interpolation")

		self.parser.add_option("--flip-type", dest="fliptype",
			help="CTF correction method", metavar="TYPE",
			type="choice", choices=self.flipoptions, default="emanpart" )

	#=======================
	def checkConflicts(self):
		super(Makestack2Loop,self).checkConflicts()
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
		if self.params['xmipp-norm'] is not None or self.params['xmipp-norm-before'] is not None:
			self.xmippexe = apParam.getExecPath("xmipp_normalize", die=True)
		if self.params['particlelabel'] == 'user' and self.params['rotate'] is True:
			apDisplay.printError("User selected targets do not have rotation angles")
		if self.params['particlelabel'] == 'helical' and self.params['rotate'] is False:
			apDisplay.printWarning("Rotate parameter is not set, helical filaments will not be aligned")
			

	def resetStack(self):
		if self.params['commit'] is True:
			self.insertStackRun()
		else:
			stackfile=os.path.join(self.params['rundir'], self.params['single'])
			apFile.removeStack(stackfile)

	def setStartingParticleNumber(self):
		self.resetStack()
		if self.params['commit'] is True:
			self.particleNumber = self.getExistingStackInfo()
			self.existingParticleNumber=self.particleNumber
		else:
			self.particleNumber = 0

	def checkRequireCtf(self):
			return self.params['ctfcutoff'] or self.params['mindefocus'] or self.params['maxdefocus'] or self.params['phaseflipped']

	#=======================
	def preLoopFunctions(self):
		super(Makestack2Loop,self).preLoopFunctions()

		### create an edge map for edge statistics
		box = self.boxsize
		### use a radius one pixel less than the boxsize
		self.edgemap = imagefun.filled_circle((box,box), box/2.0-1.0)

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
		if self.params['xmipp-norm'] is not None and self.params['xmipp-norm-before'] is False:
			self.xmippNormStack(stackpath)

		apDisplay.printColor("Timing stats", "blue")
		self.printTimeStats("Batch Boxer", self.batchboxertimes)
		self.printTimeStats("Ctf Correction", self.ctftimes)
		self.printTimeStats("Stack Merging", self.mergestacktimes)
		self.printTimeStats("Mean/Std Read", self.meanreadtimes)
		self.printTimeStats("DB Insertion", self.insertdbtimes)

	#=======================
	def xmippNormStack(self, stackpath):
			### convert stack into single spider files
			selfile = apXmipp.breakupStackIntoSingleFiles(stackpath)	

			### setup Xmipp command
			apDisplay.printMsg("Using Xmipp to normalize particle stack")
			normtime = time.time()
			xmippopts = ( " "
				+" -i %s"%os.path.join(self.params['rundir'],selfile)
				+" -method Ramp "
				+" -background circle %i"%(self.boxsize/self.params['bin']*0.4)
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
		try:
			self.boxedpartdatas
		except:
			return

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
		super(Makestack2Loop,self).loopCleanUp(imgdata)
		### last remove any existing boxed files
		self.imgstackfile = None
		self.boxedpartdatas = []

if __name__ == '__main__':
	makeStack = Makestack2Loop()
	makeStack.run()



