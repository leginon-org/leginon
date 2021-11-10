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
		self.single = None

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

	def makeLatticeVectors(self):
		'''
		return lattice vectors array where (0,0) point is mapped to (0,0)
		'''
		vectors = self.getVectors(self.npoint)
		lattice_vectors = numpy.zeros(vectors.shape)
		for i in range(self.npoint):
			p = vectors[i]
			v = self.unit_vector
			lattice_vectors[i,0] = int(numpy.dot(p,v[0]))
			lattice_vectors[i,1] = int(numpy.dot(p,v[1]))
		return lattice_vectors

	def _centerVectorsOnShape(self, vectors, shape):
		'''
		shift vectors array so (0,0) input vector is now the center of the shape.
		'''
		center = numpy.array((shape[0]//2, shape[1]//2))
		centered_vectors = vectors + center
		return centered_vectors

	def makeLatticeImage(self):
		'''
		Return an image with lattice points at value of 1 while the rest at 0.
		The center of the image is the origin of the lattice.
		SingleTemplate must be set
		'''
		if self.single is None:
			raise ValueError('Single template image is required to make lattice image used in convolution')
		lattice_vectors = self.makeLatticeVectors()
		shape = self.calculateNewTemplateShape(lattice_vectors)
		lattice_vectors = self._centerVectorsOnShape(lattice_vectors, shape)
		image = numpy.zeros(shape)
		for l in list(lattice_vectors):
			image[int(l[0]),int(l[1])] = 1
		return image

	def convolve(self):
			kernel = self.single
			image = self.makeLatticeImage()
			self.convolver.setKernel(kernel)
			image = self.convolver.convolve(image=image)
			return image

	def calculateNewTemplateShape(self,lattice_vectors):
		single_shape = self.single.shape
		rows = lattice_vectors[:,0]
		cols = lattice_vectors[:,1]
		row_size = int(rows.max() - rows.min())
		col_size = int(cols.max() - cols.min())
		return row_size+single_shape[0],col_size+single_shape[1]

	def setConfig(self, npoint, single_scale):
		self.setNumberOfPoints(npoint)
		self.setSingleTemplateScale(single_scale)

	def setSquareUnitVector(self, spacing, angle_degrees):
		self.setLatticeSpacing(spacing)
		self.setLatticeAngle(angle_degrees)
		angle = self.lattice_angle
		unit_vector = numpy.array((spacing*math.sin(angle), -spacing*math.cos(angle),spacing*math.cos(angle),spacing*math.sin(angle)))
		self.setUnitVector(unit_vector.reshape((2,2)))

	def setUnitVector(self, vector):
		# 2x2 array representing unit vector of the lattice to convolve single template with.
		self.unit_vector = vector

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
	#app.readSingleTemplate(input_file)
	npoint = int(float(raw_input('Enter number of holes in template (for example, 4):')))
	'''
	spacing = float(raw_input('Enter Lattice Spacing in pixels (for example 415):'))
	template_diameter = float(raw_input('Enter template diameter as in hole finder in pixels (for example 260):'))
	single_scale = template_diameter/168.0
	angle = float(raw_input('Enter lattice angle (0,0) to (1,0) in degrees (for example 13):'))
	'''
	single_scale = 1.0
	app.setConfig(npoint, single_scale)
	# app.setSquareUnitVector(spacing, angle)
	vector = numpy.array([(-10.045871559633028, 1.3394495412844036),(1.5068807339449541, 10.045871559633028)])	
	app.setUnitVector(vector)
	print numpy.ndarray.tolist(app.makeLatticeVectors())
	#app.run()
