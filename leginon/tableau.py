#!/usr/bin/env python

import numpy
from pyami import imagefun
import math

def splitTableau(image, split):
	tabimage = numpy.zeros(image.shape, image.dtype)
	splitsize = image.shape[0]/int(split), image.shape[1]/int(split)
	for row in range(0,image.shape[0],splitsize[0]):
		rowslice = slice(row,row+splitsize[0])
		for col in range(0,image.shape[1],splitsize[1]):
			colslice = slice(col,col+splitsize[1])
			tabimage[rowslice,colslice] = imagefun.power(image[rowslice,colslice])
	return tabimage

class Tableau(object):
	def __init__(self):
		self.images = []

	def insertImage(self, image, angle=None, radius=0):
		info = {'image': image, 'angle': angle, 'radius': radius}
		self.images.append(info)

	def imageExtents(self, imageinfo):
		ang = imageinfo['angle']
		rad = imageinfo['radius']
		if (ang is None) or (not rad):
			x = y = 0
		else:
			x = int(rad * math.cos(ang))
			y = int(rad * math.sin(ang))
		center_row = -y
		center_col = x
		image = imageinfo['image']
		halfshape = image.shape[0]/2, image.shape[1]/2
		rowmin = center_row-halfshape[0]
		rowmax = center_row+halfshape[0]
		colmin = center_col-halfshape[1]
		colmax = center_col+halfshape[1]
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
		totalshape = 2*max(rowmax,-rowmin), 2*max(colmax,-colmin)
		background = self.images[0]['image'][(0,0)]
		finalimage = numpy.ones(totalshape, self.images[0]['image'].dtype)
		finalimage = background * finalimage
		center = finalimage.shape[0]/2, finalimage.shape[1]/2
		for image in self.images:
			extents = self.imageExtents(image)
			pos = center[0]+extents['row'][0], center[1]+extents['column'][0]
			imagefun.pasteInto(image['image'], finalimage, pos)

		if len(self.images) > 1:
			extents = self.imageExtents(self.images[1])
			scalerow = (extents['row'][0]+extents['row'][1])/2
			scalecol = (extents['column'][0]+extents['column'][1])/2
			scale = math.sqrt(scalerow**2+scalecol**2)
		else:
			scale = None
		return finalimage, scale




if __name__ == '__main__':
	from pyami import mrc

	shape = 16,16

	a = numpy.ones(shape)
	b = 2 * numpy.ones(shape)
	c = 3 * numpy.ones(shape)

	t = Tableau()
	for i, image in enumerate(images):
		t.insertImage(a, angle=0, radius=0)
		t.insertImage(b, angle=0, radius=16)
		t.insertImage(c, angle=numpy.pi, radius=16)

	final = t.render()
	mrc.write(final, 'final.mrc')
