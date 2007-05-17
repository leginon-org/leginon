#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import event
import imagewatcher
import threading
import node
from pyami import imagefun
import gui.wx.FFTMaker

class FFTMaker(imagewatcher.ImageWatcher):
	panelclass = gui.wx.FFTMaker.Panel
	settingsclass = data.FFTMakerSettingsData
	defaultsettings = {
		'process': False,
		'mask radius': 1.0,
		'label': '',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.postprocess = threading.Event()
		self.start()

	def processImageData(self, imagedata):
		'''
		calculate and publish fft of the imagedata
		'''
		if self.settings['process']:
			self.publishPowerImage(imagedata)

	def publishPowerImage(self, imagedata):
		imarray = imagedata['image']
		self.logger.info('Calculating power spectrum for image')
		pow = imagefun.power(imarray, self.settings['mask radius'])
		powdata = data.AcquisitionFFTData(session=self.session, source=imagedata, image=pow)

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
		iquery = data.AcquisitionImageData(session=self.session, label=label)
		images = self.research(iquery, readimages=False)
		# start with first chronologically
		images.reverse()
		for im in images:
			if self.postprocess.isSet():
				self.logger.info('stopping post processing')
				break
			## find if there is already an FFT
			fquery = data.AcquisitionFFTData(source=im)
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
