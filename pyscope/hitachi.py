# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

import copy
import math
import time
import os

import itertools

from pyscope import tem
from pyscope import hitachisocket

STAGE_DEBUG = False

class MagnificationsUninitialized(Exception):
	pass


class Hitachi(tem.TEM):
	name = 'Hitachi'
	projection_mode = 'imaging'
	def __init__(self):
		
		tem.TEM.__init__(self)

		# use External control port
		self.h = hitachisocket.HitachiSocket('192.168.10.1',12069)

		self.low_mag_mags = [50,100,200,300,400]# ignore 500 and above so that separation is easier.
		self.zoom1_mags = [
			500,700,1000,1200,1500,2000,2500,3000,4000,
			5000,6000,7000,8000,10000,12000,15000,20000,25000,30000,
			40000,50000,60000,70000,80000,100000,120000,150000,200000
			]
		self.magnifications = []
		self.magnification_index = 0

		self.probe_modes = [
			'micro',
			'fine',
			'low mag',
		]
		self.probe_mode_index_cap = {
			'micro': 30,
			'fine': 40,
			'low mag':50,
		}
		self.probe_mode_index = 0

		self.correctedstage = False
		self.corrected_alpha_stage = False
		self.alpha_backlash_delta = 3.0
		self.stage_axes = ['x', 'y', 'z', 'a']
		self.stage_range = {
			'x': (-1e-3, 1e-3),
			'y': (-1e-3, 1e-3),
			'z': (-5e-4, 5e-4),
			'a': (-math.radians(70.0), math.radians(70.0)),
			'b': (-math.radians(60.0), math.radians(60.0)),
		}
		self.minimum_stage = {
			'x':5e-8,
			'y':5e-8,
			'z':5e-8,
			'a':math.radians(0.1),
			'b':math.radians(0.1),
		}
		#TODO: we do no know the top speed for htt
		self.stage_top_speed = 29.78/127 # top speed is translated to 127
		# 40 to 127
		self.stage_speed_decimal = 100

		self.screen_current = 0.000001
		self.intensity_range = (0.0, 1.0)
		self.intensity = 0.0

		self.stigmators = {
			'condenser': {
				'x': 0.0,
				'y': 0.0,
			},
			'objective': {
				'x': 0.0,
				'y': 0.0,
			},
			'diffraction': {
				'x': 0.0,
				'y': 0.0,
				},
		}

		self.spot_sizes = range(1, 5)
		self.spot_size = self.spot_sizes[0]

		self.beam_tilt = {'x': 0.0, 'y': 0.0}
		self.beam_shift = {'x': 0.0, 'y': 0.0}
		self.diffraction_shift = {'x': 0.0, 'y': 0.0}
		self.image_shift = {'x': 0.0, 'y': 0.0}
		self.raw_image_shift = {'x': 0.0, 'y': 0.0}

		self.focus = 0.0
		self.zero_defocus = 0.0

		self.main_screen_scale = 1.0

		self.main_screen_positions = ['up', 'down']
		self.columnvalveposition = 'open'
		self.emission = 'on'
		self.BeamBlank = 'off'
		self.buffer_pressure = 30.0

		self.energy_filter = False
		self.energy_filter_width = 0.0

		self.loaded_slot_number = None
		self.is_init = True

		self.aperture_mechanism_map = {'condenser2':'COND_APT','objective':'OBJ_APT','selected area':'SA_APT'}
		self.aperture_selection = {'objective':'100','condenser_2':'unknown','selected_area':'open'}
		self.beamstop_positions = ['out','in'] # index of this list is API value to set

	def printStageDebug(self,msg):
		if STAGE_DEBUG:
			print msg

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def getColumnValvePosition(self):
		return self.getColumnValvePositions()[1-self.h.runGetCommand('EvacValve','GV',['int',])]

	def setColumnValvePosition(self, state):
		try:
			valid_index = self.getColumnValvePositions().index(state)
			self.h.runSetIntAndWait('EvacValve','GV', [1-valid_index,])
		except ValueError:
			raise RuntimeError('invalid column valve position %s' % (state,))
		except:
			raise RuntimeError('column valve position failed to set to %s' % (state,))

	def getHighTension(self):
		# convert float in kV from htt API to integer in V
		return int(1000*self.h.runGetCommand('HighVoltage','Value',['float',]))

	def setHighTension(self, value):
		if value % 1000:
			raise ValueError('API Only accepts value at precision of kV')
		kv_value = int(value/1000.0) # takes only integer in kV
		self.h.runSetCommand('HighVoltage','Value',[kv_value,],['int',])
		while True:
			if int(self.getHighTensions()) == value:
				break

	def getStagePosition(self):
		xy_submicron = self.h.runGetCommand('StageXY','Position', ['int','int'])
		a_degrees = self.h.runGetCommand('StageTilt','Position', ['float',])
		z_submicron = self.h.runGetCommand('StageZ','Position', ['int',])
		position = {
			'x': xy_submicron[0]*1e-7,
			'y': xy_submicron[1]*1e-7, 
			'z': z_submicron*1e-7,
			'a': math.radians(a_degrees),
			'b': 0.0,
		}
		return position

	def _setStagePosition(self,value):
		keys = value.keys()
		keys.sort()
		keys.reverse()
		if 'z' in keys:
			z_submicron = int(value['z']*1e7)
			self.h.runSetIntAndWait('StageZ','Move', [z_submicron,])
		if 'x' in keys or 'y' in keys:
			set_xy = self.h.runGetCommand('StageXY','Position', ['int','int'])
			if 'x' in keys:
				set_xy[0] = int(value['x']*1e7)
			if 'y' in keys:
				set_xy[1] = int(value['y']*1e7)
			print 'set to', set_xy
			self.h.runSetIntAndWait('StageXY','Move', set_xy)
		if 'a' in keys:
			a_degree = math.degrees(value['a'])
			self.h.runSetFloatAndWait('StageTilt','Move', [a_degree,])
		self.printStageDebug('----------')

	def setDirectStagePosition(self,value):
		self._setStagePosition(value)

	def checkStagePosition(self, position):
		current = self.getStagePosition()
		bigenough = {}
		minimum_stage = self.minimum_stage
		for axis in ('x', 'y', 'z', 'a', 'b'):
			if axis in position:
				delta = abs(position[axis] - current[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = position[axis]
		return bigenough

	def setStageSpeed(self, value):
		# disabled for now. Tilting speed default is rather slow.
		return
		# only for stage tilt.  Don't know the scale yet.
		self.stage_speed_decimal = int(min(value/self.stage_top_speed,127))
		self.stage_speed_decimal = max(self.stage_speed_decimal,40)
		# decimal_speed is 40 ~ 127
		self.h.runSetCommand('StageTilt','Speed', self.stage_decimal_speed,['int',])
		self.speed_deg_per_second = value

	def getStageSpeed(self):
		# hitachi API does not have a get for stage speed.
		if hasattr(self, 'stage_speed_decimal'):
			return self.stage_speed_decimal * self.stage_top_speed
		else:
			return self.stage_top_speed

	def setStagePosition(self, value):
		self.printStageDebug(value.keys())
		value = self.checkStagePosition(value)
		for axis in self.stage_axes:
			if axis == 'b':
				pass
			else:
				try:
					if value[axis] < self.stage_range[axis][0]:
						raise ValueError('Stage position %s out of range' % axis)
					if value[axis] > self.stage_range[axis][1]:
						m = 'invalid stage position for %s axis'
						raise ValueError(m % axis)
				except KeyError:
					pass

		for axis in value.keys():
			if axis == 'b' and value['b'] is not None:
				print 'exception, beta can not be set'
		# calculate pre-position
		prevalue = {}
		prevalue2 = {}
		stagenow = self.getStagePosition()
		if self.correctedstage:
			delta = 2e-6
			for axis in ('x','y','z'):
				if axis in value:
					prevalue[axis] = value[axis] - delta
		relax = 0
		if abs(relax) > 1e-9:
			for axis in ('x','y'):
				if axis in value:
					prevalue2[axis] = value[axis] + relax
		if self.corrected_alpha_stage: 
			# alpha tilt backlash only in one direction
			alpha_delta_degrees = self.alpha_backlash_delta
			if 'a' in value.keys():
					axis = 'a'
					prevalue[axis] = value[axis] - alpha_delta_degrees*3.14159/180.0
		if prevalue:
			# set all axes in prevalue
			for axis in value.keys():
				if axis not in prevalue.keys():
					prevalue[axis] = value[axis]
					del value[axis]
			self._setStagePosition(prevalue)
			time.sleep(0.2)
		if abs(relax) > 1e-9 and prevalue2:
			self._setStagePosition(prevalue2)
			time.sleep(0.2)
		return self._setStagePosition(value)

	def normalizeLens(self, lens='all'):
		pass

	def getScreenCurrent(self):
		return self.screen_current
	
	def getIntensity(self):
		hexdec = h.runGetCommand('Lens', 'C2',['hexdec',])
		print 'result item0 in decimal:%d' % (int(hexdec,16),)
		return self.intensity
	
	def setIntensity(self, value):
		if value < self.intensity_range[0] or value > self.intensity_range[1]:
			raise ValueError('invalid intensity')

	def getStigmator(self):
		return copy.deepcopy(self.stigmators)
		
	def setStigmator(self, value):
		for key in self.stigmators.keys():
			for axis in self.stigmators[key].keys():
				try:
					self.stigmators[key][axis] = value[key][axis]
				except KeyError:
					pass

	def getSpotSize(self):
		return self.spot_size
	
	def setSpotSize(self, value):
		if value not in self.spot_sizes:
			raise ValueError('invalid spot size')
		self.spot_size = value
	
	def getBeamTilt(self):
		return copy.copy(self.beam_tilt)
	
	def setBeamTilt(self, value):
		for axis in self.beam_tilt.keys():
			try:
				self.beam_tilt[axis] = value[axis]
			except KeyError:
				pass
	
	def getBeamShift(self):
		return copy.copy(self.beam_shift)

	def setBeamShift(self, value):
		for axis in self.beam_shift.keys():
			try:
				self.beam_shift[axis] = value[axis]
			except KeyError:
				pass

	def getDiffractionShift(self):
		return copy.copy(self.diffraction_shift)

	def setDiffractionShift(self, value):
		for axis in self.diffraction_shift.keys():
			try:
				self.diffraction_shift[axis] = value[axis]
			except KeyError:
				pass

	def getImageShift(self):
		return copy.copy(self.image_shift)
	
	def setImageShift(self, value):
		for axis in self.image_shift.keys():
			try:
				self.image_shift[axis] = value[axis]
			except KeyError:
				pass

	def getRawImageShift(self):
		return copy.copy(self.raw_image_shift)

	def setRawImageShift(self, value):
		for axis in self.raw_image_shift.keys():
			try:
				self.raw_image_shift[axis] = value[axis]
			except KeyError:
				pass

	def getDefocus(self):
		return self.focus - self.zero_defocus

	def setDefocus(self, value):
		self.focus = value + self.zero_defocus

	def resetDefocus(self):
		self.zero_defocus = self.focus

	def getMagnification(self, index=None):
		if index is None:
			return self.h.runGetCommand('Column','Magnification',['int',])
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications[index]
			except IndexError:
				raise ValueError('invalid magnification index')

	def getMainScreenMagnification(self, index=None):
		return self.main_screen_scale*self.getMagnification(index=index)

	def getMainScreenScale(self):
		return self.main_screen_scale

	def setMainScreenScale(self, value):
		self.main_screen_scale = value

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
			# TODO self.tecnai.Projection.Focus = 0.0
			self.setMagnificationIndex(index)
			self.mag_changed = True
		return

	def getMagnificationIndex(self, magnification=None):
		if magnification is not None:
			return self.magnifications.index(magnification)
		return self.magnification_index

	def setMagnificationIndex(self, value):
		if value < 0 or value >= len(self.magnifications):
			raise ValueError('invalid magnification index')
		self.getProbeMode()
		mag = self.magnifications[value]
		self.h.runSetIntAndWait('Column','Magnification', [mag,])

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.setProjectionSubModeMap({})
		self.magnifications = list(self.low_mag_mags)
		self.magnifications.extend(self.zoom1_mags)
		for i, mag in enumerate(self.magnifications):
			if i < len(self.low_mag_mags):
				self.addProjectionSubModeMap(mag,'LowMag',0)
			else:
				self.addProjectionSubModeMap(mag,'Zoom-1',1)

	def getMagnifications(self):
		return list(self.magnifications)

	def setMagnifications(self, magnifications):
		self.magnifications = magnifications

	def getMagnificationsInitialized(self):
		if self.magnifications:
			return True
		else:
			return False

	def _getColumnModes(self):
		mode_h, submode_h = self.h.runGetCommand('Column','Mode',['hexdec','hexdec'])
		mode_d = int(mode_h,16)
		submode_d = int(submode_h,16)
		return mode_d, submode_d

	def getProbeMode(self):
		mode_d, submode_d = self._getColumnModes()
		for probe in self.probe_modes:
			# find the first probe that passes
			if mode_d < self.probe_mode_index_cap[probe]:
				return probe
		raise ValueError('probe mode found not registered')

	def setProbeMode(self, value):
		new_probe = str(value)
		try:
			new_probe_index = self.probe_modes.index(new_probe)
		except ValueError:
			raise ValueError('invalid probe mode')
		prev_probe = self.getProbeMode()
		if prev_probe == new_probe:
			return
		prev_probe_index = self.probe_modes.index(str(prev_probe))
		base = 0
		prev_mode_d, prev_submode_d = self._getColumnModes()
		if prev_probe_index > 0:
			base = self.probe_mode_index_cap[self.probe_modes[prev_probe_index-1]]
		spot_index= prev_mode_d - base
		new_base = 0
		if new_probe_index > 0:
			new_base = self.probe_mode_index_cap[self.probe_modes[new_probe_index-1]]
		new_mode_d = new_base+spot_index
		new_mode_h = hex(new_mode_d)
		hex_length = 2 #mode code length
		submodes = {
			'micro': hex(int('00',16)),
			'fine': hex(int('00',16)),
			'low mag': hex(int('0e',16)),
		}
		submode_h = submodes[new_probe]
		print prev_mode_d
		print new_mode_h, submode_h
		self.h.runSetHexdecAndWait('Column','Mode',[new_mode_h, submode_h],['hexdec','hexdec'],hex_length=hex_length)
	def getProbeModes(self):
		return list(self.probe_modes)

	def setProjectionMode(self, value):
		# This is a fake value set.  It forces the projection mode defined by
		# the class.
		#print 'fake setting to projection mode %s' % (self.projection_mode,)
		pass

	def getMainScreenPositions(self):
		return list(self.main_screen_positions)

	def getMainScreenPosition(self):
		return self.getMainScreenPositions()[self.h.runGetCommand('Screen','Position',['int',])]

	def setMainScreenPosition(self, value):
		positions = self.getMainScreenPositions()
		if value not in positions:
			raise ValueError('invalid main screen position')
		apt_index = positions.index(value)
		self.h.runSetIntAndWait('Screen','Position', [apt_index,])
		#TODO: screen out returns much faster than gui indicates. May need sleep time

	def getFocus(self):
		return self.focus

	def setFocus(self, value):
		self.focus = value

	def getBufferTankPressure(self):
		return self.buffer_pressure

	def runBufferCycle(self):
		time.sleep(5)
		self.buffer_pressure -= 5

	def getTurboPump(self):
			if not hasattr(self, 'turbo'):
				self.turbo = 'off'
			return self.turbo

	def setTurboPump(self, value):
			self.turbo = value

	def setEmission(self, value):
		self.emission = value

	def getEmission(self):
		return self.emission

	def getBeamBlank(self):
		return self.BeamBlank
		
	def setBeamBlank(self, bb):
		self.BeamBlank = bb

	def hasAutoFiller(self):
		return False

	def exposeSpecimenNotCamera(self,seconds):
		time.sleep(seconds)

	def hasGridLoader(self):
		# 3 speciment holder is not a grid loader but similar.
		# disabled for now.
		return False

	def getGridLoaderNumberOfSlots(self):
		if not self.hasGridLoader():
			return 0
		return 3

	def getGridLoaderSlotState(self, number):
		if self.loaded_slot_number == number:
			state = 'empty'
		elif self.loaded_slot_number is None and number == 1 and self.is_init is True:
			self.is_init = False
			state = 'empty'
		else:
			state = 'occupied'
		return state

	def _loadCartridge(self, number):
		self.h.runSetIntAndWait('Stage','SpecimenNo',[number,])
		self.loaded_slot_number = number
		time.sleep(2)

	def _unloadCartridge(self):
		# multi-specimen holder does not have unload
		return

	def getGridLoaderInventory(self):
		self.getAllGridSlotStates()

	def getApertureMechanisms(self):
		'''
		Names of the available aperture mechanism
		'''
		return ['objective',]

	def getApertureSelections(self, aperture_mechanism):
		if aperture_mechanism == 'objective':
			return ['open','100']
		return ['open',]

	def getApertureSelection(self, aperture_mechanism):
		if aperture_mechanism not in self.getApertureMechanisms():
			return 'unknown'
		apt_api_name = self.aperture_mechanism_map[aperture_mechanism]
		sel_names = self.getApertureSelections(aperture_mechanism)
		sel_index = self.h.runGetCommand(apt_api_name,'Position',['int',])
		return sel_names[sel_index]

	def setApertureSelection(self, aperture_mechanism, name):
		if aperture_mechanism == 'condenser':
			aperture_mechanism = 'condenser_2'
		if name not in self.getApertureSelections(aperture_mechanism):
			# failed
			return False
		apt_api_name = self.aperture_mechanism_map[aperture_mechanism]
		apt_selections = self.getApertureSelections(aperture_mechanism)
		apt_sel_index = apt_selections.index(name)
		self.h.runSetIntAndWait(apt_api_name,'Position',[apt_sel_index,])
		return True

	def retractApertureMechanism(self, aperture_mechanism):
		return setApertureSelection(aperture_mechanism, 'open')

	def getBeamstopPosition(self):
		p_index = self.h.runGetCommand('SpotMask','Position',['int',])
		return self.beamstop_positions[p_index]

	def setBeamstopPosition(self, value):
		try:
			p_index = self.beamstop_positions.index(value)
		except:
			raise ValueError('invalid beamstop position setting %s' % (value,))
		self.h.runSetIntAndWait('SpotMask','Position',[p_index,])

