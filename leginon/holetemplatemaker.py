#!/usr/bin/env python
import numpy
import scipy

from pyami import mrc
from leginon import holeconfigurer, multihole

Configurer = holeconfigurer.Configurer

hole_template_files = {}
hole_templates = {}

class HoleTemplateMaker(Configurer):
	"""
	Hole template creation.
	default configs:{'template filename':'', 'template diameter':168, 'file diameter':168, 'invert':False, 'multiple':1, 'spacing': 100.0, 'angle':0.0})
	"""
	def __init__(self, is_testing=False):
		self.multiconvolver = multihole.TemplateConvolver()
		super(HoleTemplateMaker, self).__init__()

	def read_hole_template(self, filename):
		if filename in hole_template_files:
			return hole_template_files[filename]
		im = mrc.read(filename)
		hole_template_files[filename] = im
		return im

	def create_template(self,image_shape):
		'''
		Create hole template from file. 
		'''
		#self.config should be set before calling this.
		# read template file
		filename = self.configs['template filename']
		tempim = self.read_hole_template(filename)

		# invert if needed
		if self.configs['invert']:
			tempim_med = (tempim.min() + tempim.max()) / 2
			tempim = -tempim + 2 * tempim_med

		filediameter = self.configs['file diameter']
		diameter = self.configs['template diameter']
		scale = float(diameter) / filediameter
		# multiple hole template generation
		self.multiconvolver.setSingleTemplate(tempim)
		self.multiconvolver.setConfig(self.configs['multiple'], scale)
		angle_degrees = self.configs['angle']
		self.multiconvolver.setSquareUnitVector(self.configs['spacing'], angle_degrees)

		tempim = self.multiconvolver.makeMultiTemplate()
		#self.saveTestMrc(tempim, 'multitemplate.mrc')
		# create template of proper size
		shape = image_shape

		origshape = tempim.shape
		edgevalue = tempim[0,0]
		template = edgevalue * numpy.ones(shape, tempim.dtype)
		# make sure the tamplate is smaller than from_image in both axes #5607
		if shape[0] < origshape[0]:
				offset = int((origshape[0]-shape[0])/2.0)
				tempim = tempim[offset:offset+shape[0],:]
		if shape[1] < origshape[1]:
				offset = int((origshape[1]-shape[1])/2.0)
				tempim = tempim[:,offset:offset+shape[1]]
		# Redefine origshape which is now always equal or smaller than shape
		origshape = tempim.shape
		offset = ( int((shape[0]-origshape[0])/2.0), int((shape[1]-origshape[1])/2.0) )
		template[offset[0]:offset[0]+origshape[0], offset[1]:offset[1]+origshape[1]] = tempim
		shift = (shape[0]/2, shape[1]/2)
		template = scipy.ndimage.shift(template, shift, mode='wrap')

		template = template.astype(numpy.float32)
		return template

