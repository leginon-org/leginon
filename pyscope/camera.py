#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
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

