'''
Provides a mix-in class CameraFuncs
'''

import data
import cameraimage
import Numeric
from timer import Timer

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
		t = Timer('research image')
		try:
			if correction:
				imdata = self.researchByDataID('normalized image data')
				imagearray = imdata.content
			else:
				imdata = self.researchByDataID('image data')
				imagearray = imdata.content['image data']
				print 'IMAGEARRAY', imagearray.shape
		except Exception, detail:
			print detail
			print 'cameraAcquireArray: unable to acquire image data'
			imagearray = None
		t.stop()
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
		t = Timer('cameraState')
		if camstate is not None:
			t2 = Timer('publish camera state')
			try:
				camdata = data.EMData('camera', camstate)
				self.publishRemote(camdata)
			except Exception, detail:
				print detail
				print 'cameraState: unable to set camera state'
			t2.stop()

		try:
			newcamstate = self.researchByDataID('camera no image data')
			t.stop()
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
			sizex = 4096
			sizey = 4096
		else:
			sizex = currentcamstate.content['camera size']['x']
			sizey = currentcamstate.content['camera size']['y'] 

		binx = camstate['binning']['x']
		biny = camstate['binning']['y']
		sizex /= binx
		sizey /= biny
		pixx = camstate['dimension']['x']
		pixy = camstate['dimension']['y']
		offx = sizex / 2 - pixx / 2
		offy = sizey / 2 - pixy / 2
		if offx < 0 or offy < 0 or offx > sizex or offy > sizey:
			raise RuntimeError('invalid dimmension or binning produces invalid offset')
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
					'exposure time': 400,
					'dimension':{'x':1024,'y':1024},
					'binning':{'x':4, 'y':4},
					'offset':{'x':0,'y':0}
				}
			else:
				initstate = initstate.content

			self.cameraDefaultOffset(initstate)
			self.cameraconfigvalue['state'] = initstate

		return self.cameraconfigvalue
