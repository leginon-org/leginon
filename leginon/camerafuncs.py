'''
Provides a mix-in class CameraFuncs
'''

import data
import cameraimage
import Numeric

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def cameraAcquireArray(self, camstate=None, correction=0):
		'''
		acquire an image with optional camstate and correction
		'''
		if camstate is not None:
			self.cameraState(camstate)
		try:
			if correction:
				imdata = self.researchByDataID('normalized image data')
				imagearray = imdata.content
			else:
				imdata = self.researchByDataID('image data')
				imagearray = imdata.content['image data']
				imagearray = Numeric.array(imagearray, 'l')
		except Exception, detail:
			print detail
			print 'cameraAcquireArray: unable to acquire image data'
			imagearray = None
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
				camdata = data.EMData('camera', camstate)
				self.publishRemote(camdata)
			except Exception, detail:
				print detail
				print 'cameraState: unable to set camera state'
		try:
			newcamstate = self.researchByDataID('camera no image data')
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

		currentcamstate = self.cameraState()
		if currentcamstate is None:
			sizex = 2048
			sizey = 2048
		else:
			sizex = currentcamstate.content['camera size']['x']
			sizey = currentcamstate.content['camera size']['y'] 

		binx = camstate['binning']['x']
		biny = camstate['binning']['y']
		pixx = camstate['dimension']['x'] * binx
		pixy = camstate['dimension']['y'] * biny
		offx = sizex / 2 - pixx / 2
		offy = sizey / 2 - pixy / 2
		camstate['offset'] = {'x': offx, 'y': offy}

	def cameraConfigUIData(self):
		'''
		returns a camera configuration Spec object for UI server
		'''

		camconfig = self.registerUIData('Camera Configuration', 'struct', permissions='rw', callback=self.cameraConfig)

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
			self.cameraconfigvalue = value

		## initial value is current camera state
		if not hasattr(self, 'cameraconfigvalue'):
			self.cameraconfigvalue = {}
			self.cameraconfigvalue['auto offset'] = 1

			initstate = self.cameraState()
			if initstate is None:
				initstate = {
					'exposure time': 500,
					'dimension':{'x':512,'y':512},
					'binning':{'x':1, 'y':1},
					'offset':{'x':0,'y':0}
				}
			else:
				initstate = initstate.content

			self.cameraDefaultOffset(initstate)
			self.cameraconfigvalue['state'] = initstate

		return self.cameraconfigvalue
