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
	projection_submodes = {1:'LowMag',2:'Zoom1'}  # Do this in order.  There is no mode_id in hitachi script. The keys here are for ordering.
	projection_submode_ids = [1,2]  # Give it a fixed order
	submode_mags = {} # mag list by projection_submode id
	submode_mags[1] = [50,100,200,300,400]# ignore 500 and above so that separation is easier.
	submode_mags[2] = [
			500,700,1000,1200,1500,2000,2500,3000,4000,
			5000,6000,7000,8000,10000,12000,15000,20000,25000,30000,
			40000,50000,60000,70000,80000,100000,120000,150000,200000
			]
	# lens current range at HT 100 kV span 000000 - 3FFC00 
	lens_hex_range = {
		'OBJ':(0,1.94007),
		'C2':(0,1.70002),
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

		self.probe_modes = [
			'micro-hc',
			'micro-hr',
			'fine-hc',
			'fine-hr',
			'low mag',
		]
		self.probe_mode_index_cap = {
			'micro-hc': 15,
			'micro-hr': 30,
			'fine-hc': 35,
			'fine-hr': 40,
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

		self.loaded_slot_number = None
		self.is_init = True

		self.aperture_mechanism_map = {'condenser2':'COND_APT','objective':'OBJ_APT','selected area':'SA_APT'}
		self.aperture_selection = {'objective':'100','condenser_2':'unknown','selected_area':'open'}
		self.beamstop_positions = ['out','in'] # index of this list is API value to set
		self.coil_map = [('BT','beam_tilt'),('BH','beam_shift'),('ISF','image_shift'),('CS','condenser_stig'),('OS','objective_stig'),('IS','diffraction_stig')]
		self.stig_coil_map = {'condenser':'CS','objective':'OS','diffraction':'IS'}

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

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def setIntensityZoom(self, value):
		if self.getProbeMode() == 'low mag':
			raise ('Can not set IntensityZoom in low mag mode')
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
	
	def _scaleLensHexdecToCurrent(self,lens,hexdec):
		m = self.lens_hex_range[lens]
		d = int(hexdec,16)
		return d*(m[1] - m[0])/int('3FFC00',16) + m[0]

	def _scaleLensCurrentToHexdec(self, lens, current):
		m = self.lens_hex_range[lens]
		precision = (m[1]-m[0]) / int('3FFC00',16)
		if current - m[0] < precision:
			d = 0
		else:
			d = min(int(round((current - m[0])/precision)),int('3FFC00',16))
		return hex(d)

	def _scaleCoilHexdecToVector(self, coil, submode_name, hex_x, hex_y):
		xy = []
		axes = ('x','y')
		for i,v in enumerate((hex_x,hex_y)):
			coil_scale_name = 'coil_%s_scale' % (coil.lower(),)
			if coil.lower() != 'bt':
				m = self.getHitachiConfig('optics',coil_scale_name)[submode_name.lower()][axes[i]]
			else:
				m = self.getHitachiConfig('optics',coil_scale_name)[axes[i]]
			d = int(v,16)
			print i, d
			xy.append(d*(float(m[1] - m[0]))/int('3FFC00',16) + m[0])
		return xy

	def _scaleCoilVectorToHexdec(self, coil, submode_name, x, y):
		axes = ('x','y')
		hex_xy = []
		for i,v in enumerate((x,y)):
			coil_scale_name = 'coil_%s_scale' % (coil.lower(),)
			if coil.lower() != 'bt':
				m = self.getHitachiConfig('optics',coil_scale_name)[submode_name.lower()][axes[i]]
			else:
				m = self.getHitachiConfig('optics',coil_scale_name)[axes[i]]
			precision = float(m[1]-m[0]) / int('3FFC00',16)
			if v - m[0] < precision:
				d = 0
			else:
				d = min(int(round((v - m[0])/precision)),int('3FFC00',16))
			hex_xy.append(hex(d))
		print hex_xy
		return hex_xy

	def getLensCurrent(self, lens):
		hexdec = self.h.runGetCommand('Lens', lens,['hexdec',])
		current = self._scaleLensHexdecToCurrent(lens,hexdec)
		return current

	def setLensCurrent(self, lens, value):
		'''
		Current in Amp
		'''
		hexdec = self._scaleLensCurrentToHexdec(lens, value)
		self.h.runSetCommand('Lens', lens, ['FF',hexdec,], ['str','hexdec',], [6,])

	def getCoilVector(self, coil):
		hexdec_x, hexdec_y = self.h.runGetCommand('Coil', coil,['hexdec','hexdec'])
		submode_name = self.getProjectionSubModeName()
		x,y = self._scaleCoilHexdecToVector(coil,submode_name,hexdec_x,hexdec_y)
		return {'x':x, 'y':y}

	def setCoilVector(self, coil, valuedict):
		'''
		x,y vector in meters
		'''
		x = valuedict['x']
		y = valuedict['y']
		submode_name = self.getProjectionSubModeName()
		hexdec_x, hexdec_y = self._scaleCoilVectorToHexdec(coil,submode_name,x,y)
		self.h.runSetCommand('Coil', coil, ['FF',hexdec_x,hexdec_y,], ['str','hexdec','hexdec',], [6,6])

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
			for key in v.keys():
				new_values[stig][key]=v[key]
			self.setCoilVector(coil, new_values[stig])

	def getSpotSize(self):
		mode_d, submode_d = self._getColumnModes()
		probe, spot = self._getProbeSpotFromColumnMode(mode_d)
	
		return spot
	
	def setSpotSize(self, value):
		prev_spot = self.getSpotSize()
		if value == prev_spot:
			return
		probe = self.getProbeMode()
		mode_d, submode_d = self._getColumnModes()
		probe_index = self.probe_modes.index(probe)
		spot_index = value - 1
		base = 0
		if probe_index > 0:
			prev_probe = self.probe_modes[probe_index-1]
			base = self.probe_mode_index_cap[prev_probe]
		new_mode_d = base+spot_index
		if new_mode_d >= self.probe_mode_index_cap[probe]:
			raise ValueError('spot size assignment out of range for %s %s' %(probe, value))
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

	def getDiffractionShift(self):
		# place holder. Not implemented
		return {'x':0.0,'y':0.0}

	def setDiffractionShift(self, value):
		# place holder. Not implemented
		pass

	def getImageShiftCoil(self):
		if self.getHitachiConfig('tem_option','use_pa_imageshift'):
			return 'PA'
		else:
			return 'ISF'

	def getImageShift(self):
		coil = self.getImageShiftCoil()
		return self.getCoilVector(coil)
	
	def setImageShift(self, value):
		new_value = self.getImageShift()
		coil = self.getImageShiftCoil()
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)

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

	def getProjectorAlignShift(self):
		coil = 'PA'
		return self.getCoilVector(coil)

	def setProjectorAlignShift(self, value):
		new_value = self.getProjectorAlignShift()
		coil = 'PA'
		for key in value.keys():
			new_value[key]=value[key]
		self.setCoilVector(coil, new_value)

	def getDefocus(self):
		focus = self.getFocus()
		mag = self.getMagnification()
		defocus_current = focus - self.zero_defocus_current[mag]
		submode_name = self.getProjectionSubModeName()
		lens_scale_name = 'lens_obj_current_defocus_scale'
		m = self.getHitachiConfig('optics',lens_scale_name)[submode_name.lower()]
		if not m :
			raise RuntimeError('%s%%%s not set in hht.cfg' % (lens_scale_name.upper(), submode_name.upper()))
		defocus = defocus_current * m
		return defocus

	def setDefocus(self, value):
		submode_name = self.getProjectionSubModeName()
		lens_scale_name = 'lens_obj_current_defocus_scale'
		m = self.getHitachiConfig('optics',lens_scale_name)[submode_name.lower()]
		if not m :
			raise RuntimeError('%s%%%s not set in hht.cfg' % (lens_scale_name.upper(), submode_name.upper()))
		mag = self.getMagnification()
		lens_current_value = value / m
		focus = lens_current_value + self.zero_defocus_current[mag]
		self.setFocus(focus)
		return 

	def resetDefocus(self):
		focus = self.getFocus()
		mag = self.getMagnification()
		submode_id = self.getProjectionSubModeId()
		submode_name = self.projection_submodes[submode_id]
		focus_diff = focus - self.zero_defocus_current[mag]
		# Only reset within its own projection submode
		for mag in self.submode_mags[submode_id]:
			self.zero_defocus_current[mag] += focus_diff
		ref_mag = self.getHitachiConfig('defocus','ref_magnification')[submode_name.lower()]
		self.saveEucentricFocusAtReference(submode_name, self.zero_defocus_current[ref_mag])

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
		new_submode_name, new_submode_id = self.getProjectionSubModeMap()[mag]
		try:
			prev_mag = self.getMagnification()
			prev_submode_name, prev_submode_id = self.getProjectionSubModeMap()[prev_mag]
		except ValueError:
			raise
		need_proj_norm = False
		if prev_mag != mag:
			if prev_submode_id != new_submode_id:
				if new_submode_id == 1: #Low-Mag
					self.setProbeMode('low mag')
				if new_submode_id == 2: #Zoom1
					self.setProbeMode('micro-hc') # TODO: Will this work ? We don't have spot size info. setProbeMode will consistently cap the spot size.
			self._setMagnification(mag)
		return

	def _setMagnification(self, value):
		self.h.runSetIntAndWait('Column','Magnification', [value,])

	def findMagnifications(self):
		# fake finding magnifications and set projection submod mappings
		self.projection_submode_map = {}
		submode_ids = self.projection_submodes.keys()
		submode_ids.sort()
		self.magnifications = []
		for k in submode_ids:
			for mag in self.submode_mags[k]:
				self.addProjectionSubModeMap(mag,self.projection_submodes[k],k) #mag, mode_name, mode_id
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

	def getOrderedProjectionSubModeNames(self):
		'''
		get projection submode names ordered by mode ids.
		'''
		names = []
		for d in self.projection_submode_ids:
			names.append(self.projection_submodes[d])
		return names

	def initDefocusZero(self):
		if not self.magnifications:
			raise ValueError('Need Magnifications to correlate the table')
		ref_ufocus = {}
		try:
			for submode_id in self.projection_submode_ids:
				submode_name = self.projection_submodes[submode_id]
				ref_ufocus[submode_id] = self.getEucentricFocusAtReference(submode_name)
		except IOError:
			raise RuntimeError('Please run hht_defocus.py first to get initial values')
		focus_offset_file = self.getHitachiConfig('defocus','focus_offset_path')
		if focus_offset_file and os.path.isfile(focus_offset_file):
			f = open(focus_offset_file,'r')
			lines = f.readlines()
			mags = self.getMagnifications()
			if len(mags) != len(lines):
				f.close()
				raise ValueError('Focus offset file and Magnifications are not of the same length')
			for l in lines:
				bits = l.split('\n')[0].split('\t')
				m = int(bits[0])
				foc = float(bits[1])
				for submode_id in self.projection_submode_ids:
					if m in self.submode_mags[submode_id]:
						self.zero_defocus_current[m] = foc + ref_ufocus[submode_id]
		else:
			raise RuntimeError('Please run hht_defocus.py first to get initial values')

	def getEucentricFocusAtReference(self, p_submode_name):
		ufocus_path = self.getHitachiConfig('defocus','ref_ufocus_path')[p_submode_name.lower()]
		f = open(ufocus_path)
		lines = f.readlines()
		ufocus = float(lines[0].split('\n')[0])
		f.close()
		return ufocus

	def saveEucentricFocusAtReference(self, p_submode_name, value):
		ufocus_path = self.getHitachiConfig('defocus','ref_ufocus_path')[p_submode_name.lower()]
		f = open(ufocus_path,'w')
		f.write('%9.6f\n' % value)
		f.close()

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

	def _setColumnMode(self, mode_d):
		mode_h = hex(mode_d)
		hex_length = 2 #mode code length
		# imaging system
		# match zoom-1 values here, but don't know how it should be.
		submodes = {
			'micro-hc': hex(int('00',16)),
			'micro-hr': hex(int('02',16)),
			'fine-hc': hex(int('00',16)), # not sure how this maps, assume zoom-1 for now
			'fine-hr': hex(int('02',16)),
			'low mag': hex(int('0e',16)),
		}
		probe, spot = self._getProbeSpotFromColumnMode(mode_d)
		submode_h = submodes[probe]
		print mode_h, submode_h
		self.h.runSetHexdecAndWait('Column','Mode',[mode_h, submode_h],['hexdec','hexdec'],hex_lengths=[hex_length,])

	def getProbeMode(self):
		mode_d, submode_d = self._getColumnModes()
		probe, spot = self._getProbeSpotFromColumnMode(mode_d)
		return probe

	def _getProbeSpotFromColumnMode(self, mode_d):
		prev_probe_index_cap = 0
		for probe in self.probe_modes:
			# find the first probe that passes
			if mode_d < self.probe_mode_index_cap[probe]:
				print mode_d, prev_probe_index_cap, probe, self.probe_mode_index_cap[probe]
				spot = mode_d - prev_probe_index_cap + 1
				return probe, spot
			prev_probe_index_cap = self.probe_mode_index_cap[probe]
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
		# set spot size to be the same as previous.
		# Set to the capped index per probe mode so that normalization is consistent.
		spot_index= prev_mode_d - base
		new_base = 0
		if new_probe_index > 0:
			new_base = self.probe_mode_index_cap[self.probe_modes[new_probe_index-1]]
		new_probe_index_cap = self.probe_mode_index_cap[new_probe]
		new_mode_d = new_probe_index_cap - 1
		print "spot size assignment capped"
		self._setColumnMode(new_mode_d)

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
		return self.getLensCurrent('OBJ')

	def setFocus(self, value):
		self.setLensCurrent('OBJ', value)

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
		sel_index = self.h.runGetCommand(apt_api_name,'Position',['int',])[0]
		print sel_index
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

class HT7800(Hitachi):
	name = 'HT7800'
	projection_mode = 'imaging'
	projection_submodes = {1:'LowMag',2:'Zoom1'}  # Do this in order.  There is no mode_id in hitachi script. The keys here are for ordering.
	projection_submode_ids = [1,2]  # Give it a fixed order
	submode_mags = {} # mag list by projection_submode id
	submode_mags[1] = [50,100,200,300,400]# ignore 500 and above so that separation is easier.
	submode_mags[2] = [
			500,700,1000,1200,1500,2000,2500,3000,4000,
			5000,6000,7000,8000,10000,12000,15000,20000,25000,30000,
			40000,50000,60000,70000,80000,100000,120000,150000,200000
			]
	# lens current range at HT 100 kV span 000000 - 3FFC00 
	lens_hex_range = {
		'OBJ':(0,1.94007),
		'C2':(0,1.70002),
	}

