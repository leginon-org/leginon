'''
Provides a mix-in class CameraFuncs
'''

import data
import cameraimage

CAMSIZE = (2048,2048)

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

	def cameraConfigUISpec(self):
		'''
		returns a camera configuration Spec object for UI server
		'''

		### default state will be current state if accessable
		### otherwise a default is defined here
		try:
			#defaultcamstate = self.cameraState()
			defaultcamstate = None
		except:
			defaultcamstate = None
		if defaultcamstate is None:
			defaultcamstate = {
				'exposure time': 500,
				'binning': {'x': 1, 'y': 1},
				'dimension': {'x': 512, 'y': 512}
			}
			self.cameraDefaultOffset(defaultcamstate)

		self.defaultoffset = self.registerUIData('Auto Offset (center image on camera)', 'boolean', default=1, permissions='rw')

		self.camconfig = self.registerUIData('Parameters', 'struct', permissions='rw', default=defaultcamstate)
		self.camconfig.registerCallback(self.cameraConfigCallback)

		camcont = self.registerUIContainer('Camera Config', (self.camconfig,self.defaultoffset))
		return camcont

	def cameraConfigCallback(self, value=None):
		if value is not None:
			if self.defaultoffset.get():
				self.cameraDefaultOffset(value)
			self.cameraconfigvalue = value
			print 'value set to', value
			
		return self.cameraconfigvalue
