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

class NoEMError(Exception):
	pass

class CameraConfigError(Exception):
	pass

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
				raise NoCorrectorError('cannot communicate with Corrector')
		else:
			### create my own data from acquisition
			try:
				scopedata = self.node.researchByDataID(('scope',))
				camdata = self.node.researchByDataID(('camera',))
			except node.ResearchError:
				raise NoEMError('cannot communicate with EM')

			### move image to its own key
			numimage = camdata['image data']
			camdata['image data'] = None
			dataid = self.node.ID()
			imdata = data.CameraImageData(session=self.node.session, id=dataid,
																		image=numimage, scope=scopedata,
																		camera=camdata)
		return imdata

	def setCameraDict(self, camdict):
		'''
		configure the camera given a dict similar to CameraEMData
		'''
		camdata = data.CameraEMData(id=('camera',))
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
			self.node.logger.exception(
															'camerafuncs.state: unable to set camera state')
			raise

	def getCameraEMData(self):
		'''
		return the current camera state as a CameraEMData object
		'''
		try:
			newcamdata = self.node.researchByDataID(('camera no image data',))
			return newcamdata
		except:
			self.node.logger.exception(
									'Cannot find current camera settings, EM may not be running.')
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
		self.applyasneeded = uidata.Boolean('Apply as needed', False, 'rw',
																				persist=True)
		self.cameraparams.addObject(applymeth)
		position = {'position': (applymeth.getPosition()['position'][0], 1),
								'justify': ['top', 'bottom']}
		self.cameraparams.addObject(self.applyasneeded, position=position)
		return self.cameraparams

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
	def __init__(self, node, usercallback=None):
		uidata.Container.__init__(self, 'Camera Configuration')
		self.node = node
		self.usercallback = usercallback

		try:
			camerasize = self.node.session['instrument']['camera size']
		except KeyError:
			self.node.logger.warning(
					'Cannot get instrument camera size, camera size set to 1024x1024')
			camerasize = 1024
		self.camerasize = {'x': camerasize, 'y': camerasize}

		self.binnings = [1, 2, 4, 6, 8, 12, 16]
		self.binningscale = {'x': None, 'y': None}

		self.xydefaults = {'binning':{'x': 1,'y': 1},
											  'dimension': {'x': 512,'y': 512},
											  'offset':{'x': 0,'y': 0}}
		self.xyobjects = {'dimension':{'x': None, 'y': None},
										  'binning':{'x': None, 'y': None},
										  'offset':{'x': None, 'y': None}}
		self.configuration = {'square': False, 'centered': False}

		self.defineUserInterface()

	def _onSetBinning(self, value, axis):
		if value is None:
			value = self.xydefaults['binning'][axis]

		if value not in self.binnings:
			differences = map(lambda x: abs(x - value), self.binnings)
			value = self.binnings[differences.index(min(differences))]

		for a, uiobject in self.xyobjects['binning'].items():
			if self.square.get() or a == axis:
				previousbinning = uiobject.get()
				self.binningscale[a] = float(previousbinning) / float(value)
			else:
				self.binningscale[a] = None

			if self.square.get() and a != axis:
				if value != previousbinning:
					uiobject.set(value, callback=False, thread=True, database=True)
		return value

	def onSetXBinning(self, value):
		return self._onSetBinning(value, 'x')

	def onSetYBinning(self, value):
		return self._onSetBinning(value, 'y')

	def userSetBinning(self, value):
		for a, scale in self.binningscale.items():
			if scale is None:
				continue
			for parameter in ('dimension', 'offset'):
				parametervalue = self.xyobjects[parameter][a].get()
				scaledparametervalue = int(round(parametervalue*scale))
				if parametervalue != scaledparametervalue:
					self.xyobjects[parameter][a].set(scaledparametervalue,
																						callback=False, database=True)
			self.binningscale[a] = None
		self.onModified(value)

	def _onSetDimension(self, value, axis):
		if value is None:
			value = self.xydefaults['dimension'][axis]

		if value < 0:
			value = 0

		camerasize = self.camerasize[axis]/self.xyobjects['binning'][axis].get()
		if value > camerasize:
			value = camerasize

		offset = self.xyobjects['offset'][axis].get()
		if self.centered.get():
			centeredoffset = (camerasize - value)/2
			if centeredoffset != offset:
				self.xyobjects['offset'][axis].set(centeredoffset, callback=False,
																						thread=True, database=True)
		elif value + offset > camerasize:
			self.xyobjects['offset'][axis].set(camerasize - value, callback=False,
																					thread=True, database=True)
		if self.square.get():
			for a, uiobject in self.xyobjects['dimension'].items():
				if a == axis:
					continue
				dimension = uiobject.get()
				if dimension != value:
					uiobject.set(value, callback=False, thread=True, database=True)
					camerasize = self.camerasize[a]/self.xyobjects['binning'][a].get()
					offset = self.xyobjects['offset'][a].get()
					if self.centered.get():
						centeredoffset = (camerasize - value)/2
						if centeredoffset != offset:
							self.xyobjects['offset'][a].set(centeredoffset, callback=False,
																							thread=True, database=True)
					elif value + offset > camerasize:
						self.xyobjects['offset'][a].set(camerasize - value,
																						callback=False, thread=True,
																						database=True)

		return value

	def onSetXDimension(self, value):
		return self._onSetDimension(value, 'x')

	def onSetYDimension(self, value):
		return self._onSetDimension(value, 'y')

	def _onSetOffset(self, value, axis):
		if value is None:
			value = self.xydefaults['offset'][axis]

		if value < 0:
			value = 0

		if value > self.camerasize[axis]:
			value = self.camerasize[axis]

		camerasize = self.camerasize[axis]/self.xyobjects['binning'][axis].get()
		dimension = self.xyobjects['dimension'][axis].get()
		if value + dimension > camerasize:
			self.xyobjects['dimension'][axis].set(camerasize - value, callback=False,
																						thread=True, database=True)

			if self.square.get():
				for a, uiobject in self.xyobjects['dimension'].items():
					if a == axis:
						continue
					camerasize = self.camerasize[a]/self.xyobjects['binning'][a].get()
					dimension = uiobject.get()
					if dimension != camerasize - value:
						uiobject.set(camerasize - value, callback=False, thread=True,
													database=True)

		return value

	def onSetXOffset(self, value):
		return self._onSetOffset(value, 'x')

	def onSetYOffset(self, value):
		return self._onSetOffset(value, 'y')

	def onCentered(self, value):
		if value:
			self.xyobjects['offset']['x'].disable(thread=True)
			self.xyobjects['offset']['y'].disable(thread=True)
		else:
			self.xyobjects['offset']['x'].enable(thread=True)
			self.xyobjects['offset']['y'].enable(thread=True)

		if value:
			for axis in ('x', 'y'):
				camerasize = self.camerasize[axis]/self.xyobjects['binning'][axis].get()
				dimension = self.xyobjects['dimension'][axis].get()
				offset = self.xyobjects['offset'][axis].get()
				centeredoffset = (camerasize - dimension)/2
				if centeredoffset != offset:
					self.xyobjects['offset'][axis].set(centeredoffset, callback=False,
																							thread=True, database=True)
		return value

	def onSquare(self, value):
		if value:
			self.xyobjects['binning']['y'].disable(thread=True)
			self.xyobjects['dimension']['y'].disable(thread=True)
		else:
			self.xyobjects['binning']['y'].enable(thread=True)
			self.xyobjects['dimension']['y'].enable(thread=True)

		if value:
			xbinning = self.xyobjects['binning']['x'].get()
			ybinning = self.xyobjects['binning']['y'].get()
			if ybinning != xbinning:
				self.xyobjects['binning']['y'].set(xbinning, callback=False,
																						thread=True, database=True)
#				binningscale = float(ybinning) / float(xbinning)
#				yoffset = self.xyobjects['offset']['y'].get()
#				scaledoffset = int(round(yoffset*binningscale))
#				if yoffset != scaledoffset:
#					self.xyobjects['offset']['y'].set(scaledoffset, callback=False,
#																						thread=True, database=True)

			xdimension = self.xyobjects['dimension']['x'].get()
			ydimension = self.xyobjects['dimension']['y'].get()
			if ydimension != xdimension:
				self.xyobjects['dimension']['y'].set(xdimension, callback=False,
																							thread=True, database=True)

				ycamerasize = self.camerasize['y']/self.xyobjects['binning']['y'].get()
				yoffset = self.xyobjects['offset']['y'].get()
				if self.centered.get():
					centeredoffset = (ycamerasize - xdimension)/2
					if centeredoffset != yoffset:
						self.xyobjects['offset']['y'].set(centeredoffset, callback=False,
																							thread=True, database=True)
				elif xdimension + yoffset > ycamerasize:
					self.xyobjects['offset']['y'].set(ycamerasize - xdimension,
																						callback=False, thread=True,
																						database=True)
		return value

	def onModified(self, value):
		if self.usercallback is not None:
			configuration = self.get()
			self.usercallback(configuration)

	def defineUserInterface(self):
		self.square = uidata.Boolean('Square', self.configuration['square'],
																	'rw', persist=True)
		self.centered = uidata.Boolean('Center', self.configuration['centered'],
																		'rw', persist=True)
		self.addObject(self.square, position={'position': (0, 0)})
		self.addObject(self.centered, position={'position': (0, 1)})

		size = len(str(max(self.camerasize.values())))

		for param in ('binning', 'dimension', 'offset'):
			container = uidata.Container(param[0].upper() + param[1:])
			for i, axis in ((1, 'y'), (0, 'x')):
				default = self.xydefaults[param][axis]
				uiobject = uidata.Integer(axis, default, 'rw', persist=True, size=size)
				container.addObject(uiobject, position={'position': (0, i)})
				self.xyobjects[param][axis] = uiobject
			self.addObject(container, position={'span': (1, 2)})

		self.exposuretime = uidata.Integer('Exposure Time (ms)', 500, 'rw',
																				persist=True, size=6)
		self.addObject(self.exposuretime, position={'span': (1, 2)})

		for parameter in ('binning', 'offset', 'dimension'):
			for axis in ('y', 'x'):
				callback = getattr(self, 'onSet' + axis.upper() + parameter[0].upper()
																															+ parameter[1:])
				self.xyobjects[parameter][axis].setCallback(callback)
				if parameter == 'binning':
					usercallback = self.userSetBinning
				else:
					usercallback = self.onModified
				self.xyobjects[parameter][axis].setUserCallback(usercallback)

		self.square.setCallback(self.onSquare)
		self.centered.setCallback(self.onCentered)

	def get(self):
		parameterdict = {}
		for key in self.xyobjects:
			parameterdict[key] = {}
			for axis in ('x', 'y'):
				parameterdict[key][axis] = self.xyobjects[key][axis].get()
		parameterdict['exposure time'] = self.exposuretime.get()
		return parameterdict

	def set(self, parameterdict):
		centered = self.isCentered(parameterdict)
		self.centered.set(centered)
		square = self.isSquare(parameterdict)
		self.square.set(square)

		for key in ('binning', 'offset', 'dimension'):
			for axis in ('y', 'x'):
				self.xyobjects[key][axis].set(parameterdict[key][axis])
		self.exposuretime.set(parameterdict['exposure time'])

	def isSquare(self, parameterdict):
		for parameter in ('binning', 'dimension'):
			if parameterdict[parameter]['x'] != parameterdict[parameter]['y']:
				return False
		return True

	def isCentered(self, parameterdict):
		for axis in ('x', 'y'):
			binning = parameterdict['binning'][axis] 
			if parameterdict['offset'][axis] != \
				(self.camerasize[axis]/binning)/2 - parameterdict['dimension'][axis]/2:
				return False
		return True

	def autoOffset(self, paramdict):
		camerasize = {'x':self.camerasize, 'y':self.camerasize}
		dimension = paramdict['dimension']
		binning = paramdict['binning']
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
		paramdict['offset'] = {'x': offx, 'y': offy}

