#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
import event
import imagewatcher
import threading
import node
import calibrationclient
import numpy
import math
import pyami.quietscipy
import scipy.ndimage
from pyami import imagefun
import gui.wx.FFTMaker
from pyami import fftfun

class FFTMaker(imagewatcher.ImageWatcher):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.AcquisitionImagePublishEvent]
	panelclass = gui.wx.FFTMaker.Panel
	settingsclass = leginondata.FFTMakerSettingsData
	defaultsettings = {
		'process': False,
		'mask radius': 1.0,
		'label': '',
		'reduced': True,
		'save': False,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.calclient = calibrationclient.CalibrationClient(self)
		self.postprocess = threading.Event()
		self.start()

	def processImageData(self, imagedata):
		'''
		calculate and publish fft of the imagedata
		'''
		if self.settings['process']:
			rpixelsize = self.calclient.getImageReciprocalPixelSize(imagedata)
			pow = self.calculatePowerImage(imagedata)
			shape = pow.shape
			center = {'x':shape[1]/2,'y':shape[0]/2}
			self.ht = imagedata['scope']['high tension']
			self.cs = imagedata['scope']['tem']['cs']
			self.rpixelsize = rpixelsize
			self.panel.onNewPixelSize(rpixelsize,center,self.ht,self.cs)
			if imagedata['filename'] and self.settings['save']:
				self.publishPowerImage(imagedata,pow)

	def calculatePowerImage(self, imagedata):
			imarray = imagedata['image']
			imageshape = imarray.shape
			if imageshape[0] != imageshape[1]:
				new_dim = min(imageshape)
				imarray = imagefun.crop_at(imarray, (imageshape[0]/2,imageshape[1]/2), (new_dim,new_dim))
				imageshape = imarray.shape
			if self.settings['reduced']:
				size = max(imageshape)
				if size > 1024:
					imarray = scipy.ndimage.zoom(imarray, 1024.0/imageshape[0])
			self.logger.info('Calculating power spectrum for image')
			pow = imagefun.power(imarray, self.settings['mask radius'])
			self.setImage(numpy.asarray(pow, numpy.float32), 'Power')
			self.imageshape = imageshape
			return pow

	def estimateAstigmation(self,params):
		if self.rpixelsize['x'] != self.rpixelsize['y']:
			self.logger.error('Astigmatic defocus calculation not implemented for unequal x, y pixelsizes')
		z0, zast, ast_ratio, angle = fftfun.getAstigmaticDefocii(params,self.rpixelsize['x'],self.ht,self.cs)
		self.logger.info('z0 %.3f um, zast %.3f um (%.0f ), angle= %.1f deg' % (z0*1e6,zast*1e6,ast_ratio*100, angle*180.0/math.pi))

	def publishPowerImage(self, imagedata, powimage):
		powdata = leginondata.AcquisitionFFTData(session=self.session, source=imagedata, image=powimage)

		# filename
		self.setImageFilename(powdata)

		# not raising publish event because there is not one yet
		self.publish(powdata, database=True)
		self.logger.info('Published power spectrum for image')

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
