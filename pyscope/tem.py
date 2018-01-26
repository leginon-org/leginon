# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import baseinstrument
import config

class TEM(baseinstrument.BaseInstrument):
	name = None
	capabilities = baseinstrument.BaseInstrument.capabilities + (
		######## get only
		{'name': 'ColumnPressure', 'type': 'property'},
		{'name': 'ProjectionPressure', 'type': 'property'},
		{'name': 'BufferTankPressure', 'type': 'property'},
		{'name': 'ColumnValvePositions', 'type': 'property'},
		{'name': 'ExternalShutterStates', 'type': 'property'},
		{'name': 'FilmAutomaticExposureTime', 'type': 'property'},
		{'name': 'FilmDateTypes', 'type': 'property'},
		{'name': 'FilmExposureTime', 'type': 'property'},
		{'name': 'FilmExposureTypes', 'type': 'property'},
		{'name': 'HighTensionState', 'type': 'property'},
		{'name': 'HighTensionStates', 'type': 'property'},
		{'name': 'HolderStatus', 'type': 'property'},
		{'name': 'HolderTypes', 'type': 'property'},
		{'name': 'LowDoseModes', 'type': 'property'},
		{'name': 'LowDoseStates', 'type': 'property'},
		{'name': 'Magnifications', 'type': 'property'},
		{'name': 'MainScreenMagnification', 'type': 'property'},
		{'name': 'MainScreenPositions', 'type': 'property'},
		{'name': 'ObjectiveExcitation', 'type': 'property'},
		{'name': 'ScreenCurrent', 'type': 'property'},
		{'name': 'ShutterPositions', 'type': 'property'},
		{'name': 'SmallScreenPosition', 'type': 'property'},
		{'name': 'SmallScreenPositions', 'type': 'property'},
		{'name': 'StageStatus', 'type': 'property'},
		{'name': 'VacuumStatus', 'type': 'property'},
		{'name': 'BeamBlankedDuringCameraExchange', 'type': 'property'},

		######## get/set
		{'name': 'BeamBlank', 'type': 'property'},
		{'name': 'BeamShift', 'type': 'property'},
		{'name': 'BeamTilt', 'type': 'property'},
		{'name': 'ColumnValvePosition', 'type': 'property'},
		{'name': 'CorrectedStagePosition', 'type': 'property'},
		{'name': 'DarkFieldMode', 'type': 'property'},
		{'name': 'Defocus', 'type': 'property'},
		{'name': 'DiffractionMode', 'type': 'property'},
		{'name': 'Emission', 'type': 'property'},
		{'name': 'ExternalShutter', 'type': 'property'},
		{'name': 'FilmDateType', 'type': 'property'},
		{'name': 'FilmExposureNumber', 'type': 'property'},
		{'name': 'FilmExposureType', 'type': 'property'},
		{'name': 'FilmManualExposureTime', 'type': 'property'},
		{'name': 'FilmStock', 'type': 'property'},
		{'name': 'FilmText', 'type': 'property'},
		{'name': 'FilmUserCode', 'type': 'property'},
		{'name': 'Focus', 'type': 'property'},
		{'name': 'GunShift', 'type': 'property'},
		{'name': 'GunTilt', 'type': 'property'},
		{'name': 'HighTension', 'type': 'property'},
		{'name': 'HolderType', 'type': 'property'},
		{'name': 'ImageShift', 'type': 'property'},
		{'name': 'Intensity', 'type': 'property'},
		{'name': 'LowDose', 'type': 'property'},
		{'name': 'LowDoseMode', 'type': 'property'},
		{'name': 'Magnification', 'type': 'property'},
		{'name': 'MainScreenPosition', 'type': 'property'},
		{'name': 'ProbeMode', 'type': 'property'},
		{'name': 'RawImageShift', 'type': 'property'},
		{'name': 'Shutter', 'type': 'property'},
		{'name': 'SpotSize', 'type': 'property'},
		{'name': 'StagePosition', 'type': 'property'},
		{'name': 'Stigmator', 'type': 'property'},
		{'name': 'TurboPump', 'type': 'property'},
		{'name': 'ProjectionSubModeMap', 'type': 'property'},

		######## methods
		{'name': 'filmExposure', 'type': 'method'},
		{'name': 'findMagnifications', 'type': 'method'},
		{'name': 'normalizeLens', 'type': 'method'},
		{'name': 'postFilmExposure', 'type': 'method'},
		{'name': 'preFilmExposure', 'type': 'method'},
		{'name': 'resetDefocus', 'type': 'method'},
		{'name': 'relaxBeam', 'type': 'method'},
		{'name': 'runBufferCycle', 'type': 'method'},
		{'name': 'nextPhasePlate', 'type': 'method'},

		## optional:
		{'name': 'EnergyFilter', 'type': 'property'},
		{'name': 'EnergyFilterWidth', 'type': 'property'},
	)
	projection_lens_program = 'TEM'
	def __init__(self):
		baseinstrument.BaseInstrument.__init__(self)
		self.config_name = config.getNameByClass(self.__class__)
		self.cs = config.getConfigured()[self.config_name]['cs']
		self.projection_submode_map = {}
		self.grid_inventory = {}

	def getCs(self):
		return self.cs

	def getEnergyFiltered(self):
		return False

	def exposeSpecimenNotCamera(self,seconds):
		raise NotImplementedError()

	def getProbeMode(self):
		return 'default'

	def setProbeMode(self, probe_str):
		pass

	def getProbeModes(self):
		return ['default']

	def getProjectionSubModeMap(self):
		return self.projection_submode_map

	def setProjectionSubModeMap(self, mode_map):
		'''
		called by EM.py to set self.projetion_submode_map
		{mag:(mode_name,mode_id)}
		'''
		self.projection_submode_map = mode_map

	def addProjectionSubModeMap(self, mag, mode_name, mode_id, overwrite=False):
		# Only do it once
		overwritten = False
		if mag in self.projection_submode_map.keys():
			if not overwrite:
				return overwritten
			else:
				overwritten = True
		self.projection_submode_map[mag] = (mode_name,mode_id)
		return overwritten

	def getProjectionSubModeName(self):
		mag = self.getMagnification()
		try:
			return self.projection_submode_map[mag][0]
		except:
			# get an error if setProjectionSubModeMapping is not called from leginon/EM.py
			raise NotImplementedError()

	def relaxBeam(self,steps=3,interval=0.1,totaltime=2):
		'''
		Only needed for JEOL scopes
		'''
		pass

	def nextPhasePlate(self):
		print "next position"

	def getColumnPressure(self):
		return 1.0

	def getProjectionChamberPressure(self):
		return 1.0

	def getBufferTankPressure(self):
		return 1.0

	def getBeamBlankedDuringCameraExchange(self):
		return True

	def getRefrigerantLevel(self,id=0):
		'''
		return refrigerant level nitrogen filler. id 0 is the grid loader.
		id 1 is the column cold trap, This default is for timed filling
		regardless of the filler id.
		'''
		if self.isTimedFilling():
			return 0.0
		else:
			return 100.0

	def hasAutoFiller(self):
		return False

	def runAutoFiller(self):
		'''
		Start AutoFiller. Default is a timed filler
		'''
		pass

	def getTimedN2FillParams(self):
		'''
		Return tuple of three parameters for timed nitrogen filler.
		Item 1: a list of nitrogen fill start times in minutes since midnight.
		Item 2: length of fill time in minutes
		Item 3: minutes of clock on this computer ahead of the filler clock.
		'''
		return [],2,0


	def isTimedFilling(self):
		import datetime
		# wait time settings
		now = datetime.datetime.now()
		hr = now.hour
		minute = now.minute
		minute_since_midnight = hr*60 + minute
		return self.withinN2FillTime(minute_since_midnight)

	def withinN2FillTime(self, my_clock_now):
		'''
		check if the minute clock is within the filling period of the filler.
		my_clock_now is in unit of minute since midnight.
		myclock_ahead accounts for clock differences between my clock
		and filler clock. It can also be used to apply an earlier trigger time as
		a buffer.  For example, set to -5 to pause Leginon 5 minutes before
		a scheduled fill.
		'''
		fill_starts, fill_time, myclock_ahead = self.getTimedN2FillParams()
		# handle filler computer clock is offset slightly
		fill_starts = list(fill_starts)
		fill_starts.extend(map((lambda x: x+24*60), fill_starts))
		fill_starts.extend(map((lambda x: x-24*60), fill_starts))

		filler_clock_now = my_clock_now - myclock_ahead
		for t in fill_starts:
			if (filler_clock_now >= t and filler_clock_now < t + fill_time):
				return True
		return False

	def isAutoFillerBusy(self):
		is_busy = self.isTimedFilling()
		return is_busy

	def hasGridLoader(self):
		return False

	def getGridLoaderNumberOfSlots(self):
		return 1

	def getGridLoaderSlotState(self, number):
		return 'empty'

	def loadGridCartridge(self, number):
		if not self.hasGridLoader():
			return
		if number not in range(1,self.getGridLoaderNumberOfSlots()+1):
			return
		if self.getGridLoaderSlotState(number) != 'occupied':
			raise ValueError('Grid %d is not occupied' % number)
		# now load
		try:
			self._loadCartridge(number)
		except RuntimeError, e:
			raise RuntimeError('Grid Loading failed')

	def unloadGridCartridge(self):
		if not self.hasGridLoader():
			return
		
		has_empty = False
		for number in range(1,self.getGridLoaderNumberOfSlots()+1):
			if self.getGridLoaderSlotState(number) == 'empty':
				has_empty = True
				break
		if not has_empty:
			raise ValueError('No empty slot to unload')
		# now unload
		try:
			self._unloadCartridge()
		except RuntimeError, e:
			raise RuntimeError('Grid unLoading failed')

	def _loadCartridge(self, number):
		raise NotImplementedError()

	def _unloadCartridge(self):
		raise NotImplementedError()

	def getGridLoaderInventory(self):
		return self.grid_inventory

	def getAllGridSlotStates(self):
		if not self.hasGridLoader():
			return {}
		nslots = self.getGridLoaderNumberOfSlots()
		for i in range(nslots):
			n = i + 1
			state = self.getGridLoaderSlotState(n)
			self.grid_inventory[n] = state
		return self.grid_inventory

	def setDirectStagePosition(self,value):
		'''
		set stage position without correction or checking
		for move size.
		'''
		# equivalent to normal movement by default
		self.setStagePosition(value)

	def getDiffractionMode(self):
		# valid values: imaging or diffraction
		return 'imaging'

	def setDiffractionMode(self):
		raise NotImplementedError()

	def getVacuumStatus(self):
		# valid values: ready, off, busy, unknown
		return 'ready'

