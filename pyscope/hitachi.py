# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

import copy
import math
import time
import os
import sys
import re
import numpy
import numpy.linalg

import itertools

from pyami import moduleconfig
from pyscope import tem
from pyscope import hitachisocket

STAGE_DEBUG = True

class MagnificationsUninitialized(Exception):
	pass


configs = moduleconfig.getConfigured('hht.cfg')

class Hitachi(tem.TEM):
	name = 'Hitachi'
	projection_mode = 'imaging'
	######
	# The configuration below is a fake example. It does not represent any real instrument model
	######
	projection_submodes = {1:'lowmag',2:'zoom'}  # Do this in order.  There is no mode_id in hitachi script. The keys here are for ordering.
	projection_submode_ids = [1,2]  # Give it a fixed order

	submodes = {
			'lowmag': hex(1),
			'zoom': hex(2),
			}
	obsv_probe_modes = [
			'high-mag1',
			'low-mag1',
			] # in order of index cap
	# See Appendix of SDK documentation for range for each scope model.
	obsv_probe_mode_index_range = {
			'high-mag1': (0,5),
			'low-mag1':(40,45),
		}

	# (index_range of mode,submode index)
	# [lowmag, zoom]
	mode_id_map = [((0,5),(1,)),((5,10),(2,)),]
	# lens current range span 000000 - 3FFC00 
	lens_hex_range = {
		'OBJ':(0,2.0),
		'C2':(0,2.0),
	}

	def __init__(self):
		
		tem.TEM.__init__(self)

		if sys.platform == 'win32':
			# use External control port
			self.h = hitachisocket.HitachiSocket('192.168.10.1',12069)
		else:
			# HitachiSimu
			self.h = hitachisocket.HitachiSocket('127.0.0.1',12068)

		self.magnifications = []
		self.magnification_index = 0
		self.probe_map = self.initiateProbeMap() # key is probe group such as micro-hc, item is observation_name of the prob selected by observation_probe_to_use such as micro-hc1
		self.probe_modes = self.makeOrderedProbeModeList()
		self.submode_mags = self.initiateSubModeMags()

		self.probe_mode_index = 0

		self.correctedstage = True
		self.corrected_alpha_stage = True
		self.alpha_backlash_delta = 0.0
		self.stage_axes = ['x', 'y', 'z', 'a']
		#keep backlash correction distance from edge
		self.stage_range = self.getStageLimits()
		self.minimum_stage = {
			'x':5e-8,
			'y':5e-8,
			'z':5e-8,
			'a':math.radians(0.1),
			'b':math.radians(0.1),
		}
		#TODO: we do no know the top speed for hht
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


		self.beam_tilt = {'x': 0.0, 'y': 0.0}
		self.beam_shift = {'x': 0.0, 'y': 0.0}
		self.diffraction_shift = {'x': 0.0, 'y': 0.0}
		self.image_shift = {'x': 0.0, 'y': 0.0}
		self.raw_image_shift = {'x': 0.0, 'y': 0.0}

		self.focus = 0.0
		self.zero_defocus_current = {}

		self.main_screen_scale = 1.0

		self.main_screen_positions = ['up', 'down']
		self.columnvalveposition = 'open'
		self.emission = 'on'
		self.BeamBlank = 'off'
		self.buffer_pressure = 30.0

		self.energy_filter = False
		self.energy_filter_width = 0.0

		self.loaded_slot_number = self._getLoadedSlotNumber()
		self.is_init = True

		self.aperture_mechanism_map = {'condenser':'COND_APT','objective':'OBJ_APT','selected area':'SA_APT'}
		self.aperture_selection = {'objective':'open','condenser':'unknown','selected_area':'unknown'}
		self.beamstop_positions = ['out','in'] # index of this list is API value to set
		self.coil_map = [('BT','beam_tilt'),('BH','beam_shift'),('PA','image_shift'),('CS','condenser_stig'),('OS','objective_stig'),('IS','diffraction_stig')]
		self.stig_coil_map = {'condenser':'CS','objective':'OS','diffraction':'IS'}
		self.coil_pause = 0.3	

	def printStageDebug(self,msg):
		if STAGE_DEBUG:
			print msg

	def getHitachiConfig(self,optionname,itemname=None):
		if optionname not in configs.keys():
			return None
		if itemname is None:
			return configs[optionname]
		else:
			if itemname not in configs[optionname]:
				return None
			return configs[optionname][itemname]

	def initiateProbeMap(self):
		observation_probes_to_use = self.getHitachiConfig('optics','observation_probe_to_use')
		if not observation_probes_to_use:
			raise ValueError('Must define one of the preset illumination modes you want access as OBSERVATION_PROBE_TO_USE in hht.cfg')
		return observation_probes_to_use

	def makeOrderedProbeModeList(self):
		'''
		Return a list of probe name in the same order as self.obsv_probe_modes
		'''
		probe_modes = []
		for obsv_probe in self.obsv_probe_modes:
			if obsv_probe in self.probe_map.values():
				probe = self._mapObservationProbeToProbe(obsv_probe)
				probe_modes.append(probe)
		return probe_modes

	def initiateSubModeMags(self):
		'''
		Returns a dictionary of mags in each projection submode (i.e., imaging system mode)
		'''
		submode_mags = {}
		for s_id in self.projection_submode_ids:
			submode_mags[s_id] = []
		submode_mags = self.getHitachiConfig('optics','mags')
		for submode in submode_mags.keys():
			if submode not in self.projection_submodes.values():
				raise ValueError('%s assigned in hht.cfg MAGS is not a valid imaging mode' % submode)
		return submode_mags

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def setIntensityZoom(self, value):
		if self.getProbeMode() == 'low-mag':
			raise ('Can not set IntensityZoom in low-mag mode')
		if value is True:
			self.h.runSetCommand('Column','BrightnessLink',[])
		else:
			self.h.runSetCommand('Column','BrightnessFree',[])
		
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
		if value != 100000:
			raise ValueError('Currently only calibrated for 100 kV')
		if value % 1000:
			raise ValueError('API Only accepts value at precision of kV')
		kv_value = int(value/1000.0) # takes only integer in kV
		self.h.runSetCommand('HighVoltage','Value',[kv_value,],['int',])
		while True:
			if int(self.getHighTension()) == value:
				break
			tim.sleep(0.1)

	def getStageLimits(self):
		return self.getHitachiConfig('stage','stage_limits')

	def getStagePosition(self):
		xy_submicron = self.h.runGetCommand('StageXY','Position', ['int','int'])
		limit = self.getStageAlphaDegreeLimit()
		if abs(limit[0]) < 0.1 and abs(limit[1]) < 0.1:
			# alpha disabled
			a_degrees = 0.0
		else:
			a_degrees = self.h.runGetCommand('StageTilt','Position', ['float',])
		z_submicron = self.h.runGetCommand('StageZ','Position', ['int',])
		position = {
			'x': xy_submicron[1]*1e-7, # swap xy to make x axis the tilt axis in Leginon
			'y': xy_submicron[0]*1e-7, # swap xy to make x axis the tilt axis in Leginon
			'z': z_submicron*1e-7,
			'a': math.radians(a_degrees),
			'b': 0.0,
		}
		return position

	def getStageAlphaDegreeLimit(self):
		limits = self.getStageLimits()
		return (math.degrees(limits['a'][0]),math.degrees(limits['a'][1]))

	def _setStagePosition(self,value, alpha_precision=0.11):
		keys = value.keys()
		keys.sort()
		keys.reverse()
		if 'z' in keys:
			z_submicron = int(value['z']*1e7)
			self.h.runSetIntAndWait('StageZ','Move', [z_submicron,])
		if 'x' in keys or 'y' in keys:
			set_xy = self.h.runGetCommand('StageXY','Position', ['int','int'])
			if 'x' in keys:
				set_xy[1] = int(value['x']*1e7) # swap xy to make x axis the tilt axis in Leginon
			if 'y' in keys:
				set_xy[0] = int(value['y']*1e7) # swap xy to make x axis the tilt axis in Leginon
			self.printStageDebug('set to %s' % (set_xy,))
			# give enough time to move from one end to the other end
			self.h.runSetIntAndWait('StageXY','Move', set_xy, timeout=30)
		if 'a' in keys:
			a_degree = round(10*math.degrees(value['a']))*0.1
			limit = self.getStageAlphaDegreeLimit()
			if abs(limit[0]) < 0.1 and abs(limit[1]) < 0.1:
				# alpha is disabled.
				return
			if a_degree >= limit[0] and a_degree <= limit[1]:
				self.h.runSetFloatAndWait('StageTilt','Move', [a_degree,],precision=alpha_precision)
			else:
				raise ValueError('requested stage tilt %.1f degrees out of range' % (a_degree))
		self.printStageDebug('----------')

	def setDirectStagePosition(self,value):
		'''
		Direct set without backlash correction or range test. disabled alpha will return without setting.
		'''
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
			delta = -4e-6
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
			# The stage alpha overshoot vby up to 0.4 degrees
			# positive direction, and may be off by 0.15 degree even
			# on a second try on the same position.
			# we use prevalue the same as value in this case
			self._setStagePosition(prevalue,alpha_precision=0.3)
			time.sleep(0.2)
			self._setStagePosition(prevalue,alpha_precision=0.2)
			time.sleep(0.2)
		if abs(relax) > 1e-9 and prevalue2:
			self._setStagePosition(prevalue2)
			time.sleep(0.2)
		return self._setStagePosition(value)

	def normalizeLens(self, lens='all'):
		pass

	def getScreenCurrent(self):
		return self.screen_current
	
	def _scaleLensRawToCurrent(self,lens,d):
		'''
		decimal value scale to current with known range in hexdec.
		'''
		m = self.lens_hex_range[lens]
		return d*(m[1] - m[0])/int('3FFC00',16) + m[0]

	def _scaleLensCurrentToRaw(self, lens, current):
		'''
		current scale to digital decimal value with known range in hexdec.
		'''
		m = self.lens_hex_range[lens]
		precision = (m[1]-m[0]) / int('3FFC00',16)
		if current - m[0] < precision:
			d = 0
		else:
			d = min(int(round((current - m[0])/precision)),int('3FFC00',16))
		return d

	def _scaleCoilRawToVector(self, coil, xydict):
		xy = {}
		axes = xydict.keys()
		for k in axes:
			v = xydict[k]
			m = self._getCoilScale(coil,k)
			xy[k] = (v*(float(m[1] - m[0]))/int('3FFC00',16) + m[0])
		return xy

	def _getCoilScale(self, coil, axis):
		if coil in ('PA',):
			# deflectors in projection system is projection submode and mag dependent
			mag = self.getMagnification()
			coil_scale_name = 'coil_%s_%d_scale' % (coil.lower(), mag)
			subset = self.getProjectionSubModeName().lower()
			try:
				m = self.getHitachiConfig('optics',coil_scale_name)[subset][axis]
			except (KeyError,TypeError):
				coil_scale_name = 'coil_%s_scale' % (coil.lower(),)
				try:
					m = self.getHitachiConfig('optics',coil_scale_name)[subset][axis]
					ref_mag = self.getHitachiConfig('optics','ref_magnification')[subset]
					m = (m[0]*float(ref_mag)/mag,m[1]*float(ref_mag)/mag)
				except TypeError:
					raise ValueError('No calibration for %s in %s' % (coil, subset))
		elif coil.lower() in ('isf','os','is','ia'):
			# Objective and Intermediate, mostly the same but did find exceptions.
			mag = self.getMagnification()
			coil_scale_name = 'coil_%s_%d_scale' % (coil.lower(), mag)
			subset = self.getProjectionSubModeName().lower()
			try:
				m = self.getHitachiConfig('optics',coil_scale_name)[subset][axis]
			except (KeyError,TypeError):
				# non-mag specific
				coil_scale_name = 'coil_%s_scale' % (coil.lower(),)
				try:
					m = self.getHitachiConfig('optics',coil_scale_name)[subset][axis]
				except TypeError:
					raise ValueError('No calibration for %s in %s' % (coil, subset))
		else:
			# Illumination, certainly not mag specific
			coil_scale_name = 'coil_%s_scale' % (coil.lower())
			subset = self.getProbeMode()
			m = self.getHitachiConfig('optics',coil_scale_name)[subset][axis]
		return m

	def _scaleCoilVectorToRaw(self, coil, xydict):
		axes = xydict.keys()
		d_xy = {}
		for k in axes:
			v = xydict[k]
			m = self._getCoilScale(coil,k)
			precision = float(m[1]-m[0]) / int('3FFC00',16)
			if v - m[0] < precision:
				d = 0
			else:
				d = min(int(round((v - m[0])/precision)),int('3FFC00',16))
			d_xy[k]= d
		return d_xy

	def getLensCurrent(self, lens):
		'''
		Return current in Amp
		'''
		d_current = self.getLensCurrentRaw(lens)
		current = self._scaleLensRawToCurrent(lens,d_current)
		return current

	def getLensCurrentRaw(self, lens):
		'''
		Return lens value in raw decimal clicks
		'''
		hexdec = self.h.runGetCommand('Lens', lens,['hexdec',])
		return int(hexdec, 16)

	def setLensCurrent(self, lens, value):
		'''
		Set current in Amp
		'''
		d = self._scaleLensCurrentToRaw(lens, value)
		self.setLensCurrentRaw(lens, d)

	def setLensCurrentRaw(self, lens, d):
		'''
		Set lens value in raw decimal clicks
		'''
		hexdec = hex(d)
		self.h.runSetCommand('Lens', lens, ['FF',hexdec,], ['str','hexdec',], [6,])

	def getCoilVector(self, coil):
		'''
		Return coil xy vector dict in physical unit.
		'''
		d_xy = self.getCoilVectorRaw(coil)
		xydict = self._scaleCoilRawToVector(coil,d_xy)
		return xydict

	def getCoilVectorRaw(self, coil):
		'''
		Return coil xy vector dict in raw decimal clicks.
		'''
		hexdec_x, hexdec_y = self.h.runGetCommand('Coil', coil,['hexdec','hexdec'])
		d_xy = {'x':int(hexdec_x,16),'y':int(hexdec_y,16)}
		return d_xy

	def setProjectionCoilVector(self, coil, valuedict):
		'''
		Set coil x,y vector in physical unit.
		'''
		d_xy = self._scaleProjectionCoilVectorToRaw(coil,valuedict)
		self.setCoilVectorRaw(coil, d_xy)

	def setCoilVector(self, coil, valuedict):
		'''
		Set coil x,y vector in physical unit.
		'''
		d_xy = self._scaleCoilVectorToRaw(coil,valuedict)
		self.setCoilVectorRaw(coil, d_xy)

	def setCoilVectorRaw(self, coil, d_xy):
		'''
		Set coil x,y vector in raw decimal clicks.
		'''
		hexdec_x, hexdec_y = hex(d_xy['x']), hex(d_xy['y'])
		self.h.runSetCommand('Coil', coil, ['FF',hexdec_x,hexdec_y,], ['str','hexdec','hexdec',], [6,6])
		time.sleep(self.coil_pause)

	def getIntensity(self):
		'''
		Return as lens current
		'''
		return self.getLensCurrent('C2')
	
	def setIntensity(self, value):
		self.setLensCurrent('C2', value)

	def getStigmator(self):
		value = {}
		for key in self.stig_coil_map.keys():
			coil = self.stig_coil_map[key]
			value[key] = self.getCoilVector(coil)
		return value
		
	def setStigmator(self, value):
		new_values = self.getStigmator()
		for stig in value.keys():
			coil = self.stig_coil_map[stig]
			v = value[stig]
			# must set both axes
			for key in v.keys():
				new_values[stig][key]=v[key]
			self.setCoilVector(coil, new_values[stig])

	def getSpotSize(self):
		mode_d, submode_d = self._getColumnModes()
		obsv_probe, spot = self._getObsvProbeSpotFromColumnMode(mode_d)
	
		return spot
	
	def setSpotSize(self, value):
		'''
		Set spot size by index above the base of the observation probe.
		This is done after probe/mag are set.
		'''
		old_spot = self.getSpotSize()
		if value == old_spot:
			return
		mode_d, submode_d = self._getColumnModes()
		obsv_probe, spot = self._getObsvProbeSpotFromColumnMode(mode_d)
		obsv_probe_index = self.obsv_probe_modes.index(obsv_probe)
		spot_index = value - 1
		base = self.obsv_probe_mode_index_range[obsv_probe][0]
		new_mode_d = base+spot_index
		if new_mode_d >= self.obsv_probe_mode_index_range[obsv_probe][1]:
			raise ValueError('spot size assignment out of range for %s %s' %(obsv_probe, value))
		new_mode_h = hex(new_mode_d)
		hex_length = 2 #mode code length
		submode_h = hex(submode_d)
		self.h.runSetHexdecAndWait('Column','Mode',[new_mode_h, submode_h],['hexdec','hexdec'],hex_lengths=[hex_length,])

	def getBeamTilt(self):
		coil = 'BT'
		return self.getCoilVector(coil) # radians
	
	def setBeamTilt(self, value):
		new_value = self.getBeamTilt()
		coil = 'BT'
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)
	
	def getBeamShift(self):
		coil = 'BH'
		return self.getCoilVector(coil) # meters

	def setBeamShift(self, value):
		new_value = self.getBeamShift()
		coil = 'BH'
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)

	def getDiffractionShiftCoil(self):
		# Use PA or IA
		submode_name = self.getProjectionSubModeName()
		if 'low' in submode_name.lower():
			return None
		else:
			return 'IA'

	def getDiffractionShift(self):
		coil = self.getDiffractionShiftCoil()
		if coil:
			return self.getCoilVector(coil) # meters
		return {'x':0,'y':0}

	def setDiffractionShift(self, value):
		coil = self.getDiffractionShiftCoil()
		if not coil:
			# do nothing if coil is unknown
			return
		new_value = self.getDiffractionShift()
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)

	def getImageShiftCoil(self):
		if True:
			# Use PA or IA
			submode_name = self.getProjectionSubModeName()
			if 'low' not in submode_name.lower():
				if 'hr' in submode_name.lower():
					# Use ISF larger range in um at high mags 
					return 'ISF'
				# Use PA. better for low mag.
				return 'PA'
			else:
				return 'IA'
		else:
			# limit range
			return 'ISF'

	def getImageShift(self):
		coil = self.getImageShiftCoil()
		value = self.getCoilVector(coil)
		print 'get image shift %s=' % coil, value
		return value
	
	def setImageShift(self, value):
		coil = self.getImageShiftCoil()
		#if False:
		fine_value = self.getCoilVector(coil)
		# the following makes sure all keys have value
		for key in value.keys(): 
				fine_value[key]=value[key] 
		self.setCoilVector(coil, fine_value)
		print 'set image shift %s=' % coil, fine_value
		time.sleep(2)

	def getRawImageShift(self):
		# TODO: Is this different from ImageShift ?
		coil = self.getImageShiftCoil()
		return self.getCoilVector(coil)

	def setRawImageShift(self, value):
		# TODO: Is this different from ImageShift ?
		new_value = self.getRawImageShift()
		coil = self.getImageShiftCoil()
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)

	def makeDefocusLensName(self,submode):
		if submode.lower() != 'lowmag':
			lens='obj'
		else:
			lens='i1'
		lens_scale_name = 'lens_%s_current_defocus_scale' % (lens,)
		return lens_scale_name

	def getDefocus(self):
		focus = self.getFocus()
		mag = self.getMagnification()
		probe = self.getProbeMode()
		submode = self.getProjectionSubModeFromProbeMode(probe)
		defocus_current = focus - self.zero_defocus_current[submode][mag]
		lens_scale_name = self.makeDefocusLensName(submode)
		m = self.getHitachiConfig('optics',lens_scale_name)[submode.lower()]
		if not m :
			raise RuntimeError('%s%%%s not set in hht.cfg' % (lens_scale_name.upper(), submode.upper()))
		defocus = defocus_current * m
		return defocus

	def setDefocus(self, value):
		mag = self.getMagnification()
		probe = self.getProbeMode()
		submode = self.getProjectionSubModeFromProbeMode(probe)
		lens_scale_name = self.makeDefocusLensName(submode)
		m = self.getHitachiConfig('optics',lens_scale_name)[submode.lower()]
		if not m :
			raise RuntimeError('%s%%%s not set in hht.cfg' % (lens_scale_name.upper(), submode.upper()))
		lens_current_value = value / m
		focus = lens_current_value + self.zero_defocus_current[submode][mag]
		self.setFocus(focus)
		return 

	def resetDefocus(self):
		focus = self.getFocus()
		mag = self.getMagnification()
		probe = self.getProbeMode()
		submode = self.getProjectionSubModeFromProbeMode(probe)
		focus_diff = focus - self.zero_defocus_current[submode][mag]
		# Only reset within its own probe mode
		for mag in self.submode_mags[submode]:
			self.zero_defocus_current[submode][mag] += focus_diff
		ref_mag = self.getHitachiConfig('optics','ref_magnification')[submode.lower()]
		self.saveEucentricFocusAtReference(submode, self.zero_defocus_current[submode][ref_mag])

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
		old_mag = self.getMagnification()
		# This is run after probe mode is set in leginon/instrument.py so it should be in range.
		probe = self.getProbeMode()
		# Submode after projection mode change might not match probe
		old_submode = self._getProjectionSubMode()
		submode = self.getProjectionSubModeFromProbeMode(probe)
		if old_mag == mag and old_submode == submode:
			return
		try:
			index = self.submode_mags[submode].index(mag)
			self._setProjectionSubMode(submode)
		except ValueError as e:
			raise ValueError('invalid magnification for %s: %s' % (submode,e))
		self._setMagnification(mag)
		return

	def getProjectionSubModeFromProbeMode(self, probe):
		raise NotImplemented

	def _setMagnification(self, value):
		self.h.runSetIntAndWait('Column','Magnification', [value,])

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.projection_submode_map = {}
		self.magnifications = []
		for k in self.projection_submode_ids:
			submode = self.projection_submodes[k]
			for mag in self.submode_mags[submode]:
				self.addProjectionSubModeMap(mag,submode,k) #mag, mode_name, mode_id
		self.setProjectionSubModeMags()
		# set magnifications now that self.projection_submode_map is set
		self.setMagnificationsFromProjectionSubModes()
		self.initDefocusZero()

	def setProjectionSubModeMap(self, mode_map):
		'''
		called by EM.py to set self.projetion_submode_map
		self.projection_submode_map {mag:(mode_name,mode_id)}
		and
		self.submode_mags {mode_id:[mags]}
		'''
		self.projection_submode_map = mode_map
		self.setProjectionSubModeMags()
		self.setMagnificationsFromProjectionSubModes()
		self.initDefocusZero()

	def setMagnificationsFromProjectionSubModes(self):
		'''
		Make a sorted magnifications list
		'''
		mode_map = self.getProjectionSubModeMap()
		mags = mode_map.keys()
		mags.sort()
		if self.magnifications and mags == self.magnifications:
			# do not duplicate if exists already
			return
		self.magnifications = mags

	def setProjectionSubModeMags(self):
		'''
		initialize a dictionary of submode_indices
		mapped to sorted magnification list. Right now hitachi list is
		hard-coded at initialization.  Since it is not clear how to step them through.
		'''
		# self.submode_mags key is mode_index, and item is sorted mag list
		pass

	def getProjectionSubModeIds(self):
		'''
		get ordered projection submode index. This is an internal assignment only for Hitachi module.
		'''
		return self.projection_submode_ids

	def initDefocusZero(self):
		if not self.magnifications:
			raise ValueError('Need Magnifications to correlate the table')
		ref_ufocus = {}
		submode_used = self.getProjectionSubModes()
		try:
			for submode in submode_used:
				ref_ufocus[submode] = self.getEucentricFocusAtReference(submode)
		except IOError:
			raise RuntimeError('Please run hht_defocus.py first to get initial values')
		for submode in submode_used:
			focus_offset_file = self.getHitachiConfig('defocus','focus_offset_path')[submode]
			if focus_offset_file and os.path.isfile(focus_offset_file):
				f = open(focus_offset_file,'r')
				lines = f.readlines()
				mags = self.submode_mags[submode]
				if len(mags) != len(lines):
					f.close()
					raise ValueError('Focus offset file and Magnifications are not of the same length')
				for l in lines:
					bits = l.split('\n')[0].split('\t')
					m = int(bits[0])
					foc = float(bits[1])
					for submode in submode_used:
						if m in self.submode_mags[submode]:
							if submode not in self.zero_defocus_current.keys():
								self.zero_defocus_current[submode] = {}
							self.zero_defocus_current[submode][m] = foc + ref_ufocus[submode]
			else:
				raise RuntimeError('Please run hht_defocus.py first to get initial values')

	def getEucentricFocusAtReference(self, submode):
		ufocus_path = self.getHitachiConfig('defocus','ref_ufocus_path')[submode.lower()]
		f = open(ufocus_path)
		lines = f.readlines()
		ufocus = float(lines[0].split('\n')[0])
		f.close()
		return ufocus

	def saveEucentricFocusAtReference(self, submode, value):
		ufocus_path = self.getHitachiConfig('defocus','ref_ufocus_path')[submode.lower()]
		f = open(ufocus_path,'w')
		f.write('%9.6f\n' % value)
		f.close()

	def getMagnifications(self):
		return list(self.magnifications)

	def getMagnificationsInProbeMode(self, probe):
		return self.probe_mags[probe]
			
	def setMagnifications(self, magnifications):
		self.magnifications = magnifications

	def getMagnificationsInitialized(self):
		if self.magnifications:
			return True
		else:
			return False

	def _getColumnModes(self):
		'''
		return current column decimal values for mode and submode.
		''' 
		mode_h, submode_h = self.h.runGetCommand('Column','Mode',['hexdec','hexdec'])
		mode_d = int(mode_h,16)
		submode_d = int(submode_h,16)
		return mode_d, submode_d

	def _mapSubModeIdFromModeId(self, mode_d):
		'''
		return Column mode decimal value from given column mode decimal value.
		'''
		obsv_probe, spot = self._getObsvProbeSpotFromColumnMode(mode_d)
		submode_name = self.getProjectionSubModeFromProbeMode(obsv_probe)
		return int(self.submodes[submode_name],16)

	def _mapModeIdFromSubModeId(self, submode_d):
		'''
		return Column submode decimal value to column mode decimal value at weakest spot size.
		'''
		for i,p in enumerate(self.mode_pairs):
			if submode in p[1]:
				probe_pattern, submode_name = self.probe_submode_match_map[i]
				break
		if not matched_submode:
			raise ValueError('unknown column submode id %d' % submode_d)
		matched_probe = None
		for probe in self.getProbeModes():
			if probe_pattern in probe:
				matched_probe = probe
		if not matched_probe:
			raiseValueError('Unknow mapping from submode_id %d' % submode_d)
		return self.probe_mode_index_range[matched_probe][0]

	def _setColumnMode(self, mode_d):
		mode_h = hex(mode_d)
		submode_h = hex(self._mapSubModeIdFromModeId(mode_d))
		hex_length = 2 #mode code length
		self.h.runSetHexdecAndWait('Column','Mode',[mode_h, submode_h],['hexdec','hexdec'],hex_lengths=[hex_length,])

	def _setColumnSubMode(self, submode_d):
		mode_h = hex(self._mapModeIdFromSubModeId(submode_d))
		submode_h = hex(submode_d)
		hex_length = 2 #mode code length
		self.h.runSetHexdecAndWait('Column','Mode',[mode_h, submode_h],['hexdec','hexdec'],hex_lengths=[hex_length,])

	def _mapObservationProbeToProbe(self, observation_name):
		'''
		ObservationProbe is the observation name of a specified Column ModeID.
		For example: observation_name= micro-hc1
		Probe is the illumination system the hht.cfg scale calibratioon is done with
		For example: probe = micro-hc
		For HT7800, micro-hc1, micro-hc2, micro-hc3 all have the same hht.cfg scale calibration.
		'''
		return re.split(r'\d+$', observation_name)[0]

	def _mapProbeToObservationProbe(self, probe):
		return self.probe_map[probe]

	def getProbeMode(self):
		'''
		Return micro-hc, micro-hr, low-mag, not the preset observation name.
		'''
		mode_d, submode_d = self._getColumnModes()
		observation_probe, spot = self._getObsvProbeSpotFromColumnMode(mode_d)
		probe = self._mapObservationProbeToProbe(observation_probe)
		return probe

	def _getObsvProbeSpotFromColumnMode(self, mode_d):
		for obsv_probe in self.obsv_probe_mode_index_range.keys():
			# find the first probe that passes
			mode_range = self.obsv_probe_mode_index_range[obsv_probe]
			if mode_d >= mode_range[0] and mode_d < mode_range[1]:
				spot = mode_d - mode_range[0] + 1
				return obsv_probe, spot
		raise ValueError('observation probe mode not registered')

	def setProbeMode(self, value):
		new_probe = str(value)
		try:
			new_probe_index = self.probe_modes.index(new_probe)
		except ValueError:
			raise ValueError('invalid probe mode')
		if new_probe not in self.getProbeModes():
			raise ValueError('not a probe mode set to be used')
		old_probe = self.getProbeMode()
		if old_probe == new_probe:
			# Nothing to do
			return
		# Need change
		# Set to the minimal index (weakest beam) per probe mode so that normalization is consistent.
		# spot assignment comes latter in instrument.py
		new_obsv_probe = self._mapProbeToObservationProbe(str(new_probe))
		new_obsv_probe_index_range = self.obsv_probe_mode_index_range[new_obsv_probe]
		new_mode_d = new_obsv_probe_index_range[0]
		print "use weakest spot size assignment as normalization for probe mode change"
		self._setColumnMode(new_mode_d)

	def getProbeModes(self):
		# This include only those mapped to observation probe mode that we want to allow access to.
		return list(self.probe_modes)

	def getProjectionSubModes(self):
			return self.projection_submodes.values()

	def getProjectionSubModeName(self):
		'''
		Overwrite tem.py getProjectionSubModeName.
		projection_submode_map does not work with hitachi scope since submode has different mag list.
		Some are overlapped.
		'''
		mode_d, submode_d = self._getColumnModes()
		for submode in self.submodes.keys():
			if submode_d == int(self.submodes[submode],16):
				return submode
		raise ValueError('current submode not registered')

	def _getProjectionSubMode(self):
		return self.getProjectionSubModeName()

	def setProjectionMode(self, value):
		# This is a fake value set.  It forces the projection mode defined by
		# the class.
		#print 'fake setting to projection mode %s' % (self.projection_mode,)
		pass

	def _setProjectionSubMode(self, submode_name):
		if self._getProjectionSubMode() == submode_name:
			return
		submode_h = self.submodes[submode_name]
		submode_d = int(submode_h,16)
		mode_h = hex(self._mapModeIdFromSubModeId(submode_d))
		hex_length = 2 #mode code length
		self.h.runSetHexdecAndWait('Column','Mode',[mode_h, submode_h],['hexdec','hexdec'],hex_lengths=[hex_length,])

	def getMainScreenPositions(self):
		return list(self.main_screen_positions)

	def getMainScreenPosition(self):
		return self.getMainScreenPositions()[self.h.runGetCommand('Screen','Position',['int',])]

	def setMainScreenPosition(self, value):
		positions = self.getMainScreenPositions()
		if value not in positions:
			raise ValueError('invalid main screen position')
		if self.getMainScreenPosition() == value:
			return
		opt_index = positions.index(value)
		self.h.runSetIntAndWait('Screen','Position', [opt_index,])
		if value == 'down':
			return
		#screen out returns much faster than gui indicates. Need sleep time
		delay = self.getHitachiConfig('tem option','main_screen_up_delay')
		if delay:
			delay_time = float(delay)
		else:
			# minimal 1 second
			delay_time = 1.0
		time.sleep(delay_time)

	def getFocus(self):
		return self.getLensCurrent('OBJ')

	def setFocus(self, value):
		self.setLensCurrent('OBJ', value)

	def getColumnPressure(self):
		return self.h.runGetCommand('EvacGauge','FRG',['float','float','float'])[0] #In unit of Pa

	def getBufferTankPressure(self):
		return self.h.runGetCommand('EvacGauge','PIG',['float','float','float'])[0] #In unit of Pa

	def runBufferCycle(self):
		raise AttributeError('no control of buffer pump on this instrument')

	def getTurboPump(self):
		return 'unknown'

	def setTurboPump(self, value):
		raise AttributeError('no control of buffer pump on this instrument')

	def setEmission(self, value):
		# just set it on or off.
		if value < self.getEmission():
			status = 0
		else:
			status = 1
		return self.h.runSetIntAndWait('Beam','Status',[status,])

	def getEmission(self):
		return self.h.runGetCommand('EmissionCurrent','Value',['float',]) #In unit of micro Amp

	def getBeamBlank(self):
		# not sure how to map this.  Consider off all the time.
		return 'off'
		
	def setBeamBlank(self, bb):
		return

	def hasAutoFiller(self):
		return False

	def exposeSpecimenNotCamera(self,seconds):
		raise RuntimError('No post specimen shutter')

	def hasGridLoader(self):
		# 3 speciment holder is not a grid loader but similar.
		return True

	def getGridLoaderNumberOfSlots(self):
		if not self.hasGridLoader():
			return 0
		return 3

	def getGridLoaderSlotState(self, number):
		if self._getLoadedSlotNumber() == number:
			state = 'loaded'
		elif self.loaded_slot_number is None and number == 1 and self.is_init is True:
			self.is_init = False
			state = 'empty'
		else:
			state = 'occupied'
		return state

	def _getLoadedSlotNumber(self):
		return int(self.h.runGetCommand('Stage','SpecimenNo'))

	def _loadCartridge(self, number):
		old_number = self._getLoadedSlotNumber()
		if old_number == number:
			return
		# This set does not have received message as normal.
		self.h.runSetIntAndWait('Stage','SpecimenNo',[number,])
		self.loaded_slot_number = number
		# The stage is still moving within the target number when it is returned from wait.
		# it will return to {'x':0,'y':0}
		while 1:
			p = self.getStagePosition()
			if abs(p['x']) < 1e-6 and abs(p['y']) < 1e-6:
				break

	def _unloadCartridge(self):
		# multi-specimen holder does not have unload
		return

	def getGridLoaderInventory(self):
		return self.getAllGridSlotStates()

	def getApertureMechanisms(self):
		'''
		Names of the available aperture mechanism
		'''
		mechanisms = self.getHitachiConfig('aperture').keys()
		mechanisms.sort()
		return mechanisms

	def getApertureSelections(self, aperture_mechanism):
		selections = self.getHitachiConfig('aperture', aperture_mechanism)
		if not selections:
			return ['unknown',]
		return selections

	def getApertureSelection(self, aperture_mechanism):
		if aperture_mechanism not in self.getApertureMechanisms():
			return 'unknown'
		apt_api_name = self.aperture_mechanism_map[aperture_mechanism]
		sel_names = self.getApertureSelections(aperture_mechanism)
		sel_index = self.h.runGetCommand(apt_api_name,'Position',['int',])
		return sel_names[sel_index]

	def setApertureSelection(self, aperture_mechanism, name):
		if aperture_mechanism not in self.getApertureMechanisms():
			# failed
			return False
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

class HT7800(Hitachi):
	name = 'HT7800'
	projection_mode = 'imaging'
	projection_submodes = {1:'lowmag',2:'zoom1-hc',3:'zoom1-hr'}  # There is no id in hitachi SDK. The keys here are for ordering.
	projection_submode_ids = [1,2,3]  # Give it a fixed order
	# imaging system
	submodes = {
			'zoom1-hc': hex(int('00',16)),
			'zoom1-hr': hex(int('02',16)),
			'diff1-hc': hex(int('0a',16)),
			'diff1-hr': hex(int('0c',16)),
			'lowmag': hex(int('0e',16)),
		}
	# illumination system
	obsv_probe_modes = [
			'micro-hc1',
			'micro-hc2',
			'micro-hc3',
			'micro-hr1',
			'micro-hr2',
			'micro-hr3',
			'fine-hc',
			'fine-hr',
			'low-mag',
			] # in order of index range
	# index_range, base 0, not including the last index
	obsv_probe_mode_index_range = {
			'micro-hc1': (0,5),
			'micro-hc2': (5,10),
			'micro-hc3': (10,15),
			'micro-hr1': (15,20),
			'micro-hr2': (20,25),
			'micro-hr3': (25,30),
			'fine-hc': (30,35),
			'fine-hr': (35,40),
			'low-mag':(40,50),
		}

	# pair combined probe_mode_index_range with column submode index
	# The list is ordered the same as probe_submode_match_map
	mode_id_map = [((0,14),(0,10)),((15,29),(2,12)),((40,49),(14,))]
	# lens current range at HT 100 kV span 000000 - 3FFC00 
	lens_hex_range = {
		'OBJ':(0,1.94007),
		'C2':(0,1.70002),
	}
	probe_submode_match_map = [('hc','zoom1-hc'),('hr','zoom1-hr'),('low','lowmag')]

	def setColumnValvePosition(self, state):
		# Do not allow user control of gun valve on HT7800
		pass

	def getProjectionSubModeFromProbeMode(self, probe):
		# match pattern in the probe name to find the submode
		for m in self.probe_submode_match_map:
			if m[0] in probe:
				# probe name that has the pattern
				return m[1]
		raise ValueError('Do not know how to guess projection submode from %s' % probe)

	def getProbeModeFromProjectionSubMode(self, submode):
		for probe in self.getProbeModes():
			for m in self.probe_submode_match_map:
				if submode == m[1] and m[0] in probe:
					return probe
		raise ValueError('Do not know how to guess probe mode from %s' % submode)
