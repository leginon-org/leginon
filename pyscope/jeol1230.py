# jeol1230.py is implemented for Jeol 1230 electron microscope
# Author: Minghui Hu, mhu@nysbc.org, New York Structural Biology Center

# from pyscope import jeol1230 ; j = jeol1230.jeol1230()

import time
import math
from pyscope import tem
from pyscope import jeol1230lib
from pyscope import jeol1230cal

try:
	import pythoncom
except:
	pass

Debug = False

class MagnificationsUninitialized(Exception):
	pass

class jeol1230(tem.TEM):
	name = 'jeol1230'
	def __init__(self):
		if Debug == True:
			print 'from jeol1230.py class_defination'
		
		tem.TEM.__init__(self)
		self.correctedstage = True
		self.jeol1230lib = jeol1230lib.jeol1230lib()
		self.magnifications = []
		self.mainscreenscale = 1.0						# What is this? Possibly, ratio of screen to film

	def getHighTensionStates(self):
		if Debug == True:
			print 'from jeol1230.py getHighTensionStates'
		hts = ['off', 'on', 'disabled']
		return hts


	def getHighTensionState(self):
		if Debug == True:
			print 'from jeol1230.py getHighTensionState'
		highTensionState = self.jeol1230lib.getHighTensionState()
		return highTensionState


	def getHighTension(self):
		if Debug == True:
			print 'from jeol1230.py getHighTension'
		if self.jeol1230lib.getHighTensionState() == 'on':
			highTension = self.jeol1230lib.getHighTension()
		else:
			highTension = 0
		return highTension


	def setHighTension(self, value):
		if Debug == True:
			print 'from jeol1230.py setHighTension'
		return True


	def getColumnValvePositions(self):
		if Debug == True:
			print "from jeol1230.py getColumnValvePositions"
		return ['on', 'off','unknown']

	
	def getColumnValvePosition(self):						# modified by Minghui
		if Debug == True:
			print 'from jeol1230.py getColumnValvePostion'
		return self.getBeamState()


	def setColumnValvePosition(self, state):   				# state = 'on' or 'off'
		if Debug == True:
			print 'from jeol1230.py setColumnValvePosition'
		if self.jeol1230lib.setBeamOnOff(state) == True:
			return True
		else:
			return False


	def getBeamState(self):
		if Debug == True:
			print "from jeol1230.py getBeamState"
		beamState = self.jeol1230lib.getBeamState()
		return beamState

	def getTurboPump(self):				# Now, the pump is the beam for jeol1230 added by minghui
		if Debug == True:
			print "from jeol1230.py getTurboPump"
		beamState = self.jeol1230lib.getBeamState()
		return beamState


	def setBeamState(self, mode):
		if Debug == True:
			print "from jeol1230.py setBeamOnOff"
		if self.jeol1230lib.setBeamState(mode) == True:
			return True
		else:
			return False


	def setTurboPump(self, mode):		# Now, the pump is the beam for jeol1230 added by minghui
		if Debug == True:
			print "from jeol1230.py setTurboPump"
		if self.jeol1230lib.setBeamState(mode) == True:
			return True
		else:
			return False


	def setMagnifications(self, magnifications):
		if Debug == True:
			print 'from jeol1230.py setMagnifications'
		self.magnifications = magnifications
		return True


	def findMagnifications(self):								# search mag table
		if Debug == True:										# Why do we need to FIND?
			print 'from jeol1230.py findMagnifications'
		magnifications = jeol1230cal.screenup_mag
		self.setMagnifications(magnifications)
		return True


	def getMagnificationsInitialized(self):						# Check if there is value in self.mag
		if Debug == True:
			print "from jeol1230.py getMagnificationsInitialized"
		if self.magnifications:
			return True
		else:
			return False


	def getMagnifications(self):
		if Debug == True:
			print "from jeol1230.py getMagnifications"
		return self.magnifications


	def getMagnification(self, index=None):						# return the Mag value from index or current mag
		if Debug == True:
			print "from jeol1230.py getMagnification"
		if index is None:
			return self.jeol1230lib.getMagnification()
		elif int(index) > 40 or int(index) < 0:
			print '    Valid magnification index should be 0-40'
			return
		else:
			return self.magnifications[index]


	def getMainScreenMagnification(self):						# return the actual Mag value
		if Debug == True:
			print 'from jeol1230.py getMainScreenMagnification'
		return self.jeol1230lib.getMagnification()


	def _emcGetMagPosition(self,mag,screenUp):              	#  get Mag index position
		if Debug == True:
			print 'from jeol1230.py _emcGetMagPostion'
		magRange = 40											# mag index is between 0 and 40, totally 41
		mags = jeol1230cal.screenup_mag
		for i in range(0,magRange):
			if int(mag) <= mags[i]:
				break
		if i > magRange:
			print '    magnification out of range'
		return i


	def getMagnificationIndex(self, mag):
		if Debug == True:
			print 'from jeol1230.py getMagnificationIndex'
		index = self._emcGetMagPosition(mag,0)
		return int(index)


	def setMagnification(self, mag):							# set magnifications
		if Debug == True:
			print 'from jeol1230.py setMagnification'
		self.jeol1230lib.setMagnification(mag)
		return True


	def setMagnificationIndex(self, value):
		if Debug == True:
			print 'from jeol1230.py setMagnificationIndex'
		mag = self.getMagnification(value)
		if self.jeol1230lib.setMagnification(mag) == True:
			return True
		else:
			return False


	def setMainScreenScale(self, mainscreenscale):		    	# overwrite the preset
		if Debug == True:
			print 'from jeol1230.py setMainScreenScale'
		self.mainscreenscale = mainscreenscale
		return True


	def getMainScreenScale(self):
		if Debug == True:
			print 'from jeol1230.py getMainScreenScale'
		return self.mainscreenscale								# What is screen scale?


	def getSpotSize(self):                              		# get the spotsize from 1 to 5
		if Debug == True:
			print 'from jeol1230.py getSpotSize'
		spotsize = self.jeol1230lib.getSpotSize()
		return spotsize


	def setSpotSize(self, ss, relative = 'absolute'):       	# set the spotsize from 1 to 5, ss might be a string
		if Debug == True:
			print 'from jeol1230.py setSpotSize'
		if relative == 'absolute':
			s = ss
		else:
			s = self.getSpotSize() + ss
		si = int(s)
		if self.jeol1230lib.setSpotSize(si) == True:
			return True
		else:
			return False


	def getStagePosition(self):                              	# return position in meter, angle in pi
		if Debug == True:
			print "from jeol1230.py getStagePosition"
		value = {'x': None, 'y': None, 'z': None, 'a': None}
		pos = self.jeol1230lib.getStagePosition()
		value['x'] = float(pos['x']/1e6)
		value['y'] = float(pos['y']/1e6)
		value['z'] = float(pos['z']/1e6)
		value['a'] = float(pos['a']/57.3)
		return value


	def setStagePosition(self, value):							# receive position in meter, angle in pi
		if Debug == True:
			print 'from jeol1230.py setStagePosition'
			print 'Sent value in Jeol1230 is: ', value
		Backlash = 20e-6											# 20 um
		prevalue = {'x': None, 'y': None, 'z': None, 'a': None}
		for axis in ('x', 'y', 'z', 'a'):
			if axis in value:
				if axis == 'a':
					prevalue[axis] = value[axis]*57.4
					mode = 'fine'
					self.jeol1230lib.setStagePosition(axis,prevalue[axis],mode)
				elif axis == 'z':
					prevalue[axis] = value[axis]*1e6
					mode = 'fine'
					self.jeol1230lib.setStagePosition(axis,prevalue[axis],mode)
				else:
					if self.correctedstage == False:
						prevalue[axis] = value[axis]*1e6
						mode = 'coarse'
						self.jeol1230lib.setStagePosition(axis,prevalue[axis],mode)
					else:
						prevalue[axis] = (value[axis] - Backlash)*1e6
						mode = 'coarse'
						self.jeol1230lib.setStagePosition(axis,prevalue[axis],mode)
						prevalue[axis] = value[axis]*1e6
						mode = 'fine'
						self.jeol1230lib.setStagePosition(axis,prevalue[axis],mode)			# in micrometer
		return True


	def getCorrectedStagePosition(self):
		if Debug == True:
			print 'from jeol1230.py getCorrectedStagePosition'
		return self.correctedstage


	def setCorrectedStagePosition(self, value):
		if Debug == True:
			print 'from setCorrectedStagePosition'
		self.correctedstage = bool(value)
		return self.correctedstage								# will return True or False

	
	def getDefocus(self):										# Leginon requires meter unit(negative)
		if Debug == True:
			print 'from jeol1230.py getDefocus'
		defocus = self.jeol1230lib.getDefocus()
		return float(defocus)


	def setDefocus(self, defocus, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setDefocus'
		if relative == 'absolute':
			ss = float(defocus)
		else:
			ss = float(defocus) + self.getDefocus()
		if self.jeol1230lib.setDefocus(ss) == True:
			return True
		else:
			return False

	# focus is recoreded as a reference for proceeding Z-height adjustment.
	# The native focus value from Tecnai is normalized to -1 to 1.
	def getFocus(self):											# unit is meter
		if Debug == True:
			print 'from getFocus'
		pos = self.jeol1230lib.getStagePosition()
		focus  = float(pos['z'])/1e6
		return focus


	def setFocus(self, value):									# unit is meter
		if Debug == True:
			print 'from setFocus'
		if self.jeol1230lib.setStagePosition('z', float(value)*1e6, 'coarse') ==  True:   # move stage in Z direction only
			return Ture
		else:
			return False


	def resetDefocus(self, value = 0):
		if Debug == True:
			print 'from jeol1230.py resetDefocus'
		self.jeol1230lib.resetDefocus(value)
		return True


	def getResetDefocus(self):
		if Debug == True:
			print 'from jeol1230.py getResetDefocus'
		self.jeol1230lib.resetDefocus(0)
		return True


	def getObjectiveExcitation(self):
		if Debug == True:
			print 'from getObjectiveExcitation'
		return NotImplementedError()


	def getIntensity(self):
		if Debug == True:
			print 'from jeol1230.py getIntensity'
		intensity = self.jeol1230lib.getIntensity()
		return int(intensity)


	def setIntensity(self, intensity, relative = 'absolute'):
		if Debug == True:
			print 'from from jeol1230.py setIntensity'
		if relative == 'absolute':
			ss = int(intensity)
		else:
			ss = int(intensity) + self.getIntensity()
		if self.jeol1230lib.setIntensity(ss) == True:
			return True
		else:
			return False


	def getBeamTilt(self):
		if Debug == True:
			print 'from getBeamTilt'
		beamtilt = {'x': None, 'y': None}
		beamtilt = self.jeol1230lib.getBeamTilt()
		return beamtilt


	def setBeamTilt(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setBeamTilt'
		for axis in ('x', 'y'):
			if axis in vector:
				if relative == 'absolute':
					self.jeol1230lib.setBeamTilt(axis, vector[axis])
				else:
					now = {'x': None, 'y': None}
					now = self.jeol1230lib.getBeamTilt()
					target = {'x': None, 'y': None}
					target[axis] = int(now[axis]) + int(vector[axis])
					self.jeol1230lib.setBeamTilt(axis, target[axis])
		return True


	def getBeamShift(self):
		if Debug == True:
			print 'from jeol1230.py getBeamShift'
		value = {'x': None, 'y': None}
		value = self.jeol1230lib.getBeamShift()
		return value


	def setBeamShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setBeamShift'
		for axis in ('x', 'y'):
			if axis in vector:
				if relative == 'absolute':
					self.jeol1230lib.setBeamShift(axis, vector[axis])
				else:
					now = {'x': None, 'y': None}
					now = self.jeol1230lib.getBeamShift()
					target = {'x': None, 'y': None}
					target[axis] = int(now[axis]) + int(vector[axis])
					self.jeol1230lib.setBeamShift(axis, target[axis])
		return True


	def getImageShift(self):									# Low dose in meter
		if Debug == True:
			print 'from jeol1230.py getImageShift'
		vector = {'x': None, 'y': None}
		vector = self.jeol1230lib.getImageShift()
		return vector

	
	def setImageShift(self, vector, relative = 'absolute'):		# Low dose in memter
		if Debug == True:
			print 'from jeol1230.py setImageShift'
		for axis in ('x', 'y'):
			if axis in vector:
				if relative == 'absolute':
					self.jeol1230lib.setImageShift(axis, vector[axis])
				else:
					now = {'x': None, 'y': None}
					now = self.jeol1230lib.getImageShift()
					target = {'x': None, 'y': None}
					target[axis] = int(now[axis]) + int(vector[axis])
					self.jeol1230lib.setImageShift(axis, target[axis])
		return True


	def getStigmator(self):
		if Debug == True:
			print 'from jeol1230.py getStigmator'
		vector = {'condenser': {'x': None, 'y': None},'objective': {'x': None, 'y': None},'diffraction': {'x': None, 'y': None}}
		vector = self.jeol1230lib.getStigmator()
		return vector
		
	
	def setStigmator(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setStigmator'
			print '    vector is', vector, relative
		for key in ('condenser', 'objective', 'diffraction'):
			if key in vector:
				for axis in ('x','y'):
					if axis in vector[key]:
						if relative == 'absolute':
							self.jeol1230lib.setStigmator(key, axis, vector[key][axis])
						else:
							now = {'condenser': {'x': None, 'y': None},
									'objective': {'x': None, 'y': None},
									'diffraction': {'x': None, 'y': None}}
							now = self.jeol1230lib.getStigmator()
							value = {'condenser': {'x': None, 'y': None},
									'objective': {'x': None, 'y': None},
									'diffraction': {'x': None, 'y': None}}							
							value[key][axis] = int(now[key][axis]) + int(vector[key][axis])
							self.jeol1230lib.setStigmator(key, axis, value[key][axis])
		return True


	def getGunShift(self):
		if Debug == True:
			print 'from getGunShift'
		return NotImplementedError()


	def setGunShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setGunShift'
		return NotImplementedError()


	def getGunTilt(self):
		if Debug == True:
			print 'from getGunTilt'
		return NotImplementedError()


	def setGunTilt(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setGunTilt'
		return NotImplementedError()


	def getDarkFieldMode(self):
		if Debug == True:
			print 'from jeol1230.py getDarkFieldMode'
		return 'on'


	def setDarkFieldMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setDarkFieldMode'
		return True


	def getRawImageShift(self):									# HRTEM mode in memter
		if Debug == True:
			print 'from jeol1230.py getRawImageShift'
		vector = {'x': None, 'y': None}
		vector = self.jeol1230lib.getImageShift()
		return vector


	def setRawImageShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setRawImageShift'
		now = {'x': None, 'y': None}
		now = self.jeol1230lib.getImageShift()
		for axis in ('x', 'y'):
			if axis in vector:
				if relative == 'absolute':
					self.jeol1230lib.setImageShift(axis, vector[axis])
				else:
					target = {'x': None, 'y': None}
					target[axis] = int(now[axis]) + int(vector[axis])
					self.jeol1230lib.setImageShift(axis, target[axis])
		return True


	def getVacuumStatus(self):
		if Debug == True:
			print "from jeol1230.py getVacuumStatus"
		return 'unknown'

	
	def getColumnPressure(self):
		if Debug == True:
			print 'from jeol1230.py getColumnPressure'
		return 1.0

	
	def getFilmStock(self):
		if Debug == True:
			print 'from jeol1230.py getFilmStock'
		return 1


	def setFilmStock(self):
		if Debug == True:
			print 'from jeol1230.py setFilmStock'
		return NotImplementedError()


	def getFilmExposureNumber(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureNumber'
		return 1


	def setFilmExposureNumber(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmExposureNumber'
		return NotImplementedError()


	def getFilmExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureTime'
		return 1.0


	def getFilmExposureTypes(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureTypes'
		return ['manual', 'automatic','unknown']


	def getFilmExposureType(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureType'
		return 'unknown'


	def setFilmExposureType(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmExposureType'
		return NotImplementedError()


	def getFilmAutomaticExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmAutomaticExposureTime'
		return 1.0


	def getFilmManualExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmManualExposureTime'
		return 1


	def setFilmManualExposureTime(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmManualExposureTime'
		return NotImplementedError()


	def getFilmUserCode(self):
		if Debug == True:
			print 'from jeol1230.py getFilmUserCode'
		return str('mhu')


	def setFilmUserCode(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmUserCode'
		return NotImplementedError()


	def getFilmDateTypes(self):
		if Debug == True:
			print 'from jeol1230.py getFilmDateTypes'
		return ['no date', 'DD-MM-YY', 'MM/DD/YY', 'YY.MM.DD', 'unknown']


	def getFilmDateType(self):
		if Debug == True:
			print 'from jeol1230.py getFilmDateType'
		return 'unknown'


	def setFilmDateType(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmDateType'
		return NotImplementedError()

	
	def getFilmText(self):
		if Debug == True:
			print 'from jeol1230.py getFilmText'
		return str('Minghui Hu')


	def setFilmText(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmText'
		return NotImplementedError()

	
	def getShutter(self):
		if Debug == True:
			print 'from jeol1230.py getShutter'
		return 'unknown'


	def setShutter(self, state):
		if Debug == True:
			print 'from jeol1230.py setShutter'
		return NotImplementedError()


	def getShutterPositions(self):
		if Debug == True:
			print 'from jeol1230.py getShutterPositions'
		return ['open', 'closed','unknown']


	def getExternalShutterStates(self):
		if Debug == True:
			print 'from jeol1230.py getExternalShutterStates'
		return ['connected', 'disconnected','unknown']

	def getExternalShutter(self):    						# no external shutter available from CM
		if Debug == True:
			print 'from jeol1230.py getExternalShutter'
		return 'unknown'


	def setExternalShutter(self, state):
		if Debug == True:
			print 'from jeol1230.py setExternalShutter'
		return NotImplementedError()


	def normalizeLens(self, lens = 'all'):
		if Debug == True:
			print 'from jeol1230.py normalizeLens'
		return NotImplementedError()


	def getScreenCurrent(self):									# small screen must be down, unit in Ampire
		if Debug == True:
			print 'from jeol1230.py getScreenCurrent'
		return 1.0


	def getMainScreenPositions(self):
		if Debug == True:
			print 'from jeol1230.py getMainScreenPositions'
		return ['up', 'down', 'unknown']


	def setMainScreenPosition(self, mode):
		if Debug == True:
			print 'from jeol1230.py setMainScreenPosition'
		return True										# I changed it to true


	def getMainScreenPosition(self):
		if Debug == True:
			print 'from jeol1230.py getManinScreenPostion'
		return 'down'


	def getSmallScreenPositions(self):
		if Debug == True:
			print 'from jeol1230.py getSmallScreenPositions'
		return ['up', 'down', 'unknown']


	def getSmallScreenPosition(self):
		if Debug == True:
			print 'from jeol1230.py getSmallScreenPosition' 
		return 'unknown'                


	def getHolderStatus(self):
		if Debug == True:
			print 'from jeol1230.py getHolderStatus'
		return 'Inserted'


	def getHolderTypes(self):
		if Debug == True:
			print 'from jeol1230.py getHolderTypes'
		return ['no holder', 'single tilt', 'cryo', 'unknown']


	def getHolderType(self):
		if Debug == True:
			print 'from jeol1230.py getHolderType'
		return 'unknown'


	def setHolderType(self, holdertype):
		if Debug == True:
			print 'from jeol1230.py setHolderType'
		return NotImplementedError()


	def getLowDoseModes(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseModes'
		return ['exposure', 'focus1', 'focus2', 'search', 'unknown', 'disabled']


	def getLowDoseMode(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseMode'
		return 'unknown'


	def setLowDoseMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setLowDoseMode'
		return NotImplementedError()


	def getLowDoseStates(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseStates'
		return ['on', 'off', 'disabled','unknown']


	def getLowDose(self):
		if Debug == True:
			print 'from jeol1230.py getLowDose'
		return 'unknown'


	def setLowDose(self, ld):
		if Debug == True:
			print 'from jeol1230.py setLowDose'
		return NotImplementedError()


	def getStageStatus(self):
		if Debug == True:
			print 'from jeol1230.py getStageStatus'
		return 'unknown'


	def getVacuumStatus(self):
		if Debug == True:
			print 'from jeol1230.py getVacuumStatus'
		return 'unknown'


	def preFilmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py preFilmExposure'
		return NotImplementedError()


	def postFilmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py postFilmExposure'
		return NotImplementedError()


	def filmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py filmExposure'
		return NotImplementedError()


	def getBeamBlank(self):
		if Debug == True:
			print 'from jeol1230.py getBeamBlank'
		return 'unknown'										# should be 'unknowm'

		
	def setBeamBlank(self, bb):									# There is no beamblank
		if Debug == True:
			print 'from jeol1230.py setBeamBlank'
		return NotImplementedError()							# I added this


	def getDiffractionMode(self):
		if Debug == True:
			print 'from jeol1230.py getDiffractionMode'
		return NotImplementedError()
		
		
	def setDiffractionMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setDiffractionMode'
		return NotImplementedError()


	def runBufferCycle(self):
		if Debug == True:
			print 'from jeol1230.py runBufferCycle'
		return NotImplementedError()
