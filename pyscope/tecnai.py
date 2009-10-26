# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import tem
import time
import sys
try:
	import nidaq
except:
	nidaq = None
use_nidaq = False

try:
	import pythoncom
	import win32com.client
	import winerror
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
		adacom = None
except ImportError:
	pass

# if a stage position movement is less than the following, then ignore it
minimum_stage = {
	'x': 5e-8,
	'y': 5e-8,
	'z': 5e-8,
	'a': 6e-5,
	'b': 6e-5,
}

class MagnificationsUninitialized(Exception):
	pass

class Tecnai(tem.TEM):
	name = 'Tecnai'
	def __init__(self):
		tem.TEM.__init__(self)
		self.correctedstage = True
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

		try:
			self.tecnai = win32com.client.Dispatch('Tecnai.Instrument')
		except pythoncom.com_error, (hr, msg, exc, arg):
			raise RuntimeError('unable to initialize Tecnai interface, %s' % msg)

		try:
			self.tom = win32com.client.Dispatch('TEM.Instrument.1')
		except pythoncom.com_error, (hr, msg, exc, arg):
			print 'unable to initialize TOM Moniker interface, %s' % msg
                        self.tom = None

		try:
			self.lowdose = win32com.client.Dispatch('LDServer.LdSrv')
		except pythoncom.com_error, (hr, msg, exc, arg):
			print 'unable to initialize low dose interface, %s' % msg
			self.lowdose = None

		try:
			self.exposure = win32com.client.Dispatch('adaExp.TAdaExp',
																					clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
		except:
			self.exposure = None

		self.magnifications = []
		self.mainscreenscale = 44000.0 / 50000.0

	def getMagnificationsInitialized(self):
		if self.magnifications:
			return True
		else:
			return False

	def setCorrectedStagePosition(self, value):
		self.correctedstage = bool(value)
		return self.correctedstage

	def getCorrectedStagePosition(self):
		return self.correctedstage

	def checkStagePosition(self, position):
		current = self.getStagePosition()
		bigenough = {}
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

	def getHighTensionStates(self):
		return ['off', 'on', 'disabled']

	def getHighTensionState(self):
		state = self.tecnai.Gun.HTState
		if state == win32com.client.constants.htOff:
			return 'off'
		elif state == win32com.client.constants.htOn:
			return 'on'
		elif state == win32com.client.constants.htDisabled:
			return 'disabled'
		else:
			raise RuntimeError('unknown high tension state')

	def getHighTension(self):
		return float(self.tecnai.Gun.HTValue)
	
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
	
	def resetDefocus(self):
		self.tecnai.Projection.ResetDefocus()

	def getMagnification(self, index=None):
		if index is None:
			return int(round(self.tecnai.Projection.Magnification))
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications[index]
			except IndexError:
				raise ValueError('invalid magnification index')

	def getMainScreenMagnification(self):
		return int(round(self.tecnai.Projection.Magnification*self.mainscreenscale))

	def getMainScreenScale(self):
		return self.mainscreenscale

	def setMainScreenScale(self, mainscreenscale):
		self.mainscreenscale = mainscreenscale

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
	
		try:
			index = self.magnifications.index(mag)
		except ValueError:
			raise ValueError('invalid magnification')

		self.setMagnificationIndex(index)
		return

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			return self.tecnai.Projection.MagnificationIndex - 1
		elif not self.getMagnificationsInitialized():
			raise MagnificationsUninitialized
		else:
			try:
				return self.magnifications.index(magnification)
			except IndexError:
				raise ValueError('invalid magnification')

	def setMagnificationIndex(self, value):
		self.tecnai.Projection.MagnificationIndex = value + 1

	def getMagnifications(self):
		return self.magnifications

	def setMagnifications(self, magnifications):
		self.magnifications = magnifications

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
			magnifications.append(self.getMagnification())
			previousindex = index
			index += 1
		self.setMagnifications(magnifications)
		self.setMagnificationIndex(savedindex)
	
	def getStagePosition(self):
		value = {}
		value['x'] = float(self.tecnai.Stage.Position.X)
		value['y'] = float(self.tecnai.Stage.Position.Y)
		value['z'] = float(self.tecnai.Stage.Position.Z)
		value['a'] = float(self.tecnai.Stage.Position.A)
		if use_nidaq:
			value['b'] = nidaq.getBeta() * 3.14159 / 180.0
		else:
			try:
				value['b'] = float(self.tecnai.Stage.Position.B)
			except:
				pass
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
			if use_nidaq and key == 'b':
				deg = value / 3.14159 * 180.0
				nidaq.setBeta(deg)
				continue
			setattr(pos, key.upper(), value)
			axes |= getattr(win32com.client.constants, 'axis' + key.upper())

		if axes == 0:
			return
		try:
			self.tecnai.Stage.Goto(pos, axes)
		except pythoncom.com_error, (hr, msg, exc, arg):
			#print 'Stage.Goto failed with error %d: %s' % (hr, msg)
			if exc is None:
				raise ValueError('no extended error information, assuming stage limit was hit')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					raise ValueError('no extended error information, assuming stage limit was hit')
				else:
					raise RuntimeError(text)

#		for key in position:
#			while abs(getattr(self.tecnai.Stage.Position, key.upper())
#								- getattr(pos, key.upper())) > tolerance:
#				time.sleep(polltime)
	
	def getLowDoseStates(self):
		return ['on', 'off', 'disabled']

	def getLowDose(self):
		try:
			if (self.lowdose.IsInitialized == 1) and (self.lowdose.LowDoseActive == win32com.client.constants.IsOn):
				return 'on'
			else:
				return 'off'
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				# No extended error information, assuming low dose is disabled
				return 'disabled'
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					# No extended error information, assuming low dose is disabled
					return 'disabled'
				else:
					raise RuntimeError(text)
 
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
					raise RuntimerError(text)

	def getLowDoseModes(self):
		return ['exposure', 'focus1', 'focus2', 'search', 'unknown', 'disabled']

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
					raise RuntimerError(text)
		
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
					raise RuntimerError(text)
	
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

	def getShutterPositions(self):
		return ['open', 'closed']

	def setShutter(self, state):
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

	def getSmallScreenPosition(self):
		if self.tecnai.Camera.IsSmallScreenDown:
			return 'down'
		else:
			return 'up'

	def setMainScreenPosition(self, mode):
		if mode == 'up':
			self.tecnai.Camera.MainScreen = win32com.client.constants.spUp
		elif mode == 'down':
			self.tecnai.Camera.MainScreen = win32com.client.constants.spDown
		else:
			raise ValueError
		time.sleep(2)

	def getHolderStatus(self):
		if adacom is None:
			raise RuntimeError('getHolderStatus requires adaExp')
		if self.exposure.SpecimenHolderInserted == adacom.constants.eInserted:
			return 'inserted'
		elif self.exposure.SpecimenHolderInserted == adacom.constants.eNotInserted:
			return 'not inserted'
		else:
			return 'unknown'

	def getHolderTypes(self):
		return ['no holder', 'single tilt', 'cryo', 'unknown']

	def getHolderType(self):
		if self.exposure is None:
			raise RuntimeError('getHolderType requires adaExp')
		if self.exposure.CurrentSpecimenHolderName == u'No Specimen Holder':
			return 'no holder'
		elif self.exposure.CurrentSpecimenHolderName == u'Single Tilt':
			return 'single tilt'
		elif self.exposure.CurrentSpecimenHolderName == u'ST Cryo Holder':
			return 'cryo'
		else:
			return 'unknown'

	def setHolderType(self, holdertype):
		if self.exposure is None:
			raise RuntimeError('setHolderType requires adaExp')
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
		if adacom is None:
			raise RuntimeError('getStageStatus requires adaExp')
		if self.exposure.GonioLedStatus == adacom.constants.eOn:
			return 'busy'
		elif self.exposure.GonioLedStatus == adacom.constants.eOff:
			return 'ready'
		else:
			return 'unknown'

	def getTurboPump(self):
		if adacom is None:
			raise RuntimeError('getTurboPump requires adaExp')
		if self.exposure.GetTmpStatus == adacom.constants.eOn:
			return 'on'
		elif self.exposure.GetTmpStatus == adacom.constants.eOff:
			return 'off'
		else:
			return 'unknown'

	def setTurboPump(self, mode):
		if adacom is None:
			raise RuntimeError('setTurboPump requires adaExp')
		if mode == 'on':
			self.exposure.SetTmp(adacom.constants.eOn)
		elif mode == 'off':
			self.exposure.SetTmp(adacom.constants.eOff)
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

	def runBufferCycle(self):
		try:
			self.tecnai.Vacuum.RunBufferCycle()
		except pythoncom.com_error, (hr, msg, exc, arg):
			if exc is None:
				raise RuntimeError('no extended error information')
			else:
				wcode, source, text, helpFile, helpId, scode = exc
				if winerror.SUCCEEDED(wcode) and text is None:
					raise RuntimeError('no extended error information')
				else:
					raise RuntimeError(text)

	def setEmission(self, value):
		self.tom.Gun.Emission = value

	def getEmission(self):
		return self.tom.Gun.Emission
