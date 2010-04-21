# jeol1230.py is implemented for Jeol 1230 electron microscope
# Copyright by New York Structural Biology Center
# from pyScope import jeol1230 ; j = jeol1230.jeol1230()

import time
import math
from pyscope import tem
from pyscope import jeol1230lib

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
		self.mainscreenscale = 1.0

	# define three high tension states
	def getHighTensionStates(self):
		if Debug == True:
			print 'from jeol1230.py getHighTensionStates'
		hts = ['off', 'on', 'disabled']
		return hts

	# get high tenstion status as on or off
	def getHighTensionState(self):
		if Debug == True:
			print 'from jeol1230.py getHighTensionState'
		highTensionState = self.jeol1230lib.getHighTensionState()
		return highTensionState

	# get high tenstion voltage
	def getHighTension(self):
		if Debug == True:
			print 'from jeol1230.py getHighTension'
		if self.jeol1230lib.getHighTensionState() == 'on':
			highTension = self.jeol1230lib.getHighTension()
		else:
			highTension = 0
		return highTension

	# turn on or off high tension
	def setHighTension(self, mode = 'off'):
		if Debug == True:
			print 'from jeol1230.py setHighTension'
		return True

	# get three colum valve positions, not work for 1230
	def getColumnValvePositions(self):
		if Debug == True:
			print "from jeol1230.py getColumnValvePositions"
		return ['on', 'off','unknown']

	# attension: changed this to beam state
	def getColumnValvePosition(self):
		if Debug == True:
			print 'from jeol1230.py getColumnValvePostion'
		return self.getBeamState()

	# attension: change this to beam state
	def setColumnValvePosition(self, state = 'off'):
		if Debug == True:
			print 'from jeol1230.py setColumnValvePosition'
		if self.jeol1230lib.setBeamOnOff(state) == True:
			return True
		else:
			return False

	# get the beam satus as on or off
	def getBeamState(self):
		if Debug == True:
			print "from jeol1230.py getBeamState"
		beamState = self.jeol1230lib.getBeamState()
		return beamState

	# attension: pump is changed to beam operation
	def getTurboPump(self):
		if Debug == True:
			print "from jeol1230.py getTurboPump"
		beamState = self.jeol1230lib.getBeamState()
		return beamState

	# attension: set the beam status
	def setBeamState(self, mode = 'off'):
		if Debug == True:
			print "from jeol1230.py setBeamOnOff"
		if self.jeol1230lib.setBeamState(mode) == True:
			return True
		else:
			return False

	def setEmission(self, value):
		modes = {True:'on',False:'off'}
		self.setBeamState(modes[value])

	def getEmission(self):
		return self.tom.Gun.Emission

	# attension: set the beam status, the same as the above
	def setTurboPump(self, mode = 'off'):
		if Debug == True:
			print "from jeol1230.py setTurboPump"
		if self.jeol1230lib.setBeamState(mode) == True:
			return True
		else:
			return False

	# initialize all possible magnifications
	def setMagnifications(self, magnifications):
		if Debug == True:
			print 'from jeol1230.py setMagnifications'
		self.magnifications = magnifications
		return True

	# get all possible magnifications
	def findMagnifications(self):
		if Debug == True:
			print 'from jeol1230.py findMagnifications'
		magnifications = jeol1230lib.magnification
		self.setMagnifications(magnifications)
		return True

	# check if self.magnifications is initialized sucessfully
	def getMagnificationsInitialized(self):
		if Debug == True:
			print "from jeol1230.py getMagnificationsInitialized"
		if self.magnifications:
			return True
		else:
			return False

	# return self.magnifications
	def getMagnifications(self):
		if Debug == True:
			print "from jeol1230.py getMagnifications"
		return self.magnifications

	# return a magnification number using an index
	def getMagnification(self, index = None):
		if Debug == True:
			print "from jeol1230.py getMagnification"
		if index is None:
			return self.jeol1230lib.getMagnification()
		elif int(index) > 40 or int(index) < 0:
			print '    Valid magnification index should be 0-40'
			return
		else:
			return self.magnifications[index]

	# return the actual Mag value
	def getMainScreenMagnification(self):
		if Debug == True:
			print 'from jeol1230.py getMainScreenMagnification'
		return self.jeol1230lib.getMagnification()

	#  get mag index position between 0 and 40
	def _emcGetMagPosition(self,magnification):
		if Debug == True:
			print 'from jeol1230.py _emcGetMagPostion'
		magRange = 40
		mags = jeol1230lib.magnification
		for magIndex in range(0,magRange):
			if int(magnification) <= mags[magIndex]:
				break
		if magIndex > magRange:
			print '    magnification out of range'
		return magIndex

	# get mag index position between 0 and 40
	def getMagnificationIndex(self, magnification):
		if Debug == True:
			print 'from jeol1230.py getMagnificationIndex'
		magIndex = self._emcGetMagPosition(magnification)
		return int(magIndex)

	# set magnification using magnification
	def setMagnification(self, magnification):
		if Debug == True:
			print 'from jeol1230.py setMagnification'
		self.jeol1230lib.setMagnification(magnification)
		return True

	# set magnification using magnification index
	def setMagnificationIndex(self, magIndex):
		if Debug == True:
			print 'from jeol1230.py setMagnificationIndex'
		magnification = self.getMagnification(magIndex)
		if self.jeol1230lib.setMagnification(magnification) == True:
			return True
		else:
			return False

	# don't understand it well, but it works
	def setMainScreenScale(self, mainscreenscale = 1.0):
		if Debug == True:
			print 'from jeol1230.py setMainScreenScale'
		self.mainscreenscale = mainscreenscale
		return True

	# anyway, it works
	def getMainScreenScale(self):
		if Debug == True:
			print 'from jeol1230.py getMainScreenScale'
		return self.mainscreenscale

	# get current spot size
	def getSpotSize(self):
		if Debug == True:
			print 'from jeol1230.py getSpotSize'
		spotsize = self.jeol1230lib.getSpotSize()
		return spotsize

	# set spot size between 1 and 5 as a string
	def setSpotSize(self, spotSize, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setSpotSize'
		if relative == 'absolute':
			s = int(spotSize)
		else:
			s = int(self.getSpotSize() + spotSize)
		if self.jeol1230lib.setSpotSize(s) == True:
			return True
		else:
			return False

	# return position in meter, angle in pi
	def getStagePosition(self):
		if Debug == True:
			print "from jeol1230.py getStagePosition"
		value = {'x': None, 'y': None, 'z': None, 'a': None}
		pos = self.jeol1230lib.getStagePosition()
		value['x'] = float(pos['x']/1e6)
		value['y'] = float(pos['y']/1e6)
		value['z'] = float(pos['z']/1e6)
		value['a'] = float(pos['a']/57.3)
		return value

	# receive position in meter, angle in pi, backlash is 30 um
	def setStagePosition(self, value):
		if Debug == True:
			print 'from jeol1230.py setStagePosition'
		Backlash = 30e-6
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
				elif axis == 'x' or axis == 'y':
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
				else:
					return False
		return True

	# default is correct stage movement
	def getCorrectedStagePosition(self):
		if Debug == True:
			print 'from jeol1230.py getCorrectedStagePosition'
		return self.correctedstage

	# set the stage move to back or not
	def setCorrectedStagePosition(self, value = 'True'):
		if Debug == True:
			print 'from setCorrectedStagePosition'
		self.correctedstage = bool(value)
		return self.correctedstage

	# get defocus value, Leginon requires meter unit(negative)
	def getDefocus(self):
		if Debug == True:
			print 'from jeol1230.py getDefocus'
		defocus = self.jeol1230lib.getDefocus()
		return float(defocus)

	# set defocus value
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
	# unit is meter
	def getFocus(self):											
		if Debug == True:
			print 'from getFocus'
		pos = self.jeol1230lib.getStagePosition()
		focus  = float(pos['z'])/1e6
		return focus

	# set focus, unit is meter
	def setFocus(self, value):
		if Debug == True:
			print 'from setFocus'
		if self.jeol1230lib.setStagePosition('z', float(value)*1e6, 'coarse') ==  True:   # move stage in Z direction only
			return Ture
		else:
			return False

	# reset eucentric focus, it works when the reset button is clicked
	def resetDefocus(self, value = 0):
		if Debug == True:
			print 'from jeol1230.py resetDefocus'
		self.jeol1230lib.resetDefocus(value)
		return True

	# not sure about this
	def getResetDefocus(self):
		if Debug == True:
			print 'from jeol1230.py getResetDefocus'
		self.jeol1230lib.resetDefocus(0)
		return True

	# required by leginon
	def getObjectiveExcitation(self):
		if Debug == True:
			print 'from getObjectiveExcitation'
		return NotImplementedError()

	# get beam intensity
	def getIntensity(self):
		if Debug == True:
			print 'from jeol1230.py getIntensity'
		intensity = self.jeol1230lib.getIntensity()
		return int(intensity)

	# set beam intensity
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

	# get beam tilt
	def getBeamTilt(self):
		if Debug == True:
			print 'from getBeamTilt'
		beamtilt = {'x': None, 'y': None}
		beamtilt = self.jeol1230lib.getBeamTilt()
		return beamtilt

	# set beam tilt
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

	# get beam shift
	def getBeamShift(self):
		if Debug == True:
			print 'from jeol1230.py getBeamShift'
		value = {'x': None, 'y': None}
		value = self.jeol1230lib.getBeamShift()
		return value

	# set beam shift
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

	# get image shift in meter
	def getImageShift(self):
		if Debug == True:
			print 'from jeol1230.py getImageShift'
		vector = {'x': None, 'y': None}
		vector = self.jeol1230lib.getImageShift()
		return vector

	# set image shift in meter
	def setImageShift(self, vector, relative = 'absolute'):
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

	# get stigmator setting
	def getStigmator(self):
		if Debug == True:
			print 'from jeol1230.py getStigmator'
		vector = {'condenser': {'x': None, 'y': None},'objective': {'x': None, 'y': None},'diffraction': {'x': None, 'y': None}}
		vector = self.jeol1230lib.getStigmator()
		return vector

	# set stigmator setting
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

	# not implimented
	def getGunShift(self):
		if Debug == True:
			print 'from getGunShift'
		return NotImplementedError()

	# not implimented
	def setGunShift(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from setGunShift'
		return NotImplementedError()

	# not implimented
	def getGunTilt(self):
		if Debug == True:
			print 'from getGunTilt'
		return NotImplementedError()

	# not implimented
	def setGunTilt(self, vector, relative = 'absolute'):
		if Debug == True:
			print 'from jeol1230.py setGunTilt'
		return NotImplementedError()

	# not implimented
	def getDarkFieldMode(self):
		if Debug == True:
			print 'from jeol1230.py getDarkFieldMode'
		return 'on'

	# not implimented
	def setDarkFieldMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setDarkFieldMode'
		return True

	# not sure, but return in meter
	def getRawImageShift(self):
		if Debug == True:
			print 'from jeol1230.py getRawImageShift'
		vector = {'x': None, 'y': None}
		vector = self.jeol1230lib.getImageShift()
		return vector

	# not implimented
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

	# not implimented
	def getVacuumStatus(self):
		if Debug == True:
			print "from jeol1230.py getVacuumStatus"
		return 'unknown'

	# not implimented
	def getColumnPressure(self):
		if Debug == True:
			print 'from jeol1230.py getColumnPressure'
		return 1.0

	# not implimented
	def getFilmStock(self):
		if Debug == True:
			print 'from jeol1230.py getFilmStock'
		return 1

	# not implimented
	def setFilmStock(self):
		if Debug == True:
			print 'from jeol1230.py setFilmStock'
		return NotImplementedError()

	# not implimented
	def getFilmExposureNumber(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureNumber'
		return 1

	# not implimented
	def setFilmExposureNumber(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmExposureNumber'
		return NotImplementedError()

	# not implimented
	def getFilmExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureTime'
		return 1.0

	# not implimented
	def getFilmExposureTypes(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureTypes'
		return ['manual', 'automatic','unknown']

	# not implimented
	def getFilmExposureType(self):
		if Debug == True:
			print 'from jeol1230.py getFilmExposureType'
		return 'unknown'

	# not implimented
	def setFilmExposureType(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmExposureType'
		return NotImplementedError()

	# not implimented
	def getFilmAutomaticExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmAutomaticExposureTime'
		return 1.0

	# not implimented
	def getFilmManualExposureTime(self):
		if Debug == True:
			print 'from jeol1230.py getFilmManualExposureTime'
		return 1

	# not implimented
	def setFilmManualExposureTime(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmManualExposureTime'
		return NotImplementedError()

	# not implimented
	def getFilmUserCode(self):
		if Debug == True:
			print 'from jeol1230.py getFilmUserCode'
		return str('mhu')

	# not implimented
	def setFilmUserCode(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmUserCode'
		return NotImplementedError()

	# not implimented
	def getFilmDateTypes(self):
		if Debug == True:
			print 'from jeol1230.py getFilmDateTypes'
		return ['no date', 'DD-MM-YY', 'MM/DD/YY', 'YY.MM.DD', 'unknown']

	# not implimented
	def getFilmDateType(self):
		if Debug == True:
			print 'from jeol1230.py getFilmDateType'
		return 'unknown'

	# not implimented
	def setFilmDateType(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmDateType'
		return NotImplementedError()

	# not implimented
	def getFilmText(self):
		if Debug == True:
			print 'from jeol1230.py getFilmText'
		return str('Minghui Hu')

	# not implimented
	def setFilmText(self, value):
		if Debug == True:
			print 'from jeol1230.py setFilmText'
		return NotImplementedError()

	# not implimented
	def getShutter(self):
		if Debug == True:
			print 'from jeol1230.py getShutter'
		return 'unknown'

	# not implimented
	def setShutter(self, state):
		if Debug == True:
			print 'from jeol1230.py setShutter'
		return NotImplementedError()

	# not implimented
	def getShutterPositions(self):
		if Debug == True:
			print 'from jeol1230.py getShutterPositions'
		return ['open', 'closed','unknown']

	# not implimented
	def getExternalShutterStates(self):
		if Debug == True:
			print 'from jeol1230.py getExternalShutterStates'
		return ['connected', 'disconnected','unknown']

	# not implimented
	def getExternalShutter(self):
		if Debug == True:
			print 'from jeol1230.py getExternalShutter'
		return 'unknown'

	# not implimented
	def setExternalShutter(self, state):
		if Debug == True:
			print 'from jeol1230.py setExternalShutter'
		return NotImplementedError()

	# not implimented
	def normalizeLens(self, lens = 'all'):
		if Debug == True:
			print 'from jeol1230.py normalizeLens'
		return NotImplementedError()

	# not implimented
	def getScreenCurrent(self):
		if Debug == True:
			print 'from jeol1230.py getScreenCurrent'
		return 1.0

	# not implimented
	def getMainScreenPositions(self):
		if Debug == True:
			print 'from jeol1230.py getMainScreenPositions'
		return ['up', 'down', 'unknown']

	# not implimented
	def setMainScreenPosition(self, mode):
		if Debug == True:
			print 'from jeol1230.py setMainScreenPosition'
		return True				# I changed it to true

	# not implimented
	def getMainScreenPosition(self):
		if Debug == True:
			print 'from jeol1230.py getManinScreenPostion'
		return 'down'

	# not implimented
	def getSmallScreenPositions(self):
		if Debug == True:
			print 'from jeol1230.py getSmallScreenPositions'
		return ['up', 'down', 'unknown']

	# not implimented
	def getSmallScreenPosition(self):
		if Debug == True:
			print 'from jeol1230.py getSmallScreenPosition'
		return 'unknown'

	# not implimented
	def getHolderStatus(self):
		if Debug == True:
			print 'from jeol1230.py getHolderStatus'
		return 'Inserted'

	# not implimented
	def getHolderTypes(self):
		if Debug == True:
			print 'from jeol1230.py getHolderTypes'
		return ['no holder', 'single tilt', 'cryo', 'unknown']

	# not implimented
	def getHolderType(self):
		if Debug == True:
			print 'from jeol1230.py getHolderType'
		return 'unknown'

	# not implimented
	def setHolderType(self, holdertype):
		if Debug == True:
			print 'from jeol1230.py setHolderType'
		return NotImplementedError()

	# not implimented
	def getLowDoseModes(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseModes'
		return ['exposure', 'focus1', 'focus2', 'search', 'unknown', 'disabled']

	# not implimented
	def getLowDoseMode(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseMode'
		return 'unknown'

	# not implimented
	def setLowDoseMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setLowDoseMode'
		return NotImplementedError()

	# not implimented
	def getLowDoseStates(self):
		if Debug == True:
			print 'from jeol1230.py getLowDoseStates'
		return ['on', 'off', 'disabled','unknown']

	# not implimented
	def getLowDose(self):
		if Debug == True:
			print 'from jeol1230.py getLowDose'
		return 'unknown'

	# not implimented
	def setLowDose(self, ld):
		if Debug == True:
			print 'from jeol1230.py setLowDose'
		return NotImplementedError()

	# not implimented
	def getStageStatus(self):
		if Debug == True:
			print 'from jeol1230.py getStageStatus'
		return 'unknown'

	# not implimented
	def getVacuumStatus(self):
		if Debug == True:
			print 'from jeol1230.py getVacuumStatus'
		return 'unknown'

	# not implimented
	def preFilmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py preFilmExposure'
		return NotImplementedError()

	# not implimented
	def postFilmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py postFilmExposure'
		return NotImplementedError()

	# not implimented
	def filmExposure(self, value):
		if Debug == True:
			print 'from jeol1230.py filmExposure'
		return NotImplementedError()

	# not implimented
	def getBeamBlank(self):
		if Debug == True:
			print 'from jeol1230.py getBeamBlank'
		return 'unknown'

	# not implimented
	def setBeamBlank(self, bb):
		if Debug == True:
			print 'from jeol1230.py setBeamBlank'
		return NotImplementedError()

	# not implimented
	def getDiffractionMode(self):
		if Debug == True:
			print 'from jeol1230.py getDiffractionMode'
		return NotImplementedError()

	# not implimented
	def setDiffractionMode(self, mode):
		if Debug == True:
			print 'from jeol1230.py setDiffractionMode'
		return NotImplementedError()

	# not implimented
	def runBufferCycle(self):
		if Debug == True:
			print 'from jeol1230.py runBufferCycle'
		return NotImplementedError()
