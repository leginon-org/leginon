#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import tem
import time
import sys

try:
	import pythoncom
	import win32com.client
	import winerror
except ImportError:
	pass

try:
	try:
		import tecnaicom
	except ImportError:
		from pyScope import tecnaicom
except ImportError:
	pass

try:
	try:
		import ldcom
	except ImportError:
		from pyScope import ldcom
except ImportError:
	pass

try:
	try:
		import adacom
	except ImportError:
		from pyScope import adacom
except ImportError:
	pass

class Tecnai(tem.TEM):
	name = 'Tecnai'
	magtable = [
		21, 28, 38, 56, 75, 97, 120, 170, 220, 330, 420, 550, 800, 1100, 1500, 2100,
		1700, 2500, 3500, 5000, 6500, 7800, 9600, 11500, 14500, 19000, 25000, 29000,
		50000, 62000, 80000, 100000, 150000, 200000, 240000, 280000, 390000, 490000,
		700000,
	]

	mainscreenmagtable = [
		18.5, 25, 34, 50, 66, 86, 105, 150, 195, 290, 370, 490, 710, 970, 1350,
		1850, 1500, 2200, 3100, 4400, 5800, 6900, 8500, 10000, 13000, 17000, 22000,
		25500, 44000, 55000, 71000, 89000, 135000, 175000, 210000, 250000, 350000,
		430000, 620000,
	]

	def __init__(self):
		tem.TEM.__init__(self)
		self.correctedstage = True
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

		try:
			self.tecnai = win32com.client.Dispatch('Tecnai.Instrument')
		except pythoncom.com_error, (hr, msg, exc, arg):
			raise RuntimeError('unable to initialize Tecnai interface, %s' % msg)

		try:
			self.lowdose = win32com.client.Dispatch('LDServer.LdSrv')
		except pythoncom.com_error, (hr, msg, exc, arg):
			raise RuntimeError('unable to initialize low dose interface, %s' % msg)

		try:
			self.exposure = win32com.client.Dispatch('adaExp.TAdaExp',
																					clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
		except pythoncom.com_error, (hr, msg, exc, arg):
			raise RuntimeError('unable to initialize exposure adapter, %s' % msg)

		self.magnifications = map(float, self.magtable)
		self.sortedmagnifications = list(self.magnifications)
		self.sortedmagnifications.sort()
		self.mainscreenmagnifications = map(float, self.mainscreenmagtable)

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
			'main screen magnification': {'get': 'getMainScreenMagnification'},
			'magnification index': {'get': 'getMagnificationIndex',
															'set': 'setMagnificationIndex'},
			'magnifications': {'get': 'getMagnifications'},
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
			'magnification': {'type': float, 'values': self.magnifications},
			'magnification index': {'type': int},
			'magnifications': {'type': list},
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
			'main screen position': ['small screen position'],
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
			self.tecnai.NormalizeAll()
		elif lens == 'objective':
			self.tecnai.Projection.Normalize(win32com.client.constants.pnmObjective)
		elif lens == 'projector':
			self.tecnai.Projection.Normalize(win32com.client.constants.pnmProjector)
		elif lens == 'allprojection':
			self.tecnai.Projection.Normalize(win32com.client.constants.pnmAll)
		elif lens == 'spotsize':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmSpotsize)
		elif lens == 'intensity':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmIntensity)
		elif lens == 'condenser':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmCondenser)
		elif lens == 'minicondenser':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmMiniCondenser)
		elif lens == 'objectivepole':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmObjectivePole)
		elif lens == 'allillumination':
			self.tecnai.Illumination.Normalize(win32com.client.constants.nmAll)
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
	
	def getHighTension(self):
		return int(self.tecnai.Gun.HTValue)
	
	def setHighTension(self, ht):
		self.tecnai.Gun.HTValue = ht
	
	def getIntensity(self):
		return float(self.tecnai.Illumination.Intensity)
	
	def setIntensity(self, intensity, relative = 'absolute'):
		if relative == 'relative':
			intensity += self.tecnai.Illumination.Intensity
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.tecnai.Illumination.Intensity = intensity

	def getDarkFieldMode(self):
		if self.tecnai.Illumination.DFMode == win32com.client.constants.dfOff:
			return 'off'
		elif self.tecnai.Illumination.DFMode == win32com.client.constants.dfCartesian:
			return 'cartesian'
		elif self.tecnai.Illumination.DFMode == win32com.client.constants.dfConical:
			return 'conical'
		else:
			raise SystemError
		
	def setDarkFieldMode(self, mode):
		if mode == 'off':
			self.tecnai.Illumination.DFMode = win32com.client.constants.dfOff
		elif mode == 'cartesian':
			self.tecnai.Illumination.DFMode = win32com.client.constants.dfCartesian
		elif mode == 'conical':
			self.tecnai.Illumination.DFMode = win32com.client.constants.dfConical
		else:
			raise ValueError
	
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
		value['condenser']['x'] = \
			float(self.tecnai.Illumination.CondenserStigmator.X)
		value['condenser']['y'] = \
			float(self.tecnai.Illumination.CondenserStigmator.Y)
		value['objective']['x'] = \
			float(self.tecnai.Projection.ObjectiveStigmator.X)
		value['objective']['y'] = \
			float(self.tecnai.Projection.ObjectiveStigmator.Y)
		value['diffraction']['x'] = \
			float(self.tecnai.Projection.DiffractionStigmator.X)
		value['diffraction']['y'] = \
			float(self.tecnai.Projection.DiffractionStigmator.Y)

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
		value['x'] = float(self.tecnai.Illumination.RotationCenter.X)
		value['y'] = float(self.tecnai.Illumination.RotationCenter.Y)

		return value
	
	def setBeamTilt(self, vector, relative = 'absolute'):
		if relative == 'relative':
			try:
				vector['x'] += self.tecnai.Illumination.RotationCenter.X
			except KeyError:
				pass
			try:
				vector['y'] += self.tecnai.Illumination.RotationCenter.Y
			except KeyError:
				pass
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		vec = self.tecnai.Illumination.RotationCenter
		try:
			vec.X = vector['x']
		except KeyError:
			pass
		try:
			vec.Y = vector['y']
		except KeyError:
			pass
		self.tecnai.Illumination.RotationCenter = vec
	
	def getBeamShift(self):
		value = {'x': None, 'y': None}
		value['x'] = float(self.tecnai.Illumination.Shift.X)
		value['y'] = float(self.tecnai.Illumination.Shift.Y)

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
		value['x'] = float(self.tecnai.Projection.ImageBeamShift.X)
		value['y'] = float(self.tecnai.Projection.ImageBeamShift.Y)
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
		if relative == 'relative':
			defocus += self.tecnai.Projection.Defocus
		elif relative == 'absolute':
			pass
		else:
			raise ValueError
		
		self.tecnai.Projection.Defocus = defocus
	
	def resetDefocus(self, value):
		if not value:
			return
		self.tecnai.Projection.ResetDefocus()

	def getResetDefocus(self):
		return False
	
	def getMagnification(self):
		index = self.tecnai.Projection.MagnificationIndex
		if index < 1:
			index = 1
		return float(self.magnifications[index - 1])

	def getMainScreenMagnification(self):
		index = self.tecnai.Projection.MagnificationIndex
		if index < 1:
			index = 1
		return float(self.mainscreenmagnifications[index - 1])

	def setMagnification(self, mag):
		try:
			mag = float(mag)
		except:
			raise TypeError
		prevmag = self.sortedmagnifications[0]
	
		for m in self.sortedmagnifications:
			if m > mag:
				break
			prevmag = m
			
		index = self.magnifications.index(prevmag) + 1
		self.tecnai.Projection.MagnificationIndex = index
		return

	def getMagnificationIndex(self):
		return self.tecnai.Projection.MagnificationIndex - 1

	def setMagnificationIndex(self, value):
		self.tecnai.Projection.MagnificationIndex  = value + 1

	def getMagnifications(self):
		return self.magnifications
	
	def getStagePosition(self):
		value = {'x': None, 'y': None, 'z': None, 'a': None}
		if(self.tecnai.Stage.Holder == win32com.client.constants.hoDoubleTilt):
			value['b'] = None
		value['x'] = float(self.tecnai.Stage.Position.X)
		value['y'] = float(self.tecnai.Stage.Position.Y)
		value['z'] = float(self.tecnai.Stage.Position.Z)
		value['a'] = float(self.tecnai.Stage.Position.A)
		if 'b' in value:
			value['b'] = float(self.tecnai.Stage.Position.B)
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
			setattr(pos, key.upper(), value)
			axes |= getattr(win32com.client.constants, 'axis' + key.upper())

		try:
			self.tecnai.Stage.Goto(pos, axes)
		except pythoncom.com_error, (hr, msg, exc, arg):
			print 'Stage.Goto failed with error %d: %s' % (hr, msg)
			if exc is None:
				print 'No extended error information, assuming stage limit was hit'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					print 'No extended error information, assuming stage limit was hit'
				else:
					# ?
					pass

#		for key in position:
#			while abs(getattr(self.tecnai.Stage.Position, key.upper())
#								- getattr(pos, key.upper())) > tolerance:
#				time.sleep(polltime)
	
	def getLowDose(self):
		try:
			if (self.lowdose.IsInitialized == 1) and (self.lowdose.LowDoseActive == win32com.client.constants.IsOn):
				return 'on'
			else:
				return 'off'
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				return 'disabled'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					return 'disabled'
				else:
					# ?
					pass
 
	def setLowDose(self, ld):
		try:
			if ld == 'off' :
				self.lowdose.LowDoseActive = win32com.client.constants.IsOff
			elif ld == 'on':
				if self.lowdose.IsInitialized == 0:
					raise RuntimeError('Low dose is not initialized')
				else:
					self.lowdose.LowDoseActive = win32com.client.constants.IsOn
			else:
				raise ValueError
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				raise RuntimeError('Low dose is not enabled')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					raise RuntimeError('Low dose is not enabled')
				else:
					# ?
					pass

	def getLowDoseMode(self):
		try:
			if self.lowdose.LowDoseState == win32com.client.constants.eExposure:
				return 'exposure'
			elif self.lowdose.LowDoseState == win32com.client.constants.eFocus1:
				return 'focus1'
			elif self.lowdose.LowDoseState == win32com.client.constants.eFocus2:
				return 'focus2'
			elif self.lowdose.LowDoseState == win32com.client.constants.eSearch:
				return 'search'
			else:
				return 'unknown'
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				return 'disabled'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					return 'disabled'
				else:
					# ?
					pass
		
	def setLowDoseMode(self, mode):
		try:
			if mode == 'exposure':
				self.lowdose.LowDoseState = win32com.client.constants.eExposure
			elif mode == 'focus1':
				self.lowdose.LowDoseState = win32com.client.constants.eFocus1
			elif mode == 'focus2':
				self.lowdose.LowDoseState = win32com.client.constants.eFocus2
			elif mode == 'search':
				self.lowdose.LowDoseState = win32com.client.constants.eSearch
			else:
				raise ValueError
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disenabled
				raise RuntimeError('Low dose is not enabled')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disenabled
					raise RuntimeError('Low dose is not enabled')
				else:
					# ?
					pass
	
	def getDiffractionMode(self):
		if self.tecnai.Projection.Mode == win32com.client.constants.pmImaging:
			return 'imaging'
		elif self.tecnai.Projection.Mode == win32com.client.constants.pmDiffraction:
			return 'diffraction'
		else:
			raise SystemError
		
	def setDiffractionMode(self, mode):
		if mode == 'imaging':
			self.tecnai.Projection.Mode = win32com.client.constants.pmImaging
		elif mode == 'diffraction':
			self.tecnai.Projection.Mode = win32com.client.constants.pmDiffraction
		else:
			raise ValueError
		
		return 0

	def setShutter(self, state):
		if state == 'open':
			if self.exposure.OpenShutter != 0:
				raise RuntimeError('Open shutter failed')
		elif state == 'closed':
			if self.exposure.CloseShutter != 0:
				raise RuntimeError('Close shutter failed')
		else:
			raise ValueError('Invalid value for setShutter \'%s\'' % (state,))

	def getShutter(self):
		status = self.exposure.ShutterStatus
		if status:
			return 'closed'
		else:
			return 'open'

	def setExternalShutter(self, state):
		if state == 'connected':
			if self.exposure.ConnectExternalShutter != 0:
				raise RuntimeError('Connect shutter failed')
		elif state == 'disconnected':
			if self.exposure.DisconnectExternalShutter != 0:
				raise RuntimeError('Disconnect shutter failed')
		else:
			raise ValueError('Invalid value for setExternalShutter \'%s\'' % (state,))
		
	def getExternalShutter(self):
		status = self.exposure.ExternalShutterStatus
		if status:
			return 'connected'
		else:
			return 'disconnected'

	def preFilmExposure(self, value):
		if not value:
			return

		if self.getFilmStock() < 1:
			raise RuntimeError('No film to take exposure')

		if self.exposure.LoadPlate != 0:
			raise RuntimeError('Load plate failed')
		if self.exposure.ExposePlateLabel != 0:
			raise RuntimeError('Expose plate label failed')

	def postFilmExposure(self, value):
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

	def getMainScreen(self):
		timeout = 5.0
		sleeptime = 0.05
		while (self.tecnai.Camera.MainScreen
						== win32com.client.constants.spUnknown):
			time.sleep(sleeptime)
			if self.tecnai.Camera.MainScreen != win32com.client.constants.spUnknown:
				break
			timeout -= sleeptime
			if timeout <= 0.0:
				return 'unknown'
		if self.tecnai.Camera.MainScreen == win32com.client.constants.spUp:
			return 'up'
		elif self.tecnai.Camera.MainScreen == win32com.client.constants.spDown:
			return 'down'
		else:
			return 'unknown'

	def getSmallScreen(self):
		if self.tecnai.Camera.IsSmallScreenDown:
			return 'down'
		else:
			return 'up'

	def setMainScreen(self, mode):
		if mode == 'up':
			self.tecnai.Camera.MainScreen = win32com.client.constants.spUp
		elif mode == 'down':
			self.tecnai.Camera.MainScreen = win32com.client.constants.spDown
		else:
			raise ValueError

	def getHolderStatus(self):
		if self.exposure.SpecimenHolderInserted == adacom.constants.eInserted:
			return 'inserted'
		elif self.exposure.SpecimenHolderInserted == adacom.constants.eNotInserted:
			return 'not inserted'
		else:
			return 'unknown'

	def getHolderType(self):
		if self.exposure.CurrentSpecimenHolderName == u'No Specimen Holder':
			return 'no holder'
		elif self.exposure.CurrentSpecimenHolderName == u'Single Tilt':
			return 'single tilt'
		elif self.exposure.CurrentSpecimenHolderName == u'ST Cryo Holder':
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
			if self.exposure.SpecimenHolderName(i) == holderstr:
				self.exposure.SetCurrentSpecimenHolder(i)
				return

		raise SystemError('no such holder available')

	def getStageStatus(self):
		if self.exposure.GonioLedStatus == adacom.constants.eOn:
			return 'busy'
		elif self.exposure.GonioLedStatus == adacom.constants.eOff:
			return 'ready'
		else:
			return 'unknown'

	def getTurboPump(self):
		if self.exposure.GetTmpStatus == adacom.constants.eOn:
			return 'on'
		elif self.exposure.GetTmpStatus == adacom.constants.eOff:
			return 'off'
		else:
			return 'unknown'

	def setTurboPump(self, mode):
		if mode == 'on':
			self.exposure.SetTmp(adacom.constants.eOn)
		elif mode == 'off':
			self.exposure.SetTmp(adacom.constants.eOff)
		else:
			raise ValueError

	def getColumnValves(self):
		if self.tecnai.Vacuum.ColumnValvesOpen:
			return 'open'
		else:
			return 'closed'

	def setColumnValves(self, state):
		if state == 'closed':
			self.tecnai.Vacuum.ColumnValvesOpen = 0
		elif state == 'open':
			self.tecnai.Vacuum.ColumnValvesOpen = 1
		else:
			raise ValueError

	def getVacuumStatus(self):
		status = self.tecnai.Vacuum.Status
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
		return float(self.tecnai.Vacuum.Gauges('P4').Pressure)

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

	def getFilmDateType(self):
		filmdatetype = self.tecnai.Camera.PlateLabelDateType
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
			self.tecnai.Camera.PlateLabelDateType \
				= win32com.client.constants.dtNoDate
		elif value == 'DD-MM-YY':
			self.tecnai.Camera.PlateLabelDateType \
				= win32com.client.constants.dtDDMMYY
		elif value == 'MM/DD/YY':
			self.tecnai.Camera.PlateLabelDateType \
				= win32com.client.constants.dtMMDDYY
		elif value == 'YY.MM.DD':
			self.tecnai.Camera.PlateLabelDateType \
				= win32com.client.constants.dtYYMMDD
		else:
			raise ValueError('Invalid film date type specified')

class TecnaiPolara(Tecnai):
	name = 'Tecnai Polara'
	magtable = [
		62, 76, 100, 125, 175, 220, 280, 360, 480, 650, 790, 990, 1200, 1800, 2300,
		2950, 3000, 4500, 5600, 9300, 13500, 18000, 22500, 27500, 34000, 41000,
		50000, 61000, 77000, 95000, 115000, 160000, 200000, 235000, 310000, 400000,
		470000, 630000, 800000,
	]

	mainscreenmagtable = [
		54, 67, 91, 110, 155, 195, 250, 320, 430, 570, 700, 880, 1100, 1600, 2050,
		2600, 2650, 3900, 5000, 8200, 12000, 15500, 20000, 24500, 29500, 36000,
		44000, 54000, 68000, 84000, 105000, 140000, 175000, 210000, 275000, 350000,
		420000, 560000, 710000
	]

