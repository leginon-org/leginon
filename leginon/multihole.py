#!/usr/bin/env python

import math
import numpy
import scipy.ndimage
import os

from pyami import mrc, convolver, affine2

class TemplateConvolver(object):
	'''
	Convolve hole template with its lattice to make a new template.
	'''
	def __init__(self):
		self.convolver = convolver.Convolver()

	def readSingleTemplate(self, input_file):
		self.setSingleTemplate(mrc.read(input_file))

	def setSingleTemplate(self,array):
		self.single = array

	def setNumberOfPoints(self,n):
		self.npoint = n

	def setLatticeSpacing(self,pixels):
		self.lattice_spacing = pixels

	def setLatticeAngle(self,degrees):
		self.lattice_angle = math.radians(degrees)

	def setSingleTemplateScale(self,scale):
		self.single_scale = scale

	def getLatticeSpacing(self):
		return self.lattice_spacing

	def getLatticeAngle(self):
		return math.degrees(self.lattice_angle)

	def getVectors(self, npoint):
		'''
		get lattice point vectors. Works up to 9 points.
		'''
		if npoint % 2:
			is_odd = True
		else:
			is_odd = False
		vectors = [(-1,-1),(1,1),(1,-1),(-1,1)]
		if is_odd:
			base_vectors = [(0,0),(-1,0),(1,0),(0,1),(0,-1)]
			vectors = base_vectors + vectors
		vectors = numpy.array(vectors[:npoint])
		if not is_odd:
			vectors = vectors * 1.0/2
		return vectors

	def scaleSingleTemplate(self):
		self.single = scipy.ndimage.zoom(self.single,self.single_scale)

	def makeLatticeImage(self, points):
		vectors = self.getVectors(points)
		spacing = self.lattice_spacing
		angle = self.lattice_angle
		unit_vector = numpy.array((spacing*math.sin(angle), -spacing*math.cos(angle),spacing*math.cos(angle),spacing*math.sin(angle)))
		unit_vector = unit_vector.reshape((2,2))
		lattice_vectors = numpy.zeros(vectors.shape)
		for i in range(points):
			p = vectors[i]
			v = unit_vector
			lattice_vectors[i,0] = int(numpy.dot(p,v[0]))
			lattice_vectors[i,1] = int(numpy.dot(p,v[1]))
		shape = self.calculateNewTemplateShape(lattice_vectors)
		image = numpy.zeros(shape)
		center = numpy.array((shape[0]//2, shape[1]//2))
		lattice_vectors = lattice_vectors + center
		for l in list(lattice_vectors):
			image[int(l[0]),int(l[1])] = 1
		return image

	def convolve(self):
			kernel = self.single
			image = self.makeLatticeImage(self.npoint)
			self.convolver.setKernel(kernel)
			image = self.convolver.convolve(image=image)
			return image

	def calculateNewTemplateShape(self,lattice_vectors):
		single_shape = self.single.shape
		rows = lattice_vectors[:,0]
		cols = lattice_vectors[:,1]
		row_size = rows.max() - rows.min()
		col_size = cols.max() - cols.min()
		return row_size+single_shape[0],col_size+single_shape[1]

	def setConfig(self, npoint, spacing, angle, single_scale):
		self.setNumberOfPoints(npoint)
		self.setLatticeSpacing(spacing)
		self.setLatticeAngle(angle)
		self.setSingleTemplateScale(single_scale)

	def makeMultiTemplate(self):
		self.scaleSingleTemplate()
		template_image = self.convolve()
		return template_image

	def run(self):
		template_image = self.makeMultiTemplate()
		outfile = './%dholetemplate.mrc' % (self.npoint)
		outfile = os.path.abspath(outfile)
		print 'output the template file as\n %s' % outfile 
		mrc.write(template_image,outfile)

if __name__ == '__main__':
	input_file = '/Users/acheng/myami/leginon/holetemplate.mrc'

	app = TemplateConvolver()
	app.readSingleTemplate(input_file)
	npoint = int(float(raw_input('Enter number of holes in template (for example, 4):')))
	spacing = float(raw_input('Enter Lattice Spacing in pixels (for example 415):'))
	template_diameter = float(raw_input('Enter template diameter as in hole finder in pixels (for example 260):'))
	single_scale = template_diameter/168.0
	angle = float(raw_input('Enter lattice angle (0,0) to (1,0) in degrees (for example 13):'))
	app.setConfig(npoint, spacing, angle, single_scale)
	app.run()
