# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

import copy
import math
from . import tem
import threading
import time
import json
import os

import itertools

try:
	from . import nidaq
except:
	nidaq = None

simu_autofiller = False
STAGE_DEBUG = False

class SimTEM(tem.TEM):
	name = 'SimTEM'
	projection_mode = 'imaging'
	def __init__(self):
		tem.TEM.__init__(self)

		self.high_tension = 120000.0
		self.cfeg_flashing = 0

		self.magnifications = [
			50,
			100,
			500,
			1000,
			5000,
			25000,
			50000,
		]
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
		if nidaq is not None:
			self.stage_axes.append('b')
		self.stage_range = {
			'x': (-1e-3, 1e-3),
			'y': (-1e-3, 1e-3),
			'z': (-5e-4, 5e-4),
			'a':(math.radians(-70),math.radians(70)),
			'b':(math.radians(-90),math.radians(90)), # no limit
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
		self.stage_top_speed = 29.78
		self.stage_speed_fraction = 1.0

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

		self.spot_sizes = list(range(1, 11))
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

		self.resetRefrigerant()
		self.loaded_slot_number = None
		self.is_init = True

		self.aperture_selection = {'objective':'100','condenser_2':'70','selected_area':'open'}
		if 'simpar' in self.conf and self.conf['simpar'] and os.path.isdir(self.conf['simpar']):
			self.simpar_dir = self.conf['simpar']
			self.resetSimPar()
		else:
			self.simpar_dir = None

	def resetSimPar(self):
		if self.simpar_dir:
			# reset to empty file
			f = open(os.path.join(self.simpar_dir,'simpar.json'),'w')
			f.close()

	def saveSimPar(self,key,value):
		if self.simpar_dir:
			# open the file or both read and write and thus locked from others
			f = open(os.path.join(self.simpar_dir,'simpar.json'),'r+')
			try:
				self.all_simpar = json.loads(f.read())
			except ValueError:
				self.all_simpar = {}
			self.all_simpar[key] = value
			# move pointer back to the start
			f.seek(0)
			jstr = json.dumps(self.all_simpar, indent=2, separators=(',',':'))
			f.write(jstr)
			# truncate extra old stuff
			f.truncate()
			f.close()

	def printStageDebug(self,msg):
		if STAGE_DEBUG:
			print(msg)

	def resetRefrigerant(self):
		self.autofiller_busy = False
		self.level0 = 100.0
		self.level1 = 100.0
		if simu_autofiller:
			t = threading.Thread(target=self.useRefrigerant)
			t.setDaemon(True)
			t.start()

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def getColumnValvePosition(self):
		return self.columnvalveposition

	def setColumnValvePosition(self, state):
		if state in ('open','closed'):
			self.columnvalveposition = state
		else:
			raise RuntimeError('invalid column valve position %s' % (state,))

	def getHighTension(self):
		return self.high_tension

	def setHighTension(self, value):
		self.high_tension = value

	def getColdFegFlashing(self):
		value = self.cfeg_flashing
		value_map = [('error', -1), ('off',0),('on',1)]
		if value == -1:
			raise RuntimeError('CFEG Flashing in error state')
		values = map((lambda x: x[1]), value_map)
		state = value_map[values.index(value)][0]
		return state

	def setColdFegFlashing(self, state):
		# On starts flashing, Off stops flashing
		if state == self.getColdFegFlashing():
			# do nothing
			return
		value_map = [('off',0), ('on',1)]
		states = map((lambda x: x[0]), value_map)
		value = value_map[states.index(state)][1]
		self.cfeg_flashing = value
		# TODO: how long before the the state change in get ?
		time.sleep(5)
		if state == 'on':
			while self.getColdFegFlashing() == 'on':
				time.sleep(5)
				self.cfeg_flashing = 0
		return

	def getStagePosition(self):
		try:
			beta = nidaq.getBeta()
			self.stage_position.update({'b':beta})
		except:
			# give values so it is behaved like real tem implementation
			self.stage_position.update({'b':0.0})
		return copy.copy(self.stage_position)

	def getStageLimits(self):
		limits = self.stage_range
		return limits

	def _setStagePosition(self,value):
		# check limit here so that direct move will also be caught
		self.checkStageLimits(value)
		keys = list(value.keys())
		keys.sort()
		for axis in keys:
				self.printStageDebug('%s: %s' % (axis, value[axis]))
				try:
					self.stage_position[axis] = value[axis]
				except KeyError:
					continue
		self.printStageDebug('----------')

	def setDirectStagePosition(self,value):
		self._setStagePosition(value)

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
		minimum_stage = self.minimum_stage
		for axis in ('x', 'y', 'z', 'a', 'b'):
			if axis in position:
				delta = abs(position[axis] - current[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = position[axis]
		return bigenough

	def setStageSpeed(self, value):
		self.speed_deg_per_second = value
		self.stage_speed_fraction = min(value/self.stage_top_speed,1.0)

	def getStageSpeed(self):
			return self.stage_speed_fraction * self.stage_top_speed

	def setStagePosition(self, value):
		self.printStageDebug(list(value.keys()))
		value = self.checkStagePosition(value)

		for axis in list(value.keys()):
			if axis == 'b' and value['b'] is not None:
				try:
					nidaq.setBeta(value['b'])
				except:
					print('exception, beta not set')
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
			if 'a' in list(value.keys()):
					axis = 'a'
					prevalue[axis] = value[axis] - alpha_delta_degrees*3.14159/180.0
		if prevalue:
			# set all axes in prevalue
			for axis in list(value.keys()):
				if axis not in list(prevalue.keys()):
					prevalue[axis] = value[axis]
					del value[axis]
			self._setStagePosition(prevalue)
			time.sleep(0.2)
		if abs(relax) > 1e-9 and prevalue2:
			self._setStagePosition(prevalue2)
			time.sleep(0.2)
		if self.stage_speed_fraction < 1.0:
			if 'a' in list(value.keys()):
				alpha_delta = math.degrees(abs(value['a']-stagenow['a']))
				move_time = alpha_delta / (self.stage_speed_fraction*self.stage_top_speed)
				time.sleep(max(move_time,0.2))
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
		for key in list(self.stigmators.keys()):
			for axis in list(self.stigmators[key].keys()):
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
		for axis in list(self.beam_tilt.keys()):
			try:
				self.beam_tilt[axis] = value[axis]
			except KeyError:
				pass
	
	def getBeamShift(self):
		return copy.copy(self.beam_shift)

	def setBeamShift(self, value):
		for axis in list(self.beam_shift.keys()):
			try:
				self.beam_shift[axis] = value[axis]
			except KeyError:
				pass

	def getDiffractionShift(self):
		return copy.copy(self.diffraction_shift)

	def setDiffractionShift(self, value):
		for axis in list(self.diffraction_shift.keys()):
			try:
				self.diffraction_shift[axis] = value[axis]
			except KeyError:
				pass

	def getImageShift(self):
		return copy.copy(self.image_shift)
	
	def setImageShift(self, value):
		for axis in list(self.image_shift.keys()):
			try:
				self.image_shift[axis] = value[axis]
			except KeyError:
				pass

	def getRawImageShift(self):
		return copy.copy(self.raw_image_shift)

	def setRawImageShift(self, value):
		for axis in list(self.raw_image_shift.keys()):
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
				self.addProjectionSubModeMap(mag,'mode0',0,'mode0')
			else:
				self.addProjectionSubModeMap(mag,'mode1',1,'mode1')

	def getMagnifications(self):
		return list(self.magnifications)

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
		#print('fake setting to projection mode %s' % (self.projection_mode,))
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

	def getEnergyFiltered(self):
		return True

	def getEnergyFilter(self):
		return self.energy_filter

	def setEnergyFilter(self, value):
		#print('TEM energy filter', value)
		self.energy_filter = bool(value)

	def getEnergyFilterWidth(self):
		return self.energy_filter_width

	def setEnergyFilterWidth(self, value):
		#print('TEM energy filter width = ', value)
		self.energy_filter_width = float(value)

	def getRefrigerantLevel(self,id=0):
		if id == 0:
			level = self.level0
		else:
			level = self.level1
		print(id, level)
		return level

	def hasAutoFiller(self):
		return True

	def runAutoFiller(self):
		self.autofiller_busy = True
		self.ventRefrigerant()
		self.addRefrigerant(4)
		if self.level0 <=40 or self.level1 <=40:
			self.autofiller_busy = True
			raise RuntimeError('Force fill failed')
		self.addRefrigerant(4)
		self.autofiller_busy = False

	def resetAutoFillerError(self):
		self.autofiller_busy = False
		self.level0 = 100
		self.level1 = 100

	def isAutoFillerBusy(self):
		return self.autofiller_busy

	def useRefrigerant(self):
		while 1:
			self.level0 -= 11
			self.level1 -= 11
			if self.level1 <= 0:
				print('empty col')
			self.level0 = max(self.level0,0.0)
			self.level1 = max(self.level1,0.0)
			print('using', self.level0, self.level1)
			time.sleep(4)

	def ventRefrigerant(self):
		self.level0 -= 10
		self.level1 -= 10
		print('venting', self.level0, self.level1)
		time.sleep(2)

	def addRefrigerant(self,cycle):
		for i in range(cycle):
			self.level0 += 20
			self.level1 += 20
			print('adding', self.level0, self.level1)
			time.sleep(2)

	def getAutoFillerRemainingTime(self):
		if simu_autofiller:
			return min(self.level0, self.level1)
		else:
			return -60

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
		print('beamstop set to %s' % (value,))
		self.beamstop_position = value

class SimTEM300(SimTEM):
	name = 'SimTEM300'
	def __init__(self):
		SimTEM.__init__(self)

		self.high_tension = 300000.0

		self.magnifications = [
			1550,
			2250,
			3600,
			4800,
			130000
		]
		self.magnification_index = 0

		self.probe_modes = [
			'micro',
			'nano',
		]

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.setProjectionSubModeMap({})
		for mag in self.magnifications:
			if mag < 2000:
				self.addProjectionSubModeMap(mag,'LM',0,'lm')
			else:
				self.addProjectionSubModeMap(mag,'SA',1,'hm')

class SimDiffrTEM(SimTEM):
	name = 'SimDiffrTEM'
	projection_mode = 'diffraction'
	def __init__(self):
		SimTEM.__init__(self)

		self.magnifications = [
			70,
			120,
			520,
			1200,
			5200,
			27000,
			52000,
		]
		self.high_tension = 120000.0

	def getProjectionMode(self):
		return self.projection_mode

class SimDiffrTEM300(SimDiffrTEM):
	name = 'SimDiffrTEM300'
	projection_mode = 'diffraction'
	def __init__(self):
		SimDiffrTEM.__init__(self)
		# to use with SimTEM300
		self.high_tension = 300000.0

class SimGlacios(SimTEM):
	name = 'SimGlacios'
	def __init__(self):
		SimTEM.__init__(self)

		self.high_tension = 200000.0

		self.magnifications = [
			155,
			1250,
			8500,
			150000
		]
		self.magnification_index = 0

		self.probe_modes = [
			'micro',
			'nano',
		]

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.setProjectionSubModeMap({})
		for mag in self.magnifications:
			if mag < 1000:
				self.addProjectionSubModeMap(mag,'LM',1,'lm')
			elif mag < 2600:
				self.addProjectionSubModeMap(mag,'Mi',2,'hm')
			else:
				self.addProjectionSubModeMap(mag,'SA',3,'hm')

class SimDiffrGlacios(SimDiffrTEM):
	name = 'SimDiffrGlacios'
	projection_mode = 'diffraction'
	def __init__(self):
		SimDiffrTEM.__init__(self)
		self.high_tension = 200000.0
		self.magnifications = [
			1100,
			2750,
		]
