#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
'''
Provides high level functions to access camera
'''

import node
import data
try:
	import numarray as Numeric
except:
	import Numeric
import event

class CameraError(Exception):
	pass

class NoCorrectorError(CameraError):
	pass

class CameraConfigError(CameraError):
	pass

class SetCameraError(CameraError):
	pass

class GetCameraError(CameraError):
	pass

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def __init__(self, node):
		self.node = node
		if hasattr(node, 'emclient'):
			self.emclient = self.node.emclient
		else:
			raise RuntimeError('no instrument client')
		self.correctedimageref = None
		self.node.addEventInput(event.CorrectedCameraImagePublishEvent,
														self.handleCorrectedImagePublish)

	def handleCorrectedImagePublish(self, ievent):
		eventdata = ievent.special_getitem('data', dereference=False)
		self.node.logger.debug('handleCorrectedImagePublish: %s' % (eventdata,))
		self.correctedimageref = ievent

	def getCorrectedImage(self):
		if self.correctedimageref is not None:
			return self.correctedimageref['data']

	def acquireCameraImageData(self, correction=True):
		'''
		Acquire data from the camera, optionally corrected
		'''
		if correction:
			# get image data from corrector node
			try:
				imdata = self.getCorrectedImage()
			except node.ResearchError:
				raise NoCorrectorError('cannot communicate with Corrector')
		else:
			# create my own data from acquisition
			scopedata = self.emclient.getScope()
			try:
				objectivestig = scopedata['stigmator']['objective']
			except:
				objectivestig = 'cannot get objective stig'
			self.node.logger.debug('Objective stig for image: %s' %  (objectivestig,))
			camdata = self.emclient.getImage()
			numimage = camdata['image data']
			camdata['image data'] = None
			camdatanoimage = data.CameraEMData(initializer=camdata)
			imdata = data.CameraImageData(session=self.node.session,
																		image=numimage,
																		scope=scopedata,
																		camera=camdatanoimage)
		return imdata

	def setCameraDict(self, camdict):
		'''
		configure the camera given a dict similar to CameraEMData
		'''
		if camdict is None:
			raise ValueError('invalid camera configuartion dictionary')
		camdata = data.CameraEMData()
		camdata.friendly_update(camdict)
		self.setCameraEMData(camdata)

	def getCameraDict(self):
		'''
		get current camera configuration as a dict
		'''
		camdata = self.getCameraEMData()
		return dict(camdata)

	def validateCameraEMData(self, camdata):
		'''
		raise an excpeption if there is a problem in a CameraEMData
		'''
		camsize = self.node.session['instrument']['camera size']
		dim = camdata['dimension']
		bin = camdata['binning']
		off = camdata['offset']

		## offset must not be negative
		if off['x'] < 0 or off['y'] < 0:
			raise CameraConfigError('illegal offset: %s' % (off,))
		## dimension must be greater than 0
		if dim['x'] < 1 or dim['y'] < 1:
			raise CameraConfigError('illegal dimension: %s' % (dim,))
		## offset, binning, dimension must not cause out of bounds
		for axis in ('x','y'):
			bound = off[axis] + bin[axis] * dim[axis]
			if bound > camsize:
				message = 'out of bounds: offset(%s)+binning(%s)*dimension(%s) = %s, camsize: %s' % (off[axis],bin[axis],dim[axis],bound,camsize)
				raise CameraConfigError(message)

	def setCameraEMData(self, camdata):
		'''
		Sets the camera state using camdata.
		'''
		if not isinstance(camdata, data.CameraEMData):
			raise TypeError('camdata not type CameraEMData')
		self.validateCameraEMData(camdata)
		try:
			self.node.logger.debug('setCameraEMData: %s' % (camdata,))
			self.node.emclient.setCamera(camdata)
		except Exception, detail:
			raise SetCameraError('unable to set camera state')

	def getCameraEMData(self):
		'''
		return the current camera state as a CameraEMData object
		'''
		try:
			newcamdata = self.emclient.getCamera()
			return newcamdata
		except:
			raise GetCameraError('unable to get camera state')

