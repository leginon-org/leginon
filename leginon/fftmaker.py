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
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)

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
		imid = imagedata['id']
		print 'calculating power spectrum for image', imid
		pow = imagefun.power(imarray)
		powdata = data.AcquisitionFFTData(id=self.ID(), source=imagedata, image=pow)

		# filename
		self.setImageFilename(powdata)

		# not raising publish event because there is not one yet
		self.publish(powdata, database=True)
		print 'published power spectrum for image', imid

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.ignore_images = uidata.Boolean('Ignore Images', False, 'rw', persist=True)

		container = uidata.LargeContainer('FFT Maker')
		container.addObjects((self.ignore_images,))

		self.uiserver.addObject(container)

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		rootname = self.getRootName(imagedata)
		print 'rootname', rootname

		mystr = 'pow'
		sep = '_'
		parts = (rootname, mystr)

		filename = sep.join(parts)
		print 'FILENAME', filename

		imagedata['filename'] = filename

	def getRootName(self, imagedata):
		'''
		get the root name of an image from its parent
		'''
		parent_image = imagedata['source']

		## use root name from parent image
		parent_root = parent_image['filename']
		return parent_root
