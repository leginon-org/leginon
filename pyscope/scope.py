#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
class Scope:
	def exit(self):
		pass
	def normalizeLens(self, lens = "all"):
		raise NotImplementedError
	def getScreenCurrent(self):
		raise NotImplementedError
	def getGunTilt(self):
		raise NotImplementedError
	def setGunTilt(self, vector, relative = "absolute"):
		raise NotImplementedError
	def getGunShift(self):
		raise NotImplementedError
	def setGunShift(self, vector, relative = "absolute"):
		raise NotImplementedError
	def getHighTension(self):
		raise NotImplementedError
	def setHighTension(self, ht):
		raise NotImplementedError
	def getIntensity(self):
		raise NotImplementedError
	def setIntensity(self, intensity, relative = "absolute"):
		raise NotImplementedError
	def getDarkFieldMode(self):
		raise NotImplementedError
	def setDarkFieldMode(self, mode):
		raise NotImplementedError
	def getBeamBlank(self):
		raise NotImplementedError
	def setBeamBlank(self, bb):
		raise NotImplementedError
	def getStigmator(self):
		raise NotImplementedError
	def setStigmator(self, stigs, relative = "absolute"):
		raise NotImplementedError
	def getSpotSize(self):
		raise NotImplementedError
	def setSpotSize(self, ss, relative = "absolute"):
		raise NotImplementedError
	def getBeamTilt(self):
		raise NotImplementedError
	def setBeamTilt(self, vector, relative = "absolute"):
		raise NotImplementedError
	def getBeamShift(self):
		raise NotImplementedError
	def setBeamShift(self, vector, relative = "absolute"):
		raise NotImplementedError
	def getImageShift(self):
		raise NotImplementedError
	def setImageShift(self, vector, relative = "absolute"):
		raise NotImplementedError
	def getDefocus(self):
		raise NotImplementedError
	def setDefocus(self, defocus, relative = "absolute"):
		raise NotImplementedError
	def resetDefocus(self):
		raise NotImplementedError
	def getMagnification(self):
		raise NotImplementedError
	def setMagnification(self, mag):
		raise NotImplementedError
	def getStagePosition(self):
		raise NotImplementedError
	def setStagePosition(self, position, relative = "absolute"):
		raise NotImplementedError
	def getLowDose(self):
		raise NotImplementedError
	def setLowDose(self, ld):
		raise NotImplementedError
	def getLowDoseMode(self):
		raise NotImplementedError
	def setLowDoseMode(self, mode):
		raise NotImplementedError
	def getDiffractionMode(self):
		raise NotImplementedError
	def setDiffractionMode(self, mode):
		raise NotImplementedError
	def filmExposure(self):
		raise NotImplementedError
	def getScreen(self):
		raise NotImplementedError
	def setScreen(self, mode):
		raise NotImplementedError
	def getHolderStatus(self):
		raise NotImplementedError
	def getHolderType(self):
		raise NotImplementedError
	def setHolderType(self, holdertype):
		raise NotImplementedError
	def getStageStatus(self):
		raise NotImplementedError
	def getTurboPump(self):
		raise NotImplementedError
	def setTurboPump(self, mode):
		raise NotImplementedError
	def getColumnValves(self):
		raise NotImplementedError
	def setColumnValves(self, state):
		raise NotImplementedError
	def getVacuumStatus(self):
		raise NotImplementedError
	def getColumnPressure(self):
		raise NotImplementedError
