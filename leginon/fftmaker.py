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
import Mrc
import threading
import uidata
import node
import imagefun

class FFTMaker(imagewatcher.ImageWatcher):
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.defineUserInterface()
		self.start()

	def processImageData(self, imagedata):
		'''
		calculate and publish fft of the imagedata
		'''
		if self.ignore_images.get():
			return
		self.publishPowerImage(imagedata)

	def publishPowerImage(self, imagedata):
		imarray = imagedata['image']
		self.logger.info('Calculating power spectrum for image')
		maskrad = self.maskrad.get()
		pow = imagefun.power(imarray, maskrad)
		powdata = data.AcquisitionFFTData(session=self.session, source=imagedata, image=pow)

		# filename
		self.setImageFilename(powdata)

		# not raising publish event because there is not one yet
		self.publish(powdata, database=True)
		self.logger.info('Published power spectrum for image')

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.ignore_images = uidata.Boolean('Ignore Images', True, 'rw', persist=True)
		self.maskrad = uidata.Float('Mask Radius (% of imagewidth)', 0.01, 'rw', persist=True)

		container = uidata.LargeContainer('FFT Maker')
		container.addObjects((self.ignore_images,self.maskrad))

		self.uicontainer.addObject(container)

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
