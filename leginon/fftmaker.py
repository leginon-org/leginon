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

		self.stop_post = threading.Event()
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
			if self.stop_post.isSet():
				self.logger.info('stopping post processing')
				break
			## find if there is already an FFT
			fquery = data.AcquisitionFFTData(source=im)
			fft = self.research(fquery, readimages=False)
			if fft:
				continue
			## read image
			num = im['image'].read()
			im.__setitem__('image', num, force=True)
			self.publishPowerImage(im)

	def uiStartPostProcess(self):
		label = self.postlabel.get()
		self.stop_post.clear()
		self.processByLabel(label)

	def uiStopPostProcess(self):
		self.logger.info('will stop after next iteration')
		self.stop_post.set()

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.ignore_images = uidata.Boolean('Ignore Images', True, 'rw', persist=True)
		self.maskrad = uidata.Float('Mask Radius (% of imagewidth)', 0.01, 'rw', persist=True)

		postproc = uidata.Container('Post Processing')
		self.postlabel = uidata.String('Label', '', 'rw', persist=True)
		poststart = uidata.Method('Start', self.uiStartPostProcess)
		poststop = uidata.Method('Stop', self.uiStopPostProcess)
		postproc.addObjects((self.postlabel, poststart, poststop))

		container = uidata.LargeContainer('FFT Maker')
		container.addObjects((self.ignore_images,self.maskrad, postproc))

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
