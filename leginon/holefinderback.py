#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
import pyami.quietscipy
import scipy.ndimage
from pyami import imagefun, convolver, correlator, mrc, arraystats
import ice
import lattice


import numpy
ma = numpy.ma
import math
from pyami import imagefun, mrc, arraystats, correlator, convolver
import pyami.circle
import os

from leginon import jahcfinderback, statshole, holetemplatemaker, lattice

###################
### Because of the use of __result, the subclass don't get them as attribute. AC 2021
###################
class HoleFinder(jahcfinderback.HoleFinder):
	'''
	Create an instance of HoleFinder:
		hf = HoleFinder()
	Give it an image to work with:
		hf['original'] = some_numeric_array
	Configure the processes:
		hf.configure_template(min_radius, max_radius)
		hf.configure_lattice(tolerance, spacing, minspace)
		hf.configure_holestats(radius)
		hf.configure_ice(i0, tmin, tmax)
	Do the processes step by step, or the whole thing:
		hf.find_holes()
	'''
	correlator_from_result = 'edges'
	def __init__(self, is_testing=False):
		self.setComponents()
		self.setDefaults()
		self.save_mrc = is_testing
		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None,
			'edges': None,
			'template': None,
			'correlation': None,
			'threshold': None,
			'blobs': None,
			#'vector': None,
			'lattice': None,
			'holes': None,
			'markedholes': None,
			'holes2': None,
			'markedholes2': None,
			'holes3': None, # center holes to use after convolution, in case holes2 is empty after ice filtering
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('edges',),
			'edges': ('correlation',),
			'template': ('correlation',),
			'correlation': ('threshold','blobs'),
			#'threshold': ('blobs','vector'),
			'threshold': ('blobs',),
			'blobs': ('lattice',),
			#'vector': ('lattice',),
			'lattice': ('holes',),
			'holes': ('holes2','markedholes','holes3'),
			'markedholes': (),
			'holes2': ('markedholes2','holes3'),
			'markedholes2': (),
			'holes3':(),
		}

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()
		self.edgefinder = convolver.Convolver()

	def setDefaults(self):
		super(HoleFinder, self).setDefaults()
		## some default configuration parameters
		self.edges_config = {'filter': 'sobel', 'size': 9, 'sigma': 1.4, 'abs': False, 'lp':True, 'lpsig':1.0, 'thresh':100.0, 'edges': True}

	def __getitem__(self, key):
		return self.__results[key]

	def __setitem__(self, key, value):
		## only some images are allowed to be set externally
		## (right now, only original)
		if key in ('original',):
			self.__update_result(key, value)
			self._set_image(value)

	def __update_result(self, key, image):
		'''
		This updates a result in the self.__results dict.
		It also clears all dependent results.
		'''
		## clear my dependents recursively
		for depkey in self.__dependents[key]:
			self.__update_result(depkey, None)
		## update this result
		self.__results[key] = image

	def update_result(self, key, image):
		'''
		update __results in this module. Must copy to the subclass in a different module.
		'''
		self.__update_result(key, image)

	def get_result(self,key):
		'''
		get __result in this module. Must copy to the subclass in a different module.
		'''
		return self.__results[key]

	def configure_edges(self, filter=None, size=None, sigma=None, absvalue=None, lpsig=None, thresh=None, edges=None):
		if filter is not None:
			self.edges_config['filter'] = filter
		if sigma is not None:
			self.edges_config['sigma'] = sigma
		if absvalue is not None:
			self.edges_config['abs'] = absvalue
		if lpsig is not None:
			self.edges_config['lpsig'] = lpsig
		if thresh is not None:
			self.edges_config['thresh'] = thresh
		if edges is not None:
			self.edges_config['edges'] = edges

	def find_edges(self):
		'''
		find edges on the original image
		'''
		if self.get_result('original') is None:
			raise RuntimeError('no original image to find edges on')

		sourceim = self.get_result('original')
		sigma = self.edges_config['lpsig']
		edgethresh = self.edges_config['thresh']

		smooth = scipy.ndimage.gaussian_filter(sourceim, sigma)
		if self.save_mrc:
			mrc.write(smooth, 'smooth.mrc')

		edges = scipy.ndimage.generic_gradient_magnitude(smooth, derivative=scipy.ndimage.sobel)

		if self.save_mrc:
			mrc.write(edges, 'gradient.mrc')
		if edgethresh:
			edges = imagefun.threshold(edges, edgethresh)

		self.__update_result('edges', edges)
		if self.save_mrc:
			mrc.write(edges, 'edges.mrc')

	def run_holefinder(self):
		'''
		Return external hole finder holes found
		'''
		if self.get_result('original') is None:
			raise RuntimeError('need original image to run hole finding')
		self.find_edges()
		self.create_template()
		self.correlate_template()
		self.threshold_correlation()
		self.find_blobs()
		self.blobs_to_lattice()

if __name__ == '__main__':
	from pyami import numpil
	hf = HoleFinder(is_testing=True)
	leginon_dir = os.path.dirname(os.path.abspath(__file__))
	hf['original'] = numpil.read(os.path.join(leginon_dir,'hl_example.jpg'))
	hf.threshold = 1.6
	template_file= os.path.join(leginon_dir,'hole_edge_template.mrc')
	hf.configure_edges(filter='sobel', size=9, sigma=1.4, absvalue=False, lpsig=3, thresh=10, edges=True)
	hf.configure_template(diameter=51, filename=template_file, filediameter=168, multiple=1, spacing=200.0,angle=25.0)
	hf.configure_correlation(cortype='cross', corfilt=(2.0,),cor_image_min=0)
	hf.configure_threshold(threshold=3.5, threshold_method="Threshold = mean + A * stdev")
	hf.configure_blobs(maxblobs=20, maxblobsize=5000, minblobsize=30, minblobroundness=0.1)
	hf.configure_lattice(tolerance=0.1, spacing=210)
	print('saved test mrc imagings in current directory')
	hf.configure_ice(i0=110, tmin=0.0)
	hf.configure_convolve(conv_vect=[(0,0),])
	hf.configure_sample(classes=2, samples=2, category='thickness-mean')
	hf.find_holes()
	print('first holes of',len(hf['holes']),hf['holes'][0].stats)
	print('first holes2 of',len(hf['holes2']),hf['holes2'][0].stats)
