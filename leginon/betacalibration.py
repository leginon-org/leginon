import node
import math

class BetaCalibration(node.Node):
	def __init__(self, id, managerlocation):
		node.Node.__init__(self, id, managerlocation)

	def imageshift(self, EMnodeid, imageshiftguess, imageshiftrange, \
				correlationthreshold, pixelshiftrange, attempts):

		imageshift = imageshiftguess

		for i in xrange(attempts):
			imagepair = imagePair(EMnodeid, imageshift)
			correlationdata = correlation.correlation(imagepair[0], \
													imagepair[1], 0, 1, 1)
			pixelshiftmagnitude = math.sqrt(cdata['phase correlation peak'][0]**2
																	+ cdata['phase correlation peak'][1]**2)

			if self.noCorrelation(cdata, correlationthreshold):
				# images don't correlate, need smaller shift
				imageshift = self.adjustRange(imageshift, imageshiftrange, 1)
			else: # images correlate, check if pixel shift is good
				if (pixelshiftmagnitude >= pixelshiftrange[0]) \
							and (pixelshiftmagnitude <= pixelshiftrange[1]):
					return {'pixel shift': cdata['phase correlation peak'],
									'image shift': imageshift}
				elif pixelshiftmagnitude >= pixelshiftrange[0]:
					imageshift = self.adjustRange(imageshift, imageshiftrange, 1)
				elif pixelshiftmagnitude <= pixelshiftrange[1]:
					imageshift = self.adjustRange(imageshift, imageshiftrange, 0)
		return None

	# hopefully imageshiftrange reference is modified
	def adjustRange(self, imageshift, imageshiftrange, use):
		imageshiftrange[not use] = imageshift
		return (imageshiftrange[1] - imageshiftrange[0])/2 + imageshiftrange[0]

	def noCorrelation(self, correlationdata, correlationthreshold):
		if correlationdata['phase correlation image'][correlationdata['phase correlation peak']] < correlationthreshold:
			return 1
		else:
			return 0

	def imagePair(self, EMnodeid, shift):
		self.publishRemote(EMnodeid, \
						data.EMData({'image shift': {'x': -imageshift/2, 'y': 0.0})
		image1 = self.arrayImage(self.researchByDataID('camera'))
		self.publishRemove(EMnodeid, \
						data.EMData({'image shift': {'x': imageshift/2, 'y': 0.0})
		image2 = self.arrayImage(self.researchByDataID('camera'))
		return (image1, image2)

	def arrayImage(self, idata):
		return Numeric.reshape(Numeric.array(array.array(idata.content['datatype code'], base64.decodestring(idata.content['image data']))), (idata.content['y dimension'], idata.content['x dimension']))

