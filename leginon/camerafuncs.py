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
		self.__cameraconfig = data.CameraConfigData()
		self.__cameraconfig.update(leginonconfig.CAMERA_CONFIG)

	def acquireCameraImageData(self, camconfig=None, correction=True):
		## try to use UI camera config if none was specified
		if camconfig == 'UI':
			try:
				use = self.useconfig.get()
			except:
				use = False
			if use:
				camconfig = self.cameraConfig()
			else:
				camconfig = None

		# now configure the camera if a camera config is available
		if camconfig is not None:
			print 'CONFIGURING CAMERA'
			camdata = self.configToEMData(camconfig)
			self.currentCameraEMData(camdata)
			print 'DONE CONFIG'

		if correction:
			### get image data from corrector node
			try:
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
			imdata = data.CameraImageData(session=self.node.session, id=dataid, image=numimage, scope=scopedata, camera=camdata)
			#print 'created imdata'
		return imdata

	def currentCameraEMData(self, camdata=None):
		'''
		Sets the camera state using camdata.
		If called without camdata, return the current camera state
		'''
#		t = Timer('camerafuncs state')
		if camdata is not None:
			if not isinstance(camdata, data.CameraEMData):
				raise TypeError('camdata not type CameraEMData')
#			t2 = Timer('publish camera state')
			try:
				self.node.publishRemote(camdata)
			except Exception, detail:
				print 'camerafuncs.state: unable to set camera state'
				raise
#			t2.stop()

		try:
			newcamdata = self.node.researchByDataID(('camera no image data',))
#			t.stop()
			return newcamdata
		except:
			#self.node.outputWarning('Cannot find current camera settings, EM may not be running.')
			print('Cannot find current camera settings, EM may not be running.')
			return None

	def autoOffset(self, camconfig):
		'''
		recalculate the image offset from the dimensions
		to get an image centered on the camera
		camconfig must be a CameraConfigData instance
		camconfig['offset'] will be set to new value
		'''
		camsize = self.node.session['instrument']['camera size']
		if not camsize:
			raise RuntimeError('instrument camsize: %s... maybe you are not connected to an instrument')
		camsize = {'x':camsize, 'y':camsize}
		bin = camconfig['binning']
		dim = camconfig['dimension']
		offset = autoOffset(camsize, dim, bin)
		camconfig['offset'] = offset

	def uiGetDictData(self, uidict):
		uidictdata = {}
		for key, value in uidict.items():
			if isinstance(value, uidata.Data):
				uidictdata[key] = value.get()
			else:
				uidictdata[key] = self.uiGetDictData(value)
		return uidictdata

	def uiSetDictData(self, uidict, dictdata):
		for key, value in uidict.items():
			if key in dictdata:
				if isinstance(value, uidata.Data):
					value.set(dictdata[key], callback=False)
				else:
					self.uiSetDictData(value, dictdata[key])

#	def uiCallback(self, value):
#		cameraconfig = self.uiGetDictData(self.uicameradict)
#		print 'cameraconfig =', cameraconfig
#		try:
#			cameraconfig = dict(self.cameraConfig(cameraconfig))
#		except KeyError, e:
#			print e
#			pass
#		self.uiSetDictData(self.uicameradict, cameraconfig)
#		return None

	def uiSet(self):
		cameraconfig = self.uiGetDictData(self.uicameradict)
		try:
			cameraconfig = dict(self.cameraConfig(cameraconfig))
		except:
			cameraconfig = {}
		self.uiSetDictData(self.uicameradict, cameraconfig)

	def configUIData(self):
		'''
		returns camera configuration UI object
		'''

		self.uicameradict = {}
		cameraparameterscontainer = uidata.Container('Camera Configuration')
		self.useconfig = uidata.Boolean('Use This Configuration', False, permissions='rw', persist=True)
		cameraparameterscontainer.addObject(self.useconfig)

		parameters = [('exposure time', 'Exposure time', uidata.Float, 500.0, 'rw'),
									('auto offset', 'Auto offset', uidata.Boolean, True, 'rw'),
									('auto square', 'Auto square', uidata.Boolean, True, 'rw')]

		pairs = [('dimension', 'Dimension', ['x', 'y'], uidata.Integer, [512, 512]),
							('offset', 'Offset', ['x', 'y'], uidata.Integer, [0, 0]),
							('binning', 'Binning', ['x', 'y'], uidata.Integer, [1, 1])]

		for key, name, axes, datatype, values, in pairs:
			self.uicameradict[key] = {}
			container = uidata.Container(name)
			for i in range(len(axes)):
				self.uicameradict[key][axes[i]] = datatype(axes[i], values[i], 'rw', persist=True)
				container.addObject(self.uicameradict[key][axes[i]])
			cameraparameterscontainer.addObject(container)

		for key, name, datatype, value, permissions in parameters:
			self.uicameradict[key] = datatype(name, value, permissions, persist=True)
			cameraparameterscontainer.addObject(self.uicameradict[key])

		setmethod = uidata.Method('Apply', self.uiSet)
		cameraparameterscontainer.addObject(setmethod)

		self.uiSet()
		return cameraparameterscontainer

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
				c['offset']['y'] = c['offset']['x']
			if c['auto offset']:
				self.autoOffset(c)
		return copy.deepcopy(self.__cameraconfig)

class SmartCameraParameters(uidata.Container):
	def __init__(self, node):
		uidata.Container.__init__(self, 'Camera Parameters')
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
			print 'camera size will be faked: 4096x4096'
			self.camerasize = 4096

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
		testmeth = uidata.Method('Test', self.test)

		self.squaretoggle = uidata.Boolean('Square', self.xyoptions['square'], 'rw', persist=True, callback=self.squareToggleCallback)
		self.centeredtoggle = uidata.Boolean('Centered', self.xyoptions['centered'], 'rw', persist=True, callback=self.centeredToggleCallback)

		self.addObjects((self.squaretoggle, self.centeredtoggle, self.xycontainer, self.exposuretime, testmeth))

	def test(self):
		params = self.get()
		print 'params', params

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
		pass

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
		## create a copy and then do aufoOffset on it
		tmpdict = copy.deepcopy(paramdict)
		self.autoOffset(tmpdict)
		## check if it was auto offset to begin with
		if axis in ('x','y'):
			if tmpdict['offset'][axis] != paramdict['offset'][axis]:
				return False
		return True
