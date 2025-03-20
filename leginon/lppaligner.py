#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
from leginon import acq as acquisition
from leginon import node, leginondata
from leginon import calibrationclient
import threading
from leginon import event
import time
import math
from pyami import imagefun, fftfun, ordereddict
import numpy
import scipy.ndimage as nd
import copy
import leginon.gui.wx.LppAligner
from leginon import player

class LppAligner(acquisition.Acquisition):
	panelclass = leginon.gui.wx.LppAligner.Panel
	settingsclass = leginondata.LppAlignerSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'global view offset':0.0,
		'compress ratio':8,
		'rotation':0.0,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):

		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.deltaz = 0.0
		self.v0 = 0.0

	def setParallelIlluminationOffsetToScope(self,view_type='on-plane'):
		errstr = 'paralllel illumination offset to instrument failed: %s'
		settings_name = '%s view offset' % view_type
		value = self.settings[settings_name]
		try:
			self.instrument.tem.ParallelIlluminationOffset = value
		except:
			self.logger.error(errstr % 'unable to access instrument')
			return
		self.logger.info('set parallel illumination offset to %7.5f' % (value))

	def preAcquire(self, presetdata, emtarget=None, channel=None, reduce_pause=False):
		super(LppAligner,self).preAcquire(presetdata, emtarget, channel, reduce_pause)
		self.v0 = self.instrument.tem.ParallelIlluminationOffset
		self.setParallelIlluminationOffsetToScope('global')

	def resetParallelIlluminationOffset(self):
		self.instrument.tem.ParallelIlluminationOffset = self.v0
		
	def compress(self, arr, rot_angle,ratio):
		arr = nd.rotate(arr, rot_angle,mode='nearest') # angle in degrees
		shape = arr.shape
		pad_axis_len = (shape[1]//ratio)*ratio + int(shape[1]%ratio > 0)*ratio
		pad_shape = list(shape)
		pad_shape[1] = pad_axis_len
		pad_arr = numpy.ones(pad_shape)*arr.mean()
		pad_arr[:,:shape[1]] = arr
		stack_shape = (shape[0],pad_axis_len//ratio,ratio)
		pad_arr = pad_arr.reshape(stack_shape)
		arr = numpy.sum(pad_arr, axis=2)
		return arr

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we acquire an image and then compress along x-axis 
		'''
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status

		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)
		args = (presetdata, emtarget, defaultchannel)
		try:
			if self.settings['background']:
				self.clearCameraEvents()
				t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
				t.start()
				self.waitExposureDone()
			else:
				self.acquirePublishDisplayWait(*args)
			myimage = self.imagedata['image']
			cmp_image = self.compress(myimage, self.settings['rotation'], self.settings['ratio'])
			self.setImage(cmp_image, 'Compressed')
		except:
			self.resetParallelIlluminationOffset()
			self.resetComaCorrection()
			raise
		finally:
			self.resetParallelIlluminationOffset()
			is_failed = self.resetComaCorrection()
			if is_failed:
				self.player.pause()
		return status

