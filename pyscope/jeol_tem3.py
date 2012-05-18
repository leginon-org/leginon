# import win32com.client  - do not need this line any more
import pythoncom
import win32com.client
import sys
import pywintypes
import time
import ToTEM
import gatan
import tem

"""
The file ToTEM.pyd is required, which is the exactly same ToTEM.dll but changed file extension to .pyd for python.  

Some python versions take .pyd extension instead of .dll.
Put ToTEM,pyd or ToTEM.dll in <python dir>/DLLs
"""

class Jeol(tem.TEM):
	name = 'Jeol'
	def __init__(self):
		self.nominal_magtable = [
			100, 120, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000, 2500, 3000, 
			4000, 5000, 6000, 8000, 10000, 12000, 15000, 20000, 30000, 40000, 50000, 60000, 80000, 
			100000, 120000, 150000, 200000, 250000, 300000, 400000, 500000, 600000, 800000, 1000000, 1200000
		]
								
# old		self.real_magtable = [
#			128, 165, 211, 274, 318, 381, 512, 661, 782, 1045, 1650, 2080, 2300, 3270, 4080, 4430, 5000,
#			6090, 7280, 10600, 12400, 15500, 19400, 27500, 37400, 48200, 64300, 81000, 95000, 123000, 
#			161000, 196000, 240000, 300000, 405000, 500000, 704000, 870000, 1020000, 1340000, 1441500, 1680000
#		]
				
#old2		self.real_magtable = [
#			140, 171, 221, 273, 335, 401, 570, 680, 815, 1060, 1790, 2220, 2440, 3560, 4250, 4700, 5190,
#			6460, 7820, 10760, 13510, 16370, 20900, 29400, 36800, 47800, 63200, 79600, 92700, 127900, 
#			169300, 198000, 255000, 340000, 425000, 513000, 600000, 700000, 800000, 990000, 1240000, 1360000
#		]

		self.real_magtable = [
			165, 182, 210, 290, 400, 450, 570, 680, 780, 1000, 1770, 2260, 2430, 3460, 4350, 4880, 5580,
			6570, 7900, 10370, 12970, 16800, 19100, 24400, 28000, 34300, 45500, 58100, 68700, 86600, 
			110000, 130000, 177000, 236000, 425000, 513000, 600000, 700000, 800000, 990000, 1240000, 1360000
		]
		
								
		self.magTable = [{'index': 1, 'up': 165, 'down': 100},
				{'index': 2, 'up': 182, 'down': 120},
				{'index': 3, 'up': 210, 'down': 150},
				{'index': 4, 'up': 290, 'down': 200},
				{'index': 5, 'up': 400, 'down': 250},
				{'index': 6, 'up': 450, 'down': 300},
				{'index': 7, 'up': 570, 'down': 400},
				{'index': 8, 'up': 680, 'down': 500},
				{'index': 9, 'up': 780, 'down': 600},
				{'index': 10, 'up': 1000, 'down': 800},
				{'index': 25, 'up': 28000, 'down': 25000},
				{'index': 11, 'up': 1770, 'down': 1000},
				{'index': 12, 'up': 2260, 'down': 1200},
				{'index': 13, 'up': 2430, 'down': 1500},
				{'index': 14, 'up': 3460, 'down': 2000},
				{'index': 15, 'up': 4350, 'down': 2500},
				{'index': 16, 'up': 4880, 'down': 3000},
				{'index': 17, 'up': 5580, 'down': 4000},
				{'index': 18, 'up': 6570, 'down': 5000},
				{'index': 19, 'up': 7900, 'down': 6000},
				{'index': 20, 'up': 10370, 'down': 8000},
				{'index': 21, 'up': 12970, 'down': 10000},
				{'index': 22, 'up': 16800, 'down': 12000},
				{'index': 23, 'up': 19100, 'down': 15000},
				{'index': 24, 'up': 24400, 'down': 20000},
				{'index': 26, 'up': 34300, 'down': 30000},
				{'index': 27, 'up': 45500, 'down': 40000},
				{'index': 28, 'up': 58100, 'down': 50000},
				{'index': 29, 'up': 68700, 'down': 60000},
				{'index': 30, 'up': 86600, 'down': 80000},
				{'index': 31, 'up': 110000, 'down': 100000},
				{'index': 32, 'up': 130000, 'down': 120000},
				{'index': 33, 'up': 177000, 'down': 150000},
				{'index': 34, 'up': 236000, 'down': 200000},
				{'index': 35, 'up': 425000, 'down': 250000},
				{'index': 36, 'up': 513000, 'down': 300000},
				{'index': 37, 'up': 600000, 'down': 400000},
				{'index': 38, 'up': 700000, 'down': 500000},
				{'index': 39, 'up': 800000, 'down': 600000},
				{'index': 40, 'up': 990000, 'down': 800000},
				{'index': 41, 'up': 1240000, 'down': 1000000},
				{'index': 42, 'up': 1360000, 'down': 1200000}]
		
		self.magnifications = self.real_magtable # map(float, self.real_magtable)
		self.sortedmagnifications = list(self.magnifications)
		self.sortedmagnifications.sort()
		
		# magnification constant
		self.MAG1 = 0
		self.MAG2 = 1
		self.LowMAG = 2
		self.SAMA = 3
		self.DIFF = 4
		
		self.theMagMode = self.MAG1
		
		# constants for Jeol Hex value
		self.ZERO = 32768
		self.MAX = 65535
		self.MIN = 0
		self.SCALE_FACTOR = 32767
		
		# one ccd pixel is 30x30 micrometer square
		self.CCD_PIXEL_SIZE = 0.00003 

		self.IMAGESHIFT_ORIGIN_X = 32768
		self.IMAGESHIFT_ORIGIN_Y = 32768
		self.IMAGESHIFT_FACTOR_X = 0.000000000508
		self.IMAGESHIFT_FACTOR_Y = 0.000000000434
		self.IMAGESHIFT_FACTOR_X_LowMAG = 0.0000000132
		self.IMAGESHIFT_FACTOR_Y_LowMAG = 0.000000012

		self.BEAMSHIFT_ORIGIN_X = 32768
		self.BEAMSHIFT_ORIGIN_Y = 32768
		self.BEAMSHIFT_FACTOR_X = 0.0000000252
		self.BEAMSHIFT_FACTOR_Y = 0.0000000246
		self.BEAMSHIFT_FACTOR_X_LowMAG = 0.000000092
		self.BEAMSHIFT_FACTOR_Y_LowMAG = 0.000000092
    
		self.BEAMTILT_ORIGIN_X = 32768
		self.BEAMTILT_ORIGIN_Y = 32768
		self.BEAMTILT_FACTOR_X = 0.00000065
		self.BEAMTILT_FACTOR_Y = 0.00000062

		# initial objective lens
		# self.theObjectLensCoarse = 35470
		self.theObjectLensCoarse = 35432
		self.theObjectLensFine = 33624
		self.theObjectMini = 63828
		
		self.theFocusMAG1 = 0.0
		self.theFocusLowMAG = 0.0
		self.theScreenPos = 'up'
		
		# beam blank
		self.BEAM_BLANK_ON = 1
		self.BEAM_BLANK_OFF = 0
		
		# gatan object
		self.ccd = gatan.Gatan()
		
		self.initializeJeol()
		
		self.CL3Table = {'100':65535, '800':41237, '8k':37004, '60k':38117}
		
		# if a stage position movement is less than the following, then ignore it
		self.minimum_stage = {
			'x': 1e-6,
			'y': 1e-6,
			'z': 1e-6,
			'a': 5e-1,
		}
		
	def cmpmags(self, x, y):
		key = self.theScreenPos

		if x[key] < y[key]: 
			return -1
		elif x[key] == y[key]: 
			return 0
		elif x[key] > y[key]: 
			return 1

	def getCCDPixelCal(self):
		for mag in self.magTable:
			print mag['up'], ' : ',mag['down'], ' : ',  self.CCD_PIXEL_SIZE / mag['up'], ' : ', mag['up']
			
	def toJeol(self, val):
		return self.ZERO + int(round(self.SCALE_FACTOR * val))

	def toLeginon(self, val):
		val = val - self.ZERO
		return float(val) / self.SCALE_FACTOR

	def normalizeLens(self, lens = "all"):
	# not available in Jeol EM
		return 0

	def initializeScreenPosition(self):
		self.theScreenPos = "up"   # start with the screen position up
		ToTEM.SetScreen(1)
		return 0

	def initializeJeol(self):
		# 1. checking the communication to microscope
		if ToTEM.GetCheckMicroscope() != 0:
			print 'Communication Error: Jeol 3100 is not ready to serve.' 
			return
			
		# 2.1 setting the mag mode LowMag and defining low mag focus for the future defocus
		ToTEM.SelectFunctionMode(self.LowMAG)
		ToTEM.SetOM(self.theObjectMini)
		self.theFocusLowMAG = self.theObjectMini
		
		# 2.2 setting the mag mode LMAG and defining focus for the future defocus
		ToTEM.SelectFunctionMode(self.MAG1)
	
		# 3. defining focus plane for the future defocus length
		ToTEM.SetOLFine(self.theObjectLensFine)
		ToTEM.SetOLCoarse(self.theObjectLensCoarse)
		self.theFocusMAG1 = self.theObjectLensFine + (self.theObjectLensCoarse * 32)
		
		print 'Jeol is MAG1 mode and focus is defined for the future defocus.'
		
		# 4. initializing screen position as 'up'
		ToTEM.SetScreen(1)
		self.theScreenPos = 'up'
		
		# 5. MDS photo mode is set for film recording
		if ToTEM.GetMDSMode() != 3:
			ToTEM.SetMDSMode(3)
		
		return
		
	def getScreenCurrent(self):
		return ToTEM.GetCurrentDensity()
		

	def getGunTilt(self):
		tilt = ToTEM.GetGunTilt()
		return {"x" : self.toLeginon(tilt[0]), "y" : self.toLeginon(tilt[1])}
    
	def setGunTilt(self, vector, relative = "absolute"):
		currentTilt = self.getGunTilt()
		if relative == "relative":
			try:
				vector["x"] += currentTilt[0]
				vector["y"] += currentTilt[1]
			except KeyError:
				pass
		elif relative == "absolute":
			pass
		else:
			raise ValueError

		try:
			ToTEM.SetGunTilt(self.toJeol(vector["x"]), self.toJeol(vector["y"]))
		except KeyError:
			pass

		return 0

	def getGunShift(self):
		tilt = ToTEM.GetGunShift()
		return {"x" : self.toLeginon(tilt[0]), "y" : self.toLeginon(tilt[1])}

	def setGunShift(self, vector, relative = "absolute"):
		currentShift = self.getGunShift()
		if relative == "relative":
			try:
				vector["x"] += currentShift[0]
				vector["y"] += currentShift[1]
			except KeyError:
				pass
		elif relative == "absolute":
			pass
		else:
			raise ValueError

		try:
			ToTEM.SetGunShift(self.toJeol(vector["x"]), self.toJeol(vector["y"]))
		except KeyError:
			pass

		return 0
  
 	def getHighTensionStates(self):
 		print 'high tension:', 'on'
  		return ['off', 'on', 'disabled']

	def getHighTension(self):
		ht = ToTEM.GetHTValue()
		return int(ht)

	def setHighTension(self, ht):
		ToTEM.SetHTValue(ht)
		return 0

	# intensity is controlled by condenser lense 3
	def getIntensity(self):
		intensity = ToTEM.GetBrightness()
		return float(intensity) / self.MAX

	def setIntensity(self, intensity, relative = "absolute"):
		if relative == "relative":
			intensity += self.getIntensity()
		elif relative == "absolute":
			pass
		else:
			raise ValueError
	
		ToTEM.SetBrightness(int(round(intensity*self.MAX)))
		return 0
		
	def getDarkFieldMode(self):
		return 0

	def setDarkFieldMode(self, mode):
		return 0

	def getBeamBlank(self):
		if ToTEM.GetBeamBlank() == 0:
			return "off"
		elif ToTEM.GetBeamBlank() == 1:
			return "on"
		else:
			raise SystemError

	def setBeamBlank(self, bb):
		if bb == "off" :
			ToTEM.SetBeamBlank(0)
		elif bb == "on":
			ToTEM.SetBeamBlank(1)
		else:
			raise ValueError

	# the DiffractionStigmator of tecnai is the IntermediateStigmator of Jeol
	def getStigmator(self):
		stigs = ToTEM.GetStigmator()
		return {"condenser" : {"x" : self.toLeginon(stigs[0]), "y" : self.toLeginon(stigs[1])},
				"objective" : {"x" : self.toLeginon(stigs[2]), "y" : self.toLeginon(stigs[3])},
				"diffraction" : {"x" : self.toLeginon(stigs[4]), "y" : self.toLeginon(stigs[5])}
				} 
    
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
				ToTEM.SetCondenserStigmator(self.toJeol(stigmator["x"]), self.toJeol(stigmator["y"]))
			elif key == "objective":
				ToTEM.SetObjectiveStigmator(self.toJeol(stigmator["x"]), self.toJeol(stigmator["y"]))
			elif key == "diffraction":
				ToTEM.SetIntermediateStigmator(self.toJeol(stigmator["x"]), self.toJeol(stigmator["y"]))
			else:
				raise ValueError
    
	def getSpotSize(self):
		return ToTEM.GetSpotSize()

	def setSpotSize(self, ss, relative = "absolute"):
		if relative == "relative":
			ss += self.getSpotSize()
		elif relative == "absolute":
			pass
		else:
			raise ValueError
 
		ToTEM.SetSpotSize(ss)
	
	def getBeamTilt(self):
		tilt = ToTEM.GetBeamTilt()
	        
		tilt_x = (tilt[0] - self.BEAMTILT_ORIGIN_X)
		tilt_y = (tilt[1] - self.BEAMTILT_ORIGIN_Y)
		return {"x" : tilt_x * self.BEAMTILT_FACTOR_X, "y" : tilt_y * self.BEAMTILT_FACTOR_Y}
	        
	def setBeamTilt(self, vector, relative = "absolute"):
		if relative == "relative":
			tilt = self.getBeamTilt()
			try:
				vector["x"] += tilt["x"]
	 			vector["y"] += tilt["y"]
	 		except KeyError:
	 			pass
		elif relative == "absolute":
			pass
		else:
			raise ValueError
	
		tilt_x = int(round(vector['x'] / self.BEAMTILT_FACTOR_X)) + self.BEAMTILT_ORIGIN_X
		tilt_y = int(round(vector['y'] / self.BEAMTILT_FACTOR_Y)) + self.BEAMTILT_ORIGIN_Y
		
		print ">>>>>>>>>>>>>>>>> Set Beam Tilt : (", tilt_x, tilt_y, ")"
		
		try:
			ToTEM.SetBeamTilt(tilt_x, tilt_y)
		except KeyError:
			pass

	def getBeamShift(self):
		shift = ToTEM.GetBeamShift()
		shift_x = shift[0] - self.BEAMSHIFT_ORIGIN_X
		shift_y = shift[1] - self.BEAMSHIFT_ORIGIN_Y
		
		if self.theMagMode == self.LowMAG:
			return {"x" : shift_x * self.BEAMSHIFT_FACTOR_X_LowMAG, "y" : shift_y * self.BEAMSHIFT_FACTOR_Y_LowMAG}
		elif self.theMagMode == self.MAG1:
			return {"x" : shift_x * self.BEAMSHIFT_FACTOR_X, "y" : shift_y * self.BEAMSHIFT_FACTOR_Y}

	def setBeamShift(self, vector, relative = "absolute"):
		shift = self.getBeamShift()
		if relative == "relative":
			try:
				vector["x"] += shift["x"]
				vector["y"] += shift["y"]
			except KeyError:
				pass
		elif relative == "absolute":
			pass
		else:
			raise ValueError
	

		try:
			shift['x'] = vector['x']
		except KeyError:
			pass
		try:
			shift['y'] = vector['y']
		except KeyError:
			pass
			
		if self.theMagMode == self.LowMAG:
			x_shift = int(round(shift["x"] / self.BEAMSHIFT_FACTOR_X_LowMAG))
			y_shift = int(round(shift["y"] / self.BEAMSHIFT_FACTOR_Y_LowMAG))
		elif self.theMagMode == self.MAG1:
			x_shift = int(round(shift["x"] / self.BEAMSHIFT_FACTOR_X))
			y_shift = int(round(shift["y"] / self.BEAMSHIFT_FACTOR_Y))
		
		print "beam shift", x_shift, y_shift
	
		try:
			ToTEM.SetBeamShift(x_shift + self.BEAMSHIFT_ORIGIN_X, y_shift + self.BEAMSHIFT_ORIGIN_Y)
		except KeyError:
			pass
    	
	def getImageShift(self):
		if self.theMagMode == self.LowMAG:
			shift = ToTEM.GetImageShift2()
			
			shift_x = shift[0] - self.IMAGESHIFT_ORIGIN_X
			shift_y = shift[1] - self.IMAGESHIFT_ORIGIN_Y
			#print "get image shift (jeol): ", shift_x, shift_y;
			
			return {"x" : self.IMAGESHIFT_FACTOR_X_LowMAG * shift_x, "y" : self.IMAGESHIFT_FACTOR_Y_LowMAG * shift_y}
		else:
			shift = ToTEM.GetImageShift1()
			
			shift_x = shift[0] - self.IMAGESHIFT_ORIGIN_X
			shift_y = shift[1] - self.IMAGESHIFT_ORIGIN_Y
			#print "get image shift (jeol): ", shift_x, shift_y;
			
			return {"x" : self.IMAGESHIFT_FACTOR_X * shift_x, "y" : self.IMAGESHIFT_FACTOR_Y * shift_y}
		
	
	def setImageShift(self, vector, relative = "absolute"):
		shift = self.getImageShift()
		
		if relative == "relative":
			try:
				vector["x"] += shift["x"]
				vector["y"] += shift["y"]
			except KeyError:
				pass
		elif relative == "absolute":
			pass
		else:
			raise ValueError

		try:
			shift['x'] = vector['x']
		except KeyError:
			pass
		try:
			shift['y'] = vector['y']
		except KeyError:
			pass
			
		if self.theMagMode == self.LowMAG:
			x_shift = int(round(shift['x'] / self.IMAGESHIFT_FACTOR_X_LowMAG))
			y_shift = int(round(shift['y'] / self.IMAGESHIFT_FACTOR_Y_LowMAG))
			ToTEM.SetImageShift2(x_shift + self.IMAGESHIFT_ORIGIN_X, y_shift + self.IMAGESHIFT_ORIGIN_Y)
			
		else:
			x_shift = int(round(shift['x'] / self.IMAGESHIFT_FACTOR_X))
			y_shift = int(round(shift['y'] / self.IMAGESHIFT_FACTOR_Y))
			ToTEM.SetImageShift1(x_shift + self.IMAGESHIFT_ORIGIN_X, y_shift + self.IMAGESHIFT_ORIGIN_Y)
		
		print "set image shift (leginon): ", shift['x'], shift['y']
		print "set image shift (jeol): ", x_shift, y_shift
          
	def getDefocus(self):
		if self.theMagMode == self.LowMAG:
			focus_mini = ToTEM.GetOM()
			defocus_steps = focus_mini - self.theFocusLowMAG
			return defocus_steps * 0.00000001
		elif self.theMagMode == self.MAG1:
			focus_fine = ToTEM.GetOLFine()
			focus_coarse = ToTEM.GetOLCoarse()
			focus = focus_fine + (focus_coarse * 32)
			defocus_steps = focus - self.theFocusMAG1
			return defocus_steps * 0.0000000058
		else:
			return 0.0
                
	def setDefocus(self, defocus, relative = "absolute"):
		if defocus == 0.0:
			if self.theMagMode == self.LowMAG:
				ToTEM.SetOM(self.theFocusLowMAG)
			elif self.theMagMode == self.MAG1:
				focus = self.theFocusMAG1
				focus_coarse = int(focus / 32)
				focus_fine = focus - (focus_coarse * 32)
				print 'focus coarse:', focus_coarse, 'fine:', focus_fine
				ToTEM.SetOLCoarse(focus_coarse)
				ToTEM.SetOLFine(focus_fine)
			else:
				pass
			return 0
		
		if relative == 'relative':
			defocus += self.getDefocus()
		elif relative == 'absolute':
			pass

		print self.theMagMode
		
		if self.theMagMode == self.LowMAG:
			defocus_steps = int(round(defocus / 0.00000001))
			ToTEM.SetOM(self.theFocusLowMAG + defocus_steps)
		elif self.theMagMode == self.MAG1:
			defocus_steps = int(round(defocus / 0.0000000058))
			focus = self.theFocusMAG1 + defocus_steps
			focus_coarse = int(focus / 32)
			focus_fine = focus - (focus_coarse * 32)
			print 'focus coarse:', focus_coarse, 'fine:', focus_fine
			ToTEM.SetOLCoarse(focus_coarse)
			ToTEM.SetOLFine(focus_fine)
		else:
			return 1
		return 0

	
	def resetDefocus(self, value):
		if not value:
			return 1
		
		if self.theMagMode == self.LowMAG:
			self.theFocusLowMAG = ToTEM.GetOM()
		elif self.theMagMode == self.MAG1:
			focus_fine = ToTEM.GetOLFine()
			focus_coarse = ToTEM.GetOLCoarse()
			self.theFocusMAG1 = focus_fine + (focus_coarse * 32)
			return 0
		else:
			return 1
    
	def getMagnification(self):
		key = self.theScreenPos
	
		mag_value = ToTEM.GetMagnification()
		
		print mag_value 
		
		for mag in self.magTable:
			if mag['down'] == mag_value:
				return mag[key]
		
	def getMagnifications(self):
		return self.magnifications
		

	def getMagnificationIndex(self, magnification=None):
		if magnification is None:
			return 0
		else:
			try:
				return self.magnifications.index(magnification)
			except IndexError:
				raise ValueError('invalid magnification')

	def setMagnificationIndex(index):
		key = self.theScreenPos
		
		for mag in self.magTable:
			if mag['index'] == index + 1:
				self.theMagMode = ToTEM.SetMagnification(mag['down'])
				return 0		
		return 1
	
	def setMagnification(self, mag_value):
		key = self.theScreenPos
		
		for mag in self.magTable:
			if mag[key] == mag_value:
				self.theMagMode = ToTEM.SetMagnification(mag['down'])
				return 0
		return 1
	
	def checkStagePosition(self, position):
		current = self.getStagePosition()
		bigenough = {}
		for axis in ('x', 'y', 'z', 'a'):
			if axis in position:
				delta = abs(position[axis] - current[axis])
				if delta > self.minimum_stage[axis]:
					bigenough[axis] = position[axis]
		print bigenough
		return bigenough
	
	def getStagePosition(self):
		stagePosition = ToTEM.GetStagePosition()
		position = {"x" : stagePosition[0]/1000000000,
					"y" : stagePosition[1]/1000000000,
					"z" : stagePosition[2]/1000000000,
					"a" : stagePosition[3],
					"b" : stagePosition[4]}
		return position
	
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
			ToTEM.SetStagePositionZ(position["z"] * 1000000000)
		except KeyError:
			pass
		else:
			stop = 1
			while stop: 
				time.sleep(.1)
				stop = (ToTEM.GetStageStatus())[2]

		try:
			tmp_x = position['x'] + 0.00002
			ToTEM.SetStagePositionX(tmp_x * 1000000000)
			
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] + 0.00002
			ToTEM.SetStagePositionX(tmp_x * 1000000000)
		# else:
		stop = 1
		while stop: 
			time.sleep(.1)
			stop = (ToTEM.GetStageStatus())[0]

			
		try:
			tmp_y = position['y'] + 0.00002
			ToTEM.SetStagePositionY(tmp_y * 1000000000)
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] + 0.00002
			ToTEM.SetStagePositionY(tmp_y * 1000000000)
		# else:
		stop = 1
		while stop: 
			time.sleep(.1)
			stop = (ToTEM.GetStageStatus())[1]
		
		try:
			ToTEM.SetStagePositionXTilt(position["a"])
		except KeyError:
			pass
		else:
			stop = 1
			while stop: 
				time.sleep(.1)
				stop = (ToTEM.GetStageStatus())[3]
	
		try:
			ToTEM.SetStagePositionYTilt(position["b"])
		except KeyError:
			pass
		else:
			stop = 1
			while stop: 
				time.sleep(.1)
				stop = (ToTEM.GetStageStatus())[4]
				
		try:
			tmp_x = position['x'] - 0.00002
			ToTEM.SetStagePositionX(tmp_x * 1000000000)
			
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['x'] = tmp_pos['x']
			tmp_x = position['x'] - 0.00002
			ToTEM.SetStagePositionX(tmp_x * 1000000000)
		# else:
		stop = 1
		while stop: 
			time.sleep(.1)
			stop = (ToTEM.GetStageStatus())[0]

			
		try:
			tmp_y = position['y'] - 0.00002
			ToTEM.SetStagePositionY(tmp_y * 1000000000)
		except KeyError:
			# for stage hysteresis removal
			tmp_pos = self.getStagePosition()
			position['y'] = tmp_pos['y']
			tmp_y = position['y'] - 0.00002
			ToTEM.SetStagePositionY(tmp_y * 1000000000)
		# else:
		stop = 1
		while stop: 
			time.sleep(.1)
			stop = (ToTEM.GetStageStatus())[1]
				
		# for stage hysteresis removal
		
		try:
			ToTEM.SetStagePositionX(position["x"] * 1000000000)
		except KeyError:
			pass
		else:
			stop = 1
			while stop: 
				time.sleep(.1)
				stop = (ToTEM.GetStageStatus())[0]

		try:
			ToTEM.SetStagePositionY(position["y"] * 1000000000)
		except KeyError:
			pass
		else:
			stop = 1
			while stop: 
				time.sleep(.1)
				stop = (ToTEM.GetStageStatus())[1]

		return 0

	def getLowDoseStates(self):
		return ['on','off', 'disabled']
    	
	def getLowDose(self):
		ld = ToTEM.GetMDSMode()
		if (ld == 0): 
			return "off"
		else:
			return "on"
 
	def setLowDose(self, ld):
		if ld == "off" :
			ToTEM.EndMDSMode()
		elif ld == "on" :
			ToTEM.SetMDSMode(1)
		else:		
			raise ValueError

	def getLowDoseModes(self):
		return ['exposure', 'focus1', 'search', 'unknown', 'disabled']
		
	def getLowDoseMode(self):
		if ToTEM.GetMDSMode() == 3:
			return "exposure"
		elif ToTEM.GetMDSMode() == 2:
			return "focus1"
		elif ToTEM.GetMDSMode() == 1:
			return "search"
		else:
			return "unknown"

	def setLowDoseMode(self, mode):
		if mode == "exposure":
			ToTEM.SetMDSMode(3)
		elif mode == "focus1":
			ToTEM.SetMDSMode(2)
		elif mode == "focus2":
			ToTEM.SetMDSMode(2)
		elif mode == "search":
			ToTEM.SetMDSMode(1)
		else:
			raise ValueError
    
	def getDiffractionMode(self):
		mode = ToTEM.GetFunctionMode()
		if mode == 0:
			return "imaging"
		elif mode == 1:
			return "imaging"
		elif mode == 4:
			return "diffraction"
		else:
			raise SystemError
	
	def setDiffractionMode(self, mode):
		if mode == "imaging":
			ToTEM.SelectFunctionMode(0)
		elif mode == "diffraction":
			ToTEM.SelectFunctionMode(4)
		else:
			raise ValueError
	
		return 0
	
	def getScreenCurrent(self):
		sc = ToTEM.GetCurrentDensity()
		sc *= 0.0000000001
		return sc

	def getMainScreenPositions(self):
		return ['up', 'down', 'unknown']
		
	def getMainScreenPosition(self):
		return self.theScreenPos
		
	def setMainScreenPosition(self, pos):
		self.theScreenPos = pos
		if (pos == 'up'):
			ToTEM.SetScreen(1)
		elif (pos == 'down'):
			ToTEM.SetScreen(0)
		else:
			raise KeyError
			
		return 0
	
		
	'''
	ToTEM Camera function list
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
		status = ToTEM.GetCameraStatus()
		return status
		
	def setFilmLoadingMode(self, m = 0):
		ToTEM.SelectFilmLoadingMode(m)
		return 0
		
	def takePhoto(self):
		ToTEM.TakePhoto()
		return 0
		
	def cancelPhoto(self):
		ToTEM.CancelPhoto()
		return 0
		
	def getExposeTime(self):
		ToTEM.GetExpTime()
		return 0
	
	def setExposeTime(self, time):
		ToTEM.SetExpTime(time)
		return 0
		
	def preFilmExposure(self, value):
		if not value:
			return
		
		if ToTEM.GetUnused() < 1:
			raise RuntimeError('No film to take exposure')

		ToTEM.LoadFilm()
		time.sleep(6)
		
		return
		
	def postFilmExposure(self, value):
		if not value:
			return
			
		ToTEM.EjectFilm()
		
		return

##############################		
# For testing purpose

	def filmThing(self):
		self.preFilmExposure()
		#self.filmExposure()
		self.postFilmExposure()
		
	def getIShift(self):
		ish = ToTEM.GetImageShift()
		return {'x':ish[0], 'y':ish[1]}

	def setIShift(self, vector, relative = "absolute"):
		return ToTEM.SetImageShift(vector['x'], vector['y'])
		
	def getBShift(self):
		bsh = ToTEM.GetBeamShift()
		return {'x':bsh[0], 'y':bsh[1]}

	def setBShift(self, vector, relative = "absolute"):
		return ToTEM.SetBeamShift(vector['x'], vector['y'])

	def BShiftChange(self, x, y):
		b_shift = ToTEM.GetBeamShift()
		ToTEM.SetBeamShift(b_shift[0] + x, b_shift[1] + y)
		ToTEM.SetBeamShift(b_shift[0], b_shift[1])
		return 0
		
#
#############################
