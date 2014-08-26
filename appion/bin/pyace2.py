#!/usr/bin/env python

#pythonlib
import os
import re
import sys
import math
import time
import glob
import numpy
import shutil
import subprocess
#appion
from appionlib import apFile
from appionlib import apParam
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert
# other myami
from pyami import mrc, primefactor, imagefun

class Ace2Loop(appionLoop2.AppionLoop):
	"""
	appion Loop function that
	runs Craig's ace2 program
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def preLoopFunctions(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.ace2exe = self.getACE2Path()
		self.ctfrundata = None
		return

	#======================
	def getACE2Path(self):
		exename = 'ace2.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			ace2exe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ace2exe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ace2exe

	#======================
	def postLoopFunctions(self):
		pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*.corrected.mrc')
		apFile.removeFilePattern(pattern)
		ctfdb.printCtfSummary(self.params, self.imgtree)

	#======================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return True

		ctfvalue = ctfdb.getBestCtfByResolution(imgdata, msg=False)

		if ctfvalue is None:
			return True

		if conf > self.params['reprocess']:
			# small, unbinned images can give same defocus values for 1 & 2:
			if self.params['bin'] == 1 or ctfvalue['defocus1'] != ctfvalue['defocus2']:
				return False
		return True

	#======================
	def processImage(self, imgdata):
		self.ctfvalues = {}
		bestdef  = ctfdb.getBestCtfByResolution(imgdata, msg=True)
		apix = apDatabase.getPixelSize(imgdata)
		if (not (self.params['onepass'] and self.params['zeropass'])):
			maskhighpass = False
			ace2inputpath = os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc")
		else:
			maskhighpass = True
			filterimg = apImage.maskHighPassFilter(imgdata['image'],apix,1,self.params['zeropass'],self.params['onepass'])
			ace2inputpath = os.path.join(self.params['rundir'],imgdata['filename']+".mrc")
			mrc.write(filterimg,ace2inputpath)

		# make sure that the image is a square
		dimx = imgdata['camera']['dimension']['x']
		dimy = imgdata['camera']['dimension']['y']
		if dimx != dimy:
			dims = [dimx,dimy]
			dims.sort()
			apDisplay.printMsg("resizing image: %ix%i to %ix%i" % (dimx,dimy,dims[0],dims[0]))
			mrcarray = apImage.mrcToArray(ace2inputpath,msg=False)
			clippedmrc = apImage.frame_cut(mrcarray,[dims[0],dims[0]])
			ace2inputpath = os.path.join(self.params['rundir'],imgdata['filename']+".mrc")
			apImage.arrayToMrc(clippedmrc,ace2inputpath,msg=False)

		### pad out image to speed up FFT calculations for non-standard image sizes
		print "checking prime factor"
		if primefactor.isGoodStack(dimx) is False:
			goodsize = primefactor.getNextEvenPrime(dimx)
			factor = float(goodsize) / float(dimx)
			apDisplay.printMsg("padding image:  %ix%i to %ix%i" % (dimx,dimy,dimx*factor,dimy*factor))
			mrcarray = apImage.mrcToArray(ace2inputpath,msg=False)
#			paddedmrc = imagefun.pad(mrcarray, None, factor)
			paddedmrc = apImage.frame_constant(mrcarray, (dimx*factor,dimy*factor), cval=mrcarray.mean())
			ace2inputpath = os.path.join(self.params['rundir'],imgdata['filename']+".mrc")
			apImage.arrayToMrc(paddedmrc,ace2inputpath,msg=False)

		inputparams = {
			'input': ace2inputpath,
			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'apix': apix,
			'binby': self.params['bin'],
		}

		### make standard input for ACE 2
		apDisplay.printMsg("Ace2 executable: "+self.ace2exe)
		commandline = ( self.ace2exe
			+ " -i " + str(inputparams['input'])
			+ " -b " + str(inputparams['binby'])
			+ " -c " + str(inputparams['cs'])
			+ " -k " + str(inputparams['kv'])
			+ " -a " + str(inputparams['apix'])
			+ " -e " + str(self.params['edge_b'])+","+str(self.params['edge_t'])
			+ " -r " + str(self.params['rotblur'])
			+ "\n" )

		### run ace2
		apDisplay.printMsg("running ace2 at "+time.asctime())
		apDisplay.printColor(commandline, "purple")

		t0 = time.time()

		if self.params['verbose'] is True:
			ace2proc = subprocess.Popen(commandline, shell=True)
		else:
			aceoutf = open("ace2.out", "a")
			aceerrf = open("ace2.err", "a")
			ace2proc = subprocess.Popen(commandline, shell=True, stderr=aceerrf, stdout=aceoutf)

		ace2proc.wait()

		### check if ace2 worked
		basename = os.path.basename(ace2inputpath)
		imagelog = basename+".ctf.txt"
		if not os.path.isfile(imagelog) and self.stats['count'] <= 1:
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)

			if self.params['verbose'] is True:
				ace2proc = subprocess.Popen(commandline, shell=True)
			else:
				aceoutf = open("ace2.out", "a")
				aceerrf = open("ace2.err", "a")
				ace2proc = subprocess.Popen(commandline, shell=True, stderr=aceerrf, stdout=aceoutf)

			ace2proc.wait()

		if self.params['verbose'] is False:
			aceoutf.close()
			aceerrf.close()
		if not os.path.isfile(imagelog):
			lddcmd = "ldd "+self.ace2exe
			lddproc = subprocess.Popen(lddcmd, shell=True)
			lddproc.wait()
			apDisplay.printError("ace2 did not run")
		apDisplay.printMsg("ace2 completed in " + apDisplay.timeString(time.time()-t0))

		### parse log file
		self.ctfvalues = {
			'cs': self.params['cs'],
			'volts': imgdata['scope']['high tension'],
		}
		logf = open(imagelog, "r")
		apDisplay.printMsg("reading log file %s"%(imagelog))
		for line in logf:
			sline = line.strip()
			if re.search("^Final Defocus: ", sline):
				### old ACE2
				apDisplay.printError("This old version of ACE2 has a bug in the astigmastism, please upgrade ACE2 now")
				#parts = sline.split()
				#self.ctfvalues['defocus1'] = float(parts[2])
				#self.ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				#self.ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("^Final Defocus \(m,m,deg\):", sline):
				### new ACE2
				apDisplay.printMsg("Reading new ACE2 defocus")
				parts = sline.split()
				#print parts
				self.ctfvalues['defocus1'] = float(parts[3])
				self.ctfvalues['defocus2'] = float(parts[4])
				# ace2 defines negative angle from +x toward +y
				self.ctfvalues['angle_astigmatism'] = -float(parts[5])
			elif re.search("^Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("^Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		apDisplay.printMsg("============")
		avgdf = (self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])/2.0
		ampconst = 100.0*self.ctfvalues['amplitude_contrast']
		pererror = 100.0 * (self.ctfvalues['defocus1']-self.ctfvalues['defocus2']) / avgdf
		apDisplay.printMsg("Defocus: %.3f x %.3f um (%.2f percent astigmatism)"%
			(self.ctfvalues['defocus1']*1.0e6, self.ctfvalues['defocus2']*1.0e6, pererror ))
		apDisplay.printMsg("Angle astigmatism: %.2f degrees"%(self.ctfvalues['angle_astigmatism']))
		apDisplay.printMsg("Amplitude contrast: %.2f percent"%(ampconst))

		apDisplay.printColor("Final confidence: %.3f"%(self.ctfvalues['confidence']),'cyan')

		### double check that the values are reasonable
		if avgdf > self.params['maxdefocus'] or avgdf < self.params['mindefocus']:
			apDisplay.printWarning("bad defocus estimate, not committing values to database")
			self.badprocess = True

		if ampconst < 0.0 or ampconst > 80.0:
			apDisplay.printWarning("bad amplitude contrast, not committing values to database")
			self.badprocess = True

		if self.ctfvalues['confidence'] < 0.2:
			apDisplay.printWarning("bad confidence value, not committing values to database")
			self.badprocess = True

		## create power spectra jpeg
		mrcfile = imgdata['filename']+".mrc.edge.mrc"
		if os.path.isfile(mrcfile):
			jpegfile = os.path.join(self.powerspecdir, apDisplay.short(imgdata['filename'])+".jpg")
			ps = apImage.mrcToArray(mrcfile,msg=False)
			c = numpy.array(ps.shape)/2.0
			ps[c[0]-0,c[1]-0] = ps.mean()
			ps[c[0]-1,c[1]-0] = ps.mean()
			ps[c[0]-0,c[1]-1] = ps.mean()
			ps[c[0]-1,c[1]-1] = ps.mean()
			#print "%.3f -- %.3f -- %.3f"%(ps.min(), ps.mean(), ps.max())
			ps = numpy.log(ps+1.0)
			ps = (ps-ps.mean())/ps.std()
			cutoff = -2.0*ps.min()
			ps = numpy.where(ps > cutoff, cutoff, ps)
			cutoff = ps.mean()
			ps = numpy.where(ps < cutoff, cutoff, ps)
			#print "%.3f -- %.3f -- %.3f"%(ps.min(), ps.mean(), ps.max())
			apImage.arrayToJpeg(ps, jpegfile, msg=False)
			apFile.removeFile(mrcfile)
			self.ctfvalues['graph3'] = jpegfile
		otherfiles = glob.glob(imgdata['filename']+".*.txt")

		### remove extra debugging files
		for filename in otherfiles:
			if filename[-9:] == ".norm.txt":
				continue
			elif filename[-8:] == ".ctf.txt":
				continue
			else:
				apFile.removeFile(filename)

		if maskhighpass and os.path.isfile(ace2inputpath):
			apFile.removeFile(ace2inputpath)

		return

	#======================
	def commitToDatabase(self, imgdata):
		if self.ctfrundata is None:
			self.insertRunData()

		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrundata, self.params['rundir'])
		return True

	#======================
	def insertRunData(self):
		paramq = appiondata.ApAce2ParamsData()
		paramq['bin']     = self.params['bin']
		paramq['reprocess'] = self.params['reprocess']
		paramq['cs']      = self.params['cs']
		paramq['stig']    = True
		paramq['min_defocus'] = self.params['mindefocus']
		paramq['max_defocus'] = self.params['maxdefocus']
		paramq['edge_thresh'] = self.params['edge_t']
		paramq['edge_blur'] = self.params['edge_b']
		paramq['rot_blur']  = self.params['rotblur']
		paramq['refine2d']  = self.params['refine2d']
		paramq['onepass']   = self.params['onepass']
		paramq['zeropass']  = self.params['zeropass']

		runq=appiondata.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = self.getSessionData()
		runq['hidden']  = False
		runq['path']    = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['ace2_params'] = paramq
		runq.insert()
		self.ctfrundata = runq

	#======================
	def setupParserOptions(self):
		### values
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=1,
			help="Binning of the image before FFT", metavar="#")
		self.parser.add_option("--mindefocus", dest="mindefocus", type="float", default=0.1e-6,
			help="Minimal acceptable defocus (in meters)", metavar="#")
		self.parser.add_option("--maxdefocus", dest="maxdefocus", type="float", default=15e-6,
			help="Maximal acceptable defocus (in meters)", metavar="#")
		self.parser.add_option("--edge1", dest="edge_b", type="float", default=12.0,
			help="Canny edge parameters Blur Sigma", metavar="#")
		self.parser.add_option("--edge2", dest="edge_t", type="float", default=0.001,
			help="Canny edge parameters Edge Treshold(0.0-1.0)", metavar="#")
		self.parser.add_option("--rotblur", dest="rotblur", type="float", default=0.0,
			help="Rotational blur for low contrast CTF (in degrees), default 0", metavar="#")
		### true/false
		self.parser.add_option("--refine2d", dest="refine2d", default=False,
			action="store_true", help="Refine the defocus after initial ACE with 2d cross-correlation")
		self.parser.add_option("--verbose", dest="verbose", default=True,
			action="store_true", help="Show all ace2 messages")
		self.parser.add_option("--quiet", dest="verbose", default=True,
			action="store_false", help="Hide all ace2 messages")
		self.parser.add_option("--onepass", dest="onepass", type="float",
			help="Mask High pass filter radius for end of gradient mask in Angstroms", metavar="FLOAT")
		self.parser.add_option("--zeropass", dest="zeropass", type="float",
			help="Mask High pass filter radius for zero mask in Angstroms", metavar="FLOAT")
		#self.parser.add_option("--refineapix", dest="refineapix", default=False,
		#	action="store_true", help="Refine the pixel size")

	#======================
	def checkConflicts(self):
		if self.params['bin'] < 1:
			apDisplay.printError("bin must be positive")
		if (self.params['mindefocus'] is not None and
				(self.params['mindefocus'] > 1e-3 or self.params['mindefocus'] < 1e-9)):
			apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=1.5e-6")
		if (self.params['maxdefocus'] is not None and
				(self.params['maxdefocus'] > 1e-3 or self.params['maxdefocus'] < 1e-9)):
			apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=1.5e-6")
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())

		return


if __name__ == '__main__':
	imgLoop = Ace2Loop()
	imgLoop.run()


