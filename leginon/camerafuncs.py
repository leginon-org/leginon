'''
Provides a mix-in class CameraFuncs
'''

import data
import cameraimage

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
		## it would be nice to get this all in one research
		## can't use 'camera' because don't want image data
		try:
			print 'researching camera no image data'
			newcamstate = self.researchByDataID('camera no image data')
			print 'done researching camera no image data'
			return newcamstate
		except Exception, detail:
			print detail
			print 'cameraState: unable to get camera state'
			return None

	def cameraConfigUISpec(self):
		'''
		returns a camera configuration Spec object for UI
		'''
		### Camera State Data Spec
		defaultsize = (512,512)
		camerasize = (2048,2048)
		offset = cameraimage.centerOffset(camerasize,defaultsize)
		defaultcamstate = {
			'exposure time': 500,
			'binning': {'x':1, 'y':1},
			'dimension': {'x':defaultsize[0], 'y':defaultsize[1]},
			'offset': {'x': offset[0], 'y': offset[1]}
		}
		camconfig = self.registerUIData('Camera Config', 'struct', default=defaultcamstate, permissions='rw')
		return camconfig

