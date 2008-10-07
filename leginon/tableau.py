
import numpy
from pyami import imagefun

class Tableau(object):
	def __init__(self, radius):
		self.images = []
		self.radius = radius

	def insertImage(self, image, angle):
		info = {'image': image, 'angle': angle}
		self.images.append(info)

	def imageExtents(self, imageinfo):
		center_row = int(self.radius * numpy.cos(imageinfo['angle']))
		center_col = int(self.radius * numpy.cos(imageinfo['angle']))
		image = imageinfo['image']
		rowmin = center_row-image.shape[0]
		rowmax = center_row+image.shape[0]
		colmin = center_col-image.shape[1]
		colmax = center_col+image.shape[1]
		print {'row': (rowmin,rowmax), 'column': (colmin,colmax)}
		return {'row': (rowmin,rowmax), 'column': (colmin,colmax)}

	def render(self):
		rowmin = 0
		rowmax = 0
		colmin = 0
		colmax = 0
		for image in self.images:
			extents = self.imageExtents(image)
			if extents['row'][0] < rowmin:
				rowmin = extents['row'][0]
			if extents['row'][1] > rowmax:
				rowmax = extents['row'][1]
			if extents['column'][0] < colmin:
				colmin = extents['column'][0]
			if extents['column'][1] > colmax:
				colmax = extents['column'][1]
		totalshape = rowmax-rowmin, colmax-colmin
		finalimage = numpy.zeros(totalshape, self.images[0]['image'].dtype)
		center = finalimage.shape[0]/2, finalimage.shape[1]/2
		for image in self.images:
			extents = self.imageExtents(image)
			pos = center[0]+extents['row'][0], center[1]+extents['column'][0]
			imagefun.pasteInto(image['image'], finalimage, pos)

		return finalimage
