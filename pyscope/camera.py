class camera:
	def __init__(self):
		self.binning = []
		self.size = {'x': 0,  'y': 0}

	def getImage(self, xOff, yOff, xDim, yDim, xBin, yBin, expTime):
		raise NotImplementedError
