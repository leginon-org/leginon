'''
Provides high level functions to access camera
'''

import leginonconfig
import node
import data
import cameraimage
import Numeric
import copy
import uidata
from timer import Timer

class NoCorrectorError(Exception):
	pass

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def __init__(self, node):
		self.node = node
		self.__cameraconfig = data.CameraConfigData()
		self.__cameraconfig.update(leginonconfig.CAMERA_CONFIG)
		self.camsize = None

	def acquireCameraImageData(self, camconfig=None, correction=None):
		## configure camera
		if camconfig is not None:
			print 'CONFIGURING CAMERA'
			camdata = self.configToEMData(camconfig)
			self.currentCameraEMData(camdata)
			print 'DONE CONFIG'

		if correction is None:
			cor = self.cameraConfig()['correct']
		else:
			cor = correction

		if cor:
			### get image data from corrector node
			try:
				print 'TRY'
				imdata = self.node.researchByDataID(('corrected image data',))
			except node.ResearchError:
				print 'EXC'
				raise NoCorrectorError('maybe corrector node is not running')
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
			self.node.printException()
			return None

	def autoOffset(self, camconfig):
		'''
		recalculate the image offset from the dimensions
		to get an image centered on the camera
		camconfig must be a CameraConfigData instance
		camconfig['offset'] will be set to new value
		'''
		if not self.camsize:
			self.camsize = {}
			currentcamdata = self.currentCameraEMData()
			if currentcamdata is None:
				self.camsize['x'] = 4096
				self.camsize['y'] = 4096
			else:
				self.camsize['x'] = currentcamdata['camera size']['x']
				self.camsize['y'] = currentcamdata['camera size']['y'] 

		sizex = self.camsize['x']
		sizey = self.camsize['y']

		binx = camconfig['binning']['x']
		biny = camconfig['binning']['y']
		sizex /= binx
		sizey /= biny
		pixx = camconfig['dimension']['x']
		pixy = camconfig['dimension']['y']
		offx = sizex / 2 - pixx / 2
		offy = sizey / 2 - pixy / 2
		if offx < 0 or offy < 0 or offx > sizex or offy > sizey:
			self.node.printerror('invalid dimension or binning produces invalid offset')
		camconfig['offset'] = {'x': offx, 'y': offy}

	def configUIData(self):
		'''
		returns camera configuration UI object
		'''

		return uidata.Struct('Camera Configuration', None, 'rw', self.uiConfig)

	def uiConfig(self, value=None):
		'''
		wrapper around CameraConfigData so it works with UI
		'''
		myconfig = self.cameraConfig(value)
		d = dict(myconfig)
		for key in ('id', 'session'):
			try:
				del d[key]
			except KeyError:
				pass
		return d

	def configToEMData(self, configdata):
		newconfig = copy.deepcopy(configdata)
		newemdata = data.CameraEMData()
		newemdata.friendly_update(newconfig)
		newemdata['id'] = ('camera',)
		return newemdata

	def cameraConfig(self, newconfig=None):
		'''
		get/set my CameraConfigData
		'''
		if newconfig is not None:
			newc = copy.deepcopy(newconfig)
			self.__cameraconfig.update(newc)
			c = self.__cameraconfig
			if c['auto square']:
				c['dimension']['y'] = c['dimension']['x']
				c['binning']['y'] = c['binning']['x']
			if c['auto offset']:
				self.autoOffset(c)
		return copy.deepcopy(self.__cameraconfig)
