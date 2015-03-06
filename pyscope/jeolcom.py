import time
import math
import sys
import comtypes.client
from pyscope import tem
from pyscope import jeolconfig

# function modes
FUNCTION_MODES = {'mag1':0,'mag2':1,'lowmag':2,'diff':3}
FUNCTION_MODE_ORDERED_NAMES = ['mag1','mag2','lowmag','diff']

# identifier for dector
MAIN_SCREEN = 13

# MDS modes
MDS_OFF = 0
MDS_SEARCH = 1
MDS_FOCUS = 2
MDS_PHOTO = 3

# aperture ids
CLA = 1
OLA = 2
HCA = 3
SAA = 4

# constants for Jeol Hex value
ZERO = 32768
MAX = 65535
MIN = 0
SCALE_FACTOR = 32767

# coarse-fine ratio for OL
COARSE_SCALE = 32


def toJeol(val):
	return ZERO + int(round(SCALE_FACTOR * val))

def toLeginon(val):
	return float(val - ZERO)/SCALE_FACTOR

class Jeol(tem.TEM):
	name = 'Jeol'
	def __init__(self):
		tem.TEM.__init__(self)

		# initial COM in multithread mode if not initialized otherwise
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except WindowsError:
			comtypes.CoInitialize()

		# get the JEOL COM library and create the TEM3 object
		temext = comtypes.client.GetModule(('{CE70FCE4-26D9-4BAB-9626-EC88DB7F6A0A}', 3, 0))
		self.tem3 = comtypes.client.CreateObject(temext.TEM3, comtypes.CLSCTX_ALL)

		# initialize each interface from the TEM3 object
		self.ht3 = self.tem3.CreateHT3()
		self.eos3 = self.tem3.CreateEOS3()
		self.lens3 = self.tem3.CreateLens3()
		self.def3 = self.tem3.CreateDef3()
		self.detector3 = self.tem3.CreateDetector3()
		self.camera3 = self.tem3.CreateCamera3()
		self.mds3 = self.tem3.CreateMDS3()
		self.stage3 = self.tem3.CreateStage3()
		self.feg3 = self.tem3.CreateFEG3()
		self.filter3 = self.tem3.CreateFilter3()
		self.apt3 = self.tem3.CreateApt3()

		# wait for interface to activate
		result = None
		timeout = False
		t0 = time.time()
		while result != 0 and not timeout:
			ht, result = self.ht3.GetHTValue()
			time.sleep(1)
			t1 = time.time()
			if t1-t0 > 60:
				timout = True
				sys.exit(1)

		self.setJeolConfigs()

		self.magnifications = []
		# submode_mags keys are submode_indices and values are magnification list in the submode
		self.submode_mags = {}
		# initialize zero defocus values from jeol.cfg
		self.zero_defocus_om = self.getJeolConfig('om standard focus')
		self.zero_defocus_ol = self.getJeolConfig('ol standard focus')

	def __del__(self):
		comtypes.CoUninitialize()

	def setJeolConfigs(self):
		self.jeolconfigs = jeolconfig.getConfigured()

	def getJeolConfig(self,optionname,itemname=None):
		if itemname is None:
			return self.jeolconfigs[optionname]
		else:
			return self.jeolconfigs[optionname][itemname]

	def setProjectionSubModes(self):
		mode_names = self.getJeolConfig('eos','use_modes')
		for name in mode_names:
			mode_index = FUNCTION_MODES[name]
			self.projection_submodes[mode_index] = name

	def setProjectionSubModeMap(self, mode_map):
		'''
		called by EM.py to set self.projetion_submode_map
		self.projection_submode_map {mag:(mode_name,mode_id)}
		and
		self.submode_mags {mode_id:[mags]}
		'''
		self.projection_submode_map = mode_map
		self.setProjectionSubModeMags()

	def setProjectionSubModeMags(self):
		'''
		initialize a dictionary of submode_indices
		mapped to sorted magnification list
		'''
		if not self.submode_mags:
			for m in self.projection_submode_map:
				v = self.projection_submode_map[m]
				if v[1] not in self.submode_mags.keys():
					self.submode_mags[v[1]] = []
				self.submode_mags[v[1]].append(m)
			map((lambda x: self.submode_mags[x].sort()),self.submode_mags.keys())

	def normalizeLens(self, lens = "all"):
		pass

	def getGunTilt(self):
		tilt_x, tilt_y, result = self.def3.GetGunA1()
		return {'x' : toLeginon(tilt_x), 'y' : toLeginon(tilt_y)}
 
	def setGunTilt(self, vector, relative = "absolute"):
		current_tilt = self.getGunTilt()
		tilt_x = current_tilt['x']
		tilt_y = current_tilt['y']
		if relative == 'relative':
			if 'x' in vector:
				tilt_x += vector['x']
			if 'y' in vector:
				tilt_y += vector['y']
		elif relative == 'absolute':
			if 'x' in vector:
				tilt_x = vector['x']
			if 'y' in vector:
				tilt_y = vector['y']
		else:
			raise ValueError

		self.def3.SetGunA1(toJeol(tilt_x), toJeol(tilt_y))

	def getGunShift(self):
		shift_x, shift_y, result = self.def3.GetGunA2()
		return {'x' : toLeginon(shift_x), 'y' : toLeginon(shift_y)}

	def setGunShift(self, vector, relative = "absolute"):
		current_shift = self.getGunShift()
		shift_x = current_shift['x']
		shift_y = current_shift['y']
		if relative == 'relative':
			if 'x' in vector:
				shift_x += vector['x']
			if 'y' in vector:
				shift_y += vector['y']
		elif relative == 'absolute':
			if 'x' in vector:
				shift_x = vector['x']
			if 'y' in vector:
				shift_y = vector['y']
		else:
			raise ValueError

		self.def3.SetGunA2(toJeol(shift_x), toJeol(shift_y))
 
	def getHighTensionStates(self):
		return ['off', 'on', 'disabled']

	def getHighTension(self):
		ht, result = self.ht3.GetHTValue()
		return float(ht)

	def setHighTension(self, ht):
#		result = self.ht3.SetHTValue(float(ht))
		pass

	def getColumnValvePositions(self):
		return ['open', 'closed']

	def getColumnValvePosition(self):
		position, result = self.feg3.GetBeamValve()
		if position:
			return 'open'
		else:
			return 'closed'

	def setColumnValvePosition(self, position):
		if position == 'open':
			self.feg3.SetBeamValve(1)
		elif posision == 'closed':
			self.feg3.SetBeamValve(0)
		else:
			raise ValueError

	# intensity is controlled by condenser lens 3
	def getIntensity(self):
		intensity, result = self.lens3.GetCL3()
		return float(intensity)/MAX

	def setIntensity(self, intensity, relative = 'absolute'):
		if relative == 'relative':
			intensity += self.getIntensity()
		elif relative == 'absolute':
			pass
		else:
			raise ValueError

		result = self.lens3.SetCL3(int(round(intensity*MAX)))
		
	def getDarkFieldMode(self):
		pass

	def setDarkFieldMode(self, mode):
		pass

	def getBeamBlank(self):
		bb, result = self.def3.GetBeamBlank()
		if bb == 0:
			return 'off'
		elif bb == 1:
			return 'on'
		else:
			raise SystemError

	def setBeamBlank(self, bb):
		if bb == 'off':
			result = self.def3.SetBeamBlank(0)
		elif bb == 'on':
			result = self.def3.SetBeamBlank(1)
		else:
			raise ValueError

	# the DiffractionStigmator of tecnai is the IntermediateStigmator of Jeol
	def getStigmator(self):
		c_x, c_y, result = self.def3.GetCLs()
		o_x, o_y, result = self.def3.GetOLs()
		d_x, d_y, result = self.def3.GetILs()
		return {"condenser": {"x": toLeginon(c_x), "y": toLeginon(c_y)},
			"objective": {"x": toLeginon(o_x), "y": toLeginon(o_y)},
			"diffraction": {"x": toLeginon(d_x), "y": toLeginon(d_y)}} 
 
	def setStigmator(self, stigs, relative = "absolute"):
		for key in stigs.keys():
			stigmators = self.getStigmator()
			if key == "condenser":
				stigmator = stigmators["condenser"]
			elif key == "objective":
				stigmator = stigmators["objective"]
			elif key == "diffraction":
				stigmator = stigmators["diffraction"]
			else:
				raise ValueError
			
			if relative == "relative":
				try:
					stigs[key]["x"] += stigmator["x"]
					stigs[key]["y"] += stigmator["y"]
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError

			try:
				stigmator["x"] = stigs[key]["x"]
				stigmator["y"] = stigs[key]["y"]
			except KeyError:
				pass

			if key == "condenser":
				result = self.def3.SetCLs(toJeol(stigmator["x"]), toJeol(stigmator["y"]))
			elif key == "objective":
				result = self.def3.SetOLs(toJeol(stigmator["x"]), toJeol(stigmator["y"]))
			elif key == "diffraction":
				result = self.def3.SetILs(toJeol(stigmator["x"]), toJeol(stigmator["y"]))
			else:
				raise ValueError
 
	def getSpotSize(self):
		spot_size, result = self.eos3.GetSpotSize()
		return spot_size + 1

	def setSpotSize(self, ss, relative = "absolute"):
		if relative == "relative":
			ss += self.getSpotSize()
		elif relative == "absolute":
			pass
		else:
			raise ValueError
 
		result = self.eos3.SelectSpotSize(ss - 1)
	
	def getBeamTilt(self):
		tilt_x, tilt_y, result = self.def3.GetCLA2()
		return {"x": (tilt_x - ZERO)*self.getJeolConfig('def','beamtilt_factor_x'), "y": (tilt_y - ZERO)*self.getJeolConfig('def','beamtilt_factor_y')}

	def setBeamTilt(self, vector, relative = "absolute"):
		current_tilt = self.getBeamTilt()
		tilt_x = current_tilt['x']
		tilt_y = current_tilt['y']
		if relative == 'relative':
			if 'x' in vector:
				tilt_x += vector['x']
			if 'y' in vector:
				tilt_y += vector['y']
		elif relative == 'absolute':
			if 'x' in vector:
				tilt_x = vector['x']
			if 'y' in vector:
				tilt_y = vector['y']
		else:
			raise ValueError

		tilt_x = int(round(tilt_x/self.getJeolConfig('def','beamtilt_factor_x'))) + ZERO
		tilt_y = int(round(tilt_y/self.getJeolConfig('def','beamtilt_factor_y'))) + ZERO

		result = self.def3.SetCLA2(tilt_x, tilt_y)

	def getBeamShift(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			scale_x, scale_y = self.getJeolConfig('def','beamshift_factor_x_lowmag'), self.getJeolConfig('def','beamshift_factor_y_lowmag')
		elif mode == FUNCTION_MODES['mag1']:
			scale_x, scale_y = self.getJeolConfig('def','beamshift_factor_x_mag1'), self.getJeolConfig('def','beamshift_factor_y_mag1')
		else:
			raise RuntimeError('Beam shift functions not implemented in this mode (%d, "%s")' % (mode, name))
		shift_x, shift_y, result = self.def3.GetCLA1()

		x = (shift_x - ZERO)*scale_x
		y = (shift_y - ZERO)*scale_y

		return {"x": x, "y": y}

	def setBeamShift(self, vector, relative = "absolute"):

		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			scale_x, scale_y = self.getJeolConfig('def','beamshift_factor_x_lowmag'), self.getJeolConfig('def','beamshift_factor_y_lowmag')
		elif mode == FUNCTION_MODES['mag1']:
			scale_x, scale_y = self.getJeolConfig('def','beamshift_factor_x_mag1'), self.getJeolConfig('def','beamshift_factor_y_mag1')
		else:
			raise RuntimeError('Beam shift functions not implemented in this mode (%d, "%s")' % (mode, name))
		
		if relative == 'relative':
			current_shift = self.getBeamShift()
			if 'x' in vector:
				shift_x = vector['x'] + current_shift['x']
			if 'y' in vector:
				shift_y = vector['y'] + current_shift['y']
		elif relative == 'absolute':
			if 'x' in vector:
				shift_x = vector['x']
			if 'y' in vector:
				shift_y = vector['y']
		else:
			raise ValueError

		x, y, result = self.def3.GetCLA1()
		if 'x' in vector:
			x = int(round(shift_x/scale_x))+ZERO
		if 'y' in vector:
			y = int(round(shift_y/scale_y))+ZERO

		result = self.def3.SetCLA1(x, y)
 
	def getImageShift(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			scale_x, scale_y = self.getJeolConfig('def','imageshift_factor_x_lowmag'), self.getJeolConfig('def','imageshift_factor_y_lowmag')
			if self.getJeolConfig('tem option','use_pla'):
				shift_x, shift_y, result = self.def3.GetPLA()
			else:
				shift_x, shift_y, result = self.def3.GetIS1()
		elif mode == FUNCTION_MODES['mag1']:
			scale_x, scale_y = self.getJeolConfig('def','imageshift_factor_x_mag1'), self.getJeolConfig('def','imageshift_factor_y_mag1')
			if self.getMagnification() <= 4000:
				scale_x *= self.getJeolConfig('def','imageshift_factor_x_mag1_4000')
				scale_y *= self.getJeolConfig('def','imageshift_factor_y_mag1_4000')
			if self.getJeolConfig('tem option','use_pla'):
				shift_x, shift_y, result = self.def3.GetPLA()
			else:
				shift_x, shift_y, result = self.def3.GetIS1()
		else:
			raise RuntimeError('Image shift functions not implemented in this mode (%d, "%s")' % (mode, name))		
		return {"x": (shift_x - ZERO)*scale_x, "y": (shift_y - ZERO)*scale_y}
	
	def setImageShift(self, vector, relative = "absolute"):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			scale_x, scale_y = self.getJeolConfig('def','imageshift_factor_x_lowmag'), self.getJeolConfig('def','imageshift_factor_y_lowmag')
		elif mode == FUNCTION_MODES['mag1']:
			scale_x, scale_y = self.getJeolConfig('def','imageshift_factor_x_mag1'), self.getJeolConfig('def','imageshift_factor_y_mag1')
			if self.getMagnification() <= 4000:
				scale_x *= self.getJeolConfig('def','imageshift_factor_x_mag1_4000')
				scale_y *= self.getJeolConfig('def','imageshift_factor_y_mag1_4000')
		else:
			raise RuntimeError('Image shift functions not implemented in this mode (%d, "%s")' % (mode, name))
		current_shift = self.getImageShift()
		shift_x = current_shift['x']
		shift_y = current_shift['y']
		if relative == 'relative':
			if 'x' in vector:
				shift_x += vector['x']
			if 'y' in vector:
				shift_y += vector['y']
		elif relative == 'absolute':
			if 'x' in vector:
				shift_x = vector['x']
			if 'y' in vector:
				shift_y = vector['y']
		else:
			raise ValueError

		if mode == FUNCTION_MODES['lowmag']:
			if self.getJeolConfig('tem option','use_pla'):
				result = self.def3.SetPLA(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)
			else:
				result = self.def3.SetIS1(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)
		elif mode == FUNCTION_MODES['mag1']:
			if self.getJeolConfig('tem option','use_pla'):
				result = self.def3.SetPLA(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)
			else:
				result = self.def3.SetIS1(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)

	def setFocusOLWithBeamShift(self, value):
		beam_shift_x, beam_shift_y, result = self.def3.GetCLA1()
		self.setRawFocusOL(value)
		result = self.def3.SetCLA1(beam_shift_x, beam_shift_y)

	def getFocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			OM, result = self.lens3.GetOM()
			return self.getJeolConfig('lens','om_scale')*OM
		elif mode == FUNCTION_MODES['mag1']:
			OL = self.getRawFocusOL()
			return self.getJeolConfig('lens','ol_scale')*(OL)
		else:
			raise RuntimeError('Focus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def setFocus(self, value):
		mode, name, result = self.eos3.GetFunctionMode()
		if mode == FUNCTION_MODES['lowmag']:
			self.lens3.SetOM(int(round(value/self.getJeolConfig('lens','om_scale'))))
		elif mode == FUNCTION_MODES['mag1']:
			# ZERO is when OLc=8000 hexa OLf=0000
			value = int(round(value/self.getJeolConfig('lens','ol_scale')))
			self.setFocusOLWithBeamShift(value)
		else:
			raise RuntimeError('Focus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def setRawFocusOM(self, value):
		self.lens3.SetOM(int(value))

	def getRawFocusOM(self):
		OM, result = self.lens3.GetOM()
		return OM

	def setRawFocusOL(self, value):
		OLc, OLf = self.toOLcOLf(value)
		self.lens3.SetOLc(OLc)
		self.lens3.SetOLf(OLf)

	def getRawFocusOL(self):
		OLf, result = self.lens3.GetOLf()
		OLc, result = self.lens3.GetOLc()
		OL = self.fromOLcOLf(OLc,OLf)
		return OL

	def getZeroDefocusOM(self):
		mag = self.getMagnification()
		zero_defocus_om = None
		if mag in self.zero_defocus_om.keys():
			zero_defocus_om = self.zero_defocus_om[mag]
		elif self.zero_defocus_om.keys():
			zero_defocus_om = self.zero_defocus_om[max(self.zero_defocus_om.keys())]
		return zero_defocus_om

	def setZeroDefocusOM(self):
		mag = self.getMagnification()
		if self.projection_submode_map[mag][0] != 'lowmag':
			return
		zero_defocus_om, result = self.lens3.GetOM()
		self.zero_defocus_om[mag] = zero_defocus_om
		return zero_defocus_om

	def getZeroDefocusOL(self):
		mag = self.getMagnification()
		zero_defocus_ol = None
		if mag in self.zero_defocus_ol.keys():
			zero_defocus_ol = self.zero_defocus_ol[mag]
		elif self.zero_defocus_ol.keys():
			zero_defocus_ol = self.zero_defocus_ol[max(self.zero_defocus_ol.keys())]
		return zero_defocus_ol

	def setZeroDefocusOL(self):
		mag = self.getMagnification()
		# set zero_defocus_ol only if it is a is in the range
		if self.projection_submode_map[mag][0] != 'mag1':
			print 'outside the mag range for zero defocus OL'
			return
		# set at the closest mag value but not higher
		items = self.zero_defocus_ol.items()
		ol_mags = self.zero_defocus_ol.keys()
		ol_mags.sort()
		while ol_mags:
			if mag >= int(ol_mags[-1]):
				break
			ol_mags.pop()
		if len(ol_mags):
			print 'zero_defocus set at %d' % (int(ol_mags[-1]))
			self.zero_defocus_ol[ol_mags[-1]] = self.getRawFocusOL()
		else:
			print 'zero_defocus no ol_mags set at %d' % (int(mag))
			self.zero_defocus_ol['%d' % (int(mag),)] = self.getRawFocusOL()

	def getDefocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			OM, result = self.lens3.GetOM()
			zero_defocus_om = self.getZeroDefocusOM()
			return self.getJeolConfig('lens','om_scale')*(OM - zero_defocus_om)
		elif mode == FUNCTION_MODES['mag1']:
			OL = self.getRawFocusOL()
			zero_defocus_ol = self.getZeroDefocusOL()
			return self.getJeolConfig('lens','ol_scale')*(OL - zero_defocus_ol)
		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def setDefocus(self, defocus, relative='absolute'):
		mode, name, result = self.eos3.GetFunctionMode()
		
		if defocus == 0.0:
			if relative == 'relative':
				return
			elif relative != 'absolute':
				raise ValueError
			elif mode == FUNCTION_MODES['lowmag']:
				self.lens3.SetOM(self.getZeroDefocusOM())
			elif mode == FUNCTION_MODES['mag1']:
				zero_defocus_ol = self.getZeroDefocusOL()
				self.setFocusOLWithBeamShift(zero_defocus_ol)
			else:
				raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))
			return
		
		if mode == FUNCTION_MODES['lowmag']:
			if relative == 'relative':
				defocus += self.getDefocus()
			elif relative != 'absolute':
				raise ValueError
			self.lens3.SetOM(self.getZeroDefocusOM() + int(round(defocus/self.getJeolConfig('lens','om_scale'))))
		elif mode == FUNCTION_MODES['mag1']:
			if relative == 'relative':
				raise RuntimeError('not implemented')
			elif relative == 'absolute':
				value = int(round(defocus/self.getJeolConfig('lens','ol_scale')))
				zero_defocus_ol = self.getZeroDefocusOL()
				self.setFocusOLWithBeamShift(zero_defocus_ol + value)
			else:
				raise ValueError

		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def toOLcOLf(self,ticks):
		coarse_tick_addition = 0
		fine_ticks = ticks % COARSE_SCALE + ZERO + ZERO / COARSE_SCALE
		coarse_ticks = (ticks - fine_ticks) / COARSE_SCALE
		return coarse_ticks, fine_ticks

	def fromOLcOLf(self,OLc, OLf):
		return OLc * COARSE_SCALE + OLf

	def _resetDefocus(self):
		print '_resetDefocus is called'
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag'] and not self.getZeroDefocusOM():
			self.setZeroDefocusOM()
		# only set if not set previously.  Does this mean it only get set once in a session ?
		elif mode == FUNCTION_MODES['mag1'] and not self.getZeroDefocusOL():
			print 'setZeroDefocusOL in _resetDefocus'
			self.setZeroDefocusOL()
	
	def resetDefocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == FUNCTION_MODES['lowmag']:
			self.setZeroDefocusOM()
		elif mode == FUNCTION_MODES['mag1']:
			self.setZeroDefocusOL()
		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def _getMagnification(self):
		value, unit_str, label_str, result = self.eos3.GetMagValue()
		return value

	def getMagnification(self):
		mag = self._getMagnification()
		return mag

	def getMainScreenMagnification(self):
		value, unit_str, label_str, result = self.eos3.GetMagValue()
		return value
		
	def getMagnifications(self):
		return self.magnifications

	def setMagnifications(self, mags):
		# This is called by EM node with magnifications list input
		self.magnifications = mags

		# This might be possible to be moved to somewhere else
		if self.projection_submode_map:
			# set zero defocus for current mag mode only
			self._resetDefocus()
	
	def setMagnificationsFromProjectionSubModes(self):
		mode_map = self.getProjectionSubModeMap()
		if self.magnifications:
			# do not duplicate if exists already
			return
		mags = mode_map.keys()
		mags.sort()
		self.magnifications = mags

	def getMagnificationsInitialized(self):
		if self.magnifications:
			return True
		else:
			return False

	def findMagnifications(self):
		'''
		Go through magnifications to register magnifications.
		'''
		# One of the first functions to run during installation to get valid magnification values
		savedmode, name, result = self.eos3.GetFunctionMode()
		savedmag, unit_str, label_str, result = self.eos3.GetMagValue()

		if savedmode not in (FUNCTION_MODES['lowmag'],FUNCTION_MODES['mag1']):
			raise ValueError('Current function mode %s not implemented' % name)
		mags = {}
		for mode_name in self.getJeolConfig('eos','use_modes'):
			mode_index = FUNCTION_MODES[mode_name]
			self.eos3.SelectFunctionMode(mode_index)
			mags[mode_index] = []
			mag_index=0
			while True:
				self.eos3.SetSelector(mag_index)
				magvalue = self.eos3.GetMagValue()
				mag = magvalue[0]
				# no error is returned when index is out of range.  The mag just
				# does not change.
				if mag not in mags[mode_index]:
					mags[mode_index].append(mag)
					self.addProjectionSubModeMap(mag,mode_name,mode_index,overwrite=True)
					mag_index += 1
				else:
					break
		# set magnifications now that self.projection_submode_map is set
		self.setMagnificationsFromProjectionSubModes()
		self.setProjectionSubModeMags()
		# return to the original mag
		self.setMagnification(savedmag)

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			magnification = self._getMagnification()
		try:
			return self.magnifications.index(magnification)
		except ValueError:
			raise ValueError('invalid magnification')

	def setMagnificationIndex(self, value):
		if value <= len(self.magnifications):
			return self.setMagnification(self.magnifications[value])

	def calculateSelectorIndex(self, mode_index, mag):
		return self.submode_mags[mode_index].index(mag)

	def setMagnification(self, value):
		'''
		Set Magnification by value string or number
		'''
		try:
			value = int(round(value))
		except TypeError:
			# magnification value from choice string selection is a string
			try:
				value = int(value)
			except:
				raise TypeError
	
		if value not in self.projection_submode_map.keys():
			raise ValueError

		if not self.submode_mags:
			raise RuntimeError
		
		old_mode_index, name, result = self.eos3.GetFunctionMode()
		new_mode_name = self.projection_submode_map[value][0]
		new_mode_index = self.projection_submode_map[value][1]
		result = self.eos3.SelectFunctionMode(new_mode_index)
		if new_mode_index == FUNCTION_MODES['lowmag'] and old_mode_index != FUNCTION_MODES['lowmag']:
				#set to an arbitrary low mag to remove distortion
				self.eos3.SetSelector(self.submode_mags[FUNCTION_MODES['lowmag']][-1])
		self.eos3.SetSelector(self.calculateSelectorIndex(new_mode_index, value))
		self._resetDefocus()
		return

	def getProjectionSubModeIndex(self):
		mode_index, name, result = self.eos3.GetFunctionMode()
		return mode_index

	def getProjectionSubModeName(self):
		mode_index, name, result = self.eos3.GetFunctionMode()
		return FUNCTION_MODE_ORDERED_NAMES[mode_index]

	def getStagePosition(self):
		x, y, z, a, b, result = self.stage3.GetPos()
		position = {
			'x' : x/self.getJeolConfig('stage','stage_scale_xyz'),
			'y' : y/self.getJeolConfig('stage','stage_scale_xyz'),
			'z' : z/self.getJeolConfig('stage','stage_scale_xyz'),
			'a' : math.radians(a),
			'b' : math.radians(b)
		}
		return position

	def _isStageMoving(self):
		# check if stage is moving
		x, y, z, tx, ty, result = self.stage3.GetStatus()
		return x or y or z or tx or ty

	def _waitForStage(self):
		# wait for stage to stop moving
		while self._isStageMoving(): 
			time.sleep(0.1)

	def setStagePosition(self, position, relative='absolute'):
		# move relative or absolute, add current position for relative
		if relative == 'relative':
			current_position = self.getStagePosition()
			for axis in position:
				try:
					position[axis] += current_position[axis]
				except KeyError:
					pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError

		# set stage position and wait for movement to stop
		if 'z' in position:
			result = self.stage3.SetZ(position['z']*self.getJeolConfig('stage','stage_scale_xyz'))

		if 'x' in position:
			result = self.stage3.SetX(position['x']*self.getJeolConfig('stage','stage_scale_xyz'))

		if 'y' in position:
			result = self.stage3.SetY(position['y']*self.getJeolConfig('stage','stage_scale_xyz'))

		if 'a' in position:
			result = self.stage3.SetTiltXAngle(math.degrees(position['a']))

		if 'b' in position:
			result = self.stage3.SetTiltYAngle(math.degrees(position['b']))

		self._waitForStage()

	'''
	def setStagePosition(self, position, relative = "absolute"):
		if relative == "relative":
			pos = self.getStagePosition()
			position["x"] += pos["x"] 
			position["y"] += pos["y"] 
			position["z"] += pos["z"]
			position["a"] += pos["a"]
			position["b"] += pos["b"]
		elif relative == "absolute":
			pass
		else:
			raise ValueError

		value = self.checkStagePosition(position)
		if not value:
			return

		try:
			result = self.stage3.SetZ(position["z"] * self.getJeolConfig('stage','stage_scale_xyz'))
		except KeyError:
			pass
		else:
			z = 1
			while z: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			tmp_x = position['x'] + STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * self.getJeolConfig('stage','stage_scale_xyz'))

		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] + STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * self.getJeolConfig('stage','stage_scale_xyz'))
		# else:
		x = 1
		while x: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			tmp_y = position['y'] + STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * self.getJeolConfig('stage','stage_scale_xyz'))
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] + STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * self.getJeolConfig('stage','stage_scale_xyz'))
		# else:
		y = 1
		while y: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			result = self.stage3.SetTiltXAngle(math.degrees(position["a"]))
		except KeyError:
			pass
		else:
			tx = 1
			while tx: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			result = self.stage3.SetTiltYAngle(math.degrees(position["b"]))
		except KeyError:
			pass
		else:
			ty = 1
			while ty: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			tmp_x = position['x'] - STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * self.getJeolConfig('stage','stage_scale_xyz'))

		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] - STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * self.getJeolConfig('stage','stage_scale_xyz'))
		# else:
		x = 1
		while x: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			tmp_y = position['y'] - STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * self.getJeolConfig('stage','stage_scale_xyz'))
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] - STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * self.getJeolConfig('stage','stage_scale_xyz'))
		# else:
		y = 1
		while y: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()
				
		# for stage hysteresis removal
		try:
			result = self.stage3.SetX(position["x"] * self.getJeolConfig('stage','stage_scale_xyz'))
		except KeyError:
			pass
		else:
			x = 1
			while x: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			result = self.stage3.SetY(position["y"] * self.getJeolConfig('stage','stage_scale_xyz'))
		except KeyError:
			pass
		else:
			y = 1
			while y: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		return 0
	'''

	def getLowDoseStates(self):
		return ['on', 'off', 'disabled']
   	
	def getLowDose(self):
		mode, result = self.mds3.GetMdsMode()
		if mode == MDS_OFF: 
			return 'off'
		elif mode in (MDS_SEARCH, MDS_FOCUS, MDS_PHOTO):
			return 'on'
		else:
			return 'disabled'
 
	def setLowDose(self, ld):
		if ld == 'off':
			result = self.mds3.EndMDSMode()
		elif ld == 'on':
			result = self.mds3.SetSearchMode()
		else:		
			raise ValueError

	def getLowDoseModes(self):
		return ['exposure', 'focus1', 'search', 'unknown', 'disabled']
		
	def getLowDoseMode(self):
		mode, result = self.mds3.GetMdsMode()
		if mode == MDS_OFF:
			return 'disabled'
		elif mode == MDS_SEARCH:
			return 'search'
		elif mode == MDS_FOCUS:
			return 'focus1'
		elif mode == MDS_PHOTO:
			return 'exposure'
		else:
			return 'unknown'

	def setLowDoseMode(self, mode):
		if mode == 'exposure':
			result = self.mds3.SetPhotosetMode()
		elif mode == 'focus1':
			result = self.mds3.SetFocusMode()
		elif mode == 'search':
			result = self.mds3.SetSearchMode()
		elif mode == 'disabled':
			result = self.mds3.EndMdsMode()
		else:
			raise ValueError
   
	def getDiffractionMode(self):
		mode, result = self.eos3.GetFunctionMode()
		if mode in (FUNCTION_MODES['lowmag'], FUNCTION_MODES['mag1']):
			return "imaging"
		elif mode == FUNCTION_MODES['diff']:
			return "diffraction"
		else:
			raise SystemError

	def setDiffractionMode(self, mode):
		if mode == "imaging":
			result = self.eos3.SelectFunctionMode(FUNCTION_MODES['mag1'])
		elif mode == "diffraction":
			result = self.eos3.SelectFunctionMode(FUNCTION_MODES['diff'])
		else:
			raise ValueError
		return 0

	def getScreenCurrent(self):
		value, result = self.camera3.GetCurrentDensity()
		return value*self.getJeolConfig('camera','curent_density_scale')

	def getMainScreenPositions(self):
		return ['up', 'down', 'unknown']
		
	def getMainScreenPosition(self):
		position, result = self.detector3.GetPosition(MAIN_SCREEN)
		if position == 1:
			return 'down'
		else:
			return 'up'

	def setMainScreenPosition(self, position):
		if position == 'up':
			result = self.detector3.SetPosition(MAIN_SCREEN, 0)
		elif position == 'down':
			result = self.detector3.SetPosition(MAIN_SCREEN, 1)
		else:
			raise ValueError

	def getEnergyFiltered(self):
		return self.getJeolConfig('tem option','energy_filter')

	def getEnergyFilter(self):
		position, result = self.filter3.GetSlitPosition()
		return bool(position)

	def setEnergyFilter(self, value):
		if value:
			result = self.filter3.SetSlitPosition(1)
		else:
			result = self.filter3.SetSlitPosition(0)

	def getEnergyFilterWidth(self):
		width, result = self.filter3.GetSlitWidth()
		return width

	def setEnergyFilterWidth(self, value):
		result = self.filter3.SetSlitWidth(value)

	def alignEnergyFilterZeroLossPeak(self):
		pass

	def getApertures(self):
		return ['condenser', 'objective', 'high contrast', 'selected area']

	def _getApertureKind(self, name):
		if name == 'condenser':
			return CLA
		elif name == 'objective':
			return OLA
		elif name == 'high contrast':
			return HCA
		elif name == 'selected area':
			return SAA
		else:
			raise ValueError('Invalid aperture name specified')

	def _getApertureSizes(self, name):
		if name == 'condenser':
			return self.getJeolConfig('apt','cla_sizes')
		elif name == 'objective':
			return self.getJeolConfig('apt','ola_sizes')
		elif name == 'high contrast':
			return self.getJeolConfig('apt','hca_sizes')
		elif name == 'selected area':
			return self.getJeolConfig('apt','saa_sizes')
		else:
			raise ValueError('Invalid aperture name specified')


	def getApertureSizes(self):
		sizes = {}

		names = self.getApertures()

		for name in names:
			sizes[name] = self._getApertureSizes(name)

		return sizes

	def getApertureSize(self):
		'''
		get current aperture size of each kind.  Returns
		a dictionary with the name as the key and the size
		in meters as the item
		'''
		sizes = {}

		names = self.getApertures()

		for name in names:
			kind = self._getApertureKind(name)
			# Despite the name, this gives not the size
			# but a number as the current aperture position
			index, result = self.apt3.GetSize(kind)

			for i in range(10):
				if result != 0:
					time.sleep(.1)
					size, result = self.apt3.GetSize(kind)

			if result != 0:
				raise SystemError('Get %s aperture size failed' % name)

			size_list = self._getApertureSizes(name)

			try:
				sizes[name] = size_list[index]
			except ValueError:
				raise SystemError('No %s aperture size for index %d' % (name,index))

		return sizes

	def setApertureSize(self, sizes):

		current_kind, result = self.apt3.GetKind()

		for name in sizes:
			kind = self._getApertureKind(name)

			size_list = self._getApertureSizes(name)

			try:
				index = size_list.index(sizes[name])
			except ValueError:
				raise ValueError('Invalid %s aperture size %d specified' % (name, sizes[name]))

			current_index, result = self.apt3.GetSize(kind)
			for i in range(10):
				if result != 0:
					time.sleep(.1)
					current_index, result = self.apt3.GetSize(kind)

			if result != 0:
				raise SystemError('Get %s aperture size failed' % name)
			if index != current_index:

				result = self.apt3.SelectKind(kind)

				if current_index > index:
					result = self.apt3.SetSize(index - 1)
					result = None
					# should add timeout
					while result != 0:
						set_index, result = self.apt3.GetSize(kind)
						time.sleep(.1)

				result = self.apt3.SetSize(index)
				result = None
				# should add timeout
				while result != 0:
					set_index, result = self.apt3.GetSize(kind)
					time.sleep(.1)

		result = self.apt3.SelectKind(current_kind)

	def getAperturePosition(self):
		positions = {}

		names = self.getApertures()

		current_kind, result = self.apt3.GetKind()

		for name in names:
			kind = self._getApertureKind(name)

			result = self.apt3.SelectKind(kind)

			x, y, result = self.apt3.GetPosition()
			for i in range(10):
				if result != 0:
					time.sleep(.1)
					x, y, result = self.apt3.GetPosition()

			if result != 0:
				raise SystemError('Get %s aperture position failed' % name)

			positions[name] = {'x': x, 'y': y}

		result = self.apt3.SelectKind(current_kind)

		return positions

	def setAperturePosition(self, positions):
		current_kind, result = self.apt3.GetKind()

		for name in positions:
			p = positions[name]
			if 'x' in p and type(p['x']) is not int:
				raise TypeError
			if 'y' in p and type(p['y']) is not int:
				raise TypeError
			

			kind = self._getApertureKind(name)

			result = self.apt3.SelectKind(kind)

			x, y, result = self.apt3.GetPosition()

			if 'x' in p and p['x'] != x or 'y' in p and p['y'] != y:
				result = self.apt3.SetPosition(p['x'], p['y'])

		result = self.apt3.SelectKind(current_kind)

	def _setSpecialMag(self):
		result = self.eos3.SelectFunctionMode(FUNCTION_MODES['mag1'])
		result = self.lens3.SetOLc(12646)
		result = self.lens3.SetOLf(34439)
		result = self.lens3.SetOM(41801)

	'''
	Camera function list
		::TakePhoto 
		::CancelPhoto 
		::SetExpTime
		::GetExpTime
		::SelectFilmLoadingMode	- 0 : manual operation / 1 : auto operation 1 / 2 : auto operation 2
		::GetShutterMode		- Shutter modes are
		::SetShutterMode		- 0 : manual exposure / 1 : automatic exposure / 2 : bulb
		::GetShutterPosition	- Shutter positions are
		::SetShutterPosition	- 0 : open / 1 : close / 2 : exposure
		::ExposeShutter
	'''	
	def getCameraStatus(self):
		status, result = self.camera3.GetStatus()
		return status

	def setFilmLoadingMode(self, feed = 0):
		result = self.camera3.SelectFilmLoadingMode(feed)

	def takePhoto(self):
		result = self.camera3.TakePhoto()

	def cancelPhoto(self):
		result = self.camera3.CancelPhoto()

	def getExposeTime(self):
		time, result = self.camera3.GetExpTime()
		return time

	def setExposeTime(self, time):
		result = self.camera3.SetExpTime(time)

	def preFilmExposure(self, value):
		if not value:
			return
		value, result = self.camera3.GetUnused()
		if value < 1:
			raise RuntimeError('No film to take exposure')

		self.camera3.LoadFilm()
		time.sleep(6)
		
		return

	def postFilmExposure(self, value):
		if not value:
			return
		result = self.camera3.EjectFilm()
		return

	def getProbeMode(self):
		return 'default'

	def setProbeMode(self, probe_str):
		pass

	def getProbeModes(self):
		return ['default']

	def exposeSpecimenNotCamera(self,exptime=0):
		if exptime == 0:
			return
		self.setMainScreenPosition('down')
		time.sleep(exptime)
		self.setMainScreenPosition('up')
