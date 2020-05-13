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

class Hitachi(tem.TEM):
	name = 'Hitachi'
	projection_mode = 'imaging'
	def __init__(self):
		tem.TEM.__init__(self)

		self.h = hitachisocket.HitachiSocket('192.168.10.1',12068)

		self.high_tension = 100000.0

		self.magnifications = []
		self.magnification_index = 0

		self.probe_modes = [
			'micro',
			'nano',
		]
		self.probe_mode_index = 0

		self.correctedstage = False
		self.corrected_alpha_stage = False
		self.alpha_backlash_delta = 3.0
		self.stage_axes = ['x', 'y', 'z', 'a']
		self.stage_range = {
			'x': (-1e-3, 1e-3),
			'y': (-1e-3, 1e-3),
			'z': (-5e-4, 5e-4),
			'a': (-math.pi/2, math.pi/2),
		}
		self.minimum_stage = {
			'x':5e-8,
			'y':5e-8,
			'z':5e-8,
			'a':math.radians(0.01),
			'b':1e-4,
		}
		self.stage_position = {}
		for axis in self.stage_axes:
			self.stage_position[axis] = 0.0
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
		self.main_screen_position = self.main_screen_positions[0]
		self.columnvalveposition = 'open'
		self.emission = 'on'
		self.BeamBlank = 'off'
		self.buffer_pressure = 30.0
		self.beamstop_position = 'out'

		self.energy_filter = False
		self.energy_filter_width = 0.0

		self.loaded_slot_number = None
		self.is_init = True

		self.aperture_selection = {'objective':'100','condenser_2':'70','selected_area':'open'}

	def printStageDebug(self,msg):
		if STAGE_DEBUG:
			print msg

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def getColumnValvePosition(self):
		return self.getColumnValvePositions()[1-self.h.runGetCommand('EvacValve','GV',['int',]))

	def setColumnValvePosition(self, state):
		try:
			valid_index = self.getColumnValvePositions().index(state)
			self.h.runSetIntAndWait('EvacValve','GV', 1-valid_index)
		except ValueError:
			raise RuntimeError('invalid column valve position %s' % (state,))
		except:
			raise RuntimeError('column valve position failed to set to %s' % (state,))

	def getHighTension(self):
		# convert float in kV from htt SDK to V
		return 1000*self.h.runGetCommand('HighVoltage','Value',['float',]))

	def setHighTension(self, value):
		kv_value = int(value/1000.0) # takes only integer in kV
		self.h.runSetCommand('HighVoltage','Value',[kv_value,],['int',]))
		self.high_tension = value

	def getStagePosition(self):
		return copy.copy(self.stage_position)

	def _setStagePosition(self,value):
		keys = value.keys()
		keys.sort()
		keys.reverse()
		if 'z' in keys:
			z_submicron = int(value['z']*1e6)
			self.h.runSetIntAndWait('StageZ','Move', z_submicron)
		if 'x' in keys or 'y' in keys:
			set_xy = self.h.runGetCommand('StageXY','Position', ['int','int'])
			if 'x' in keys:
				set_xy[0] = int(value['x']*1e6)
			if 'y' in keys:
				set_xy[1] = int(value['y']*1e6)
			self.h.runSetIntAndWait('StageXY','Move', set_xy)
		if 'a' in keys:
			a_degree = math.degrees(value['a'])
			self.h.runSetFloatAndWait('StageTilt','Move', a_degree)
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
		return
		# only for stage tilt.  Don't know the scale yet.
		self.stage_speed_decimal = int(min(value/self.stage_top_speed,127))
		self.stage_speed_decimal = max(self.stage_speed_decimal,40)
		# decimal_speed is 40 ~ 127
		self.h.runSetCommand('StageTilt','Speed', self.stage_decimal_speed,['int',])
		self.speed_deg_per_second = value

	def getStageSpeed(self):
		# hitachi SDK does not have a get for stage speed.
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
			index = self.magnification_index
		try:
			return self.magnifications[index]
		except IndexError:
			raise ValueError('invalid magnification')

	def getMainScreenMagnification(self, index=None):
		return self.main_screen_scale*self.getMagnification(index=index)

	def getMainScreenScale(self):
		return self.main_screen_scale

	def setMainScreenScale(self, value):
		self.main_screen_scale = value

	def setMagnification(self, value):
		try:
			self.magnification_index = self.magnifications.index(value)
			self.saveSimPar('magnification', value)
		except ValueError:
			raise ValueError('invalid magnification')

	def getMagnificationIndex(self, magnification=None):
		if magnification is not None:
			return self.magnifications.index(magnification)
		return self.magnification_index

	def setMagnificationIndex(self, value):
		if value < 0 or value >= len(self.magnifications):
			raise ValueError('invalid magnification index')
		self.magnification_index = value

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.setProjectionSubModeMap({})
		for mag in self.magnifications:
			if mag < 5000:
				self.addProjectionSubModeMap(mag,'mode0',0)
			else:
				self.addProjectionSubModeMap(mag,'mode1',1)

	def getMagnifications(self):
		return list(self.magnifications)

	def setMagnifications(self, magnifications):
		self.magnifications = magnifications

		self.magnifications = magnifications

	def getMagnificationsInitialized(self):
		return True

	def getProbeMode(self):
		index = self.probe_mode_index
		try:
			return self.probe_modes[index]
		except IndexError:
			raise ValueError('invalid probe mode')

	def setProbeMode(self, value):
		try:
			self.probe_mode_index = self.probe_modes.index(str(value))
		except ValueError:
			raise ValueError('invalid probe mode')

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
		return self.main_screen_position

	def setMainScreenPosition(self, value):
		if value not in self.main_screen_positions:
			raise ValueError('invalid main screen position')
		self.main_screen_position = value

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
		return True

	def getGridLoaderNumberOfSlots(self):
		if not self.hasGridLoader():
			return 0
		return 4

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
		self.loaded_slot_number = number
		time.sleep(2)

	def _unloadCartridge(self):
		self.loaded_slot_number = None

	def getGridLoaderInventory(self):
		self.getAllGridSlotStates()

	def getApertureMechanisms(self):
		'''
		Names of the available aperture mechanism
		'''
		return ['condenser_2', 'objective', 'selected_area']

	def getApertureSelections(self, aperture_mechanism):
		if aperture_mechanism == 'objective':
			return ['open','100']
		if aperture_mechanism == 'condenser_2' or aperture_mechanism == 'condenser':
			return ['150','100','70']
		return ['open']

	def getApertureSelection(self, aperture_mechanism):
		if aperture_mechanism == 'condenser':
			aperture_mechanism = 'condenser_2'
		return self.aperture_selection[aperture_mechanism]

	def setApertureSelection(self, aperture_mechanism, name):
		if aperture_mechanism == 'condenser':
			aperture_mechanism = 'condenser_2'
		if name not in self.getApertureSelections(aperture_mechanism):
			self.aperture_selection[aperture_mechanism] = 'unknown'
			return False
		self.aperture_selection[aperture_mechanism] = name
		return True

	def retractApertureMechanism(self, aperture_mechanism):
		return setApertureSelection(aperture_mechanism, 'open')

	def getBeamstopPosition(self):
		return self.beamstop_position

	def setBeamstopPosition(self, value):
		print 'beamstop set to %s' % (value,)
		self.beamstop_position = value

