'''
Provides high level functions to access camera
'''

import data
import cameraimage
import Numeric
import copy
import uidata
from timer import Timer

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def __init__(self, node):
		self.node = node

	def acquireCameraImageData(self, camdata=None, correction=None):
		## configure camera
		if camdata is not None:
			self.currentCameraEMData(camdata)

		if correction is None:
			cor = self.config()['correct']
		else:
			cor = correction

		if cor:
			### get image data from corrector node
			imdata = self.node.researchByDataID(('corrected image data',))
		else:
			### create my own data from acquisition
			#print 'research'
			scopedata = self.node.researchByDataID(('scope',))
			#print 'scopedata =', scopedata
			camdata = self.node.researchByDataID(('camera',))
			#print 'camdata =', camdata

			### move image to its own key
			numimage = camdata['image data']
			camdata['image data'] = None
			dataid = self.node.ID()
			#print 'creating imdata'
			imdata = data.CameraImageData(id=dataid, image=numimage, scope=scopedata, camera=camdata)
			#print 'created imdata'
		return imdata

	def currentCameraEMData(self, camdata=None):
		'''
		Sets the camera state using camdata.
		If called without camdata, return the current camera state
		'''
		t = Timer('camerafuncs state')
		if camdata is not None:
			if not isinstance(camdata, data.CameraEMData):
				raise TypeError('camdata not type CameraEMData')
			t2 = Timer('publish camera state')
			try:
				self.node.publishRemote(camdata)
			except Exception, detail:
				print 'camerafuncs.state: unable to set camera state'
				raise
			t2.stop()

		try:
			newcamdata = self.node.researchByDataID(('camera no image data',))
			t.stop()
			return newcamdata
		except:
			return None

	def autoOffset(self, camdata):
		'''
		recalculate the image offset from the dimensions
		to get an image centered on the camera
		camdata must be a CameraEMData instance
		camdata['offset'] will be set to new value
		'''
		currentcamdata = self.currentCameraEMData()
		if currentcamdata is None:
			sizex = 4096
			sizey = 4096
		else:
			sizex = currentcamdata['camera size']['x']
			sizey = currentcamdata['camera size']['y'] 

		binx = camdata['binning']['x']
		biny = camdata['binning']['y']
		sizex /= binx
		sizey /= biny
		pixx = camdata['dimension']['x']
		pixy = camdata['dimension']['y']
		offx = sizex / 2 - pixx / 2
		offy = sizey / 2 - pixy / 2
		if offx < 0 or offy < 0 or offx > sizex or offy > sizey:
			self.node.printerror('invalid dimension or binning produces invalid offset')
		camdata['offset'] = {'x': offx, 'y': offy}

	def configUIData(self):
		'''
		returns camera configuration UI object
		'''

		return uidata.UIStruct('Camera Configuration', None, 'rw', self.uiConfig)

	def uiConfig(self, value=None):
		'''
		wrapper around configCameraEMData() so it works with UI
		'''
		camdata = data.CameraEMData(initializer=value['state'])
		value['state'] = camdata
		newvalue = self.configCameraEMData(value)
		camstate = copy.deepcopy(dict(newvalue['state']))
		del camstate['id']
		del camstate['session']
		del camstate['system time']
		newvalue['state'] = camstate
		return newvalue

	def configCameraEMData(self, value=None):
		print 'config, value=', value
		'''
		keeps track of a camera configuration
		not necessarily the current camera state
		(use currentCameraEMData() for that)
		'''
		## we will modify value, so make a deep copy
		value = copy.deepcopy(value)
		if value is not None:
			### make mods to state based on auto settings
			state = value['state']
			if value['auto square']:
				### an alternative would be to figure out
				### if x or y changed and set the other one
				### instead of just making x the master
				state['dimension']['y'] = state['dimension']['x']
				state['binning']['y'] = state['binning']['x']
			if value['auto offset']:
				self.autoOffset(state)
			#value['state'] = state
			self.cameraconfigvalue = value

		## set default values
		if not hasattr(self, 'cameraconfigvalue'):
			self.cameraconfigvalue = {}
			self.cameraconfigvalue['correct'] = 1
			self.cameraconfigvalue['auto square'] = 1
			self.cameraconfigvalue['auto offset'] = 1
			## attempt to get current camera state or set default
			camdata = self.currentCameraEMData()
			initstate = {}
			if camdata is None:
				print 'using default camera config'
				initstate['exposure time'] = 500
				initstate['dimension'] = {'x':1024, 'y':1024}
				initstate['binning'] = {'x':4, 'y':4}
				initstate['offset'] = {'x':0, 'y':0}
			else:
				initstate['exposure time'] = camdata['exposure time']
				initstate['dimension'] = camdata['dimension']
				initstate['binning'] = camdata['binning']
				initstate['offset'] = camdata['offset']

			self.autoOffset(initstate)
			self.cameraconfigvalue['state'] = initstate

		# return a copy of the current config value
		return copy.deepcopy(self.cameraconfigvalue)
