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
import event

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
		if hasattr(node, 'emclient'):
			self.emclient = self.node.emclient
		else:
			raise RuntimeError('CameraFuncs node needs emclient')
		self.correctedimageref = None
		self.node.addEventInput(event.CorrectedCameraImagePublishEvent, self.handleCorrectedImagePublish)

	def handleCorrectedImagePublish(self, ievent):
		self.correctedimageref = ievent

	def getCorrectedImage(self):
		if self.correctedimageref is not None:
			return self.correctedimageref['data']

	def acquireCameraImageData(self, correction=True):
		'''
		Acquire data from the camera, optionally corrected
		'''
		if correction:
			### get image data from corrector node
			try:
				imdata = self.getCorrectedImage()
			except node.ResearchError:
				raise NoCorrectorError('cannot communicate with Corrector')
		else:
			### create my own data from acquisition
			scopedata = self.emclient.getScope()
			camdata = self.emclient.getImage()

			### move image to its own key
			numimage = camdata['image data']
			camdata['image data'] = None
			imdata = data.CameraImageData(session=self.node.session, image=numimage, scope=scopedata, camera=camdata)
		return imdata

	def setCameraDict(self, camdict):
		'''
		configure the camera given a dict similar to CameraEMData
		'''
		camdata = data.CameraEMData()
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
		try:
			self.node.emclient.setCamera(camdata)
		except Exception, detail:
			self.node.logger.exception(
															'camerafuncs.state: unable to set camera state')
			raise

	def getCameraEMData(self):
		'''
		return the current camera state as a CameraEMData object
		'''
		try:
			newcamdata = self.emclient.getCamera()
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
		except AttributeError:
			camerasize = 1024

		self.camerasize = {'x': camerasize, 'y': camerasize}

		self.binnings = [1, 2, 4, 6, 8, 12, 16]
		self.binningscale = {'x': None, 'y': None}

		self.defaults = {'binning':{'x': 1,'y': 1},
										  'dimension': {'x': 512,'y': 512},
										  'offset':{'x': 0,'y': 0},
											'square': False,
											'centered': False}

		self.defineUserInterface()

	def _onSetBinning(self, value, axis):
		if value is None:
			value = self.defaults['binning'][axis]

		if value not in self.binnings:
			differences = map(lambda x: abs(x - value), self.binnings)
			value = self.binnings[differences.index(min(differences))]

		for a, uiobject in self['Binning'].items():
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
			for parameter in ('Dimension', 'Offset'):
				parametervalue = self[parameter][a].get()
				scaledparametervalue = int(round(parametervalue*scale))
				if parametervalue != scaledparametervalue:
					self[parameter][a].set(scaledparametervalue,
																	callback=False, database=True)
			self.binningscale[a] = None
		self.onModified(value)

	def _onSetDimension(self, value, axis):
		if value is None:
			value = self.defaults['dimension'][axis]

		if value < 0:
			value = 0

		camerasize = self.camerasize[axis]/self['Binning'][axis].get()
		if value > camerasize:
			value = camerasize

		offset = self['Offset'][axis].get()
		if self.centered.get():
			centeredoffset = (camerasize - value)/2
			if centeredoffset != offset:
				self['Offset'][axis].set(centeredoffset, callback=False,
																						thread=True, database=True)
		elif value + offset > camerasize:
			self['Offset'][axis].set(camerasize - value, callback=False,
																					thread=True, database=True)
		if self.square.get():
			for a, uiobject in self['Dimension'].items():
				if a == axis:
					continue
				dimension = uiobject.get()
				if dimension != value:
					uiobject.set(value, callback=False, thread=True, database=True)
					camerasize = self.camerasize[a]/self['Binning'][a].get()
					offset = self['Offset'][a].get()
					if self.centered.get():
						centeredoffset = (camerasize - value)/2
						if centeredoffset != offset:
							self['Offset'][a].set(centeredoffset, callback=False,
																							thread=True, database=True)
					elif value + offset > camerasize:
						self['Offset'][a].set(camerasize - value,
																						callback=False, thread=True,
																						database=True)

		return value

	def onSetXDimension(self, value):
		return self._onSetDimension(value, 'x')

	def onSetYDimension(self, value):
		return self._onSetDimension(value, 'y')

	def _onSetOffset(self, value, axis):
		if value is None:
			value = self.defaults['offset'][axis]

		if value < 0:
			value = 0

		camerasize = self.camerasize[axis]/self['Binning'][axis].get()
		if value > camerasize:
			value = camerasize

		dimension = self['Dimension'][axis].get()
		if value + dimension > camerasize:
			self['Dimension'][axis].set(camerasize - value, callback=False,
																	thread=True, database=True)

			if self.square.get():
				for a, uiobject in self['Dimension'].items():
					if a == axis:
						continue
					camerasize = self.camerasize[a]/self['Binning'][a].get()
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
			self['Offset']['x'].disable(thread=True)
			self['Offset']['y'].disable(thread=True)
		else:
			self['Offset']['x'].enable(thread=True)
			self['Offset']['y'].enable(thread=True)

		if value:
			for axis in ('x', 'y'):
				camerasize = self.camerasize[axis]/self['Binning'][axis].get()
				dimension = self['Dimension'][axis].get()
				offset = self['Offset'][axis].get()
				centeredoffset = (camerasize - dimension)/2
				if centeredoffset != offset:
					self['Offset'][axis].set(centeredoffset, callback=False,
																		thread=True, database=True)
		return value

	def onSquare(self, value):
		if value:
			self['Binning']['y'].disable(thread=True)
			self['Dimension']['y'].disable(thread=True)
		else:
			self['Binning']['y'].enable(thread=True)
			self['Dimension']['y'].enable(thread=True)

		if value:
			xbinning = self['Binning']['x'].get()
			ybinning = self['Binning']['y'].get()
			if ybinning != xbinning:
				self['Binning']['y'].set(xbinning, callback=False,
																	thread=True, database=True)
#				binningscale = float(ybinning) / float(xbinning)
#				yoffset = self['Offset']['y'].get()
#				scaledoffset = int(round(yoffset*binningscale))
#				if yoffset != scaledoffset:
#					self['Offset']['y'].set(scaledoffset, callback=False,
#																	thread=True, database=True)

			xdimension = self['Dimension']['x'].get()
			ydimension = self['Dimension']['y'].get()
			if ydimension != xdimension:
				self['Dimension']['y'].set(xdimension, callback=False,
																		thread=True, database=True)

				ycamerasize = self.camerasize['y']/self['Binning']['y'].get()
				yoffset = self['Offset']['y'].get()
				if self.centered.get():
					centeredoffset = (ycamerasize - xdimension)/2
					if centeredoffset != yoffset:
						self['Offset']['y'].set(centeredoffset, callback=False,
																		thread=True, database=True)
				elif xdimension + yoffset > ycamerasize:
					self['Offset']['y'].set(ycamerasize - xdimension,
																	callback=False, thread=True, database=True)
		return value

	def onModified(self, value):
		if self.usercallback is not None:
			configuration = self.get()
			self.usercallback(configuration)

	def defineUserInterface(self):
		self.square = uidata.Boolean('Square', self.defaults['square'],
																	'rw', persist=True)
		self.centered = uidata.Boolean('Center', self.defaults['centered'],
																		'rw', persist=True)
		self.addObject(self.square, position={'position': (0, 0)})
		self.addObject(self.centered, position={'position': (0, 1)})

		size = (len(str(max(self.camerasize.values()))), 1)

		for param in ('binning', 'dimension', 'offset'):
			container = uidata.Container(param[0].upper() + param[1:])
			for i, axis in ((1, 'y'), (0, 'x')):
				default = self.defaults[param][axis]
				uiobject = uidata.Integer(axis, default, 'rw', persist=True, size=size)
				container.addObject(uiobject, position={'position': (0, i)})
			self.addObject(container, position={'span': (1, 2)})

		self.exposuretime = uidata.Integer('Exposure Time (ms)', 500, 'rw',
																				persist=True, size=(6, 1))
		self.addObject(self.exposuretime, position={'span': (1, 2)})

		for parameter in ('Binning', 'Offset', 'Dimension'):
			for axis in ('y', 'x'):
				callback = getattr(self, 'onSet' + axis.upper() + parameter)
				self[parameter][axis].setCallback(callback)
				# Anchi wants to change binning
				# without other params updating
				#if parameter == 'Binning':
				#	usercallback = self.userSetBinning
				#else:
				#	usercallback = self.onModified
				usercallback = self.onModified

				self[parameter][axis].setUserCallback(usercallback)
		self.exposuretime.setUserCallback(self.onModified)
		self.square.setCallback(self.onSquare)
		self.centered.setCallback(self.onCentered)

	def get(self):
		parameterdict = {}
		for key in ('Binning', 'Dimension', 'Offset'):
			parameterdict[key.lower()] = {}
			for axis in ('x', 'y'):
				parameterdict[key.lower()][axis] = self[key][axis].get()
		parameterdict['exposure time'] = self.exposuretime.get()
		return parameterdict

	def set(self, parameterdict):
		if not self.validate(parameterdict):
			raise ValueError('Invalid parameters specified')

		centered = self.isCentered(parameterdict)
		self.centered.set(centered)

		square = self.isSquare(parameterdict)
		self.square.set(square)

		for parameter in ('Binning', 'Dimension', 'Offset'):
			for axis, uiobject in self[parameter].items():
				try:
					uiobject.set(parameterdict[parameter.lower()][axis])
				except KeyError:
					pass
		try:
			self.exposuretime.set(parameterdict['exposure time'])
		except KeyError:
			pass

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
		dimension = paramdict['dimension']
		binning = paramdict['binning']
		sizex = self.camerasize['x']
		sizey = self.camerasize['y']
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

	def validate(self, parameterdict):
		for axis, camerasize in self.camerasize.items():
			try:
				dimension = parameterdict['dimension'][axis]
			except KeyError:
				dimension = self['Dimension'][axis].get()

			try:
				offset = parameterdict['offset'][axis]
			except KeyError:
				offset = self['Offset'][axis].get()

			size = dimension + offset

			try:
				binning = parameterdict['binning'][axis]
			except KeyError:
				binning = self['Binning'][axis].get()
			
			if size > camerasize/binning:
				return False

		return True

