class camera:
	def __init__(self):
		self.arraytypecode = None

	def exit(self):
		pass

	def getImage(self, offset, dimension, binning, exposure_time):
		raise NotImplementedError
