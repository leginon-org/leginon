'''
Provides high level functions to access camera
'''

import data
import cameraimage
import Numeric
import copy
from timer import Timer

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def __init__(self, node):
		self.node = node

	def acquireArray(self, camstate=None, correction=0):
		'''
		acquire an image with optional camstate and correction
		'''
		if camstate is not None:
			self.state(camstate)
		t = Timer('research image')
		try:
			if correction:
				imdata = self.node.researchByDataID('normalized image data')
				imagearray = imdata.content
			else:
				imdata = self.node.researchByDataID('image data')
				imagearray = imdata.content['image data']
				print 'IMAGEARRAY shape', imagearray.shape
				print 'IMAGEARRAY typecode', imagearray.typecode()
		except Exception, detail:
			print detail
			print 'acquireArray: unable to acquire image data'
			imagearray = None
		t.stop()
		return imagearray

	def acquireCamera(self, camstate=None, correction=0):
		'''
		this will return entire camera data
		'''
		try:
			camdata = self.node.researchByDataID('camera')
			camstate = camdata.content
		except Exception, detail:
			print detail
			print 'acquireCamera: unable to acquire camera'
			camstate = None
		return camstate

	def state(self, camstate=None):
		'''
		Sets the camera state to camstate.
		If called without camstate, return the current camera state
		'''
		t = Timer('camerafuncs state')
		if camstate is not None:
			t2 = Timer('publish camera state')
			try:
				camdata = data.EMData('camera', camstate)
				self.node.publishRemote(camdata)
			except Exception, detail:
				print detail
				print 'camerafuncs.state: unable to set camera state'
			t2.stop()

		try:
			newcamstate = self.node.researchByDataID('camera no image data')
			t.stop()
			return newcamstate.content
		except Exception, detail:
			print detail
			print 'camerafuncs.state: unable to get camera state'
			return None

	def autoOffset(self, camstate):
		'''
		recalculate the image offset from the dimmensions
		to get an image centered on the camera
		'''

		currentcamstate = self.state()
		if currentcamstate is None:
			sizex = 4096
			sizey = 4096
		else:
			sizex = currentcamstate['camera size']['x']
			sizey = currentcamstate['camera size']['y'] 

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

	def configUIData(self):
		'''
		returns a camera configuration Spec object for UI server
		'''

		camconfig = self.node.registerUIData('Camera Configuration', 'struct', permissions='rw', callback=self.config)

		return camconfig

	def config(self, value=None):
		'''
		keeps track of a camera configuration
		not necessarily the current camera state
		(use state for that)
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
			### use the modified state
			value['state'] = state
			self.cameraconfigvalue = value

		## set default values
		if not hasattr(self, 'cameraconfigvalue'):
			self.cameraconfigvalue = {}
			self.cameraconfigvalue['auto square'] = 1
			self.cameraconfigvalue['auto offset'] = 1
			## attempt to get current camera state
			initstate = self.state()
			## if that failed, set default
			if initstate is None:
				initstate = {
					'exposure time': 500,
					'dimension':{'x':512,'y':512},
					'binning':{'x':1, 'y':1},
					'offset':{'x':0,'y':0}
				}

			self.autoOffset(initstate)
			self.cameraconfigvalue['state'] = initstate

		# return a copy of the current config value
		return copy.deepcopy(self.cameraconfigvalue)
