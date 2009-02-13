#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import fftmaker
import threading
import node
import os
import math
import time
import subprocess
import re
import numpy
import numextension
import pyami.quietscipy
import scipy.ndimage
from pyami import imagefun, mrc
import gui.wx.FFTAce
import calibrationclient
import instrument

class CTFAnalyzer(fftmaker.FFTMaker):
	eventinputs = fftmaker.FFTMaker.eventinputs
	panelclass = gui.wx.FFTAce.Panel
	settingsclass = leginondata.FFTAceSettingsData
	defaultsettings = {
		'process': False,
		'label': '',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		fftmaker.FFTMaker.__init__(self, id, session, managerlocation, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.calclient = calibrationclient.CalibrationClient(self)
		self.ace2exe = self.getACE2Path()
		self.start()

	def processImageData(self, imagedata):
		'''
		calculate and publish fft of the imagedata
		'''
		if self.settings['process']:
			pow = self.estimateCTF(imagedata)
			self.setImage(numpy.asarray(pow, numpy.float32), 'Power')

	def getACE2Path(self):
		exename = 'ace2.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			self.logger.error(exename+" was not found in path ")
		return ace2exe

	def estimateCTF(self, imagedata):
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		pixelsize = self.calclient.getPixelSize(mag, tem, cam)
		inputparams = {
			'input': os.path.join(imagedata['session']['image path'],imagedata['filename']+".mrc"),
			'cs': 2.0,
			'kv': imagedata['scope']['high tension']/1000.0,
			'apix': pixelsize*1e10,
			'binby': 1,
		}

		### make standard input for ACE 2
		commandline = ( self.ace2exe
			+ " -i " + str(inputparams['input'])
			+ " -b " + str(inputparams['binby'])
			+ " -c " + str(inputparams['cs'])
			+ " -k " + str(inputparams['kv'])
			+ " -a " + str(inputparams['apix']) + "\n" )

		### run ace2
		self.logger.info("run ace2 on %s" % (imagedata['filename']))
		#aceoutf = open("ace2.out", "a")
		#aceerrf = open("ace2.err", "a")
		t0 = time.time()
		#ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
		ace2proc = subprocess.Popen(commandline, shell=True)
		ace2proc.wait()

		### check if ace2 worked
		imagelog = imagedata['filename']+".mrc"+".ctf.txt"
		if not os.path.isfile(imagelog):
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)
			#ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
			ace2proc = subprocess.Popen(commandline, shell=True)
			ace2proc.wait()
		#aceoutf.close()
		#aceerrf.close()
		if not os.path.isfile(imagelog):
			self.logger.warning("ace2 did not run")

		### parse log file
		self.ctfvalues = {}
		logf = open(imagelog, "r")
		for line in logf:
			sline = line.strip()
			if re.search("^Final Defocus:", sline):
				parts = sline.split()
				self.ctfvalues['defocus1'] = float(parts[2])
				self.ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				self.ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("^Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("^Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		avgdf = (self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])/2.0
		ampconst = 100.0*self.ctfvalues['amplitude_contrast']
		pererror = 100.0 * (self.ctfvalues['defocus1']-self.ctfvalues['defocus2']) / avgdf
		self.logger.info("Amplitude contrast: %.2f percent"%(ampconst))
		self.logger.info("Final confidence: %.3f"%(self.ctfvalues['confidence']))
		self.logger.info("Defocus: %.3f x %.3f um, angle %.2f degress (%.2f %% astigmatism)"%
			(self.ctfvalues['defocus1']*1.0e6, self.ctfvalues['defocus2']*1.0e6, self.ctfvalues['angle_astigmatism'],pererror ))

		self.params={}
		self.params['maxdefocus']=abs(imagedata['scope']['defocus']) + 1e-5
		self.params['mindefocus']=max(abs(imagedata['scope']['defocus']) - 1e-5,1e-8)
		if avgdf < self.params['maxdefocus'] or avgdf > self.params['mindefocus']:
			#self.logger.warning("bad defocus estimate, not committing values to database")
			self.badprocess = True
		if ampconst < -0.001 or ampconst > 80.0:
			#self.logger.warning("bad amplitude contrast, not committing values to database")
			self.badprocess = True

		## create power spectra jpeg
		mrcfile = imagedata['filename']+".mrc.edge.mrc"
		pow = mrc.read(mrcfile)
		try:
			os.remove(mrcfile)
		except:
			self.logger.warning('%s could not be removed' % mrcfile)
		try:
			pow = numpy.log(pow)
		except OverflowError:
			pow = numpy.log(pow+1e-20)
		#mask_radius = int(self.settings['mask radius'] / 100.0 * pow.shape[0])
		#if mask_radius:
	#		imagefun.center_mask(pow, mask_radius)

		return imagefun.clip_power(pow,6)

	#======================

	def processByLabel(self, label):
		'''
		for each image in this session with the given label,
		calculate the FFT, until we find one that is already done
		'''
		## find images in this session with the given label
		iquery = leginondata.AcquisitionImageData(session=self.session, label=label)
		images = self.research(iquery, readimages=False)
		# start with first chronologically
		images.reverse()
		for im in images:
			if self.postprocess.isSet():
				self.logger.info('stopping post processing')
				break
			## find if there is already an FFT
			fquery = leginondata.AcquisitionFFTData(source=im)
			fft = self.research(fquery, readimages=False)
			if fft:
				continue
			self.publishPowerImage(im)

	def onStartPostProcess(self):
		label = self.settings['label']
		self.postprocess.set()
		self.processByLabel(label)

	def onStopPostProcess(self):
		self.logger.info('will stop after next iteration')
		self.postprocess.clear()

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		rootname = self.getRootName(imagedata)
		self.logger.info('Rootname %s' % (rootname,))

		mystr = 'pow'
		sep = '_'
		parts = (rootname, mystr)

		filename = sep.join(parts)
		self.logger.info('Filename %s' % (filename,))

		imagedata['filename'] = filename

	def getRootName(self, imagedata):
		'''
		get the root name of an image from its parent
		'''
		parent_image = imagedata['source']

		## use root name from parent image
		parent_root = parent_image['filename']
		return parent_root
