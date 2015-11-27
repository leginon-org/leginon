# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import tem
import time
import sys
try:
	import nidaq
except:
	nidaq = None
use_nidaq = False

try:
	import comtypes
	import comtypes.client
	com_module =  comtypes
	import winerror
except ImportError:
	pass

# This scale convert beam tilt readout in radian to 
# Tecnai or TEM Scripting Illumination.RotationCenter value
# Depending on the version,  this may be 1.0 or closer to 6
rotation_center_scale = 1.0

# if a stage position movement is less than the following, then ignore it
minimum_stage = {
	'x': 5e-8,
	'y': 5e-8,
	'z': 5e-8,
	'a': 6e-5,
	'b': 6e-5,
}

class MagnificationsUninitialized(Exception):
	pass

class Tecnai(tem.TEM):
	name = 'Tecnai'
	use_normalization = False
	def __init__(self):
		tem.TEM.__init__(self)
		self.projection_submodes = {1:'LM',2:'Mi',3:'SA',4:'Mh',5:'LAD',6:'D'}
		self.special_submode_mags = {}
		#self.special_submode_mags = {380:('EFTEM',3)}
		self.projection_submode_map = self.special_submode_mags.copy()
		
		self.correctedstage = True
		try:
			com_module.CoInitializeEx(com_module.COINIT_MULTITHREADED)
		except:
			com_module.CoInitialize()

		self.tecnai = None
		# should determine this in updatecom instead of guessing it here
		for comname in ('Tecnai.Instrument', 'TEMScripting.Instrument.1'):
			try:
				self.tecnai = comtypes.client.CreateObject(comname)
				break
			except:
				pass

		# Fatal error
		if self.tecnai is None:
			raise RuntimeError('unable to initialize Tecnai interface')
		self.tem_constants = comtypes.client.Constants(self.tecnai)
		try:
			self.tom = comtypes.client.CreateObject('TEM.Instrument.1')
		except com_module.COMError, (hr, msg, exc, arg):
			print 'unable to initialize TOM Moniker interface, %s' % msg
			self.tom = None

		try:
			self.lowdose = comtypes.client.CreateObject('LDServer.LdSrv')
		except com_module.COMError, (hr, msg, exc, arg):
			print 'unable to initialize low dose interface, %s' % msg
			self.lowdose = None

		try:
			self.exposure = comtypes.client.CreateObject('adaExp.TAdaExp',
																					clsctx=com_module.CLSCTX_LOCAL_SERVER)
			self.adacom_constants = comtypes.client.Constants(self.exposure)
		except:
			self.exposure = None

		self.magnifications = []
		self.mainscreenscale = 44000.0 / 50000.0

		## figure out which intensity property to use
		## try to move this to installation
		try:
			ia = self.tecnai.Illumination.IlluminatedArea
		except:
			self.intensity_prop = 'Intensity'
		else:
			self.intensity_prop = 'IlluminatedArea'

		## figure out which gauge to use
		## try to move this to installation
		gauges_to_try = ['PPc1', 'P4', 'IGP1']
		self.pressure_prop = None
		for gauge in gauges_to_try:
			try:
				p = self.tecnai.Vacuum.Gauges(gauge)
				self.pressure_prop = gauge
			except:
				pass

		self.probe_str_const = {'micro': self.tem_constants.imMicroProbe, 'nano': self.tem_constants.imNanoProbe}
		self.probe_const_str = {self.tem_constants.imMicroProbe: 'micro', self.tem_constants.imNanoProbe: 'nano'}

	def getMagnificationsInitialized(self):
		if self.magnifications:
			return True
		else:
			return False

	def setCorrectedStagePosition(self, value):
		self.correctedstage = bool(value)
		return self.correctedstage

	def getCorrectedStagePosition(self):
		return self.correctedstage

	def checkStagePosition(self, position):
		current = self.getStagePosition()
		bigenough = {}
		for axis in ('x', 'y', 'z', 'a', 'b'):
			if axis in position:
				delta = abs(position[axis] - current[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = position[axis]
		return bigenough

	def setStagePosition(self, value):
		# pre-position x and y (maybe others later)
		value = self.checkStagePosition(value)
		if not value:
			return
		if self.correctedstage:
			delta = 2e-6
			stagenow = self.getStagePosition()
			# calculate pre-position
			prevalue = {}
			for axis in ('x','y','z'):
				if axis in value:
					prevalue[axis] = value[axis] - delta
			if prevalue:
				self._setStagePosition(prevalue)
		return self._setStagePosition(value)

	def setStageSpeed(self, value):
		self.tom.Stage.Speed = value

	def getStageSpeed(self):
		return self.tom.Stage.Speed

	def normalizeLens(self, lens = 'all'):
		if lens == 'all':
			self.tecnai.NormalizeAll()
		elif lens == 'objective':
			self.tecnai.Projection.Normalize(self.tem_constants.pnmObjective)
		elif lens == 'projector':
			self.tecnai.Projection.Normalize(self.tem_constants.pnmProjector)
		elif lens == 'allprojection':
			self.tecnai.Projection.Normalize(self.tem_constants.pnmAll)
		elif lens == 'spotsize':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmSpotsize)
		elif lens == 'intensity':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmIntensity)
		elif lens == 'condenser':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmCondenser)
		elif lens == 'minicondenser':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmMiniCondenser)
		elif lens == 'objectivepole':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmObjectivePole)
		elif lens == 'allillumination':
			self.tecnai.Illumination.Normalize(self.tem_constants.nmAll)
		else:
			raise ValueError

	def getScreenCurrent(self):
		return float(self.tecnai.Camera.ScreenCurrent)
	
	def getGunTilt(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.tecnai.Gun.Tilt.X)
		value['y'] = float(self.tecnai.Gun.Tilt.Y)

		return value
	
	def setGunTilt(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Gun.Tilt.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Gun.Tilt.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Gun.Tilt
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Gun.Tilt = vec
	
	def getGunShift(self):
		value = {'x': None, 'y': None}
		value['x'] = self.tecnai.Gun.Shift.X
		value['y'] = self.tecnai.Gun.Shift.Y

		return value
	
	def setGunShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Gun.Shift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Gun.Shift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Gun.Shift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Gun.Shift = vec

	def getHighTensionStates(self):
		return ['off', 'on', 'disabled']

	def getHighTensionState(self):
		state = self.tecnai.Gun.HTState
		if state == self.tem_constants.htOff:
			return 'off'
		elif state == self.tem_constants.htOn:
			return 'on'
		elif state == self.tem_constants.htDisabled:
			return 'disabled'
		else:
			raise RuntimeError('unknown high tension state')

	def getHighTension(self):
		return float(self.tecnai.Gun.HTValue)
	
	def setHighTension(self, ht):
		self.tecnai.Gun.HTValue = ht
	
	def getIntensity(self):
		intensity = getattr(self.tecnai.Illumination, self.intensity_prop)
		return float(intensity)

	def setIntensity(self, intensity, relative = 'absolute'):
		if relative == 'relative':
			intensity += getattr(self.tecnai.Illumination, self.intensity_prop)
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		setattr(self.tecnai.Illumination, self.intensity_prop, intensity)

	def getDarkFieldMode(self):
		if self.tecnai.Illumination.DFMode == self.tem_constants.dfOff:
			return 'off'
		elif self.tecnai.Illumination.DFMode == self.tem_constants.dfCartesian:
			return 'cartesian'
		elif self.tecnai.Illumination.DFMode == self.tem_constants.dfConical:
			return 'conical'
		else:
			raise SystemError
		
	def setDarkFieldMode(self, mode):
		if mode == 'off':
			self.tecnai.Illumination.DFMode = self.tem_constants.dfOff
		elif mode == 'cartesian':
			self.tecnai.Illumination.DFMode = self.tem_constants.dfCartesian
		elif mode == 'conical':
			self.tecnai.Illumination.DFMode = self.tem_constants.dfConical
		else:
			raise ValueError

	def getProbeMode(self):
		const = self.tecnai.Illumination.Mode
		probe = self.probe_const_str[const]
		return probe

	def setProbeMode(self, probe_str):
		const = self.probe_str_const[probe_str]
		self.tecnai.Illumination.Mode = const

	def getProbeModes(self):
		return list(self.probe_str_const.keys())

	def getBeamBlank(self):
		if self.tecnai.Illumination.BeamBlanked == 0:
			return 'off'
		elif self.tecnai.Illumination.BeamBlanked == 1:
			return 'on'
		else:
			raise SystemError
		
	def setBeamBlank(self, bb):
		if bb == 'off' :
			self.tecnai.Illumination.BeamBlanked = 0
		elif bb == 'on':
			self.tecnai.Illumination.BeamBlanked = 1
		else:
			raise ValueError
	
	def getStigmator(self):
		value = {'condenser': {'x': None, 'y': None},
							'objective': {'x': None, 'y': None},
							'diffraction': {'x': None, 'y': None}}
		try:

			value['condenser']['x'] = \
				float(self.tecnai.Illumination.CondenserStigmator.X)
			value['condenser']['y'] = \
				float(self.tecnai.Illumination.CondenserStigmator.Y)
		except:
			# use the default value None if values not float
			pass
		try:
			value['objective']['x'] = \
				float(self.tecnai.Projection.ObjectiveStigmator.X)
			value['objective']['y'] = \
				float(self.tecnai.Projection.ObjectiveStigmator.Y)
		except:
			# use the default value None if values not float
			pass
		try:
			value['diffraction']['x'] = \
				float(self.tecnai.Projection.DiffractionStigmator.X)
			value['diffraction']['y'] = \
				float(self.tecnai.Projection.DiffractionStigmator.Y)
		except:
			# use the default value None if values not float
			# this is known to happen in newer version of std Scripting
			# in imaging mode
			pass
		return value
		
	def setStigmator(self, stigs, relative = 'absolute'):
		for key in stigs.keys():
			if key == 'condenser':
				stigmator = self.tecnai.Illumination.CondenserStigmator
			elif key == 'objective':
				stigmator = self.tecnai.Projection.ObjectiveStigmator
			elif key == 'diffraction':
				stigmator = self.tecnai.Projection.DiffractionStigmator
			else:
				raise ValueError

			if relative == 'relative':
				try:
					stigs[key]['x'] += stigmator.X
				except KeyError:
					pass
				try:
					stigs[key]['y'] += stigmator.Y
				except KeyError:
					pass
			elif relative == 'absolute':
				pass
			else:
				raise ValueError

			try:
				stigmator.X = stigs[key]['x']
			except KeyError:
					pass
			try:
				stigmator.Y = stigs[key]['y']
			except KeyError:
					pass

			if key == 'condenser':
				self.tecnai.Illumination.CondenserStigmator = stigmator
			elif key == 'objective':
				self.tecnai.Projection.ObjectiveStigmator = stigmator
			elif key == 'diffraction':
				self.tecnai.Projection.DiffractionStigmator = stigmator
			else:
				raise ValueError
	
	def getSpotSize(self):
		return int(self.tecnai.Illumination.SpotsizeIndex)
	
	def setSpotSize(self, ss, relative = 'absolute'):
		if relative == 'relative':
			ss += self.tecnai.Illumination.SpotsizeIndex
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.tecnai.Illumination.SpotsizeIndex = ss
	
	def getBeamTilt(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.tecnai.Illumination.RotationCenter.X) / rotation_center_scale
		value['y'] = float(self.tecnai.Illumination.RotationCenter.Y) / rotation_center_scale 

		return value
	
	def setBeamTilt(self, vector, relative = 'absolute'):
		if relative == 'relative':
			original_vector = self.getBeamTilt()
			try:
				vector['x'] += original_vector['x']
			except KeyError:
				pass
			try:
				vector['y'] += original_vector['y']
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Illumination.RotationCenter
		try:
			vec.X = vector['x'] * rotation_center_scale
		except KeyError:
			pass
		try:
			vec.Y = vector['y'] * rotation_center_scale
		except KeyError:
			pass
		self.tecnai.Illumination.RotationCenter = vec
	
	def getBeamShift(self):
		value = {'x': None, 'y': None}
		try:
			value['x'] = float(self.tom.Illumination.BeamShiftPhysical.X)
			value['y'] = float(self.tom.Illumination.BeamShiftPhysical.Y)
		except:
			# return None if has exception
			pass
		return value

	def setBeamShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tom.Illumination.BeamShiftPhysical.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tom.Illumination.BeamShiftPhysical.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tom.Illumination.BeamShiftPhysical
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tom.Illumination.BeamShiftPhysical = vec
	
	def getImageShift(self):
		value = {'x': None, 'y': None}
		try:
			value['x'] = float(self.tecnai.Projection.ImageBeamShift.X)
			value['y'] = float(self.tecnai.Projection.ImageBeamShift.Y)
		except:
			# return None if has exception
			pass
		return value
	
	def setImageShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Projection.ImageBeamShift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Projection.ImageBeamShift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Projection.ImageBeamShift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Projection.ImageBeamShift = vec
	
	def getRawImageShift(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.tecnai.Projection.ImageShift.X)
		value['y'] = float(self.tecnai.Projection.ImageShift.Y)
		return value
	
	def setRawImageShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Projection.ImageShift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Projection.ImageShift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Projection.ImageShift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Projection.ImageShift = vec
	
	def getDefocus(self):
		return float(self.tecnai.Projection.Defocus)
	
	def setDefocus(self, defocus, relative = 'absolute'):
		old_defocus = self.tecnai.Projection.Defocus
		if relative == 'relative':
			defocus += old_defocus
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		# normalize by always sending Eucentric focus first
		self.tecnai.Projection.Focus = 0.0
		self.tecnai.Projection.Defocus = defocus
	
	def resetDefocus(self):
		self.tecnai.Projection.ResetDefocus()

	def getMagnification(self, index=None):
		if index is None:
			return int(round(self.tecnai.Projection.Magnification))
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications[index]
			except IndexError:
				raise ValueError('invalid magnification index')

	def getMainScreenMagnification(self):
		return int(round(self.tecnai.Projection.Magnification*self.mainscreenscale))

	def getMainScreenScale(self):
		return self.mainscreenscale

	def setMainScreenScale(self, mainscreenscale):
		self.mainscreenscale = mainscreenscale

	def getProjectionSubModeIndex(self):
		'''
		get from current condition.
		'''
		return self.tecnai.Projection.SubMode

	def getProjectionSubModeName(self):
		'''
		get from current condition.
		'''
		mag = self.getMagnification()
		if mag not in self.special_submode_mags:
			return self.projection_submodes[self.tecnai.Projection.SubMode]
		else:
			return self.special_submode_mags[mag][0]

	def normalizeProjectionForMagnificationChange(self, new_mag_index):
		'''
		Normalize objective and projector if submode indices are
		not adjacent.  This is necessary because of a lack of feature
		in the normalization options from TUI. Insert this before
		new magnification is set.
		'''
		try:
			# This assumes that we are still at the old mag.
			old_submode_index = self.tecnai.Projection.SubMode
		except:
			raise ValueError('can not get projection submode')
		self.setMagnificationIndex(new_mag_index)
		new_submode_index = self.getProjectionSubModeIndex()
		if abs(old_submode_index - new_submode_index) > 1:
		#if True:
			# normalizeLens function returns after it finishes
			self.normalizeLens('allprojection')
		else:
			# mag settings returns before normalization initiated
			# from TUI is finished
			time.sleep(2)
		return

	def setMagnification(self, mag):
		if not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized

		try:
			mag = int(round(mag))
		except TypeError:
			try:
				mag = int(mag)
			except:
				raise TypeError
	
		try:
			index = self.magnifications.index(mag)
		except ValueError:
			raise ValueError('invalid magnification')
		if self.use_normalization:
			self.normalizeProjectionForMagnificationChange(index)
		self.setMagnificationIndex(index)
		return

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			return self.tecnai.Projection.MagnificationIndex - 1
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications.index(magnification)
			except IndexError:
				raise ValueError('invalid magnification')

	def setMagnificationIndex(self, value):
		self.tecnai.Projection.MagnificationIndex = value + 1

	def getMagnifications(self):
		return self.magnifications

	def setMagnifications(self, magnifications):
		self.magnifications = magnifications

	def findMagnifications(self):
		savedindex = self.getMagnificationIndex()
		magnifications = []
		previousindex = None
		index = 0
		while True:
			self.setMagnificationIndex(index)
			index = self.getMagnificationIndex()
			if index == previousindex:
				break
			mag = self.getMagnification()
			magnifications.append(mag)
			self.registerProjectionSubMode(mag)
			previousindex = index
			index += 1
		print self.getProjectionSubModeMap()
		self.setMagnifications(magnifications)
		self.setMagnificationIndex(savedindex)

	def registerProjectionSubMode(self, mag):
		'''
		Add current magnification to submode_mags.
		TEM Scripting orders magnificatiions by projection submode.
		'''
		mode_id = self.getProjectionSubModeIndex()
		name = self.getProjectionSubModeName()
		print mag, mode_id,name
		if mode_id not in self.projection_submodes.keys():
			raise ValueError('unknown projection submode')
		self.projection_submode_map[mag] = (name,mode_id)

	def getStagePosition(self):
		value = {'x':None,'y':None,'z':None,'a':None,'b':None}
		try:
			value['x'] = float(self.tecnai.Stage.Position.X)
			value['y'] = float(self.tecnai.Stage.Position.Y)
			value['z'] = float(self.tecnai.Stage.Position.Z)
		except:
			pass
		try:
			value['a'] = float(self.tecnai.Stage.Position.A)
		except:
			pass
		if use_nidaq:
			value['b'] = nidaq.getBeta() * 3.14159 / 180.0
		else:
			try:
				value['b'] = float(self.tecnai.Stage.Position.B)
			except:
				pass
		return value

	def _setStagePosition(self, position, relative = 'absolute'):
#		tolerance = 1.0e-4
#		polltime = 0.01

		if relative == 'relative':
			for key in position:
				position[key] += getattr(self.tecnai.Stage.Position, key.upper())
		elif relative != 'absolute':
			raise ValueError
		
		pos = self.tecnai.Stage.Position

		axes = 0
		for key, value in position.items():
			if use_nidaq and key == 'b':
				deg = value / 3.14159 * 180.0
				nidaq.setBeta(deg)
				continue
			setattr(pos, key.upper(), value)
			axes |= getattr(self.tem_constants, 'axis' + key.upper())

		if axes == 0:
			return
		try:
			self.tecnai.Stage.Goto(pos, axes)
		except com_module.COMError, (hr, msg, exc, arg):
			#print 'Stage.Goto failed with error %d: %s' % (hr, msg)
			if exc is None:
				raise ValueError('no extended error information, assuming stage limit was hit')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					raise ValueError('no extended error information, assuming stage limit was hit')
				else:
					raise RuntimeError(text)

#		for key in position:
#			while abs(getattr(self.tecnai.Stage.Position, key.upper())
#								- getattr(pos, key.upper())) > tolerance:
#				time.sleep(polltime)
	
	def getLowDoseStates(self):
		return ['on', 'off', 'disabled']

	def getLowDose(self):
		try:
			if (self.lowdose.IsInitialized == 1) and (self.lowdose.LowDoseActive == self.tem_constants.IsOn):
				return 'on'
			else:
				return 'off'
		except com_module.COMError, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disabled
				return 'disabled'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disabled
					return 'disabled'
				else:
					raise RuntimeError(text)
 
	def setLowDose(self, ld):
		try:
			if ld == 'off' :
				self.lowdose.LowDoseActive = self.tem_constants.IsOff
			elif ld == 'on':
				if self.lowdose.IsInitialized == 0:
					raise RuntimeError('Low dose is not initialized')
				else:
					self.lowdose.LowDoseActive = self.tem_constants.IsOn
			else:
				raise ValueError
		except com_module.COMError, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				raise RuntimeError('Low dose is not enabled')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					raise RuntimeError('Low dose is not enabled')
				else:
					raise RuntimerError(text)

	def getLowDoseModes(self):
		return ['exposure', 'focus1', 'focus2', 'search', 'unknown', 'disabled']

	def getLowDoseMode(self):
		try:
			if self.lowdose.LowDoseState == self.tem_constants.eExposure:
				return 'exposure'
			elif self.lowdose.LowDoseState == self.tem_constants.eFocus1:
				return 'focus1'
			elif self.lowdose.LowDoseState == self.tem_constants.eFocus2:
				return 'focus2'
			elif self.lowdose.LowDoseState == self.tem_constants.eSearch:
				return 'search'
			else:
				return 'unknown'
		except com_module.COMError, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				return 'disabled'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					return 'disabled'
				else:
					raise RuntimerError(text)
		
	def setLowDoseMode(self, mode):
		try:
			if mode == 'exposure':
				self.lowdose.LowDoseState = self.tem_constants.eExposure
			elif mode == 'focus1':
				self.lowdose.LowDoseState = self.tem_constants.eFocus1
			elif mode == 'focus2':
				self.lowdose.LowDoseState = self.tem_constants.eFocus2
			elif mode == 'search':
				self.lowdose.LowDoseState = self.tem_constants.eSearch
			else:
				raise ValueError
		except com_module.COMError, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				raise RuntimeError('Low dose is not enabled')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					raise RuntimeError('Low dose is not enabled')
				else:
					raise RuntimerError(text)
	
	def getDiffractionMode(self):
		if self.tecnai.Projection.Mode == self.tem_constants.pmImaging:
			return 'imaging'
		elif self.tecnai.Projection.Mode == self.tem_constants.pmDiffraction:
			return 'diffraction'
		else:
			raise SystemError
		
	def setDiffractionMode(self, mode):
		if mode == 'imaging':
			self.tecnai.Projection.Mode = self.tem_constants.pmImaging
		elif mode == 'diffraction':
			self.tecnai.Projection.Mode = self.tem_constants.pmDiffraction
		else:
			raise ValueError
		
		return 0

	def getShutterPositions(self):
		'''
		Shutter refers to the shutter controlled through adaExp.
		Use BeamBlanker functions to control pre-specimen shuttering
		accessable from tem scripting.
		'''
		return ['open', 'closed']

	def setShutter(self, state):
		'''
		Shutter refers to the shutter controlled through adaExp.
		Use BeamBlanker functions to control pre-specimen shuttering
		accessable from tem scripting.
		'''
		if self.exposure is None:
			raise RuntimeError('setShutter requires adaExp')
		if state == 'open':
			if self.exposure.OpenShutter != 0:
				raise RuntimeError('Open shutter failed')
		elif state == 'closed':
			if self.exposure.CloseShutter != 0:
				raise RuntimeError('Close shutter failed')
		else:
			raise ValueError('Invalid value for setShutter \'%s\'' % (state,))

	def getShutter(self):
		'''
		Shutter refers to the shutter controlled through adaExp.
		Use BeamBlanker functions to control pre-specimen shuttering
		accessable from tem scripting.
		'''
		if self.exposure is None:
			raise RuntimeError('getShutter requires adaExp')
		status = self.exposure.ShutterStatus
		if status:
			return 'closed'
		else:
			return 'open'

	def getExternalShutterStates(self):
		return ['connected', 'disconnected']

	def setExternalShutter(self, state):
		if self.exposure is None:
			raise RuntimeError('setExternalShutter requires adaExp')
		if state == 'connected':
			if self.exposure.ConnectExternalShutter != 0:
				raise RuntimeError('Connect shutter failed')
		elif state == 'disconnected':
			if self.exposure.DisconnectExternalShutter != 0:
				raise RuntimeError('Disconnect shutter failed')
		else:
			raise ValueError('Invalid value for setExternalShutter \'%s\'' % (state,))
		
	def getExternalShutter(self):
		if self.exposure is None:
			raise RuntimeError('getExternalShutter requires adaExp')
		status = self.exposure.ExternalShutterStatus
		if status:
			return 'connected'
		else:
			return 'disconnected'

	def preFilmExposure(self, value):
		if self.exposure is None:
			raise RuntimeError('preFilmExposure requires adaExp')
		if not value:
			return

		if self.getFilmStock() < 1:
			raise RuntimeError('No film to take exposure')

		if self.exposure.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.exposure.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')

	def postFilmExposure(self, value):
		if self.exposure is None:
			raise RuntimeError('postFilmExposure requires adaExp')
		if not value:
			return

		if self.exposure.UnloadPlate != 0:
			raise RuntimeError('Unload plate failed')
#		if self.exposure.UpdateExposureNumber != 0:
#			raise RuntimeError('Update exposure number failed')

	def filmExposure(self, value):
		if not value:
			return

		'''
		if self.getFilmStock() < 1:
			raise RuntimeError('No film to take exposure')

		if self.exposure.CloseShutter != 0:
			raise RuntimeError('Close shutter (pre-exposure) failed')
		if self.exposure.DisconnectExternalShutter != 0:
			raise RuntimeError('Disconnect external shutter failed')
		if self.exposure.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.exposure.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')
		if self.exposure.OpenShutter != 0:
			raise RuntimeError('Open (pre-exposure) shutter failed')
		'''
		
		self.tecnai.Camera.TakeExposure()
		
		'''
		if self.exposure.CloseShutter != 0:
			raise RuntimeError('Close shutter (post-exposure) failed')
		if self.exposure.UnloadPlate != 0:
			raise RuntimeError('Unload plate failed')
		if self.exposure.UpdateExposureNumber != 0:
			raise RuntimeError('Update exposure number failed')
		if self.exposure.ConnectExternalShutter != 0:
			raise RuntimeError('Connect external shutter failed')
		if self.exposure.OpenShutter != 0:
			raise RuntimeError('Open shutter (post-exposure) failed')
		'''

	def getMainScreenPositions(self):
		return ['up', 'down', 'unknown']

	def getMainScreenPosition(self):
		timeout = 5.0
		sleeptime = 0.05
		while (self.tecnai.Camera.MainScreen
						== self.tem_constants.spUnknown):
			time.sleep(sleeptime)
			if self.tecnai.Camera.MainScreen != self.tem_constants.spUnknown:
				break
			timeout -= sleeptime
			if timeout <= 0.0:
				return 'unknown'
		if self.tecnai.Camera.MainScreen == self.tem_constants.spUp:
			return 'up'
		elif self.tecnai.Camera.MainScreen == self.tem_constants.spDown:
			return 'down'
		else:
			return 'unknown'

	def getSmallScreenPosition(self):
		if self.tecnai.Camera.IsSmallScreenDown:
			return 'down'
		else:
			return 'up'

	def setMainScreenPosition(self, mode):
		if mode == 'up':
			self.tecnai.Camera.MainScreen = self.tem_constants.spUp
		elif mode == 'down':
			self.tecnai.Camera.MainScreen = self.tem_constants.spDown
		else:
			raise ValueError
		time.sleep(2)

	def getHolderStatus(self):
		if self.exposure is None:
			raise RuntimeError('getHolderStatus requires adaExp')
		if self.exposure.SpecimenHolderInserted == self.adacom_constants.eInserted:
			return 'inserted'
		elif self.exposure.SpecimenHolderInserted == self.adacom_constants.eNotInserted:
			return 'not inserted'
		else:
			return 'unknown'

	def getHolderTypes(self):
		return ['no holder', 'single tilt', 'cryo', 'unknown']

	def getHolderType(self):
		if self.exposure is None:
			raise RuntimeError('getHolderType requires adaExp')
		if self.exposure.CurrentSpecimenHolderName == u'No Specimen Holder':
			return 'no holder'
		elif self.exposure.CurrentSpecimenHolderName == u'Single Tilt':
			return 'single tilt'
		elif self.exposure.CurrentSpecimenHolderName == u'ST Cryo Holder':
			return 'cryo'
		else:
			return 'unknown'

	def setHolderType(self, holdertype):
		if self.exposure is None:
			raise RuntimeError('setHolderType requires adaExp')
		if holdertype == 'no holder':
			holderstr = u'No Specimen Holder'
		elif holdertype == 'single tilt':
			holderstr = u'Single Tilt'
		elif holdertype == 'cryo':
			holderstr = u'ST Cryo Holder'
		else:
			raise ValueError('invalid holder type specified')

		for i in [1,2,3]:
			if self.exposure.SpecimenHolderName(i) == holderstr:
				self.exposure.SetCurrentSpecimenHolder(i)
				return

		raise SystemError('no such holder available')

	def getStageStatus(self):
		if self.exposure is None:
			raise RuntimeError('getStageStatus requires adaExp')
		if self.exposure.GonioLedStatus == self.adacom_constants.eOn:
			return 'busy'
		elif self.exposure.GonioLedStatus == self.adacom_constants.eOff:
			return 'ready'
		else:
			return 'unknown'

	def getTurboPump(self):
		if self.exposure is None:
			raise RuntimeError('getTurboPump requires adaExp')
		if self.exposure.GetTmpStatus == self.adacom_constants.eOn:
			return 'on'
		elif self.exposure.GetTmpStatus == self.adacom_constants.eOff:
			return 'off'
		else:
			return 'unknown'

	def setTurboPump(self, mode):
		if self.exposure is None:
			raise RuntimeError('setTurboPump requires adaExp')
		if mode == 'on':
			self.exposure.SetTmp(self.adacom_constants.eOn)
		elif mode == 'off':
			self.exposure.SetTmp(self.adacom_constants.eOff)
		else:
			raise ValueError

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def getColumnValvePosition(self):
		if self.tecnai.Vacuum.ColumnValvesOpen:
			return 'open'
		else:
			return 'closed'

	def setColumnValvePosition(self, state):
		position = self.getColumnValvePosition()
		if position == 'open' and state == 'closed':
			self.tecnai.Vacuum.ColumnValvesOpen = 0
			time.sleep(2)
		elif position == 'closed' and state == 'open':
			self.tecnai.Vacuum.ColumnValvesOpen = 1
			time.sleep(3) # extra time for camera retract
		elif state in ('open','closed'):
			pass
		else:
			raise ValueError

	def getVacuumStatus(self):
		status = self.tecnai.Vacuum.Status
		if status == self.tem_constants.vsOff:
			return 'off'
		elif status == self.tem_constants.vsCameraAir:
			return 'camera'
		elif status == self.tem_constants.vsBusy:
			return 'busy'
		elif status == self.tem_constants.vsReady:
			return 'ready'
		elif status == self.tem_constants.vsUnknown:
			return 'unknown'
		elif status == self.tem_constants.vsElse:
			return 'else'
		else:
			return 'unknown'

	def getColumnPressure(self):
		if self.pressure_prop is None:
			return 0.0
		return float(self.tecnai.Vacuum.Gauges(self.pressure_prop).Pressure)

	def getObjectiveExcitation(self):
		return float(self.tecnai.Projection.ObjectiveExcitation)

	def getFocus(self):
		return float(self.tecnai.Projection.Focus)

	def setFocus(self, value):
		self.tecnai.Projection.Focus = value

	def getFilmStock(self):
		return self.tecnai.Camera.Stock

	def getFilmExposureNumber(self):
		return self.tecnai.Camera.ExposureNumber % 100000

	def setFilmExposureNumber(self, value):
		self.tecnai.Camera.ExposureNumber = (self.tecnai.Camera.ExposureNumber
																										/ 100000) * 100000 + value

	def getFilmExposureTypes(self):
		return ['manual', 'automatic']

	def getFilmExposureType(self):
		if self.tecnai.Camera.ManualExposure:
			return 'manual'
		else:
			return 'automatic'

	def setFilmExposureType(self, value):
		if value ==  'manual':
			self.tecnai.Camera.ManualExposure = True
		elif value == 'automatic':
			self.tecnai.Camera.ManualExposure = False
		else:
			raise ValueError('Invalid value for film exposure type')

	def getFilmExposureTime(self):
		if self.tecnai.Camera.ManualExposure:
			return self.getFilmManualExposureTime()
		else:
			return self.getFilmAutomaticExposureTime()

	def getFilmManualExposureTime(self):
		return float(self.tecnai.Camera.ManualExposureTime)

	def setFilmManualExposureTime(self, value):
		self.tecnai.Camera.ManualExposureTime = value

	def getFilmAutomaticExposureTime(self):
		return float(self.tecnai.Camera.MeasuredExposureTime)

	def getFilmText(self):
		return str(self.tecnai.Camera.FilmText)

	def setFilmText(self, value):
		self.tecnai.Camera.FilmText = value

	def getFilmUserCode(self):
		return str(self.tecnai.Camera.Usercode)

	def setFilmUserCode(self, value):
		self.tecnai.Camera.Usercode = value

	def getFilmDateTypes(self):
		return ['no date', 'DD-MM-YY', 'MM/DD/YY', 'YY.MM.DD', 'unknown']

	def getFilmDateType(self):
		filmdatetype = self.tecnai.Camera.PlateLabelDateType
		if filmdatetype == self.tem_constants.dtNoDate:
			return 'no date'
		elif filmdatetype == self.tem_constants.dtDDMMYY:
			return 'DD-MM-YY'
		elif filmdatetype == self.tem_constants.dtMMDDYY:
			return 'MM/DD/YY'
		elif filmdatetype == self.tem_constants.dtYYMMDD:
			return 'YY.MM.DD'
		else:
			return 'unknown'

	def setFilmDateType(self, value):
		if value == 'no date':
			self.tecnai.Camera.PlateLabelDateType \
				= self.tem_constants.dtNoDate
		elif value == 'DD-MM-YY':
			self.tecnai.Camera.PlateLabelDateType \
				= self.tem_constants.dtDDMMYY
		elif value == 'MM/DD/YY':
			self.tecnai.Camera.PlateLabelDateType \
				= self.tem_constants.dtMMDDYY
		elif value == 'YY.MM.DD':
			self.tecnai.Camera.PlateLabelDateType \
				= self.tem_constants.dtYYMMDD
		else:
			raise ValueError('Invalid film date type specified')

	def runBufferCycle(self):
		try:
			self.tecnai.Vacuum.RunBufferCycle()
		except com_module.COMError, (hr, msg, exc, arg):
			if exc is None:
				raise RuntimeError('no extended error information')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					raise RuntimeError('no extended error information')
				else:
					raise RuntimeError(text)

	def setEmission(self, value):
		self.tom.Gun.Emission = value

	def getEmission(self):
		return self.tom.Gun.Emission

	def getExpWaitTime(self):
		try:
			return self.lowdose.WaitTime
		except:
			raise RuntimeError('no low dose interface')

	def setShutterControl(self, value):
		'''
		If given boolean True, this should set the registers that allow
		camera to control the shutter.  Should also behave for other types
		of TEMs that do not have or need these registers.
		'''
		pass

	def exposeSpecimenNotCamera(self,exptime=0):
		'''
		take control of the shutters to open
		the gun blanker (pre-specimen)
		but not projection shutter (post-specimen)
		Used in pre-exposure and melting ice
		'''
		if exptime == 0:
			return
		if hasattr(self.tecnai,'BlankerShutter'):
			self.setBeamBlank('on')
			self.tecnai.BlankerShutter.ShutterOverrideOn = True
			time.sleep(1.0)
			self.setBeamBlank('off')
			time.sleep(exptime)
			self.tecnai.BlankerShutter.ShutterOverrideOn = False
			time.sleep(1.0)
			self.setBeamBlank('off')
		else:
			self.setMainScreenPosition('down')
			time.sleep(exptime)
			self.setMainScreenPosition('up')

	def runAutoFiller(self):
		'''
		Trigger autofiller refill
		'''
		self.tecnai.TemperatureControl.ForceRefill()

	def isAutoFillerBusy(self):
		try:
			isbusy = self.tecnai.TemperatureControl.DewarsAreBusyFilling
		except:
			# property not exist for older versions
			isbusy = None
		return isbusy

	def getRefrigerantLevel(self,id=0):
		'''
		Get current refrigerant level. Only works on Krios. id 0 is the
		autoloader, 1 is the column.
		'''
		return self.tecnai.TemperatureControl.RefrigerantLevel(id)

class Krios(Tecnai):
	name = 'Krios'
	use_normalization = True
	def __init__(self):
		Tecnai.__init__(self)
		self.correctedstage = False

	def setStagePosition(self, value):
		# Krios Compustage works better without preposition
		value = self.checkStagePosition(value)
		if not value:
			return
		return self._setStagePosition(value)

class EFKrios(Krios):
	name = 'EF-Krios'

class Talos(Tecnai):
	name = 'Talos'
	use_normalization = True
