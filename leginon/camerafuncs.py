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
try:
	import numarray as Numeric
except:
	import Numeric
import copy
import uidata
from timer import Timer
import event
import newdict

class NoCorrectorError(Exception):
	pass

class CameraConfigError(Exception):
	pass

class CameraError(Exception):
	pass

class SetCameraError(CameraError):
	pass

class GetCameraError(CameraError):
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
		self.node.logger.debug('handleCorrectedImagePublish: %s' % (ievent.special_getitem('data', dereference=False),))
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
			self.node.logger.debug('stig for image: %s' % (scopedata['stigmator']['objective'],))
			camdata = self.emclient.getImage()
			numimage = camdata['image data']
			camdata['image data'] = None
			camdatanoimage = data.CameraEMData(initializer=camdata)
			imdata = data.CameraImageData(session=self.node.session, image=numimage, scope=scopedata, camera=camdatanoimage)
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
			self.node.logger.debug('setCameraEMData: %s' % (camdata,))
			self.node.emclient.setCamera(camdata)
		except Exception, detail:
			#self.node.logger.exception('Unable to set camera state')
			raise SetCameraError('Unable to set camera state')

	def getCameraEMData(self):
		'''
		return the current camera state as a CameraEMData object
		'''
		try:
			newcamdata = self.emclient.getCamera()
			return newcamdata
		except:
			#self.node.logger.exception(
			#						'Cannot find current camera settings, EM may not be running.')
			raise GetCameraError('Unable to get camera state')

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

		self.cameraparams = SmartCameraParameters(self.node, persist=True)
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

def centered_square_offset(camerasize, dimension, binning):
	'''
	This calculates an offset, given camsize, dimension, and binning
	'''
	binnedcamsize = camerasize / binning
	offset = (binnedcamsize - dimension) / 2
	return offset

def centered_square_table(camerasize):
	table = []
	for dimension in (4096, 2048, 1024, 512, 256):
		if dimension > camerasize:
			continue
		for binning in (1,2,4,8,16):
			offset = centered_square_offset(camerasize, dimension, binning)
			if binning*dimension > camerasize:
				continue
			key = (dimension, binning)
			config = {'dimension':{'x':dimension,'y':dimension}, 'binning':{'x':binning,'y':binning}, 'offset':{'x':offset,'y':offset}}
			table.append( (key, config) )
	return table

class SmartCameraParameters(uidata.Container):
	'''
	This is a UI data object that packages all the camera parameters.
	It requires a node instance in the initializer which is used
	to get the camera size of the current instrument.
	'''
	def __init__(self, node, usercallback=None, persist=False):
		uidata.Container.__init__(self, 'Camera Configuration')
		self.node = node
		self.usercallback = usercallback
		self.persist = persist

		try:
			camerasize = self.node.session['instrument']['camera size']
		except (KeyError, AttributeError, TypeError):
			self.node.logger.warning(
					'Cannot get instrument camera size, camera size set to 1024x1024')
			camerasize = 1024

		self.camerasize = {'x': camerasize, 'y': camerasize}

		self.defaults = {'binning':{'x': 1,'y': 1}, 'dimension': {'x': 512,'y': 512}, 'offset':{'x': 0,'y': 0}}

		self.defineUserInterface()

	def onModified(self, value=None):
		if self.usercallback is not None:
			configuration = self.get()
			self.usercallback(configuration)

	def disableManual(self):
		for parameter in ('Binning', 'Offset', 'Dimension'):
			for axis in ('y', 'x'):
				self[parameter][axis].disable()

	def enableManual(self):
		for parameter in ('Binning', 'Offset', 'Dimension'):
			for axis in ('y', 'x'):
				self[parameter][axis].enable()

	def configSelectedCallback(self, value):
		if value == 0:
			self.enableManual()
		else:
			self.disableManual()
			configkey = self.configselectdict.keys()[value]
			configdict = self.configselectdict[configkey]
			for parameter in ('Binning', 'Offset', 'Dimension'):
				lparam = parameter.lower()
				for axis in ('y', 'x'):
					self[parameter][axis].set(configdict[lparam][axis])
		self.onModified()
		return value

	def initConfigSelector(self):
		### assume square camera
		camerasize = self.camerasize['x']
		self.configselectdict = newdict.OrderedDict()
		table = centered_square_table(camerasize)
		self.configselectdict['Manual'] = None
		for item in table:
			dim = item[0][0]
			bin = item[0][1]
			key = '%s x %s' % (dim, bin)
			self.configselectdict[key] = item[1]
		items = self.configselectdict.keys()
		configselector = uidata.SingleSelectFromList('Common Configuration', [], 0, persist=self.persist)
		configselector.setList(items)
		return configselector

	def defineUserInterface(self):
		size = (len(str(max(self.camerasize.values()))), 1)
		for param in ('dimension', 'binning', 'offset'):
			
			container = uidata.Container(param[0].upper() + param[1:])
			for i, axis in ((1, 'y'), (0, 'x')):
				default = self.defaults[param][axis]
				uiobject = uidata.Integer(axis, default, 'rw', persist=self.persist, size=size)
				container.addObject(uiobject, position={'position': (0, i)})
			self.addObject(container)

		self.configselector = self.initConfigSelector()
		self.addObject(self.configselector)

		self.exposuretime = uidata.Integer('Exposure Time (ms)', 500, 'rw', persist=self.persist, size=(6, 1))
		self.addObject(self.exposuretime)

		for parameter in ('Binning', 'Offset', 'Dimension'):
			for axis in ('y', 'x'):
				usercallback = self.onModified

				self[parameter][axis].setUserCallback(self.onModified)
		#self.configselector.setCallback(self.configSelectedCallback)
		self.configselector.setUserCallback(self.configSelectedCallback)
		self.exposuretime.setUserCallback(self.onModified)

	def get(self):
		parameterdict = {}
		config  = self.configselector.getSelectedValue()
		if config == 'Manual':
			for key in ('Binning', 'Dimension', 'Offset'):
				parameterdict[key.lower()] = {}
				for axis in ('x', 'y'):
					parameterdict[key.lower()][axis] = self[key][axis].get()
		else:
			configvalue = copy.deepcopy(self.configselectdict[config])
			parameterdict.update(configvalue)

		parameterdict['exposure time'] = self.exposuretime.get()
		return parameterdict

	def set(self, parameterdict):
		try:
			self.validate(parameterdict)
		except ValueError, e:
			self.node.logger.exception(str(e))

		for parameter in ('Binning', 'Dimension', 'Offset'):
			for axis, uiobject in self[parameter].items():
				try:
					uiobject.set(parameterdict[parameter.lower()][axis])
				except KeyError:
					pass
		### select a common config if it matches
		self.checkCommonConfig(parameterdict)

		try:
			self.exposuretime.set(parameterdict['exposure time'])
		except KeyError:
			pass

	def checkCommonConfig(self, paramdict):
		parameterdict = {}
		for key in ('Binning', 'Dimension', 'Offset'):
			parameterdict[key.lower()] = {}
			for axis in ('x', 'y'):
				parameterdict[key.lower()][axis] = self[key][axis].get()
		index = 0
		manual = True
		for key,value in self.configselectdict.items():
			if value == parameterdict:
				self.configselector.setSelected(index)
				self.disableManual()
				manual = False
				break
			index += 1
		if manual:
			self.configselector.setSelected(0)
			self.enableManual()

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
				raise ValueError('Invalid parameters specified, dim: %s, bin: %s, off: %s' % (dimension,binning,offset))
