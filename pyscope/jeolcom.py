import time
import math
import tem
import comtypes.client

# function modes
MAG1_MODE = 0
MAG2_MODE = 1
LOWMAG_MODE = 2
DIFF_MODE = 4

# identifier for dector
MAIN_SCREEN = 13

# convert to m
OM_SCALE = 6.4e-9
OL_SCALE = 2.6e-9
COARSE_SCALE = 32

# convert to pA/???^2
CURRENT_DENSITY_SCALE = 1e-10

# MDS modes
MDS_OFF = 0
MDS_SEARCH = 1
MDS_FOCUS = 2
MDS_PHOTO = 3

# constants for Jeol Hex value
ZERO = 32768
MAX = 65535
MIN = 0
SCALE_FACTOR = 32767

#BEAMTILT_FACTOR_X = 0.00000065
#BEAMTILT_FACTOR_Y = 0.00000062

BEAMTILT_FACTOR_X = 1.307e-5
BEAMTILT_FACTOR_Y = 1.307e-5

BEAMSHIFT_FACTOR_X_MAG1 = 0.0000000252
BEAMSHIFT_FACTOR_Y_MAG1 = 0.0000000246
BEAMSHIFT_FACTOR_X_LOWMAG = 0.000000092
BEAMSHIFT_FACTOR_Y_LOWMAG = 0.000000092

IMAGESHIFT_FACTOR_X_MAG1 = 0.000000000508
IMAGESHIFT_FACTOR_Y_MAG1 = 0.000000000434
IMAGESHIFT_FACTOR_X_LOWMAG = 0.0000000132
IMAGESHIFT_FACTOR_Y_LOWMAG = 0.000000012

# stage coordinates to meters
STAGE_SCALE_XYZ = 1e9

# not currently performing manual backlash correction
#STAGE_BACKLASH = 2e-6

# does the scope have an energy filter
ENERGY_FILTER = True

# apertures
CLA = 1
OLA = 2
HCA = 3
SAA = 4
CLA_SIZES = [0, 150e-6, 70e-6, 50e-6, 20e-6]
OLA_SIZES = [0, 50e-6, 30e-6, 15e-6, 5e-6]
HCA_SIZES = [0, 120e-6, 60e-6, 40e-6, 20e-6]
SAA_SIZES = [0, 100e-6, 50e-6, 20e-6, 10e-6]

low_magnifications = [
	100, 120, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000	#, 2500, 3000
]

magnifications = [
	2500, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 15000, 20000, 25000,
	30000, 40000, 50000, 60000, 80000, 100000, 120000, 150000, 200000,
	250000, 300000, 400000, 500000, 600000, 800000, 1000000, 1200000,
	1500000, 2000000
]

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
		while result != 0:
			ht, result = self.ht3.GetHTValue()
			time.sleep(1)

		# initialize zero defocus values as unset
		self.zeroOM = None
		self.zeroOLf = None
		self.zeroOLc = None
		
		# set zero defocus for current mag mode only
		self._resetDefocus()


	def __del__(self):
		comtypes.CoUninitialize()

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
		pass

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
		return {"x": (tilt_x - ZERO)*BEAMTILT_FACTOR_X, "y": (tilt_y - ZERO)*BEAMTILT_FACTOR_Y}
		
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

		tilt_x = int(round(tilt_x/BEAMTILT_FACTOR_X)) + ZERO
		tilt_y = int(round(tilt_y/BEAMTILT_FACTOR_Y)) + ZERO

		result = self.def3.SetCLA2(tilt_x, tilt_y)

	def getBeamShift(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			scale_x, scale_y = BEAMSHIFT_FACTOR_X_LOWMAG, BEAMSHIFT_FACTOR_Y_LOWMAG
		elif mode == MAG1_MODE:
			scale_x, scale_y = BEAMSHIFT_FACTOR_X_MAG1, BEAMSHIFT_FACTOR_Y_MAG1
		else:
			raise RuntimeError('Beam shift functions not implemented in this mode (%d, "%s")' % (mode, name))
		shift_x, shift_y, result = self.def3.GetCLA1()

		x = (shift_x - ZERO)*scale_x
		y = (shift_y - ZERO)*scale_y

		return {"x": x, "y": y}

	def setBeamShift(self, vector, relative = "absolute"):

		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			scale_x, scale_y = BEAMSHIFT_FACTOR_X_LOWMAG, BEAMSHIFT_FACTOR_Y_LOWMAG
		elif mode == MAG1_MODE:
			scale_x, scale_y = BEAMSHIFT_FACTOR_X_MAG1, BEAMSHIFT_FACTOR_Y_MAG1
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
		if mode == LOWMAG_MODE:
			scale_x, scale_y = IMAGESHIFT_FACTOR_X_LOWMAG, IMAGESHIFT_FACTOR_Y_LOWMAG
			#shift_x, shift_y, result = self.def3.GetIS2()
			shift_x, shift_y, result = self.def3.GetIS1()
		elif mode == MAG1_MODE:
			scale_x, scale_y = IMAGESHIFT_FACTOR_X_MAG1, IMAGESHIFT_FACTOR_Y_MAG1
			shift_x, shift_y, result = self.def3.GetIS1()
		else:
			raise RuntimeError('Image shift functions not implemented in this mode (%d, "%s")' % (mode, name))		
		return {"x": (shift_x - ZERO)*scale_x, "y": (shift_y - ZERO)*scale_y}

	def setImageShift(self, vector, relative = "absolute"):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			scale_x, scale_y = IMAGESHIFT_FACTOR_X_LOWMAG, IMAGESHIFT_FACTOR_Y_LOWMAG
		elif mode == MAG1_MODE:
			scale_x, scale_y = IMAGESHIFT_FACTOR_X_MAG1, IMAGESHIFT_FACTOR_Y_MAG1
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

		if mode == LOWMAG_MODE:
			#result = self.def3.SetIS2(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)
			result = self.def3.SetIS1(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)
		elif mode == MAG1_MODE:
			result = self.def3.SetIS1(int(round((shift_x)/scale_x))+ZERO, int(round((shift_y)/scale_y))+ZERO)

	def _setOL(self, coarse_value, fine_value):
		beam_shift_x, beam_shift_y, result = self.def3.GetCLA1()
		result = self.lens3.SetOLc(coarse_value)
		result = self.lens3.SetOLf(fine_value)
		result = self.def3.SetCLA1(beam_shift_x, beam_shift_y)

	def getFocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			OM, result = self.lens3.GetOM()
			return OM_SCALE*OM
		elif mode == MAG1_MODE:
			OLf, result = self.lens3.GetOLf()
			OLc, result = self.lens3.GetOLc()
			return OL_SCALE*(OLf + COARSE_SCALE*OLc)
		else:
			raise RuntimeError('Focus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def setFocus(self, value):
		mode, name, result = self.eos3.GetFunctionMode()
		if mode == LOWMAG_MODE:
			self.lens3.SetOM(int(round(value/OM_SCALE)))
		elif mode == MAG1_MODE:
			value = int(round(value/OL_SCALE))
			coarse_value = (value - ZERO)/COARSE_SCALE
			fine_value = value - coarse_value*COARSE_SCALE
			self._setOL(coarse_value, fine_value)
		else:
			raise RuntimeError('Focus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def getDefocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			OM, result = self.lens3.GetOM()
			return OM_SCALE*(OM - self.zeroOM)
		elif mode == MAG1_MODE:
			OLf, result = self.lens3.GetOLf()
			OLc, result = self.lens3.GetOLc()
			return OL_SCALE*(OLf - self.zeroOLf + COARSE_SCALE*(OLc - self.zeroOLc))
		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def setDefocus(self, defocus, relative='absolute'):
		mode, name, result = self.eos3.GetFunctionMode()
		
		if defocus == 0.0:
			if relative == 'relative':
				return
			elif relative != 'absolute':
				raise ValueError
			elif mode == LOWMAG_MODE:
				self.lens3.SetOM(self.zeroOM)
			elif mode == MAG1_MODE:
				self._setOL(self.zeroOLc, self.zeroOLf)
			else:
				raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))
			return

		if mode == LOWMAG_MODE:
			if relative == 'relative':
				defocus += self.getDefocus()
			elif relative != 'absolute':
				raise ValueError
			self.lens3.SetOM(self.zeroOM + int(round(defocus/OM_SCALE)))
		elif mode == MAG1_MODE:
			if relative == 'relative':
				raise RuntimeError('not implemented')
			elif relative == 'absolute':
				value = int(round(defocus/OL_SCALE))
				coarse_value = 0
				if self.zeroOLf + value < ZERO/2 or self.zeroOLf + value > (ZERO + ZERO/2):
					coarse_value = (self.zeroOLf + value - ZERO)/COARSE_SCALE
				fine_value = value - coarse_value*COARSE_SCALE
				self._setOL(self.zeroOLc + coarse_value, self.zeroOLf + fine_value)
			else:
				raise ValueError

		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def _resetDefocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE and self.zeroOM is None:
			self.zeroOM, result = self.lens3.GetOM()
		elif mode == MAG1_MODE and None in (self.zeroOLc, self.zeroOLf):
			self.zeroOLc, result = self.lens3.GetOLc()
			self.zeroOLf, result = self.lens3.GetOLf()

	def resetDefocus(self):
		mode, name, result = self.eos3.GetFunctionMode() 
		if mode == LOWMAG_MODE:
			self.zeroOM, result = self.lens3.GetOM()
		elif mode == MAG1_MODE:
			self.zeroOLf, result = self.lens3.GetOLf()
			self.zeroOLc, result = self.lens3.GetOLc()
		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

	def getMagnification(self):
		mode, name, result = self.eos3.GetFunctionMode() 

		if mode == LOWMAG_MODE:
			value, unit_str, label_str, result = self.eos3.GetMagValue()
			if value not in low_magnifications:
				raise SystemError('LOWMAG mode magnificaion not in low magnifications table')
			return value

		elif mode == MAG1_MODE:
			value, unit_str, label_str, result = self.eos3.GetMagValue()
			if value not in magnifications:
				raise SystemError('MAG1 mode magnificaion not in magnifications table')
				
			return value

		else:
			raise RuntimeError('Defocus functions not implemented in this mode (%d, "%s")' % (mode, name))

		raise SystemError

	def getMainScreenMagnification(self):
		value, unit_str, label_str, result = self.eos3.GetMagValue()
		return value
		
	def getMagnifications(self):
		return low_magnifications + magnifications

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			return 0
		else:
			try:
				return (low_magnifications + magnifications).index(magnification)
			except ValueError:
				raise ValueError('invalid magnification')

	def setMagnification(self, value):

		mode, name, result = self.eos3.GetFunctionMode()

		if value in low_magnifications:
			if mode != LOWMAG_MODE:
				result = self.eos3.SelectFunctionMode(LOWMAG_MODE)
			self.eos3.SetSelector(low_magnifications.index(value))
			self._resetDefocus()
			return

		if value in magnifications:
			if mode != MAG1_MODE:
				result = self.eos3.SelectFunctionMode(MAG1_MODE) 
			self.eos3.SetSelector(magnifications.index(value))
			self._resetDefocus()
			return

		raise ValueError

	def getStagePosition(self):
		x, y, z, a, b, result = self.stage3.GetPos()
		position = {
			'x' : x/STAGE_SCALE_XYZ,
			'y' : y/STAGE_SCALE_XYZ,
			'z' : z/STAGE_SCALE_XYZ,
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
			result = self.stage3.SetZ(position['z']*STAGE_SCALE_XYZ)

		if 'x' in position:
			result = self.stage3.SetX(position['x']*STAGE_SCALE_XYZ)

		if 'y' in position:
			result = self.stage3.SetY(position['y']*STAGE_SCALE_XYZ)

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
			result = self.stage3.SetZ(position["z"] * STAGE_SCALE_XYZ)
		except KeyError:
			pass
		else:
			z = 1
			while z: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			tmp_x = position['x'] + STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * STAGE_SCALE_XYZ)
			
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] + STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * STAGE_SCALE_XYZ)
		# else:
		x = 1
		while x: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()


		try:
			tmp_y = position['y'] + STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * STAGE_SCALE_XYZ)
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] + STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * STAGE_SCALE_XYZ)
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
			result = self.stage3.SetX(tmp_x * STAGE_SCALE_XYZ)

		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] - STAGE_BACKLASH
			result = self.stage3.SetX(tmp_x * STAGE_SCALE_XYZ)
		# else:
		x = 1
		while x: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()


		try:
			tmp_y = position['y'] - STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * STAGE_SCALE_XYZ)
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] - STAGE_BACKLASH
			result = self.stage3.SetY(tmp_y * STAGE_SCALE_XYZ)
		# else:
		y = 1
		while y: 
			time.sleep(.1)
			x, y, z, tx, ty, result = self.stage3.GetStatus()

		# for stage hysteresis removal

		try:
			result = self.stage3.SetX(position["x"] * STAGE_SCALE_XYZ)
		except KeyError:
			pass
		else:
			x = 1
			while x: 
				time.sleep(.1)
				x, y, z, tx, ty, result = self.stage3.GetStatus()

		try:
			result = self.stage3.SetY(position["y"] * STAGE_SCALE_XYZ)
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
		if mode in (LOWMAG_MODE, MAG1_MODE):
			return "imaging"
		elif mode == DIFF_MODE:
			return "diffraction"
		else:
			raise SystemError

	def setDiffractionMode(self, mode):
		if mode == "imaging":
			result = self.eos3.SelectFunctionMode(MAG1_MODE)
		elif mode == "diffraction":
			result = self.eos3.SelectFunctionMode(DIFF_MODE)
		else:
			raise ValueError

		return 0

	def getScreenCurrent(self):
		value, result = self.camera3.GetCurrentDensity()
		return value*CURRENT_DENSITY_SCALE

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
		return ENERGY_FILTER

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
			return CLA_SIZES
		elif name == 'objective':
			return OLA_SIZES
		elif name == 'high contrast':
			return HCA_SIZES
		elif name == 'selected area':
			return SAA_SIZES
		else:
			raise ValueError('Invalid aperture name specified')


	def getApertureSizes(self):
		sizes = {}

		names = self.getApertures()

		for name in names:
			sizes[name] = self._getApertureSizes(name)

		return sizes

	def getApertureSize(self):
		sizes = {}

		names = self.getApertures()

		for name in names:
			kind = self._getApertureKind(name)

			size, result = self.apt3.GetSize(kind)

			for i in range(10):
				if result != 0:
					time.sleep(.1)
					size, result = self.apt3.GetSize(kind)

			if result != 0:
				raise SystemError('Get %s aperture size failed' % name)

			size_list = self._getApertureSizes(name)

			try:
				sizes[name] = size_list[size]
			except ValueError:
				raise SystemError('No aperture size for index %d' % size)

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
		result = self.eos3.SelectFunctionMode(MAG1_MODE)
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

