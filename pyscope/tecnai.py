import scope
import sys
	
if sys.platform != 'win32':
	class tecnai(scope.scope):
		pass
else:
	import win32com.client
	import tecnaicom
	import ldcom
	import time
	
	class tecnai(scope.scope):
		def cmpmags(self, x, y):
			key = self.cmpmags_status
			if x[key] < y[key]: 
				return -1
			elif x[key] == y[key]: 
				return 0
			elif x[key] > y[key]: 
				 return 1
			
		def __init__(self):
			self.theScope = win32com.client.Dispatch("Tecnai.Instrument.1")		
			self.theLowDose = win32com.client.Dispatch("LDServer.LdSrv")
			self.theFilm = win32com.client.Dispatch("adaExp.TAdaExp")
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
	
		def getScreenCurrent(self):
			return self.theScope.Camera.ScreenCurrent
		
		def getGunTilt(self):
			return {"x" : self.theScope.Gun.Tilt.X, "y" : self.theScope.Gun.Tilt.Y}
		
		def setGunTilt(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Gun.Tilt.X
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
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Gun.Tilt = vec
			return 0
		
		def getGunShift(self):
			return {"x" : self.theScope.Gun.Shift.X, "y" : self.theScope.Gun.Shift.Y}
		
		def setGunShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Gun.Shift.X
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
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Gun.Shift = vec
			return 0
		
		def getHighTension(self):
			return self.theScope.Gun.HTValue
		
		def setHighTension(self, ht):
			self.theScope.Gun.HTValue = ht
			return 0
		
		def getIntensity(self):
			return self.theScope.Illumination.Intensity
		
		def setIntensity(self, intensity, relative = "absolute"):
			if relative == "relative":
				intensity += self.theScope.Illumination.Intensity
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			self.theScope.Illumination.Intensity = intensity
			return 0
	
		def getDarkFieldMode(self):
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
		
		def getBeamBlank(self):
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
		
		def getStigmator(self):
			 return {"condenser" : 
					 {"x" : self.theScope.Illumination.CondenserStigmator.X,
					  "y" : self.theScope.Illumination.CondenserStigmator.Y},
					"objective" :
					 {"x" : self.theScope.Projection.ObjectiveStigmator.X,
					  "y" : self.theScope.Projection.ObjectiveStigmator.Y},
					"diffraction" :
					 {"x" : self.theScope.Projection.DiffractionStigmator.X,
					  "y" : self.theScope.Projection.DiffractionStigmator.Y}
					} 
			
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
		
		def getSpotSize(self):
			return self.theScope.Illumination.SpotsizeIndex
		
		def setSpotSize(self, ss, relative = "absolute"):
			if relative == "relative":
				ss += self.theScope.Illumination.SpotsizeIndex
			elif relative == "absolute":
				pass
			else:
				raise ValueError
			
			self.theScope.Illumination.SpotsizeIndex = ss
			return 0
		
		def getBeamTilt(self):
			return {"x" : self.theScope.Illumination.RotationCenter.X, "y" : self.theScope.Illumination.RotationCenter.Y}
		
		def setBeamTilt(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Illumination.RotationCenter.X
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
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Illumination.RotationCenter = vec
			return 0
		
		def getBeamShift(self):
			return {"x" : self.theScope.Illumination.Shift.X, "y" : self.theScope.Illumination.Shift.Y}
	
		def setBeamShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Illumination.Shift.X
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
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Illumination.Shift = vec
			return 0
		
		def getImageShift(self):
			return {"x" : self.theScope.Projection.ImageBeamShift.X, "y" : self.theScope.Projection.ImageBeamShift.Y}
		
		def setImageShift(self, vector, relative = "absolute"):
			if relative == "relative":
				try:
					vector["x"] += self.theScope.Projection.ImageBeamShift.X
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
				vec.Y = vector["y"]
			except KeyError:
				pass
			self.theScope.Projection.ImageBeamShift = vec
			return 0
		
		def getDefocus(self):
			return self.theScope.Projection.Defocus
		
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
		
		def getMagnification(self):
			if self.theScope.Camera.MainScreen == win32com.client.constants.spUp:
				key = "up"
			elif self.theScope.Camera.MainScreen == win32com.client.constants.spDown:
				key = "down"
			else:   # perhaps spUnknown
				raise SystemError
	
			magindex = self.theScope.Projection.MagnificationIndex
	
			for mag in self.magTable:
				if mag['index'] == magindex:
					return mag[key]
	
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
		
		def getStagePosition(self):
			position = {"x" : self.theScope.Stage.Position.X,
						"y" : self.theScope.Stage.Position.Y,
						"z" : self.theScope.Stage.Position.Z,
						"a" : self.theScope.Stage.Position.A}
			if(self.theScope.Stage.Holder == win32com.client.constants.hoDoubleTilt):
				position["b"] = self.theScope.Stage.Position.B
			return position
		
		def setStagePosition(self, position, relative = "absolute"):
			tolerance = 1.0e-5
			polltime = 0.1
			if relative == "relative":
				try:
					position["x"] += self.theScope.Stage.Position.X
					position["y"] += self.theScope.Stage.Position.Y
					position["z"] += self.theScope.Stage.Position.Z
					position["a"] += self.theScope.Stage.Position.A
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
				self.theScope.Stage.Goto(pos, win32com.client.constants.axisZ)
				while abs(self.theScope.Stage.Position.Z - pos.Z) > tolerance:
					time.sleep(polltime)
	
			try:
				pos.Y = position["y"]
			except KeyError:
				pass
			else:
				self.theScope.Stage.Goto(pos, win32com.client.constants.axisY)
				while abs(self.theScope.Stage.Position.Y - pos.Y) > tolerance:
					time.sleep(polltime)
	
			try:
				pos.X = position["x"]
			except KeyError:
				pass
			else:
				self.theScope.Stage.Goto(pos, win32com.client.constants.axisX)
				while abs(self.theScope.Stage.Position.X - pos.X) > tolerance:
					time.sleep(polltime)
	
			try:
				pos.A = position["a"]
			except KeyError:
				pass
			else:
				self.theScope.Stage.Goto(pos, win32com.client.constants.axisA)
				while abs(self.theScope.Stage.Position.A - pos.A) > tolerance:
					time.sleep(polltime)
	
			try:
				pos.B = position["b"]
			except KeyError:
				pass
			else:
				self.theScope.Stage.Goto(pos, win32com.client.constants.axisB)
				while abs(self.theScope.Stage.Position.B - pos.B) > tolerance:
					time.sleep(polltime)
		
			return 0
		
		def getLowDose(self):
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
	
		def getLowDoseMode(self):
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
		
		def getDiffractionMode(self):
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
			hr = self.theFilm.CloseShutter
			if hr != 0:
			  return hr
			hr = self.theFilm.DisconnectExternalShutter
			if hr != 0:
			  return hr
			hr = self.theFilm.MainScreenUp
			if hr != 0:
			  return hr
			hr = self.theFilm.LoadPlate
			if hr != 0:
			  return hr
			hr = self.theFilm.ExposePlateLabel
			if hr != 0:
			  return hr
			hr = self.theFilm.OpenShutter
			if hr != 0:
			  return hr
			
			self.theScope.Camera.TakeExposure()
			
			hr = self.theFilm.CloseShutter
			if hr != 0:
			  return hr
			hr = self.theFilm.UnloadPlate
			if hr != 0:
			  return hr
			hr = self.theFilm.UpdateExposureNumber
			if hr != 0:
			  return hr
			hr = self.theFilm.MainScreenDown
			if hr != 0:
			  return hr
			hr = self.theFilm.ConnectExternalShutter
			if hr != 0:
			  return hr
			hr = self.theFilm.OpenShutter
			if hr != 0:
			  return hr
	
			return 0
