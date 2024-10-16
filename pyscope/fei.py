# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

from . import tem
import time
import sys
import subprocess
import os
import datetime
import math
from pyami import moduleconfig

# API notes:
#COMError from TEMScripting is not consistent in which
# attribute contains text information.  Need to check by trial and error.
# For example Stage.Goto has empty details attribute but text has the message.
# ApertureMechanism not avtivated in Scripting error uses details to contain the list which has the message we need on item index 1. text and message attributes are empty strings.

try:
	from . import nidaq
except:
	nidaq = None
use_nidaq = False

try:
	import comtypes
	import comtypes.client
	com_module =  comtypes
	log_path = os.path.join(os.environ['USERPROFILE'],'myami_log')
	if not os.path.isdir(log_path):
		os.mkdir(log_path)
except ImportError:
	log_path = None
	pass

configs = moduleconfig.getConfigured('fei.cfg')
configpath = moduleconfig.getConfigPath('fei.cfg')

def configHasColdFeg():
	if 'source' in configs and 'has_cold_feg' in configs['source'] and configs['source']['has_cold_feg']==True:
		return True
	return False

HAS_CFEG = configHasColdFeg()

if HAS_CFEG:
	from pyscope import fei_advscripting

class MagnificationsUninitialized(Exception):
	pass

class Tecnai(tem.TEM):
	name = 'Tecnai'
	column_type = 'tecnai'
	use_normalization = False
	projection_mode = 'imaging'
	# attribute name for getMagnification function.
	# either 'Magnification' or 'CameraLength'
	mag_attr_name = 'Magnification'
	mag_scale = 1
	stage_top_speed = 29.78
	default_stage_speed_fraction = 1.0

	def __init__(self):
		tem.TEM.__init__(self)
		self.projection_submodes = {1:'LM',2:'Mi',3:'SA',4:'Mh',5:'LAD',6:'D'}
		self.gridloader_slot_states = {0:'unknown', 1:'occupied', 2:'empty', 3:'error'}
		self.aperture_mechanism_indexmap = {'condenser2':2,'objective':4,'selected area':5}
		self.special_submode_mags = {}
		#self.special_submode_mags = {380:('EFTEM',3)}
		self.projection_submode_map = self.special_submode_mags.copy()
		
		self.correctedstage = self.getFeiConfig('stage','do_stage_xyz_backlash')
		self.corrected_alpha_stage = self.getFeiConfig('stage','do_stage_alpha_backlash')
		self.alpha_backlash_delta = self.getFeiConfig('stage','stage_alpha_backlash_angle_delta')
		self.normalize_all_after_setting = self.getFeiConfig('optics','force_normalize_all_after_setting')
		self.cold_feg_flash_types = {'low':0,'high':1}
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
			self.adv_instr = fei_advscripting.connectToFEIAdvScripting().instr
			self.source = self.adv_instr.Source
		except Exception as e:
			#print('unable to initialize Advanced Scriptiong interface, %s' % e)
			self.adv_instr = None
			self.source = None
		try:
			self.tom = comtypes.client.CreateObject('TEM.Instrument.1')
		except com_module.COMError:
			self.tom = None
		except WindowsError:
			self.tom = None

		try:
			self.lowdose = comtypes.client.CreateObject('LDServer.LdSrv')
		except:
			print('unable to initialize low dose interface')
			self.lowdose = None

		try:
			self.exposure = comtypes.client.CreateObject('adaExp.TAdaExp',
																					clsctx=com_module.CLSCTX_LOCAL_SERVER)
			self.adacom_constants = comtypes.client.Constants(self.exposure)
		except:
			self.exposure = None

		self.magnifications = []
		self.speed_deg_per_second = self.stage_top_speed
		self.stage_speed_fraction = self.default_stage_speed_fraction
		self.mainscreenscale = 44000.0 / 50000.0
		self.wait_for_stage_ready = True

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
		self.findPresureProps()

		self.probe_str_const = {'micro': self.tem_constants.imMicroProbe, 'nano': self.tem_constants.imNanoProbe}
		self.probe_const_str = {self.tem_constants.imMicroProbe: 'micro', self.tem_constants.imNanoProbe: 'nano'}

	def findPresureProps(self):
		self.pressure_prop = {}
		gauge_map = {}
		gauges_to_try = {'column':['IGPco','PPc1','P4','IGP1'],'buffer':['PIRbf','P1'],'projection':['CCGp','P3']}
		gauges_obj = self.tecnai.Vacuum.Gauges
		for i in range(gauges_obj.Count):
			g = gauges_obj.Item(i)
			gauge_map[g.Name] = i
		for location in list(gauges_to_try.keys()):
			self.pressure_prop[location] = None
			for name in gauges_to_try[location]:
				if name in list(gauge_map.keys()):
					self.pressure_prop[location] = gauge_map[name]
					break
			
	def getFeiConfig(self,optionname,itemname=None):
		if optionname not in list(configs.keys()):
			return None
		if itemname is None:
			return configs[optionname]
		else:
			if itemname not in configs[optionname]:
				return None
			return configs[optionname][itemname]

	def getDebugAll(self):
		return self.getFeiConfig('debug','all')

	def getDebugStage(self):
		return self.getFeiConfig('debug','stage')

	def getUseAutoAperture(self):
		return self.getFeiConfig('aperture','use_auto_aperture')

	def getHasFalconProtector(self):
		return self.getFeiConfig('camera','has_falcon_protector')

	def getAutoitPhasePlateExePath(self):
		value = self.getFeiConfig('phase plate','autoit_phase_plate_exe_path')
		if not value:
			# back compatibility pre 3.5
			value=self.getFeiConfig('phase plate','autoit_exe_path')
		return value

	def getAutoitGetBeamstopExePath(self):
		return self.getFeiConfig('beamstop','autoit_get_exe_path')

	def getAutoitBeamstopInExePath(self):
		return self.getFeiConfig('beamstop','autoit_in_exe_path')

	def getAutoitBeamstopOutExePath(self):
		return self.getFeiConfig('beamstop','autoit_out_exe_path')

	def getAutoitBeamstopHalfwayExePath(self):
		return self.getFeiConfig('beamstop','autoit_halfway_exe_path')

	def getRotationCenterScale(self):
		return self.getFeiConfig('optics','rotation_center_scale')

	def getMinimumStageMovement(self):
		return self.getFeiConfig('stage','minimum_stage_movement')

	def getStageLimits(self):
		limits = self.getFeiConfig('stage','stage_limits')
		if limits is None:
			limits = super(Tecnai, self).getStageLimits()
		return limits

	def getXYZStageBacklashDelta(self):
		value = self.getFeiConfig('stage','xyz_stage_backlash_delta')
		if value is None:
			value = 0
		return value

	def getXYStageRelaxDistance(self):
		relax = self.getFeiConfig('stage','xy_stage_relax_distance')
		if relax is None:
			relax = 0
		return relax

	def setCorrectedStagePosition(self, value):
		self.correctedstage = bool(value)
		return self.correctedstage

	def getCorrectedStagePosition(self):
		return self.correctedstage

	def checkStageLimits(self, position):
		self._checkStageXYZLimits(position)
		self._checkStageABLimits(position)

	def _checkStageXYZLimits(self, position):
		limit = self.getStageLimits()
		intersection = set(position.keys()).intersection(('x','y','z'))
		for axis in intersection:
			self._validateStageAxisLimit(position[axis], axis)

	def _checkStageABLimits(self, position):
		limit = self.getStageLimits()
		intersection = set(position.keys()).intersection(('a','b'))
		for axis in intersection:
			self._validateStageAxisLimit(position[axis], axis)

	def _validateStageAxisLimit(self, p, axis):
		limit = self.getStageLimits()
		if not (limit[axis][0] < p and limit[axis][1] > p):
			if axis in ('x','y','z'):
				um_p = p*1e6
				raise ValueError('Requested %s axis position %.1f um out of range.' % (axis,um_p))
			else:
				deg_p = math.degrees(p)
				raise ValueError('Requested %s axis position %.1f degrees out of range.' % (axis,deg_p))

	def checkStagePosition(self, position):
		self.checkStageLimits(position)
		current = self.getStagePosition()
		bigenough = {}
		minimum_stage = self.getMinimumStageMovement()
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
		# calculate pre-position
		prevalue = {}
		prevalue2 = {}
		# correct xyz
		if self.correctedstage:
			delta = self.getXYZStageBacklashDelta()
			for axis in ('x','y','z'):
				if axis in value:
					prevalue[axis] = value[axis] - delta
					self._validateStageAxisLimit(prevalue[axis],axis)
		# relax xy
		relax = self.getXYStageRelaxDistance()
		if abs(relax) > 1e-9:
			for axis in ('x','y'):
				if axis in value:
					prevalue2[axis] = value[axis] + relax
					self._validateStageAxisLimit(prevalue2[axis],axis)
		# preposition a
		if self.corrected_alpha_stage:
			# alpha tilt backlash only in one direction
			alpha_delta_degrees = self.alpha_backlash_delta
			if 'a' in list(value.keys()):
					axis = 'a'
					prevalue[axis] = value[axis] - alpha_delta_degrees*3.14159/180.0
					self._validateStageAxisLimit(prevalue[axis],axis)
		if prevalue:
			# set all axes in value
			for axis in list(value.keys()):
				if axis not in list(prevalue.keys()):
					prevalue[axis] = value[axis]
					# skip those requiring no further change
					del value[axis]
			self._setStagePosition(prevalue)
			time.sleep(0.2)
		# set all remaining axes in the remaining value
		if abs(relax) > 1e-9 and prevalue2:
			for axis in list(value.keys()):
				if axis not in list(prevalue2.keys()):
					prevalue2[axis] = value[axis]
					# skip those requiring no further change
					del value[axis]
			self._setStagePosition(prevalue2)
			time.sleep(0.2)
		# final position
		return self._setStagePosition(value)

	def resetStageSpeed(self):
		self.stage_speed_fraction = self.default_stage_speed_fraction
		if self.tom:
			self.tom.Stage.Speed = self.default_stage_speed_fraction

	def setStageSpeed(self, value):
		self.speed_deg_per_second = float(value)
		self.stage_speed_fraction = min(value/self.stage_top_speed,1.0)
		if self.tom:
			# tom-monikar needs to set speed first while temscripting set speed in gotowithspeed call.
			self.tom.Stage.Speed = self.stage_speed_fraction

	def getStageSpeed(self):
		if self.tom:
			return self.tom.Stage.Speed * self.stage_top_speed
		else:
			return self.stage_speed_fraction * self.stage_top_speed

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

	def hasColdFeg(self):
		if self.source:
			try:
				# test on lowT type.
				should_flash = self.source.Flashing.IsFlashingAdvised(self.cold_feg_flash_types['low'])
			except AttributeError:
				return False
			except Exception as e:
				return False
			return True
		return False

	def getFlashingAdvised(self, flash_type):
		advised_only = self.getFeiConfig('source','flash_cold_feg_only_if_advised')
		try:
			flash_type_constant = self.cold_feg_flash_types[flash_type]
			should_flash = self.source.Flashing.IsFlashingAdvised(flash_type_constant)
		except AttributeError as e:
			return False
		except KeyError:
			print('flash type can only be %s' % list(self.cold_feg_flash_types.keys()))
			return False
		except Exception as e:
			print('other getFlashAdvised exception %s' % e)
			return False
		if advised_only:
			return should_flash
		else:
			if flash_type == 'low':
				# only low temp can flash without advised.
				return True
		return should_flash

	def getColdFegFlashing(self):
		return 'off'

	def setColdFegFlashing(self,state):
		# 'on' starts flashing, 'off' stops flashing
		# tfs flashing can not be stopped.
		if not self.hasColdFeg():
			return
		# low temperature (lowT) flashing can be done any time even if not advised.
		# highT flashing can only be done if advised.
		# It will give COMError if tried
		if state != 'on':
			# tfs flashing can not be stopped.
			return
		for flash_type in ('high','low'):
			if self.getFlashingAdvised(flash_type):
				flash_type_constant = self.cold_feg_flash_types[flash_type]
				try:
					self.source.Flashing.PerformFlashing(flash_type_constant)
					# no need to do lowT flashing if highT is done
					break
				except Exception as e:
					raise RuntimeError(e)

	def getColdFegBeamCurrent(self):
		# Cold FEG beam current is used to decide whether to flash or not.
		# Unit is Amp.  Returns -1.0 if not available
		if self.source and self.hasColdFeg():
			return float(self.source.BeamCurrent)
		return -1.0

	def getExtractorVoltage(self):
		# FEG extractor voltage. Unit is Voltage
		# Returns -1.0 if not available
		if self.source:
			try:
				return float(self.source.ExtractorVoltage)
			except:
				return -1.0

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
		return int(round(float(self.tecnai.Gun.HTValue)))
	
	def setHighTension(self, ht):
		self.tecnai.Gun.HTValue = float(ht)
	
	def getMinimumIntensityMovement(self):
		value = self.getFeiConfig('optics','minimum_intensity_movement')
		if value is None or value < 1e-8:
			return 1e-8
		else:
			return value

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
		prev_int = self.getIntensity()
		intensity_step = self.getMinimumIntensityMovement()
		if self.getDebugAll():
				print('prev_int', prev_int)
				print('minimum_intensity_movement', intensity_step)
				print('target_intensity', intensity)
		# Try don't include intensity change for normalize_all
		# since it is not done in TUI
		#if abs(prev_int-intensity) > intensity_step:
		#	self.setAutoNormalizeEnabled(False)
		setattr(self.tecnai.Illumination, self.intensity_prop, intensity)
		# Normalizations
		if self.normalize_all_after_setting:
			if self.getDebugAll():
				self.need_normalize_all
			if self.need_normalize_all:
				if self.getDebugAll():
					print('normalize all')
				self.normalizeLens('all')
		# sleep for intensity change
		extra_sleep = self.getFeiConfig('camera','extra_protector_sleep_time')
		if self.need_normalize_all and extra_sleep:
			time.sleep(extra_sleep)
		#reset changed flag
		self.setAutoNormalizeEnabled(True)

	def setAutoNormalizeEnabled(self, value):
		if self.normalize_all_after_setting:
			self.tecnai.AutoNormalizeEnabled = bool(value)
			self.need_normalize_all = not bool(value)
		else:
			self.need_normalize_all = False

	def getAutoNormalizeEnabled(self):
		try:
			return self.tecnai.AutoNormalizeEnabled
		except:
			# does not have such call.
			return False

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
		current_probe = self.getProbeMode()
		const = self.probe_str_const[probe_str]
		if current_probe != probe_str:
			self.setAutoNormalizeEnabled(False)
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
		if self.getBeamBlank() == bb:
			# do nothing if already there
			return
		self._setBeamBlank(bb)
		# Falcon protector delays the response of the blanker and 
		# cause it to be out of sync
		if self.getHasFalconProtector():
			i = 0
			time.sleep(0.5)
			if self.getBeamBlank() != bb:
				if i < 10:
					time.sleep(0.5)
					if self.getDebugAll():
						print('retry BeamBlank operation')
					self._setBeamBlank(bb)
					i += 1
				else:
					raise SystemError

	def _setBeamBlank(self, bb):
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
		for key in list(stigs.keys()):
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
		prev = self.getSpotSize()
		if prev != ss:
			self.setAutoNormalizeEnabled(False)
			self.tecnai.Illumination.SpotsizeIndex = ss

	def getBeamTilt(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.tecnai.Illumination.RotationCenter.X) / self.getRotationCenterScale()
		value['y'] = float(self.tecnai.Illumination.RotationCenter.Y) / self.getRotationCenterScale() 

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
		if abs(vec.X-vector['x'])+abs(vec.Y-vector['y']) < 1e-6:
			# 1 urad move is ignored.
			return
		try:
			vec.X = vector['x'] * self.getRotationCenterScale()
		except KeyError:
			pass
		try:
			vec.Y = vector['y'] * self.getRotationCenterScale()
		except KeyError:
			pass
		self.tecnai.Illumination.RotationCenter = vec
	
	def getBeamShift(self):
		value = {'x': None, 'y': None}
		try:
			value['x'] = float(self.tecnai.Illumination.Shift.X)
			value['y'] = float(self.tecnai.Illumination.Shift.Y)
		except:
			# return None if has exception
			pass
		return value

	def setBeamShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Illumination.Shift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Illumination.Shift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Illumination.Shift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Illumination.Shift = vec
	
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
		d = 0.0
		for k in list(vector.keys()):
			temvalue = getattr(vec, k.upper())
			d += abs(temvalue - vector[k])
		if d < 1e-9:
			# 1 nm move is ignored.
			return
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Projection.ImageBeamShift = vec

	def getDiffractionShift(self):
		value = {'x': None, 'y': None}
		try:
			value['x'] = float(self.tecnai.Projection.DiffractionShift.X)
			value['y'] = float(self.tecnai.Projection.DiffractionShift.Y)
		except:
			# return None if has exception
			pass
		return value

	def setDiffractionShift(self, vector, relative = 'absolute'):
		if vector['x'] is None or vector['y'] is None:
			if self.getDebugAll():
				print('diffraction shift not defined. No change.')
			return
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Projection.DiffractionShift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Projection.DiffractionShift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		# Real setting part
		vec = self.tecnai.Projection.DiffractionShift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Projection.DiffractionShift = vec

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
			return int(round(getattr(self.tecnai.Projection,self.mag_attr_name)*self.mag_scale))
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications[index]
			except IndexError:
				raise ValueError('invalid magnification index')

	def getMainScreenMagnification(self):
		return int(round(getattr(self.tecnai.Projection, self.mag_attr_name)*self.mainscreenscale))

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

		# set  projection mode if changing.
		if self.getProjectionMode() != self.projection_mode:
			self.setProjectionMode(None)
		try:
			index = self.magnifications.index(mag)
		except ValueError:
			raise ValueError('invalid magnification')
		try:
			prev_index = self.getMagnificationIndex()
		except ValueError:
			# none of the valid index
			prev_index = -1
		need_proj_norm = False
		if prev_index != index:
			# This makes defocus accuracy better like a objective 
			# normalization. This assumes that defocus will be set
			# after this not before.
			self.setAutoNormalizeEnabled(False)
			self.tecnai.Projection.Focus = 0.0
			self.setMagnificationIndex(index)
		return

	def setPreDiffractionMagnification(self):
		'''
		Set to an SA magnification index so that diffraction mode change
		goes into D not LAD mode.
		'''
		if self.getProjectionMode() != 'imaging':
			raise ValueError('Not in imaging mode')
		index = self.getFeiConfig('optics','pre_diffraction_sa_magnification_index')
		# handle not configured
		if index is None or index == -1:
			raise ValueError('Must set PRE_DIFFRACTION_SA_MAGNIFICATION to a valid mag index')
		self.tecnai.Projection.MagnificationIndex = index
		name = self.getProjectionSubModeName()
		if name != 'SA':
			raise ValueError('PRE_DIFFRACTION_SA_MAGNIFICATION_INDEX not in SA mode')
		return

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			return getattr(self.tecnai.Projection,self.mag_attr_name+'Index') - 1
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications.index(magnification)
			except IndexError:
				raise ValueError('invalid magnification')

	def setMagnificationIndex(self, value):
		setattr(self.tecnai.Projection,self.mag_attr_name+'Index', value + 1)

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
		self.getProjectionSubModeMap()
		self.setMagnifications(magnifications)
		self.setMagnificationIndex(savedindex)

	def registerProjectionSubMode(self, mag):
		'''
		Add current magnification to submode_mags.
		TEM Scripting orders magnificatiions by projection submode.
		'''
		mode_id = self.getProjectionSubModeIndex()
		mode_name = self.getProjectionSubModeName()
		if mode_id not in list(self.projection_submodes.keys()):
			raise ValueError('unknown projection submode')
		# FEI scopes don't have cases with the same mag in different mode, yet.
		if mode_name not in ('LM','LAD'):
			obj_mode_name = 'hm'
		else:
			obj_mode_name = mode_name.lower()
		self.addProjectionSubModeMap(mag, mode_name, mode_id, obj_mode_name, overwrite=True)

	def getStagePosition(self):
		value = {'x':None,'y':None,'z':None,'a':None,'b':None}
		try:
			value['x'] = float(self.tecnai.Stage.Position.X)
			value['y'] = float(self.tecnai.Stage.Position.Y)
			value['z'] = float(self.tecnai.Stage.Position.Z)
		except Exception as e:
			raise RuntimeError('get stage error: %s' % (e,))
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

	def setWaitForStageReady(self, value):
		self.wait_for_stage_ready = value

	def getWaitForStageReady(self):
		return self.wait_for_stage_ready

	def waitForStageReady(self,position_log,timeout=10):
		if not self.wait_for_stage_ready:
			return
		t0 = time.time()
		trials = 0
		while self.tecnai.Stage.Status in (2,3,4):
			trials += 1
			if time.time()-t0 > timeout/2.0:
				time.sleep(timeout/10.0)
			if time.time()-t0 > timeout:
				stage_status = self.tecnai.Stage.Status
				msg = 'stage is at status %d, not ready in %d seconds' % (int(stage_status),int(timeout))
				if self.getDebugStage():
					print(msg)
					print(position_log)
					# allow it to go through for now.
					break
				else:
					raise RuntimeError('stage is not going to ready status in %d seconds' % (int(timeout)))
		if self.getDebugStage() and trials > 0:
			print(datetime.datetime.now())
			donetime = time.time() - t0
			print('took extra %.1f seconds to get to ready status' % (donetime))

	def _setStagePosition(self, position, relative = 'absolute'):
		if self.tom is not None and self.column_type=='tecnai':
			return self._setTomStagePosition(position, relative)
		else:
			return self._setTemStagePosition(position, relative)

	def _setTemStagePosition(self, position, relative = 'absolute'):
#		tolerance = 1.0e-4
#		polltime = 0.01

		self.waitForStageReady('before setting %s' % (position,))
		if relative == 'relative':
			for key in position:
				position[key] += getattr(self.tecnai.Stage.Position, key.upper())
		elif relative != 'absolute':
			raise ValueError
		
		pos = self.tecnai.Stage.Position

		short_pos_str = ''
		axes = 0
		stage_limits = self.getStageLimits()
		for key, value in list(position.items()):
			if use_nidaq and key == 'b':
				deg = value / 3.14159 * 180.0
				nidaq.setBeta(deg)
				continue
			if key in list(stage_limits.keys()) and (value < stage_limits[key][0] or value > stage_limits[key][1]):
				raise ValueError('low-level position %s beyond stage limit at %.2e' % (key, value))
			setattr(pos, key.upper(), value)
			axes |= getattr(self.tem_constants, 'axis' + key.upper())

			setattr(pos, key.upper(), value)
			axes |= getattr(self.tem_constants, 'axis' + key.upper())
			short_pos_str +='%s %d' % (key,int(value*1e6))

		if axes == 0:
			return
		try:
			if self.stage_speed_fraction == self.default_stage_speed_fraction:
				self.tecnai.Stage.Goto(pos, axes)
			else:
				# Low speed move needs to be done on individual axis
				for key, value in list(position.items()):
					single_axis = getattr(self.tem_constants, 'axis' + key.upper())
					self.tecnai.Stage.GotoWithSpeed(pos, single_axis, self.stage_speed_fraction)
		except com_module.COMError as e:
			if self.getDebugStage():
				print(datetime.datetime.now())
				print('COMError in going to %s' % (position,))
			try:
				# used to parse e into (hr, msg, exc, arg)
				# but Issue 4794 got 'need more than 3 values to unpack' error'.
				# simplify the error handling so that it can be raised with messge.
				msg = e.text
				raise RuntimeError('Stage.Goto %s failed: %s' % (short_pos_str,msg))
			except:
				raise RuntimeError('COMError in _set %s: %s' % (short_pos_str,e))
		except:
			if self.getDebugStage():
				print(datetime.datetime.now())
				print('Other error in going to %s' % (position,))
			raise RuntimeError('_set %s Unknown error' % (short_pos_str,))
		self.waitForStageReady('after setting %s' % (position,))

	def _setTomStagePosition(self, position, relative = 'absolute'):
#		tolerance = 1.0e-4
#		polltime = 0.01

		self.waitForStageReady('before setting %s' % (position,))
		if relative == 'relative':
			for key in position:
				position[key] += getattr(self.tecnai.Stage.Position, key.upper())
		elif relative != 'absolute':
			raise ValueError
		
		pos = self.tecnai.Stage.Position

		axes = 0
		stage_limits = self.getStageLimits()
		tom_axes = {'X':0,'Y':1,'Z':2,'A':3}
		for key, value in list(position.items()):
			if use_nidaq and key == 'b':
				deg = value / 3.14159 * 180.0
				nidaq.setBeta(deg)
				continue
			if key in list(stage_limits.keys()) and (value < stage_limits[key][0] or value > stage_limits[key][1]):
				raise ValueError('position %s beyond stage limit at %.2e' % (key, value))
			setattr(pos, key.upper(), value)
			axis_I = tom_axes[key.upper()]

			try:
				self.tom.Stage.GotoWithSpeed(axis_I, getattr(pos,key.upper()))
			except com_module.COMError as e:
				if self.getDebugStage():
					print(datetime.datetime.now())
					print('COMError in going to %s' % (position,))
				try:
					# used to parse e into (hr, msg, exc, arg)
					# but Issue 4794 got 'need more than 3 values to unpack' error'.
					# simplify the error handling so that it can be raised with messge.
					msg = e.text
					raise RuntimeError('Stage.Goto failed: %s' % (msg,))
				except:
					raise RuntimeError('COMError in _setStagePosition: %s' % (e,))
			except:
				if self.getDebugStage():
					print(datetime.datetime.now())
					print('Other error in going to %s' % (position,))
				raise RuntimeError('_setStagePosition Unknown error')
		self.waitForStageReady('after setting %s' % (position,))

	def setDirectStagePosition(self,value):
		self.checkStageLimits(value)
		self._setStagePosition(value)

	def getLowDoseStates(self):
		return ['on', 'off', 'disabled']

	def getLowDose(self):
		try:
			if (self.lowdose.IsInitialized == 1) and (self.lowdose.LowDoseActive == self.tem_constants.IsOn):
				return 'on'
			else:
				return 'off'
		except com_module.COMError as e:
			# No extended error information, assuming low dose is disabled
			return 'disabled'
		except:
			raise RuntimeError('low dose error')
 
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
		except com_module.COMError as e:
			# No extended error information, assuming low dose is disenabled
			raise RuntimeError('Low dose is not enabled')
		except:
			raise RuntimeError('Unknown error')

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
		except com_module.COMError as e:
			# No extended error information, assuming low dose is disenabled
			raise RuntimeError('Low dose is not enabled')
		except:
			raise RuntimeError('Unknown error')
		
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
		except com_module.COMError as e:
			# No extended error information, assuming low dose is disenabled
			raise RuntimeError('Low dose is not enabled')
		except:
			raise RuntimeError('Unknown error')
	
	def getProjectionMode(self):
		if self.tecnai.Projection.Mode == self.tem_constants.pmImaging:
			return 'imaging'
		elif self.tecnai.Projection.Mode == self.tem_constants.pmDiffraction:
			return 'diffraction'
		else:
			raise SystemError
		
	def setProjectionMode(self, fakemode):
		# Always set to the class projection_mode.  This is a work around to
		# proxy not knowing the projection_mode of the instrument.
		mode = self.projection_mode
		if self.getProjectionMode() == mode:
			return 0
		self.setAutoNormalizeEnabled(False)
		if mode == 'imaging':
			self.tecnai.Projection.Mode = self.tem_constants.pmImaging
		elif mode == 'diffraction':
			if self.getProjectionMode() != mode:
				self.setPreDiffractionMagnification()
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
		if self.getMainScreenPosition() == mode:
			return
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
		if self.exposure.CurrentSpecimenHolderName == 'No Specimen Holder':
			return 'no holder'
		elif self.exposure.CurrentSpecimenHolderName == 'Single Tilt':
			return 'single tilt'
		elif self.exposure.CurrentSpecimenHolderName == 'ST Cryo Holder':
			return 'cryo'
		else:
			return 'unknown'

	def setHolderType(self, holdertype):
		if self.exposure is None:
			raise RuntimeError('setHolderType requires adaExp')
		if holdertype == 'no holder':
			holderstr = 'No Specimen Holder'
		elif holdertype == 'single tilt':
			holderstr = 'Single Tilt'
		elif holdertype == 'cryo':
			holderstr = 'ST Cryo Holder'
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

	def _getGaugePressure(self,location):
		# value in pascal unit
		if location not in list(self.pressure_prop.keys()):
			raise KeyError
		if self.pressure_prop[location] is None:
			return 0.0
		return float(self.tecnai.Vacuum.Gauges(self.pressure_prop[location]).Pressure)

	def getColumnPressure(self):
		return self._getGaugePressure('column')

	def getProjectionChamberPressure(self):
		return self._getGaugePressure('projection') # pascal

	def getBufferTankPressure(self):
		return self._getGaugePressure('buffer') # pascal

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
		except com_module.COMError as e:
			# No extended error information 
			raise RuntimeError('runBufferCycle COMError: no extended error information')
		except:
			raise RuntimeError('runBufferCycle Unknown error')

	def setEmission(self, value):
		etext = 'gun emission state can not be set on this instrument'
		if self.tom:
			try:
				self.tom.Gun.Emission = value
			except:
				raise RuntimeError(etext)
		else:
			# only tommoniker has gun access.
			raise RuntimeError(etext)

	def getEmission(self):
		if self.tom:
			try:
				return self.tom.Gun.Emission
			except com_module.COMError as e:
				# Emission is not defined for FEG
				return True
		# no other way to know this, but we do not want it to fail.
		return True

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

	def hasAutoFiller(self):
		try:
			return self.tecnai.TemperatureControl.TemperatureControlAvailable
		except:
			raise
			return False

	def runAutoFiller(self):
		'''
		Trigger autofiller refill. If it can not refill, a COMError
		is raised, and DewarsAreBusyFilling is set to True.  Further
		call of this function returns immediately. The function can be
		reactivated in NitrogenNTS Temperature Control with "Stop Filling"
		followed by "Recover".  It takes some time to recover.
		If ignore these steps for long enough, it does stop filling by itself
		and give Dewar increase not detected error on TUI but will not
		recover automatically.
		If both dewar levels are above 70 percent, the command is denied
		and the function returns 0
		'''
		if not self.hasAutoFiller:
			return
		t0 = time.time()
		try:
			self.tecnai.TemperatureControl.ForceRefill()
		except com_module.COMError as e:
			#COMError: (-2147155969, None, (u'[ln=102, hr=80004005] Cannot force refill', u'TEM Scripting', None, 0, None))
			# This COMError can occur when fill is slow, too.  Need to ignore it
			raise RuntimeError('Failed Force Refill')
		t1 = time.time()
		if t1-t0 < 10.0:
			raise RuntimeError('Force refill Denied: returned in %.1f sec' % (t1-t0))

	def isAutoFillerBusy(self):
		try:
			isbusy = self.tecnai.TemperatureControl.DewarsAreBusyFilling
		except:
			# property not exist for older versions
			isbusy = None
		return isbusy

	def getAutoFillerRemainingTime(self):
		'''
		Get remaining time from instrument. Unit is second.
		If it is not set to cool, the value is -60.
		'''
		try:
			remain_sec = self.tecnai.TemperatureControl.DewarsRemainingTime
		except:
			# property not exist for older versions
			remain_sec = None
		return remain_sec

	def getRefrigerantLevel(self,id=0):
		'''
		Get current refrigerant level. Only works on Krios and Artica. id 0 is the
		autoloader, 1 is the column.
		'''
		return self.tecnai.TemperatureControl.RefrigerantLevel(id)

	def nextPhasePlate(self):
		if os.path.isfile(self.getAutoitPhasePlateExePath()):
			subprocess.call(self.getAutoitPhasePlateExePath())
			error = self._checkAutoItError()
		else:
			pass

	def hasGridLoader(self):
		try:
			return self.tecnai.AutoLoader.AutoLoaderAvailable
		except:
			return False

	def _loadCartridge(self, number):
		state = self.tecnai.AutoLoader.LoadCartridge(number)
		if state != 0:
			raise RuntimeError()

	def _unloadCartridge(self):
		'''
		FIX ME: Can we specify which slot to unload to ?
		'''
		state = self.tecnai.AutoLoader.UnloadCartridge()
		if state != 0:
			raise RuntimeError()

	def getGridLoaderNumberOfSlots(self):
		if self.hasGridLoader():
			return self.tecnai.AutoLoader.NumberOfCassetteSlots
		else:
			return 0

	def getGridLoaderSlotState(self, number):
		# base 1
		if not self.hasGridLoader():
			return self.gridloader_slot_states[0]
		else:
			status = self.tecnai.AutoLoader.SlotStatus(number)
			state = self.gridloader_slot_states[status]
		return state

	def getGridLoaderInventory(self):
		if not self.grid_inventory and self.hasGridLoader():
			self.getAllGridSlotStates()
		return self.grid_inventory

	def performGridLoaderInventory(self):	
		""" need to find return states
				0 - no error, but also could be no action taken.
		"""
		return self.tecnai.AutoLoader.PerformCassetteInventory()

	def getIsEFtem(self):
		flag = self.tecnai.Projection.LensProgram
		if flag == 2:
			return True
		return False

	def hasAutoAperture(self):
		return False

	def retractApertureMechanism(self, mechanism_name):
		'''
		Retract aperture mechanism.
		'''
		return self.setApertureSelection(mechanism_name, 'open')

	def getApertureMechanisms(self):
		'''
		Names of the available aperture mechanism
		'''
		return ['condenser_2', 'objective', 'selected_area']

	def getApertureSelections(self, mechanism_name):
		'''
		get valid selection for an aperture mechanism to be used in gui,including "open" if available.
		'''
		if mechanism_name == 'condenser':
			# always look up condenser 2 value
			mechanism_name = 'condenser_2'
		names = self.getFeiConfig('aperture',mechanism_name)
		# This may be string or integer.
		names = list(map((lambda x: str(x)),names))
		return names

	def getApertureSelection(self, mechanism_name):
		'''
		Get current aperture selection of specified aperture mechanism
		as string name in um or as open.
		'''
		if not self.getUseAutoAperture():
			return 'unknown'
		if mechanism_name == 'condenser':
			# always look up condenser 2 value
			mechanism_name = 'condenser_2'
		if mechanism_name not in list(self.getFeiConfig('aperture').keys()):
			return 'unknown'
		exepath = self.getFeiConfig('aperture','autoit_aperture_selection_exe_path')
		if exepath and os.path.isfile(exepath):
			cmd = '%s "%s" %s %s get' % (exepath,configpath,self.column_type, mechanism_name)
			subprocess.call(cmd)
			error = self._checkAutoItError()
			result = self._getAutoItResult()
			if result:
				return result
		# all counted as invalid state
		return 'unknown'

	def _checkAutoItError(self, error_filename='autoit_error.log'):
		if not log_path:
			print('no log path for autoit error passing')
			return
		errorpath = os.path.join(log_path,error_filename)
		if not os.path.isfile(errorpath):
			return
		f = open(errorpath)
		msglist = f.readlines()
		f.close()
		# cleanup after read
		os.remove(errorpath)
		if msglist:
			raise ValueError(msglist[0].split('\n')[0])

	def _getAutoItResult(self, result_filename='autoit_result.log'):
		if not log_path:
			print('no log path for autoit result passing')
			return
		resultpath = os.path.join(log_path,result_filename)
		if not os.path.isfile(resultpath):
			# the result is None
			return
		f = open(resultpath)
		msglist = f.readlines()
		f.close()
		os.remove(resultpath)
		if msglist:
			return msglist[0].split('\n')[0]

	def setApertureSelection(self, mechanism_name, name):
		'''
		Set Aperture selection of a aperture mechanism with aperture name.
		Aperture name 'open' means retracted aperture. Size string in
		unit of um is used as the name for that aperture.
		return True if change is made
		'''
		if not self.getUseAutoAperture():
			return False
		if mechanism_name == 'condenser':
			# always look up condenser 2 value
			mechanism_name = 'condenser_2'
		selections = self.getApertureSelections(mechanism_name)
		if name not in selections:
			raise ValueError('Invalid selection: %s' % name)
		if name == '' or name is None:
			# nothing to do
			return False
		exepath = self.getFeiConfig('aperture','autoit_aperture_selection_exe_path')
		if exepath and os.path.isfile(exepath):
			cmd = '%s "%s" %s %s set "%s"' % (exepath,configpath,self.column_type, mechanism_name,name)
			subprocess.call(cmd)
			error = self._checkAutoItError()
			return True
		return False

	def getApertureNames(self, mechanism_name):
		'''
		Get string name list of the aperture collection in a mechanism.
		'''
		return self.getApertureSelections(mechanism_name)

	def insertSelectedApertureMechanism(self,mechanism_name, aperture_name):
		'''
		Insert an aperture selected for a mechanism.
		'''
		return self.setApertureSelection(mechanism_name, aperture_name)

	def getBeamstopPosition(self):
		methodname = 'getAutoitGetBeamstopExePath'
		exepath = getattr(self,methodname)()
		if exepath and os.path.isfile(exepath):
			subprocess.call(exepath)
			error = self._checkAutoItError()
			result = self._getAutoItResult()
			if result:
				return result
		# all counted as invalid state
		return 'unknown'

	def setBeamstopPosition(self, value):
		"""
		Possible values: ('in','out','halfway')
		Tecnically tecnai has no software control on this.
		"""
		if value == self.getBeamstopPosition():
			return
		valuecap = value[0].upper()+value[1:]
		methodname = 'getAutoitBeamstop%sExePath' % (valuecap)
		exepath = getattr(self,methodname)()
		max_trials = 5
		if exepath and os.path.isfile(exepath):
			trial = 1
			while value != self.getBeamstopPosition():
				subprocess.call(exepath)
				time.sleep(2.0)
				if self.getDebugAll() and trial > 1:
					print('beamstop positioning trial %d' % trial)
				if trial > max_trials:
					raise RuntimeError('Beamstop setting to %s failed %d times' % (value, trial))
				trial += 1

		else:
			pass

class Krios(Tecnai):
	name = 'Krios'
	column_type = 'titan'
	use_normalization = True
	def __init__(self):
		Tecnai.__init__(self)

	def hasAutoAperture(self):
		return self.getUseAutoAperture()

class Halo(Tecnai):
	'''
	Titan Halo has Titan 3 condensor system but side-entry holder.
	'''
	name = 'Halo'
	column_type = 'titan'
	use_normalization = True

	def getRefrigerantLevel(self,id=0):
		'''
		No autofiller, always filled.
		'''
		return 100, 100

class EFKrios(Krios):
	name = 'EF-Krios'
	column_type = 'titan'
	use_normalization = True
	projection_lens_program = 'EFTEM'

class Talos(Tecnai):
	name = 'Talos'
	column_type = 'talos'
	use_normalization = True

	def hasAutoAperture(self):
		return self.getUseAutoAperture()

class Arctica(Talos):
	name = 'Arctica'
	column_type = 'talos'
	use_normalization = True

	def hasAutoAperture(self):
		return self.getUseAutoAperture()

class Glacios(Arctica):
	name = 'Glacios'
	column_type = 'talos'
	use_normalization = True

class EFGlacios(Arctica):
	name = 'EF-Glacios'
	column_type = 'talos'
	use_normalization = True
	projection_lens_program = 'EFTEM'

#### Diffraction Instrument
class DiffrTecnai(Tecnai):
	name = 'DiffrTecnai'
	column_type = 'tecnai'
	use_normalization = False
	projection_mode = 'diffraction'
	mag_attr_name = 'CameraLength'
	mag_scale = 1000

class DiffrArctica(Arctica):
	name = 'DiffrArctica'
	column_type = 'talos'
	use_normalization = True
	projection_mode = 'diffraction'
	mag_attr_name = 'CameraLength'
	mag_scale = 1000

class DiffrGlacios(Glacios):
	name = 'DiffrGlacios'
	column_type = 'talos'
	use_normalization = True
	projection_mode = 'diffraction'
	mag_attr_name = 'CameraLength'
	mag_scale = 1000

class DiffrKrios(Krios):
	name = 'DiffrKrios'
	column_type = 'titan'
	use_normalization = True
	projection_mode = 'diffraction'
	mag_attr_name = 'CameraLength'
	mag_scale = 1000

class DiffrHalo(Halo):
	name = 'DiffrHalo'
	column_type = 'titan'
	use_normalization = True
	projection_mode = 'diffraction'
	mag_attr_name = 'CameraLength'
	mag_scale = 1000
