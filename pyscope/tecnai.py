#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import sys
sys.coinit_flags = 0
import pythoncom
import win32com.client
import pywintypes
import tecnaicom
import ldcom
import adacom
import time

defaultmagtable = [(21, 18.5), (28, 25), (38, 34), (56, 50), (75, 66), (97, 86),	(120, 105), (170, 150), (220, 195), (330, 290), (420, 370), (550, 490),
	(800, 710), (1100, 970), (1500, 1350), (2100, 1850), (1700, 1500),
	(2500, 2200), (3500, 3100), (5000, 4400), (6500, 5800), (7800, 6900),
	(9600, 8500), (11500, 10000), (14500, 13000), (19000, 17000), (25000, 22000),
	(29000, 25500), (50000, 44000), (62000, 55000), (80000, 71000),
	(100000, 89000), (150000, 135000), (200000, 175000), (240000, 210000),
	(280000, 250000), (390000, 350000), (490000, 430000), (700000, 620000)]

polaramagtable = [(62, 54), (76, 67), (100, 91), (125, 110), (175, 155),
	(220, 195), (280, 250), (360, 320), (480, 430), (650, 570), (790, 700),
	(990, 880), (1200, 1100), (1800, 1600), (2300, 2050), (2950, 2600),
	(3000, 2650), (4500, 3900), (5600, 5000), (9300, 8200), (13500, 12000),
	(18000, 15500), (22500, 20000), (27500, 24500), (34000, 29500),
	(41000, 36000), (50000, 44000), (61000, 54000), (77000, 68000),
	(95000, 84000), (115000, 105000), (160000, 140000), (200000, 175000),
	(235000, 210000), (310000, 275000), (400000, 350000), (470000, 420000),
	(630000, 560000), (800000, 710000)]


class Tecnai(object):
	def cmpmags(self, x, y):
		key = self.cmpmags_status
		if x[key] < y[key]: 
			return -1
		elif x[key] == y[key]: 
			return 0
		elif x[key] > y[key]: 
			 return 1
		
	def __init__(self, magtable=defaultmagtable):
		self.correctedstage = True
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self.theScope = win32com.client.Dispatch('Tecnai.Instrument')		
			self.theLowDose = win32com.client.Dispatch('LDServer.LdSrv')
			self.theAda = win32com.client.Dispatch('adaExp.TAdaExp',
																					clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
		except pythoncom.com_error:
			raise RuntimeError('Unable to initialize microscope interface[s]')

		# this was a quick way of doing things, needs to be redone
		self.magTable = []
		for i, mag in enumerate(magtable):
			self.magTable.append({'index': i + 1, 'up': mag[0], 'down': mag[1]})

		self.methodmapping = {
			'beam blank': {'get': 'getBeamBlank', 'set': 'setBeamBlank'},
			'gun tilt': {'get': 'getGunTilt', 'set': 'setGunTilt'},
			'gun shift': {'get': 'getGunShift', 'set': 'setGunShift'},
			'high tension': {'get': 'getHighTension', 'set': 'setHighTension'},
			'intensity': {'get': 'getIntensity', 'set': 'setIntensity'},
			'dark field mode': {'get': 'getDarkFieldMode', 'set': 'setDarkFieldMode'},
			'stigmator': {'get': 'getStigmator', 'set': 'setStigmator'},
			'spot size': {'get': 'getSpotSize', 'set': 'setSpotSize'},
			'beam tilt': {'get': 'getBeamTilt', 'set': 'setBeamTilt'},
			'beam shift': {'get': 'getBeamShift', 'set': 'setBeamShift'},
			'image shift': {'get': 'getImageShift', 'set': 'setImageShift'},
			'raw image shift': {'get': 'getRawImageShift', 'set': 'setRawImageShift'},
			'defocus': {'get': 'getDefocus', 'set': 'setDefocus'},
			'magnification': {'get': 'getMagnification', 'set': 'setMagnification'},
			'stage position': {'get': 'getStagePosition', 'set': 'setStagePosition'},
			'corrected stage position': {'get': 'getCorrectedStagePosition',
																		'set': 'setCorrectedStagePosition'},
			'low dose': {'get': 'getLowDose', 'set': 'setLowDose'},
			'low dose mode': {'get': 'getLowDoseMode', 'set': 'setLowDoseMode'},
			'diffraction mode': {'get': 'getDiffractionMode',
														'set': 'setDiffractionMode'},
			'reset defocus': {'set': 'resetDefocus', 'get': 'getResetDefocus'},
			'main screen position': {'get': 'getMainScreen', 'set': 'setMainScreen'},
			'small screen position': {'get': 'getSmallScreen'},
			'holder type': {'get': 'getHolderType', 'set': 'setHolderType'},
			'turbo pump': {'get': 'getTurboPump', 'set': 'setTurboPump'},
			'column valves': {'get': 'getColumnValves', 'set': 'setColumnValves'},
			'screen current': {'get': 'getScreenCurrent'},
			'holder status': {'get': 'getHolderStatus'},
			'stage status': {'get': 'getStageStatus'},
			'vacuum status': {'get': 'getVacuumStatus'},
			'column pressure': {'get': 'getColumnPressure'},
			'objective excitation': {'get': 'getObjectiveExcitation'},
			'focus': {'get': 'getFocus', 'set': 'setFocus'},
			'film stock': {'get': 'getFilmStock'},
			'film exposure number': {'get': 'getFilmExposureNumber',
																'set': 'setFilmExposureNumber'},
			'pre film exposure': {'set': 'preFilmExposure'},
			'post film exposure': {'set': 'postFilmExposure'},
			'film exposure': {'set': 'filmExposure'},
			'film exposure type': {'get': 'getFilmExposureType',
															'set': 'setFilmExposureType'},
			'film exposure time': {'get': 'getFilmExposureTime'},
			'film manual exposure time': {'get': 'getFilmManualExposureTime',
																		'set': 'setFilmManualExposureTime'},
			'film automatic exposure time': {'get': 'getFilmAutomaticExposureTime'},
			'film text': {'get': 'getFilmText', 'set': 'setFilmText'},
			'film user code': {'get': 'getFilmUserCode', 'set': 'setFilmUserCode'},
			'film date type': {'get': 'getFilmDateType', 'set': 'setFilmDateType'},
			'shutter': {'set': 'setShutter', 'get': 'getShutter'},
			'external shutter': {'set': 'setExternalShutter', 'get': 'getExternalShutter'},
		}

		self.typemapping = {
			'beam blank': {'type': str, 'values': ['on', 'off']},
			'gun tilt': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'gun shift': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'high tension': {'type': int},
			'intensity': {'type': float},
			'dark field mode': {'type': str, 'values':
																				['off', 'cartesian', 'conical']},
			'stigmator': {'type':  dict, 'values':
														{'condenser': {'type': dict, 'values':
															{'x': {'type': float}, 'y': {'type': float}}},
														'objective': {'type': dict, 'values':
															{'x': {'type': float}, 'y': {'type': float}}},
														'diffraction': {'type': dict, 'values':
															{'x': {'type': float}, 'y': {'type': float}}}}},
			'spot size': {'type': int},
			'beam tilt': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'beam shift': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'image shift': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'raw image shift': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'defocus': {'type': float},
			'magnification': {'type': float},
			# correct for holder type
			'stage position': {'type': dict, 'values':
																{'x': {'type': float}, 'y': {'type': float},
																	'z': {'type': float}, 'a': {'type': float}}},
			'corrected stage position': {'type': bool},
			'low dose': {'type': str, 'values': ['on', 'off']},
			'low dose mode': {'type': str, 'values':
																		['exposure', 'focus1', 'focus2', 'search']},
			'diffraction mode': {'type': str, 'values': ['imaging', 'diffraction']},
			'reset defocus': {'type': bool},
			'main screen position': {'type': str, 'values': ['up', 'down']},
			'small screen position': {'type': str, 'values': ['up', 'down']},
			# no unknown holder
			'holder type': {'type': str, 'values':
																			['no holder', 'single tilt', 'cryo']},
			'turbo pump': {'type': str, 'values': ['on', 'off']},
			'column valves': {'type': str, 'values': ['open', 'closed']},
			'screen current': {'type': float},
			'holder status': {'type': str},
			'stage status': {'type': str},
			'vacuum status': {'type': str},
			'column pressure': {'type': float},
			'objective excitation': {'type': float},
			'focus': {'type': float},
			'film stock': {'type': int},
			'film exposure number': {'type': int},
			'pre film exposure': {'type': bool},
			'post film exposure': {'type': bool},
			'film exposure': {'type': bool},
			'film exposure type': {'type': str, 'values': ['manual', 'automatic']},
			'film exposure time': {'type': float},
			'film manual exposure time': {'type': float},
			'film automatic exposure time': {'type': float},
			'film text': {'type': str},
			'film user code': {'type': str},
			'film date type': {'type': str,
										'values': ['no date', 'DD-MM-YY', 'MM/DD/YY', 'YY.MM.DD']},
			'shutter': {'type': str, 'values': ['open', 'closed']},
			'external shutter': {'type': str, 'values': ['connected', 'disconnected']},
		}
		self.parameterdependencies = {
			'main screen position': ['magnification'],
			'film exposure type': ['film exposure time'],
			'defocus': ['focus'],
			'reset defocus': ['defocus'],
		}

	def setCorrectedStagePosition(self, value):
		self.correctedstage = value
		return self.correctedstage

	def getCorrectedStagePosition(self):
		return self.correctedstage

	def setStagePosition(self, value):
		# pre-position x and y (maybe others later)
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

	def normalizeLens(self, lens = 'all'):
		if lens == 'all':
			self.theScope.NormalizeAll()
		elif lens == 'objective':
			self.theScope.Projection.Normalize(win32com.client.constants.pnmObjective)
		elif lens == 'projector':
			self.theScope.Projection.Normalize(win32com.client.constants.pnmProjector)
		elif lens == 'allprojection':
			self.theScope.Projection.Normalize(win32com.client.constants.pnmAll)
		elif lens == 'spotsize':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmSpotsize)
		elif lens == 'intensity':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmIntensity)
		elif lens == 'condenser':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmCondenser)
		elif lens == 'minicondenser':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmMiniCondenser)
		elif lens == 'objectivepole':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmObjectivePole)
		elif lens == 'allillumination':
			self.theScope.Illumination.Normalize(win32com.client.constants.nmAll)
		else:
			raise ValueError

	def getScreenCurrent(self):
		return float(self.theScope.Camera.ScreenCurrent)
	
	def getGunTilt(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.theScope.Gun.Tilt.X)
		value['y'] = float(self.theScope.Gun.Tilt.Y)

		return value
	
	def setGunTilt(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Gun.Tilt.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Gun.Tilt.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Gun.Tilt
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Gun.Tilt = vec
	
	def getGunShift(self):
		value = {'x': None, 'y': None}
		value['x'] = self.theScope.Gun.Shift.X
		value['y'] = self.theScope.Gun.Shift.Y

		return value
	
	def setGunShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Gun.Shift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Gun.Shift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Gun.Shift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Gun.Shift = vec
	
	def getHighTension(self):
		return int(self.theScope.Gun.HTValue)
	
	def setHighTension(self, ht):
		self.theScope.Gun.HTValue = ht
	
	def getIntensity(self):
		return float(self.theScope.Illumination.Intensity)
	
	def setIntensity(self, intensity, relative = 'absolute'):
		if relative == 'relative':
			intensity += self.theScope.Illumination.Intensity
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.theScope.Illumination.Intensity = intensity

	def getDarkFieldMode(self):
		if self.theScope.Illumination.DFMode == win32com.client.constants.dfOff:
			return 'off'
		elif self.theScope.Illumination.DFMode == win32com.client.constants.dfCartesian:
			return 'cartesian'
		elif self.theScope.Illumination.DFMode == win32com.client.constants.dfConical:
			return 'conical'
		else:
			raise SystemError
		
	def setDarkFieldMode(self, mode):
		if mode == 'off':
			self.theScope.Illumination.DFMode = win32com.client.constants.dfOff
		elif mode == 'cartesian':
			self.theScope.Illumination.DFMode = win32com.client.constants.dfCartesian
		elif mode == 'conical':
			self.theScope.Illumination.DFMode = win32com.client.constants.dfConical
		else:
			raise ValueError
	
	def getBeamBlank(self):
		if self.theScope.Illumination.BeamBlanked == 0:
			return 'off'
		elif self.theScope.Illumination.BeamBlanked == 1:
			return 'on'
		else:
			raise SystemError
		
	def setBeamBlank(self, bb):
		if bb == 'off' :
			self.theScope.Illumination.BeamBlanked = 0
		elif bb == 'on':
			self.theScope.Illumination.BeamBlanked = 1
		else:
			raise ValueError
	
	def getStigmator(self):
		value = {'condenser': {'x': None, 'y': None},
							'objective': {'x': None, 'y': None},
							'diffraction': {'x': None, 'y': None}}
		value['condenser']['x'] = \
			float(self.theScope.Illumination.CondenserStigmator.X)
		value['condenser']['y'] = \
			float(self.theScope.Illumination.CondenserStigmator.Y)
		value['objective']['x'] = \
			float(self.theScope.Projection.ObjectiveStigmator.X)
		value['objective']['y'] = \
			float(self.theScope.Projection.ObjectiveStigmator.Y)
		value['diffraction']['x'] = \
			float(self.theScope.Projection.DiffractionStigmator.X)
		value['diffraction']['y'] = \
			float(self.theScope.Projection.DiffractionStigmator.Y)

		return value
		
	def setStigmator(self, stigs, relative = 'absolute'):
		for key in stigs.keys():
			if key == 'condenser':
				stigmator = self.theScope.Illumination.CondenserStigmator
			elif key == 'objective':
				stigmator = self.theScope.Projection.ObjectiveStigmator
			elif key == 'diffraction':
				stigmator = self.theScope.Projection.DiffractionStigmator
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
				stigmator.Y = stigs[key]['y']
			except KeyError:
					pass

			if key == 'condenser':
				self.theScope.Illumination.CondenserStigmator = stigmator
			elif key == 'objective':
				self.theScope.Projection.ObjectiveStigmator = stigmator
			elif key == 'diffraction':
				self.theScope.Projection.DiffractionStigmator = stigmator
			else:
				raise ValueError
	
	def getSpotSize(self):
		return int(self.theScope.Illumination.SpotsizeIndex)
	
	def setSpotSize(self, ss, relative = 'absolute'):
		if relative == 'relative':
			ss += self.theScope.Illumination.SpotsizeIndex
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.theScope.Illumination.SpotsizeIndex = ss
	
	def getBeamTilt(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.theScope.Illumination.RotationCenter.X)
		value['y'] = float(self.theScope.Illumination.RotationCenter.Y)

		return value
	
	def setBeamTilt(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Illumination.RotationCenter.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Illumination.RotationCenter.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Illumination.RotationCenter
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Illumination.RotationCenter = vec
	
	def getBeamShift(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.theScope.Illumination.Shift.X)
		value['y'] = float(self.theScope.Illumination.Shift.Y)

		return value

	def setBeamShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Illumination.Shift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Illumination.Shift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Illumination.Shift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Illumination.Shift = vec
	
	def getImageShift(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.theScope.Projection.ImageBeamShift.X)
		value['y'] = float(self.theScope.Projection.ImageBeamShift.Y)
		return value
	
	def setImageShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Projection.ImageBeamShift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Projection.ImageBeamShift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Projection.ImageBeamShift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Projection.ImageBeamShift = vec
	
	def getRawImageShift(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.theScope.Projection.ImageShift.X)
		value['y'] = float(self.theScope.Projection.ImageShift.Y)
		return value
	
	def setRawImageShift(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.theScope.Projection.ImageShift.X
			except KeyError:
				pass
			try:
				vector['y'] += self.theScope.Projection.ImageShift.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.theScope.Projection.ImageShift
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.theScope.Projection.ImageShift = vec
	
	def getDefocus(self):
		return float(self.theScope.Projection.Defocus)
	
	def setDefocus(self, defocus, relative = 'absolute'):
		if relative == 'relative':
			defocus += self.theScope.Projection.Defocus
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.theScope.Projection.Defocus = defocus
	
	def resetDefocus(self, value):
		if not value:
			return
		self.theScope.Projection.ResetDefocus()

	def getResetDefocus(self):
		return False
	
	def getMagnification(self):
		if self.theScope.Camera.MainScreen == win32com.client.constants.spUp:
			key = 'up'
		elif self.theScope.Camera.MainScreen == win32com.client.constants.spDown:
			key = 'down'
		else:   # perhaps spUnknown
			raise SystemError

		magindex = self.theScope.Projection.MagnificationIndex

		for mag in self.magTable:
			if mag['index'] == magindex:
				return float(mag[key])

		raise SystemError			

	def setMagnification(self, mag):
		if self.theScope.Camera.MainScreen == win32com.client.constants.spUp:
			key = 'up'
		elif self.theScope.Camera.MainScreen == win32com.client.constants.spDown:
			key = 'down'
		else:   # perhaps spUnknown
			raise SystemError

		self.cmpmags_status = key

		self.magTable.sort(self.cmpmags)

		prevmag = self.magTable[0]
		
		for imag in self.magTable:
			if imag[key] > mag:
				 self.theScope.Projection.MagnificationIndex = prevmag['index']
				 return
			prevmag = imag
			
		self.theScope.Projection.MagnificationIndex = prevmag['index']
		return
	
	def getStagePosition(self):
		value = {'x': None, 'y': None, 'z': None, 'a': None}
		if(self.theScope.Stage.Holder == win32com.client.constants.hoDoubleTilt):
			value['b'] = None
		value['x'] = float(self.theScope.Stage.Position.X)
		value['y'] = float(self.theScope.Stage.Position.Y)
		value['z'] = float(self.theScope.Stage.Position.Z)
		value['a'] = float(self.theScope.Stage.Position.A)
		if 'b' in value:
			value['b'] = float(self.theScope.Stage.Position.B)
		return value

	def _setStagePosition(self, position, relative = 'absolute'):
#		tolerance = 1.0e-4
#		polltime = 0.01

		if relative == 'relative':
			for key in position:
				position[key] += getattr(self.theScope.Stage.Position, key.upper())
		elif relative != 'absolute':
			raise ValueError
		
		pos = self.theScope.Stage.Position

		axes = 0
		for key, value in position.items():
			setattr(pos, key.upper(), value)
			axes |= getattr(win32com.client.constants, 'axis' + key.upper())

		try:
			self.theScope.Stage.Goto(pos, axes)
		except pywintypes.com_error:
			print 'Stage limit hit'
#		for key in position:
#			while abs(getattr(self.theScope.Stage.Position, key.upper())
#								- getattr(pos, key.upper())) > tolerance:
#				time.sleep(polltime)
	
	def getLowDose(self):
		try:
			if (self.theLowDose.IsInitialized == 1) and (self.theLowDose.LowDoseActive == win32com.client.constants.IsOn):
				return 'on'
			else:
				return 'off'
		except pythoncom.com_error:
			return 'disabled'
 
	def setLowDose(self, ld):
		try:
			if ld == 'off' :
				self.theLowDose.LowDoseActive = win32com.client.constants.IsOff
			elif ld == 'on':
				if self.theLowDose.IsInitialized == 0:
					raise RuntimeError('Low dose is not initialized')
				else:
					self.theLowDose.LowDoseActive = win32com.client.constants.IsOn
			else:
				raise ValueError
		except pythoncom.com_error:
			raise RuntimeError('Low dose is not enabled')

	def getLowDoseMode(self):
		try:
			if self.theLowDose.LowDoseState == win32com.client.constants.eExposure:
				return 'exposure'
			elif self.theLowDose.LowDoseState == win32com.client.constants.eFocus1:
				return 'focus1'
			elif self.theLowDose.LowDoseState == win32com.client.constants.eFocus2:
				return 'focus2'
			elif self.theLowDose.LowDoseState == win32com.client.constants.eSearch:
				return 'search'
			else:
				return 'unknown'
		except pythoncom.com_error:
			return 'disabled'
		
	def setLowDoseMode(self, mode):
		if mode == 'exposure':
			self.theLowDose.LowDoseState = win32com.client.constants.eExposure
		elif mode == 'focus1':
			self.theLowDose.LowDoseState = win32com.client.constants.eFocus1
		elif mode == 'focus2':
			self.theLowDose.LowDoseState = win32com.client.constants.eFocus2
		elif mode == 'search':
			self.theLowDose.LowDoseState = win32com.client.constants.eSearch
		else:
			raise ValueError

		return 0
	
	def getDiffractionMode(self):
		if self.theScope.Projection.Mode == win32com.client.constants.pmImaging:
			return 'imaging'
		elif self.theScope.Projection.Mode == win32com.client.constants.pmDiffraction:
			return 'diffraction'
		else:
			raise SystemError
		
	def setDiffractionMode(self, mode):
		if mode == 'imaging':
			self.theScope.Projection.Mode = win32com.client.constants.pmImaging
		elif mode == 'diffraction':
			self.theScope.Projection.Mode = win32com.client.constants.pmDiffraction
		else:
			raise ValueError
		
		return 0

	def setShutter(self, state):
		if state == 'open':
			if self.theAda.OpenShutter != 0:
				raise RuntimeError('Open shutter failed')
		elif state == 'closed':
			if self.theAda.CloseShutter != 0:
				raise RuntimeError('Close shutter failed')
		else:
			raise ValueError("setShutter state must be 'open' or 'closed', not %s" % (state,))

	def getShutter(self):
		status = self.theAda.ShutterStatus
		if status:
			return 'closed'
		else:
			return 'open'

	def setExternalShutter(self, state):
		if state == 'connected':
			if self.theAda.ConnectExternalShutter != 0:
				raise RuntimeError('Connect shutter failed')
		elif state == 'disconnected':
			if self.theAda.DisconnectExternalShutter != 0:
				raise RuntimeError('Disconnect shutter failed')
		else:
			raise ValueError("setExternalShutter state must be 'connected' or 'disconnected', not %s" % (state,))
		
	def getExternalShutter(self):
		status = self.theAda.ExternalShutterStatus
		if status:
			return 'connected'
		else:
			return 'disconnected'

	def preFilmExposure(self, value):
		if not value:
			return

		if self.getFilmStock() < 1:
			raise RuntimeError('No film to take exposure')

		if self.theAda.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.theAda.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')

	def postFilmExposure(self, value):
		if not value:
			return

		if self.theAda.UnloadPlate != 0:
			raise RuntimeError('Unload plate failed')
#		if self.theAda.UpdateExposureNumber != 0:
#			raise RuntimeError('Update exposure number failed')

	def filmExposure(self, value):
		if not value:
			return

		'''
		if self.getFilmStock() < 1:
			raise RuntimeError('No film to take exposure')

		if self.theAda.CloseShutter != 0:
			raise RuntimeError('Close shutter (pre-exposure) failed')
		if self.theAda.DisconnectExternalShutter != 0:
			raise RuntimeError('Disconnect external shutter failed')
		if self.theAda.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.theAda.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')
		if self.theAda.OpenShutter != 0:
			raise RuntimeError('Open (pre-exposure) shutter failed')
		'''
		
		self.theScope.Camera.TakeExposure()
		
		'''
		if self.theAda.CloseShutter != 0:
			raise RuntimeError('Close shutter (post-exposure) failed')
		if self.theAda.UnloadPlate != 0:
			raise RuntimeError('Unload plate failed')
		if self.theAda.UpdateExposureNumber != 0:
			raise RuntimeError('Update exposure number failed')
		if self.theAda.ConnectExternalShutter != 0:
			raise RuntimeError('Connect external shutter failed')
		if self.theAda.OpenShutter != 0:
			raise RuntimeError('Open shutter (post-exposure) failed')
		'''

	def getMainScreen(self):
		if self.theAda.MainScreenStatus == 1:
			return 'up'
		else:
			return 'down'

	def getSmallScreen(self):
		if self.theScope.Camera.IsSmallScreenDown:
			return 'down'
		else:
			return 'up'

	def setMainScreen(self, mode):
		if mode == 'up':
			self.theAda.MainScreenUp
		elif mode == 'down':
			self.theAda.MainScreenDown
		else:
			raise ValueError

	def getHolderStatus(self):
		if self.theAda.SpecimenHolderInserted == adacom.constants.eInserted:
			return 'inserted'
		elif self.theAda.SpecimenHolderInserted == adacom.constants.eNotInserted:
			return 'not inserted'
		else:
			return 'unknown'

	def getHolderType(self):
		if self.theAda.CurrentSpecimenHolderName == u'No Specimen Holder':
			return 'no holder'
		elif self.theAda.CurrentSpecimenHolderName == u'Single Tilt':
			return 'single tilt'
		elif self.theAda.CurrentSpecimenHolderName == u'ST Cryo Holder':
			return 'cryo'
		else:
			return 'unknown holder'

	def setHolderType(self, holdertype):
		if holdertype == 'no holder':
			holderstr = u'No Specimen Holder'
		elif holdertype == 'single tilt':
			holderstr = u'Single Tilt'
		elif holdertype == 'cryo':
			holderstr = u'ST Cryo Holder'
		else:
			raise ValueError('invalid holder type specified')

		for i in [1,2,3]:
			if self.theAda.SpecimenHolderName(i) == holderstr:
				self.theAda.SetCurrentSpecimenHolder(i)
				return

		raise SystemError('no such holder available')

	def getStageStatus(self):
		if self.theAda.GonioLedStatus == adacom.constants.eOn:
			return 'busy'
		elif self.theAda.GonioLedStatus == adacom.constants.eOff:
			return 'ready'
		else:
			return 'unknown'

	def getTurboPump(self):
		if self.theAda.GetTmpStatus == adacom.constants.eOn:
			return 'on'
		elif self.theAda.GetTmpStatus == adacom.constants.eOff:
			return 'off'
		else:
			return 'unknown'

	def setTurboPump(self, mode):
		if mode == 'on':
			self.theAda.SetTmp(adacom.constants.eOn)
		elif mode == 'off':
			self.theAda.SetTmp(adacom.constants.eOff)
		else:
			raise ValueError

	def getColumnValves(self):
		if self.theScope.Vacuum.ColumnValvesOpen:
			return 'open'
		else:
			return 'closed'

	def setColumnValves(self, state):
		if state == 'closed':
			self.theScope.Vacuum.ColumnValvesOpen = 0
		elif state == 'open':
			self.theScope.Vacuum.ColumnValvesOpen = 1
		else:
			raise ValueError

	def getVacuumStatus(self):
		status = self.theScope.Vacuum.Status
		if status == win32com.client.constants.vsOff:
			return 'off'
		elif status == win32com.client.constants.vsCameraAir:
			return 'camera'
		elif status == win32com.client.constants.vsBusy:
			return 'busy'
		elif status == win32com.client.constants.vsReady:
			return 'ready'
		elif status == win32com.client.constants.vsUnknown:
			return 'unknown'
		elif status == win32com.client.constants.vsElse:
			return 'else'
		else:
			return 'unknown'

	def getColumnPressure(self):
		return float(self.theScope.Vacuum.Gauges('P4').Pressure)

	def getObjectiveExcitation(self):
		return float(self.theScope.Projection.ObjectiveExcitation)

	def getFocus(self):
		return float(self.theScope.Projection.Focus)

	def setFocus(self, value):
		self.theScope.Projection.Focus = value

	def getFilmStock(self):
		return self.theScope.Camera.Stock

	def getFilmExposureNumber(self):
		return self.theScope.Camera.ExposureNumber % 100000

	def setFilmExposureNumber(self, value):
		self.theScope.Camera.ExposureNumber = (self.theScope.Camera.ExposureNumber
																										/ 100000) * 100000 + value

	def getFilmExposureType(self):
		if self.theScope.Camera.ManualExposure:
			return 'manual'
		else:
			return 'automatic'

	def setFilmExposureType(self, value):
		if value ==  'manual':
			self.theScope.Camera.ManualExposure = True
		elif value == 'automatic':
			self.theScope.Camera.ManualExposure = False
		else:
			raise ValueError('Invalid value for film exposure type')

	def getFilmExposureTime(self):
		if self.theScope.Camera.ManualExposure:
			return self.getFilmManualExposureTime()
		else:
			return self.getFilmAutomaticExposureTime()

	def getFilmManualExposureTime(self):
		return float(self.theScope.Camera.ManualExposureTime)

	def setFilmManualExposureTime(self, value):
		self.theScope.Camera.ManualExposureTime = value

	def getFilmAutomaticExposureTime(self):
		return float(self.theScope.Camera.MeasuredExposureTime)

	def getFilmText(self):
		return str(self.theScope.Camera.FilmText)

	def setFilmText(self, value):
		self.theScope.Camera.FilmText = value

	def getFilmUserCode(self):
		return str(self.theScope.Camera.Usercode)

	def setFilmUserCode(self, value):
		self.theScope.Camera.Usercode = value

	def getFilmDateType(self):
		filmdatetype = self.theScope.Camera.PlateLabelDateType
		if filmdatetype == win32com.client.constants.dtNoDate:
			return 'no date'
		elif filmdatetype == win32com.client.constants.dtDDMMYY:
			return 'DD-MM-YY'
		elif filmdatetype == win32com.client.constants.dtMMDDYY:
			return 'MM/DD/YY'
		elif filmdatetype == win32com.client.constants.dtYYMMDD:
			return 'YY.MM.DD'
		else:
			return 'unknown'

	def setFilmDateType(self, value):
		if value == 'no date':
			self.theScope.Camera.PlateLabelDateType \
				= win32com.client.constants.dtNoDate
		elif value == 'DD-MM-YY':
			self.theScope.Camera.PlateLabelDateType \
				= win32com.client.constants.dtDDMMYY
		elif value == 'MM/DD/YY':
			self.theScope.Camera.PlateLabelDateType \
				= win32com.client.constants.dtMMDDYY
		elif value == 'YY.MM.DD':
			self.theScope.Camera.PlateLabelDateType \
				= win32com.client.constants.dtYYMMDD
		else:
			raise ValueError('Invalid film date type specified')

class TecnaiPolara(Tecnai):
	def __init__(self, magtable=polaramagtable):
		Tecnai.__init__(self, magtable)

