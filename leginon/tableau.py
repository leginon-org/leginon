#!/usr/bin/env python

import numpy
print 'NUMPY', numpy
from pyami import imagefun
import math

class Tableau(object):
	def __init__(self, radius):
		self.images = []
		self.radius = radius

	def insertImage(self, image, angle=None):
		if angle is None:
			center = True
		else:
			center = False
		info = {'image': image, 'angle': angle, 'center': center}
		self.images.append(info)

	def imageExtents(self, imageinfo):
		if imageinfo['angle'] is None:
			x = y = 0
		else:
			x = int(self.radius * math.cos(imageinfo['angle']))
			y = int(self.radius * math.sin(imageinfo['angle']))
		center_row = -y
		center_col = x
		image = imageinfo['image']
		halfshape = image.shape[0]/2, image.shape[1]/2
		rowmin = center_row-halfshape[0]
		rowmax = center_row+halfshape[0]
		colmin = center_col-halfshape[1]
		colmax = center_col+halfshape[1]
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
		print 'CENTER', center
		for image in self.images:
			extents = self.imageExtents(image)
			pos = center[0]+extents['row'][0], center[1]+extents['column'][0]
			print 'POS', image['image'][0,0], pos
			imagefun.pasteInto(image['image'], finalimage, pos)

		return finalimage

if __name__ == '__main__':
	from pyami import mrc

	shape = 16,16
	images = []
	nimages = 4
	angleinc = 2.0 * numpy.pi / nimages
	angles = []
	for i in range(nimages):
		image = i * numpy.ones(shape)
		images.append(image)
		angle = i * angleinc + numpy.pi/4.0
		angles.append(angle)
		print 'ANGLE', angle

	t = Tableau(radius=shape[0])
	for i, image in enumerate(images):
		t.insertImage(image, angles[i])

	final = t.render()
	mrc.write(final, 'final.mrc')
