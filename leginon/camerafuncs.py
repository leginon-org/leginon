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

	def acquireCameraImageData(self, camstate=None, correction=None):
		## configure camera
		if camstate is not None:
			self.state(camstate)

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
			imdata = data.CameraImageData(dataid, image=numimage, scope=scopedata, camera=camdata)
			#print 'created imdata'
		return imdata

	def state(self, camstate=None):
		'''
		Sets the camera state to camstate.
		If called without camstate, return the current camera state
		'''
		t = Timer('camerafuncs state')
		if camstate is not None:
			t2 = Timer('publish camera state')
			try:
				camdata = data.CameraEMData(('camera',), initializer=camstate)
				self.node.publishRemote(camdata)
			except Exception, detail:
				print 'camerafuncs.state: unable to set camera state'
				raise
			t2.stop()

		try:
			newcamstate = self.node.researchByDataID(('camera no image data',))
			t.stop()
			return newcamstate
		except:
			return None

	def autoOffset(self, camstate):
		'''
		recalculate the image offset from the dimensions
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
			self.node.printerror('invalid dimension or binning produces invalid offset')
		camstate['offset'] = {'x': offx, 'y': offy}

	def configUIData(self):
		'''
		returns camera configuration UI object
		'''

		return uidata.UIStruct('Camera Configuration', None, 'rw', self.config)

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
			self.cameraconfigvalue['correct'] = 1
			self.cameraconfigvalue['auto square'] = 1
			self.cameraconfigvalue['auto offset'] = 1
			## attempt to get current camera state
			initstate = self.state()
			## if that failed, set default
			if initstate is None:
				print '%s unable to get camera state' % (self.node.id,)
				initstate = {
					'exposure time': 500,
					'dimension':{'x':1024,'y':1024},
					'binning':{'x':4, 'y':4},
					'offset':{'x':0,'y':0}
				}
			else:
				initstate = dict(initstate)
				del initstate['id']
				del initstate['session']
				del initstate['image data']
				del initstate['camera size']
				del initstate['system time']

			self.autoOffset(initstate)
			self.cameraconfigvalue['state'] = initstate

		# return a copy of the current config value
		return copy.deepcopy(self.cameraconfigvalue)
