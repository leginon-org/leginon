#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import imageprocessor

class MaxFinder(imageprocessor.ImageProcessor):

	def processImage(self, imagedata):
		# find the max pixel in the image
		a = imagedata['image']
		n = a.argmax()
		rows = a.shape[0]
		cols = a.shape[1]
		row = n / cols
		col = n % cols
		self.logger.info('image id %d, max pixel at row=%d, col=%d' % (imagedata.dbid, row, col))
