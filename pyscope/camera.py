class Camera:
	def __init__(self):
		self.arraytypecode = None

	def exit(self):
		pass

	def getImage(self, offset, dimension, binning, exposure_time):
		raise NotImplementedError

	def getInserted(self):
		raise NotImplementedError

	def setInserted(self, value):
		raise NotImplementedError

