import node
import math
import data
import correlation
import Numeric

class BetaCalibration(node.Node):
	def __init__(self, id, managerlocation):
		node.Node.__init__(self, id, managerlocation)
		self.start()

	def main(self):
		pass

	def imageshift(self, EMnodeid, shiftrange, attempts=1, \
				correlationthreshold=0.0, pixelshiftrange=(0.0, 1024.0)):

		for i in xrange(attempts):
			imageshift = (shiftrange[1] + shiftrange[0])/2
			shiftpair = ((shiftrange[1] + shiftrange[0])/4, \
										-(shiftrange[1] + shiftrange[0])/4) 
			statepair = ({'image shift': {'x': shiftpair[0], 'y': 0.0}}, \
										{'image shift': {'x': shiftpair[1], 'y': 0.0}})
			imagepair = self.imagePair(EMnodeid, statepair)
			correlationdata = correlation.correlation(imagepair[0], \
													imagepair[1], 0, 1, 1)
			pixelshiftmagnitude = \
				math.sqrt(correlationdata['phase correlation peak'][0]**2 \
									+ correlationdata['phase correlation peak'][1]**2)

			if not self.correlates(correlationdata, correlationthreshold):
				# images don't correlate, need smaller shift
				shiftrange = (shiftrange[0], imageshift)
			else: # images correlate, check if pixel shift is good
				if (pixelshiftmagnitude >= pixelshiftrange[0]) \
							and (pixelshiftmagnitude <= pixelshiftrange[1]):
					return {'pixel shift': correlationdata['phase correlation peak'],
									'image shift': imageshift}
				elif pixelshiftmagnitude > pixelshiftrange[1]:
					shiftrange = (shiftrange[0], imageshift)
				elif pixelshiftmagnitude < pixelshiftrange[0]:
					shiftrange = (imageshift, shiftrange[1])

		return None

	def correlates(self, correlationdata, correlationthreshold):
		if correlationdata['phase correlation image'][correlationdata['phase correlation index']] > correlationthreshold:
			return 1
		else:
			return 0

	def imagePair(self, EMnodeid, statepair):
		self.publishRemote(EMnodeid, data.EMData(self.ID(), statepair[0]))
		image1 = self.researchByDataID('image data').content['image data']
		self.publishRemote(EMnodeid, data.EMData(self.ID(), statepair[1]))
		image2 = self.researchByDataID('image data').content['image data']
		return (image1, image2)

