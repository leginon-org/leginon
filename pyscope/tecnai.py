import scope
import sys
	
if sys.platform != 'win32':
	class tecnai(scope.Scope):
		pass
else:
	sys.coinit_flags = 0
	import pythoncom
	import win32com.client
	import pywintypes
#	import tecnaicom
	import ldcom
	import adacom
	import time
	
	class Tecnai(scope.Scope):
		def cmpmags(self, x, y):
			key = self.cmpmags_status
			if x[key] < y[key]: 
				return -1
			elif x[key] == y[key]: 
				return 0
			elif x[key] > y[key]: 
				 return 1
			
		def __init__(self):
			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
			self.theScope = win32com.client.Dispatch("Tecnai.Instrument")		
			self.theLowDose = win32com.client.Dispatch("LDServer.LdSrv")
			self.theAda = win32com.client.Dispatch("adaExp.TAdaExp",
																					clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
			# this was a quick way of doing things, needs to be redone
			self.magTable = [{'index': 1, 'up': 21, 'down': 18.5},
							 {'index': 2, 'up': 28, 'down': 25},
							 {'index': 3, 'up': 38, 'down': 34},
							 {'index': 4, 'up': 56, 'down': 50},
							 {'index': 5, 'up': 75, 'down': 66},
							 {'index': 6, 'up': 97, 'down': 86},
							 {'index': 7, 'up': 120, 'down': 105},
							 {'index': 8, 'up': 170, 'down': 150},
							 {'index': 9, 'up': 220, 'down': 195},
							 {'index': 10, 'up': 330, 'down': 290},
							 {'index': 11, 'up': 420, 'down': 370},
							 {'index': 12, 'up': 550, 'down': 490},
							 {'index': 13, 'up': 800, 'down': 710},
							 {'index': 14, 'up': 1100, 'down': 970},
							 {'index': 15, 'up': 1500, 'down': 1350},
							 {'index': 16, 'up': 2100, 'down': 1850},
							 {'index': 17, 'up': 1700, 'down': 1500},
							 {'index': 18, 'up': 2500, 'down': 2200},
							 {'index': 19, 'up': 3500, 'down': 3100},
							 {'index': 20, 'up': 5000, 'down': 4400},
							 {'index': 21, 'up': 6500, 'down': 5800},
							 {'index': 22, 'up': 7800, 'down': 6900},
							 {'index': 23, 'up': 9600, 'down': 8500},
							 {'index': 24, 'up': 11500, 'down': 10000},
							 {'index': 25, 'up': 14500, 'down': 13000},
							 {'index': 26, 'up': 19000, 'down': 17000},
							 {'index': 27, 'up': 25000, 'down': 22000},
							 {'index': 28, 'up': 29000, 'down': 25500},
							 {'index': 29, 'up': 50000, 'down': 44000},
							 {'index': 30, 'up': 62000, 'down': 55000},
							 {'index': 31, 'up': 80000, 'down': 71000},
							 {'index': 32, 'up': 100000, 'down': 89000},
							 {'index': 33, 'up': 150000, 'down': 135000},
							 {'index': 34, 'up': 200000, 'down': 175000},
							 {'index': 35, 'up': 240000, 'down': 210000},
							 {'index': 36, 'up': 280000, 'down': 250000},
							 {'index': 37, 'up': 390000, 'down': 350000},
							 {'index': 38, 'up': 490000, 'down': 430000},
							 {'index': 39, 'up': 700000, 'down': 620000}]
	
	
		def normalizeLens(self, lens = "all"):
			if lens == "all":
				self.theScope.NormalizeAll()
			elif lens == "objective":
				self.theScope.Projection.Normalize(win32com.client.constants.pnmObjective)
			elif lens == "projector":
				self.theScope.Projection.Normalize(win32com.client.constants.pnmProjector)
			elif lens == "allprojection":
				self.theScope.Projection.Normalize(win32com.client.constants.pnmAll)
			elif lens == "spotsize":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmSpotsize)
			elif lens == "intensity":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmIntensity)
			elif lens == "condenser":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmCondenser)
			elif lens == "minicondenser":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmMiniCondenser)
			elif lens == "objectivepole":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmObjectivePole)
			elif lens == "allillumination":
				self.theScope.Illumination.Normalize(win32com.client.constants.nmAll)
			else:
				raise ValueError
	
			return 0
	
		def getScreenCurrent(self, novalue=False):
			if novalue:
				return float
			return float(self.theScope.Camera.ScreenCurrent)
		
		def getGunTilt(self, novalue=False):
			value = {'x': None, 'y': None}

			if novalue:
				value['x'] = float
				value['y'] = float
			else:
				value['x'] = float(self.theScope.Gun.Tilt.X)
				value['y'] = float(self.theScope.Gun.Tilt.Y)

			return value
		
		def setGunTilt(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Gun.Tilt.X
				except KeyError:
					pass
				try:
					vector["y"] += self.theScope.Gun.Tilt.Y
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			vec = self.theScope.Gun.Tilt
			try:
				vec.X = vector["x"]
			except KeyError:
				pass
			try:
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Gun.Tilt = vec
			return 0
		
		def getGunShift(self, novalue=False):
			value = {'x': None, 'y': None}

			if novalue:
				value['x'] = float
				value['y'] = float
			else:
				value['x'] = self.theScope.Gun.Shift.X
				value['y'] = self.theScope.Gun.Shift.Y

			return value
		
		def setGunShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Gun.Shift.X
				except KeyError:
					pass
				try:
					vector["y"] += self.theScope.Gun.Shift.Y
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			vec = self.theScope.Gun.Shift
			try:
				vec.X = vector["x"]
			except KeyError:
				pass
			try:
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Gun.Shift = vec
			return 0
		
		def getHighTension(self, novalue=False):
			if novalue:
				return int
			return int(self.theScope.Gun.HTValue)
		
		def setHighTension(self, ht):
			self.theScope.Gun.HTValue = ht
			return 0
		
		def getIntensity(self, novalue=False):
			if novalue:
				return float
			return float(self.theScope.Illumination.Intensity)
		
		def setIntensity(self, intensity, relative = "absolute"):
			if relative == "relative":
				intensity += self.theScope.Illumination.Intensity
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			self.theScope.Illumination.Intensity = intensity
			return 0
	
		def getDarkFieldMode(self, novalue=False):
			if novalue:
				return str
			if self.theScope.Illumination.DFMode == win32com.client.constants.dfOff:
				return "off"
			elif self.theScope.Illumination.DFMode == win32com.client.constants.dfCartesian:
				return "cartesian"
			elif self.theScope.Illumination.DFMode == win32com.client.constants.dfConical:
				return "conical"
			else:
				raise SystemError
			
		def setDarkFieldMode(self, mode):
			if mode == "off":
				self.theScope.Illumination.DFMode = win32com.client.constants.dfOff
			elif mode == "cartesian":
				self.theScope.Illumination.DFMode = win32com.client.constants.dfCartesian
			elif mode == "conical":
				self.theScope.Illumination.DFMode = win32com.client.constants.dfConical
			else:
				raise ValueError
	
			return 0
		
		def getBeamBlank(self, novalue=False):
			if novalue:
				return str
			if self.theScope.Illumination.BeamBlanked == 0:
				return "off"
			elif self.theScope.Illumination.BeamBlanked == 1:
				return "on"
			else:
				raise SystemError
			
		def setBeamBlank(self, bb):
			if bb == "off" :
				self.theScope.Illumination.BeamBlanked = 0
			elif bb == "on":
				self.theScope.Illumination.BeamBlanked = 1
			else:
				raise ValueError
			
			return 0
		
		def getStigmator(self, novalue=False):
			value = {'condenser': {'x': None, 'y': None},
								'objective': {'x': None, 'y': None},
								'diffraction': {'x': None, 'y': None}}
			if novalue:
				value['condenser']['x'] = float
				value['condenser']['y'] = float
				value['objective']['x'] = float
				value['objective']['y'] = float
				value['diffraction']['x'] = float
				value['diffraction']['y'] = float
			else:
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
			
		def setStigmator(self, stigs, relative = "absolute"):
			for key in stigs.keys():
				if key == "condenser":
					stigmator = self.theScope.Illumination.CondenserStigmator
				elif key == "objective":
					stigmator = self.theScope.Projection.ObjectiveStigmator
				elif key == "diffraction":
					stigmator = self.theScope.Projection.DiffractionStigmator
				else:
					raise ValueError
		   
				if relative == "relative":
					try:
						stigs[key]["x"] += stigmator.X
					except KeyError:
						pass
					try:
						stigs[key]["y"] += stigmator.Y
					except KeyError:
						pass
				elif relative == "absolute":
					pass
				else:
					raise ValueError
	
				try:
					stigmator.X = stigs[key]["x"]
					stigmator.Y = stigs[key]["y"]
				except KeyError:
						pass
	
				if key == "condenser":
					self.theScope.Illumination.CondenserStigmator = stigmator
				elif key == "objective":
					self.theScope.Projection.ObjectiveStigmator = stigmator
				elif key == "diffraction":
					self.theScope.Projection.DiffractionStigmator = stigmator
				else:
					raise ValueError
	
			return 0
		
		def getSpotSize(self, novalue=False):
			if novalue:
				return int
			return int(self.theScope.Illumination.SpotsizeIndex)
		
		def setSpotSize(self, ss, relative = "absolute"):
			if relative == "relative":
				ss += self.theScope.Illumination.SpotsizeIndex
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			self.theScope.Illumination.SpotsizeIndex = ss
			return 0
		
		def getBeamTilt(self, novalue=False):
			value = {'x': None, 'y': None}

			if novalue:
				value['x'] = float
				value['y'] = float
			else:
				value['x'] = float(self.theScope.Illumination.RotationCenter.X)
				value['y'] = float(self.theScope.Illumination.RotationCenter.Y)

			return value
		
		def setBeamTilt(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Illumination.RotationCenter.X
				except KeyError:
					pass
				try:
					vector["y"] += self.theScope.Illumination.RotationCenter.Y
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			vec = self.theScope.Illumination.RotationCenter
			try:
				vec.X = vector["x"]
			except KeyError:
				pass
			try:
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Illumination.RotationCenter = vec
			return 0
		
		def getBeamShift(self, novalue=False):
			value = {'x': None, 'y': None}

			if novalue:
				value['x'] = float
				value['y'] = float
			else:
				value['x'] = float(self.theScope.Illumination.Shift.X)
				value['y'] = float(self.theScope.Illumination.Shift.Y)

			return value
	
		def setBeamShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Illumination.Shift.X
				except KeyError:
					pass
				try:
					vector["y"] += self.theScope.Illumination.Shift.Y
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			vec = self.theScope.Illumination.Shift
			try:
				vec.X = vector["x"]
			except KeyError:
				pass
			try:
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Illumination.Shift = vec
			return 0
		
		def getImageShift(self, novalue=False):
			value = {'x': None, 'y': None}

			if novalue:
				value['x'] = float
				value['y'] = float
			else:
				value['x'] = float(self.theScope.Projection.ImageBeamShift.X)
				value['y'] = float(self.theScope.Projection.ImageBeamShift.Y)

			return value
		
		def setImageShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Projection.ImageBeamShift.X
				except KeyError:
					pass
				try:
					vector["y"] += self.theScope.Projection.ImageBeamShift.Y
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			vec = self.theScope.Projection.ImageBeamShift
			try:
				vec.X = vector["x"]
			except KeyError:
				pass
			try:
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Projection.ImageBeamShift = vec
			return 0
		
		def getDefocus(self, novalue=False):
			if novalue:
				return float
			return float(self.theScope.Projection.Defocus)
		
		def setDefocus(self, defocus, relative = "absolute"):
			if relative == "relative":
				defocus += self.theScope.Projection.Defocus
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			self.theScope.Projection.Defocus = defocus
			return 0
		
		def resetDefocus(self):
			self.theScope.Projection.ResetDefocus()
			return 0
		
		def getMagnification(self, novalue=False):
			if novalue:
				return float
			if self.theScope.Camera.MainScreen == win32com.client.constants.spUp:
				key = "up"
			elif self.theScope.Camera.MainScreen == win32com.client.constants.spDown:
				key = "down"
			else:   # perhaps spUnknown
				raise SystemError
	
			magindex = self.theScope.Projection.MagnificationIndex
	
			for mag in self.magTable:
				if mag['index'] == magindex:
					return float(mag[key])
	
			raise SystemError			
	
		def setMagnification(self, mag):
			if self.theScope.Camera.MainScreen == win32com.client.constants.spUp:
				key = "up"
			elif self.theScope.Camera.MainScreen == win32com.client.constants.spDown:
				key = "down"
			else:   # perhaps spUnknown
				raise SystemError
	
			self.cmpmags_status = key
	
			self.magTable.sort(self.cmpmags)
	
			prevmag = self.magTable[0]
			
			for imag in self.magTable:
				if imag[key] > mag:
					 self.theScope.Projection.MagnificationIndex = prevmag['index']
					 return 0
				prevmag = imag
				
			self.theScope.Projection.MagnificationIndex = prevmag['index']
			return 0
		
		def getStagePosition(self, novalue=False):
			value = {'x': None, 'y': None, 'z': None, 'a': None}

			if(self.theScope.Stage.Holder == win32com.client.constants.hoDoubleTilt):
				value['b'] = None

			if novalue:
				value['x'] = float
				value['y'] = float
				value['z'] = float
				value['a'] = float
				if 'b' in value:
					value['b'] = float
			else:
				value['x'] = float(self.theScope.Stage.Position.X)
				value['y'] = float(self.theScope.Stage.Position.Y)
				value['z'] = float(self.theScope.Stage.Position.Z)
				value['a'] = float(self.theScope.Stage.Position.A)
				if 'b' in value:
					value['b'] = float(self.theScope.Stage.Position.B)

			return value

		def setStagePosition(self, position, relative = "absolute"):
			tolerance = 1.0e-4
			polltime = 0.1
			if relative == "relative":
				try:
					position["x"] += self.theScope.Stage.Position.X
				except KeyError:
					pass
				try:
					position["y"] += self.theScope.Stage.Position.Y
				except KeyError:
					pass
				try:
					position["z"] += self.theScope.Stage.Position.Z
				except KeyError:
					pass
				try:
					position["a"] += self.theScope.Stage.Position.A
				except KeyError:
					pass
				try:
					position["b"] += self.theScope.Stage.Position.B
				except KeyError:
					pass
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			pos = self.theScope.Stage.Position
	
			try:
				pos.Z = position["z"]
			except KeyError:
				pass
			else:
				try:
					self.theScope.Stage.Goto(pos, win32com.client.constants.axisZ)
					while abs(self.theScope.Stage.Position.Z - pos.Z) > tolerance:
						time.sleep(polltime)
				except pywintypes.com_error:
					print 'stage z-axis limit hit'
		
			try:
				pos.Y = position["y"]
			except KeyError:
				pass
			else:
				try:
					self.theScope.Stage.Goto(pos, win32com.client.constants.axisY)
					while abs(self.theScope.Stage.Position.Y - pos.Y) > tolerance:
						time.sleep(polltime)
				except pywintypes.com_error:
					print 'stage y-axis limit hit'
	
			try:
				pos.X = position["x"]
			except KeyError:
				pass
			else:
				try:
					self.theScope.Stage.Goto(pos, win32com.client.constants.axisX)
					while abs(self.theScope.Stage.Position.X - pos.X) > tolerance:
						time.sleep(polltime)
				except pywintypes.com_error:
					print 'stage x-axis limit hit'
	
			try:
				pos.A = position["a"]
			except KeyError:
				pass
			else:
				try:
					self.theScope.Stage.Goto(pos, win32com.client.constants.axisA)
					while abs(self.theScope.Stage.Position.A - pos.A) > tolerance:
						time.sleep(polltime)
				except pywintypes.com_error:
					print 'stage a-axis limit hit'
	
			try:
				pos.B = position["b"]
			except KeyError:
				pass
			else:
				try:
					self.theScope.Stage.Goto(pos, win32com.client.constants.axisB)
					while abs(self.theScope.Stage.Position.B - pos.B) > tolerance:
						time.sleep(polltime)
				except pywintypes.com_error:
					print 'stage b-axis limit hit'
		
			return 0
		
		def getLowDose(self, novalue=False):
			if novalue:
				return str
			if (self.theLowDose.IsInitialized == 1) and (self.theLowDose.LowDoseActive == win32com.client.constants.IsOn):
				return "on"
			else:
				return "off"
	 
		def setLowDose(self, ld):
			if ld == "off" :
				self.theLowDose.LowDoseActive = win32com.client.constants.IsOff
			elif ld == "on":
				if self.theLowDose.IsInitialized == 0:
					raise SystemError
				else:
					self.theLowDose.LowDoseActive = win32com.client.constants.IsOn
			else:
				raise ValueError
	
			return 0		
	
		def getLowDoseMode(self, novalue=False):
			if novalue:
				return str
			if self.theLowDose.LowDoseState == win32com.client.constants.eExposure:
				return "exposure"
			elif self.theLowDose.LowDoseState == win32com.client.constants.eFocus1:
				return "focus1"
			elif self.theLowDose.LowDoseState == win32com.client.constants.eFocus2:
				return "focus2"
			elif self.theLowDose.LowDoseState == win32com.client.constants.eSearch:
				return "search"
			else:
				raise SystemError
			
		def setLowDoseMode(self, mode):
			if mode == "exposure":
				self.theLowDose.LowDoseState = win32com.client.constants.eExposure
			elif mode == "focus1":
				self.theLowDose.LowDoseState = win32com.client.constants.eFocus1
			elif mode == "focus2":
				self.theLowDose.LowDoseState = win32com.client.constants.eFocus2
			elif mode == "search":
				self.theLowDose.LowDoseState = win32com.client.constants.eSearch
			else:
				raise ValueError
	
			return 0
		
		def getDiffractionMode(self, novalue=False):
			if novalue:
				return str
			if self.theScope.Projection.Mode == win32com.client.constants.pmImaging:
				return "imaging"
			elif self.theScope.Projection.Mode == win32com.client.constants.pmDiffraction:
				return "diffraction"
			else:
				raise SystemError
			
		def setDiffractionMode(self, mode):
			if mode == "imaging":
				self.theScope.Projection.Mode = win32com.client.constants.pmImaging
			elif mode == "diffraction":
				self.theScope.Projection.Mode = win32com.client.constants.pmDiffraction
			else:
				raise ValueError
			
			return 0

		def filmExposure(self):
			hr = self.theAda.CloseShutter
			if hr != 0:
			  return hr
			hr = self.theAda.DisconnectExternalShutter
			if hr != 0:
			  return hr
			hr = self.theAda.MainScreenUp
			if hr != 0:
			  return hr
			hr = self.theAda.LoadPlate
			if hr != 0:
			  return hr
			hr = self.theAda.ExposePlateLabel
			if hr != 0:
			  return hr
			hr = self.theAda.OpenShutter
			if hr != 0:
			  return hr
			
			self.theScope.Camera.TakeExposure()
			
			hr = self.theAda.CloseShutter
			if hr != 0:
			  return hr
			hr = self.theAda.UnloadPlate
			if hr != 0:
			  return hr
			hr = self.theAda.UpdateExposureNumber
			if hr != 0:
			  return hr
			hr = self.theAda.MainScreenDown
			if hr != 0:
			  return hr
			hr = self.theAda.ConnectExternalShutter
			if hr != 0:
			  return hr
			hr = self.theAda.OpenShutter
			if hr != 0:
			  return hr
	
			return 0

		def getScreen(self, novalue=False):
			if novalue:
				return str
			if self.theAda.MainScreenStatus == 1:
				return 'up'
			else:
				return 'down'

		def setScreen(self, mode):
			if mode == 'up':
				self.theAda.MainScreenUp
			elif mode == 'down':
				self.theAda.MainScreenDown
			else:
				raise ValueError

		def getHolderStatus(self, novalue=False):
			if novalue:
				return str
			if self.theAda.SpecimenHolderInserted == adacom.constants.eInserted:
				return 'inserted'
			elif self.theAda.SpecimenHolderInserted == adacom.constants.eNotInserted:
				return 'not inserted'
			else:
				return 'unknown'

		def getHolderType(self, novalue=False):
			if novalue:
				return str
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

		def getStageStatus(self, novalue=False):
			if novalue:
				return str
			if self.theAda.GonioLedStatus == adacom.constants.eOn:
				return 'busy'
			elif self.theAda.GonioLedStatus == adacom.constants.eOff:
				return 'ready'
			else:
				raise SystemError

		def getTurboPump(self, novalue=False):
			if novalue:
				return str
			if self.theAda.GetTmpStatus == adacom.constants.eOn:
				return 'on'
			elif self.theAda.GetTmpStatus == adacom.constants.eOff:
				return 'off'
			else:
				raise SystemError

		def setTurboPump(self, mode):
			if mode == 'on':
				self.theAda.SetTmp(adacom.constants.eOn)
			elif mode == 'off':
				self.theAda.SetTmp(adacom.constants.eOff)
			else:
				raise ValueError

		def getColumnValves(self, novalue=False):
			if novalue:
				return str
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

		def getVacuumStatus(self, novalue=False):
			if novalue:
				return str
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

		def getColumnPressure(self, novalue=False):
			if novalue:
				return float
			return float(self.theScope.Vacuum.Gauges('P4').Pressure)

