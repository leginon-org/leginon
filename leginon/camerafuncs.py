'''
Provides a mix-in class CameraFuncs
'''

import data
import cameraimage
import Numeric

#CAMSIZE = (2048,2048)
CAMSIZE = (4096,4096)

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def cameraAcquireArray(self, camstate=None, correction=0):
		'''
		acquire an image with optional camstate and correction
		'''
		print 'setting camera state'
		if camstate is not None:
			self.cameraState(camstate)
		print 'camstate set'

		print 'researching'
		try:
			if correction:
				imdata = self.researchByDataID('normalized image data')
				imagearray = imdata.content
			else:
				imdata = self.researchByDataID('image data')
				imagearray = imdata.content['image data']
				print 'type(imagearray)', type(imagearray)
				imagearray = Numeric.array(imagearray, 'l')
		except Exception, detail:
			print detail
			print 'cameraAcquireArray: unable to acquire image data'
			imagearray = None
		print 'researching done'
		return imagearray

	def cameraAcquireCamera(self, camstate=None, correction=0):
		'''
		this will return entire camera data
		'''
		try:
			camdata = self.researchByDataID('camera')
			camstate = camdata.content
		except Exception, detail:
			print detail
			print 'cameraAcquireCamera: unable to acquire camera'
			camstate = None
		return camstate

	def cameraState(self, camstate=None):
		'''
		Sets the camera state to camstate.
		If called without camstate, return the current camera state
		'''
		if camstate is not None:
			try:
				print 'publishing camera'
				camdata = data.EMData('camera', camstate)
				self.publishRemote(camdata)
				print 'publishing camera done'
			except Exception, detail:
				print detail
				print 'cameraState: unable to set camera state'
		try:
			print 'researching camera no image data'
			newcamstate = self.researchByDataID('camera no image data')
			print 'done researching camera no image data'
			return newcamstate
		except Exception, detail:
			print detail
			print 'cameraState: unable to get camera state'
			return None

	def cameraDefaultOffset(self, camstate):
		'''
		recalculate the image offset from the dimmensions
		to get an image centered on the camera
		'''
		dimx = camstate['dimension']['x']
		dimy = camstate['dimension']['x'] 
		offy = CAMSIZE[0] / 2 - dimy / 2
		offx = CAMSIZE[1] / 2 - dimx / 2
		camstate['offset'] = {'x': offx, 'y': offy}

	def cameraConfigUIData(self):
		'''
		returns a camera configuration Spec object for UI server
		'''

		defaultcamstate = {
			'exposure time': 500,
			'binning': {'x': 1, 'y': 1},
			'dimension': {'x': 512, 'y': 512}
		}
		self.cameraDefaultOffset(defaultcamstate)
		camconfigdict = {'state': defaultcamstate, 'auto offset': 1}

		camconfig = self.registerUIData('Camera Configuration', 'struct', permissions='rw', default=camconfigdict, callback=self.cameraConfig)

		return camconfig

	def cameraConfig(self, value=None):
		'''
		keeps track of a camera configuration
		not necessarily the current camera state
		(use cameraState for that)
		'''
		if value is not None:
			if value['auto offset']:
				self.cameraDefaultOffset(value['state'])
			self.__cameraconfigvalue = value
		return self.__cameraconfigvalue
