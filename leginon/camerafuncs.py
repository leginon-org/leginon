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

import leginonconfig
import node
import data
import Numeric
import copy
import uidata
from timer import Timer

class NoCorrectorError(Exception):
	pass

class CameraConfigError(Exception):
	pass

def autoOffset(camerasize, dimension, binning):
	'''
	calculate the image offset from the dimension/binning
	to get an image centered on the camera
	'''
	sizex = camerasize['x']
	sizey = camerasize['y']

	binx = binning['x']
	biny = binning['y']
	sizex /= binx
	sizey /= biny
	pixx = dimension['x']
	pixy = dimension['y']
	offx = sizex / 2 - pixx / 2
	offy = sizey / 2 - pixy / 2
	if offx < 0 or offy < 0 or offx > sizex or offy > sizey:
		raise RuntimeError('autoOffset: invalid offset calculated')
	offset = {'x': offx, 'y': offy}
	return offset

class CameraFuncs(object):
	'''
	Useful functions for nodes that use camera data
	'''
	def __init__(self, node):
		self.node = node

	def acquireCameraImageData(self, correction=True):
		'''
		Acquire data from the camera, optionally corrected
		This returns a CameraImageData object which will have
		and ID created by this node, even if the data was 
		originally created by another node (like Corrector)
		'''
		if correction:
			### get image data from corrector node
			try:
				imdata = self.node.researchByDataID(('corrected image data',))
			except node.ResearchError:
				raise NoCorrectorError('maybe corrector node is not running')
		else:
			### create my own data from acquisition
			scopedata = self.node.researchByDataID(('scope',))
			camdata = self.node.researchByDataID(('camera',))

			### move image to its own key
			numimage = camdata['image data']
			camdata['image data'] = None
			dataid = self.node.ID()
			imdata = data.CameraImageData(session=self.node.session, id=dataid, image=numimage, scope=scopedata, camera=camdata)
		return imdata

	def autoOffset(self, dimension, binning):
		camsize = self.node.session['instrument']['camera size']
		camsize = {'x':camsize, 'y':camsize}
		offset = autoOffset(camsize, dimension, binning)
		return offset

	def setCameraDict(self, camdict):
		'''
		configure the camera given a dict similar to CameraEMData
		'''
		camdata = CameraEMData(('camera',))
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
				message = 'Out of bounds: offset(%s)+binning(%s)*dimension(%s) = %s, camsize: %s' % (off[axis],bin[axis],dim[axis],bound,camsize)
				raise CameraConfigError(message)

	def setCameraEMData(self, camdata):
		'''
		Sets the camera state using camdata.
		'''
		if not isinstance(camdata, data.CameraEMData):
			raise TypeError('camdata not type CameraEMData')
		self.validateCameraEMData(camdata)
		camdata['id'] = ('camera',)
		try:
			self.node.publishRemote(camdata)
		except Exception, detail:
			print 'camerafuncs.state: unable to set camera state'
			raise

	def getCameraEMData(self):
		'''
		return the current camera state as a CameraEMData object
		'''
		try:
			newcamdata = self.node.researchByDataID(('camera no image data',))
			return newcamdata
		except:
			print('Cannot find current camera settings, EM may not be running.')
			return None

	def uiSetupContainer(self):
		'''
		Returns a container full of setup parameters.
		There are three ways that the camera can be configured prior
		to doing an acquisition:
		   1)  Explicit:  use the 'Apply' button provide here
		   2)  Slave:  do not configure, use existing config
		   3)  As needed: if 'Apply As Needed' is turned on:
		       when an acquisition is requested by the user, the
		       callback method should first call uiAutoApply before
		       acquiring images.
		'''
		container = uidata.Container('Camera Setup')

		self.cameraparams = SmartCameraParameters(self.node)
		applymeth = uidata.Method('Apply', self.uiApply)
		self.applyasneeded = uidata.Boolean('Apply as needed', False, 'rw', persist=True)

		container.addObjects((self.cameraparams, applymeth, self.applyasneeded))
		return container

	def uiApply(self):
		'''
		get params from SmartCameraParameters and set the Camera
		'''
		params = self.uiGetParams()
		self.setCameraDict(params)

	def uiGetParams(self):
		return self.cameraparams.get()

	def uiApplyAsNeeded(self):
		'''
		When a user requests image(s) to be acquired, this should be
		called before the acquisitions actually happen.
		This makes sure that the camera will be configured if 
		the 'Apply As Needed' option is turned on
		'''
		if self.applyasneeded.get():
			self.uiApply()

class SmartCameraParameters(uidata.Container):
	'''
	This is a UI data object that packages all the camera parameters.
	It requires a node instance in the initializer which is used
	to get the camera size of the current instrument.
	'''
	def __init__(self, node):
		uidata.Container.__init__(self, '')
		self.node = node

		self.setCameraSize()

		self.xyparamkeys = ('dimension', 'binning', 'offset')
		self.xydefaults = {
		  'dimension':{'x':512,'y':512},
		  'binning':{'x':1,'y':1},
		  'offset':{'x':0,'y':0},
		}
		self.xyvalues = {
		  'dimension':{'x':None,'y':None},
		  'binning':{'x':None,'y':None},
		  'offset':{'x':None,'y':None},
		}
		self.xycontainer = None
		self.xyoptions = {'square': True, 'centered': True}

		self.build()

	def setCameraSize(self):
		try:
			self.camerasize = self.node.session['instrument']['camera size']
		except:
			self.camerasize = 0

		if not self.camerasize:
			print 'There was a problem getting the current instrument camera size.'
			print 'camera size will be faked: 1024x1024'
			self.camerasize = 1024

	def squareToggleCallback(self, value):
		self.xyoptions['square'] = value
		self.fillXYContainer()
		return value

	def centeredToggleCallback(self, value):
		self.xyoptions['centered'] = value
		self.fillXYContainer()
		return value

	def build(self):
		self.xycontainer = uidata.Container('Geometry')

		self.exposuretime = uidata.Integer('Exposure Time (ms)', 500, 'rw', persist=True)
		self.squaretoggle = uidata.Boolean('Square image', self.xyoptions['square'], 'rw', persist=True, callback=self.squareToggleCallback)
		self.centeredtoggle = uidata.Boolean('Center image', self.xyoptions['centered'], 'rw', persist=True, callback=self.centeredToggleCallback)

		self.addObjects((self.squaretoggle, self.centeredtoggle, self.xycontainer, self.exposuretime))

	def get(self):
		paramdict = {}

		square = self.xyoptions['square']
		centered = self.xyoptions['centered']
		if centered:
			params = ('dimension','binning')
		else:
			params = ('dimension', 'binning', 'offset')
		for param in params:
			paramdict[param] = {}
			for axis in ('x','y'):
				paramdict[param][axis] = self.xyvalues[param][axis].get()
		if centered:
			self.autoOffset(paramdict)

		paramdict['exposure time'] = self.exposuretime.get()

		return paramdict

	def set(self, paramdict):
		'''
		this fills in the fields, but also determines if it is
		possible to use 'square' and 'centered'
		'''
		## set the toggle switches
		centered = self.isCentered(paramdict)
		self.centeredtoggle.set(centered)
		square = self.isSquare(paramdict)
		self.squaretoggle.set(square)

		if square:
			axes = ('x',)
		else:
			axes = ('x','y')

		## fill in the values
		if not centered:
			for axis in axes:
				self.xyvalues['offset'][axis].set(paramdict['offset'][axis])
		for param in ('dimension','binning'):
			for axis in axes:
				self.xyvalues[param][axis].set(paramdict[param][axis])
		self.exposuretime.set(paramdict['exposure time'])

	def clearXYContainer(self):
		if not self.xycontainer:
			return
		for param in self.xyparamkeys:
			try:
				self.xycontainer.deleteObject(param)
			except ValueError:
				pass
			for axis in ('x','y'):
				label = '%s %s' % (param, axis)
				try:
					self.xycontainer.deleteObject(label)
				except ValueError:
					pass

	def fillXYContainer(self):
		if not self.xycontainer:
			return

		self.clearXYContainer()

		square = self.xyoptions['square']
		centered = self.xyoptions['centered']
		showparams = list(self.xyparamkeys)
		if centered:
			showparams.remove('offset')
			self.xyvalues['offset']['x'] = None
			self.xyvalues['offset']['y'] = None

		for param in showparams:
			if square:
				label = '%s %s' % (param, 'x')
				default = self.xydefaults[param]['x']
				i = uidata.Integer(label, default, 'rw', persist=True)
				self.xycontainer.addObject(i)
				self.xyvalues[param]['x'] = i
				self.xyvalues[param]['y'] = i
			else:
				for axis in ('x','y'):
					label = '%s %s' % (param, axis)
					default = self.xydefaults[param][axis]
					i = uidata.Integer(label, default, 'rw', persist=True)
					self.xycontainer.addObject(i)
					self.xyvalues[param][axis] = i


	def autoOffset(self, paramdict):
		camsize = {'x':self.camerasize, 'y':self.camerasize}
		dim = paramdict['dimension']
		bin = paramdict['binning']
		paramdict['offset'] = autoOffset(camsize, dim, bin)

	def isSquare(self, paramdict):
		for param in self.xyparamkeys:
			if paramdict[param]['x'] != paramdict[param]['y']:
				return False
		return True

	def isCentered(self, paramdict):
		## create a copy and then do autoOffset on it
		tmpdict = copy.deepcopy(paramdict)
		self.autoOffset(tmpdict)
		## check if it was auto offset to begin with
		for axis in ('x','y'):
			if tmpdict['offset'][axis] != paramdict['offset'][axis]:
				return False
		return True
