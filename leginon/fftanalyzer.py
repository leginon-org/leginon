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
import numpy
import numextension
import pyami.quietscipy
import scipy.ndimage
from pyami import imagefun
from pyami import plot
import gui.wx.FFTAnalyzer
import calibrationclient
import instrument

class FFTAnalyzer(fftmaker.FFTMaker):
	eventinputs = fftmaker.FFTMaker.eventinputs
	panelclass = gui.wx.FFTAnalyzer.Panel
	settingsclass = leginondata.FFTAnalyzerSettingsData
	defaultsettings = {
		'process': False,
		'mask radius': 1.0,
		'label': '',
		'reduced': True,
		'save': False,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		fftmaker.FFTMaker.__init__(self, id, session, managerlocation, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.calclient = calibrationclient.CalibrationClient(self)
		self.start()

	def processImageData(self, imagedata):
		'''
		calculate and publish fft of the imagedata
		'''
		if self.settings['process']:
			pow = self.calculatePowerImage(imagedata)
			#self.displayPowerImage(pow)
			if imagedata['filename'] and self.settings['save']:
				self.publishPowerImage(imagedata,pow)
#			if self.settings['radial average']:
			if True:
				self.radialPlot(imagedata,pow)

	def radialPlot(self, imagedata,pow):
		scope = imagedata['scope']
		mag = scope['magnification']
		tem = scope['tem']
		camera = imagedata['camera']
		ccd = camera['ccdcamera']
		pixelsize = self.calclient.getPixelSize(mag,tem,ccd)
		if camera['binning']['x'] != camera['binning']['y']:
			self.logger.warning('Unequal binning radial average not implemented')
			return
		shape = pow.shape
		if shape[0] != shape[1]:
			self.logger.warning('Non square image shape radial average not implemented')
			return
		binned_pixelsize = pixelsize * camera['binning']['x']
		rec_pixelsize = 1/(self.imageshape[0]*1e10*binned_pixelsize)
		# calculate radial average of the power spectrum
		low = 0
		high = 0
		b = numextension.radialPower(pow, low, high)
		# plot
		indices = range(0,len(b))
		rec_pixels = map((lambda x: x*rec_pixelsize),indices)
		self.panelclass.setPlot(self.panel,rec_pixels,b)

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
