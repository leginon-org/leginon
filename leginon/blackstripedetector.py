#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
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
import gui.wx.BlackStripeDetector
#from pyami import fftfun

class BlackStripeDetector(imagewatcher.ImageWatcher):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.AcquisitionImagePublishEvent]
	panelclass = gui.wx.BlackStripeDetector.Panel
	settingsclass = leginondata.BlackStripeSettingsData
	defaultsettings = {
		'process': False,
		'pause': False,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.calclient = calibrationclient.CalibrationClient(self)
		self.postprocess = threading.Event()
		self.start()

	def processImageData(self, imagedata):
		'''
	divide image into stripes and get mean.sd of each stripe
	black stripe should have mean, sd = 0	
	returns error upon
		black stripe detection
		non standard K2 image size
	for super res, bins by 2 before calculation
		'''
		if self.settings['process']:
			k2_x = 3838
			k2_y = 3710
			swidth = 512 ######k2_x/8
			imarray = imagedata['image']
			imageshape = imarray.shape
			if imageshape[0] > 7000: # bin super res images by 2
				imarray = imagefun.bin2(imarray, 2)
				imageshape = imarray.shape
			if imageshape[0] == k2_x: #check for K2 size and rotate if necessary
				self.logger.info('image first array is 3838: %i ' % (imageshape[0],))
			elif imageshape[0] == k2_y:
				self.logger.info('image first array is 3710: %i rotating' % (imageshape[0],))
				imarray=imagefun.rotateImage90Degrees(imarray)
				imageshape = imarray.shape
			else: 
				self.logger.error('error: image size is unexpected!! Size is %i by %i' % (imageshape[0],imageshape[1]))
			ycenter = imageshape[1]/2
			for i in range (8):
				xcenter = i*swidth + 150   ###swidth/2
				stripearray =  imagefun.crop_at(imarray, (xcenter,ycenter), (100,3700))
				stripemean = numpy.mean(stripearray)
				stripesd = numpy.std(stripearray)	
				self.logger.info('xcenter %i ycenter %i stripe %i mean %f sd %f' % (xcenter, ycenter, i,stripemean,stripesd))
				if (stripemean ==0.0 and stripesd == 0.0):
					self.logger.error('error: Black stripe detected on stripe %i' % (i))


