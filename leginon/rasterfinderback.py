#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
import scipy.ndimage as ndimage
import math
from pyami import imagefun, mrc, arraystats, correlator, convolver
import pyami.circle
import os

from leginon import icefinderback, statshole, holeconfigurer, lattice

###################
### Because of the use of __result, the subclass should define update_result and get_result
###################
Configurer = holeconfigurer.Configurer

class RasterMaker(Configurer):
	def __init__(self):
		self.setDefaults({'center x':None,'center y':None,'spacing x':100,'spacing y':100,'points x':5,'points y':5,'angle':0.0})

class HoleFinder(icefinderback.IceFinder):
	'''
	Create an instance of HoleFinder:
		hf = HoleFinder()
	Give it an image to work with:
		hf['original'] = some_numeric_array
	Configure the processes:
		hf.configure_holefinder(dirname, max_radius)
	Do the processes step by step, or the whole thing:
		hf.find_holes()
	'''
	correlator_from_result = 'original'
	def __init__(self, is_testing=False):
		self.setComponents()
		self.setDefaults()
		self.lattice_matrix = None
		self.save_mrc = is_testing
		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None, # original image
			'vector': None,
			'raster': None,
			'polygon': None, #veriices
			'holes': None,  # holes with stats
			'markedholes': None,
			'holes2': None, # good holes to use after convolution, ice filtering etc.
			'markedholes2': None,
			'holes3': None, # center holes to use after convolution, in case holes2 is empty after ice filtering
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('raster',),
			'vector': (),
			'raster': ('polygon',),
			'polygon': ('holes',),
			'holes': ('holes2','markedholes','holes3'),
			'markedholes': (),
			'holes2': ('markedholes2','holes3'),
			'markedholes2': (),
			'holes3':(),
		}

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()
		self.raster = RasterMaker()

	def setDefaults(self):
		## some default configuration parameters
		super(HoleFinder, self).setDefaults() # icefinder part
		self.raster.setDefaults({'center x':None,'center y':None,'spacing x':100,'spacing y':100,'points x':5,'points y':5,'angle':0.0})
		self.save_mrc = False

	def __getitem__(self, key):
		return self.__results[key]

	def __setitem__(self, key, value):
		## only some images are allowed to be set externally
		## (right now, only original)
		if key in ('original',):
			self.update_result(key, value)
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

	def configure_centerfinder(self, script=None, job_name='hole', in_path=None, out_dir=None, score_key=None, threshold=None):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		if not in_path and self.get_result('original'):
			self.temp_in_path = '%s.mrc' % job_name
			mrc.write(self.get_result('original'), self.temp_in_path)
			in_path = self.temp_in_path

	def run_centerfinder(self):
		'''
		Return external hole finder holes found
		'''
		if self.get_result('original') is None:
			raise RuntimeError('need original image to run hole finding')
		self.blobs_to_lattice()

	def configure_raster(self, x0=None,y0=None,xspacing=None,yspacing=None,xpoints=None,ypoints=None,radians=0.0):
		#pixels and radians
		self.raster.configure({
				'center x':x0,'center y':y0,
				'spacing x':xspacing,'spacing y':yspacing,
				'points x':xpoints,'points y':ypoints,
				'angle':radians,
		})

	def make_raster_points(self):
		image =  self.get_result('original')
		if self.get_result('original') is None:
			raise RuntimeError('need original image to run target finding')
		#
		points = []

		c = self.raster.configs
		xpoints = c['points x']
		ypoints = c['points y']
		xspacing = c['spacing x']
		yspacing = c['spacing y']
		x0 = c['center x']
		y0 = c['center x']
		radians = c['angle']

		# center set to image center if None
		imageshape = image.shape
		if x0 is None:
			x0 = imageshape[1] / 2.0
		if y0 is None:
			y0 = imageshape[0] / 2.0
		#matrix
		m = numpy.array([[yspacing*numpy.cos(radians),xspacing*numpy.sin(radians)],
				[-yspacing*numpy.sin(radians),xspacing*numpy.cos(radians)]])
		self.lattice_matrix = m
		#raster making
		xlist = numpy.asarray(range(xpoints), dtype=numpy.float32)
		xlist -= ndimage.mean(xlist)
		ylist = numpy.asarray(range(ypoints), dtype=numpy.float32)
		ylist -= ndimage.mean(ylist)

		for xt in xlist:
			xshft = xt * xspacing
			for yt in ylist:
				yshft = yt * yspacing
				xrot = xshft * numpy.cos(radians) + yshft * numpy.sin(radians)
				yrot = -yshft * numpy.cos(radians) + xshft * numpy.sin(radians)
				x = int(xrot + x0)
				y = int(yrot + y0)
				if x < 0 or x >= imageshape[1]: continue
				if y < 0 or y >= imageshape[0]: continue
				points.append( (x,y) )
		self.update_result('raster', points)

	def find_center(self):
		'''
		Correlate template that is already created and configured.
		'''
		fromimage = self.correlator_from_result
		if self.get_result(fromimage) is None or self.get_result('template') is None:
			raise RuntimeError('need image %s and template before correlation' % (fromimage,))
		edges = self.get_result(fromimage)
		edges = self.maskBlack(edges)
		template = self.get_result('template')
		cortype = self.correlation_config['cortype']
		corfilt = self.correlation_config['corfilt']
		if cortype == 'cross':
			cc = correlator.cross_correlate(edges, template)
		elif cortype == 'phase':
			cc = correlator.phase_correlate(edges, template, zero=False)
		else:
			raise RuntimeError('bad correlation type: %s' % (cortype,))
		# filtering.  This does so on both cross-correlation and phase-correlation!
		if corfilt is not None:
			kernel = convolver.gaussian_kernel(*corfilt)
			self.convolver.setKernel(kernel)
			cc = self.convolver.convolve(image=cc)
		self.update_result('correlation', cc)
		self.saveTestMrc(cc, 'correlation.mrc')

	def threshold_correlation(self):
		'''
		Threshold the correlation image.
		'''
		if self.get_result('correlation') is None:
			raise RuntimeError('need correlation image to threshold')
		cc = self.get_result('correlation')

		#meth = "Threshold = mean + A * stdev"
		mean = arraystats.mean(cc)
		std = arraystats.std(cc)
		thresh = mean + self.threshold * std

		t = imagefun.threshold(cc, thresh)
		self.update_result('threshold', t)
		self.saveTestMrc(t, 'threshold.mrc')

		self.blobs_config['maxblobsize'] = maxblobsize
		im = self.get_result('correlation')
		maxsize = self.blobs_config['maxblobsize']
		minsize = self.blobs_config['minblobsize']
		maxblobs = 1
		minroundness = self.blobs_config['minblobroundness']
		blobs = imagefun.find_blobs(im, mask, border, maxblobs, maxsize, minsize, minroundness)   #wjr
		self.update_result('blobs', blobs)

	def points_to_stats_holes(self, points):
		holes = []
		for n,center in enumerate(self.swapxy(points)):
			h = {'center':center,'convolved':False} # point is in (x,y)
			holes.append(statshole.StatsHole(h, n, h.keys())) # (row, col)
		return holes

	def points_to_holes(self, points):
		holes = self.points_to_stats_holes(points)
		self.updateHoles(holes)

	def filter_by_polygon(self):
		#filtered_points = best_lattice.points
		filtered_points = self.get_result('raster')
		holes = self.points_to_stats_holes(filtered_points)
		self.updateHoles(holes)

	def mark_holes(self):
		'''
		Mark locations of the holes found on image.  This is a test function.
		'''
		if self.get_result('holes') is None or self.get_result('original') is None:
			raise RuntimeError('need original image and holes before marking holes')
		image = self.get_result('original')
		im = image.copy()
		value = arraystats.min(im)
		for hole in self.get_result('holes'):
			coord = hole.stats['center']
			imagefun.mark_image(im, coord, value)
		self.update_result('markedholes', im)
		self.saveTestMrc(im, 'markedholes.mrc')

	def swapxy(self, points):
		"""
		Swap (x,y) tuple to (y,x) on all items in the list.
		"""
		return [(point[1],point[0]) for point in points]

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.make_raster_points()
		self.filter_by_polygon()
		self.mark_holes()
		# for focus anyhole filtering, good holes are in holes2 results
		# template convolution. This will replace holes2 results
		self.make_convolved()
		self.calc_holestats(input_name='holes2')
		self.calc_ice(input_name='holes2')
		self.sampling(input_name='holes2')


if __name__ == '__main__':
	from pyami import numpil
	hf = HoleFinder()
	leginon_dir = os.path.dirname(os.path.abspath(__file__))
	hf = HoleFinder(is_testing=True)
	hf['original'] = numpil.read(os.path.join(leginon_dir,'sq_example.jpg'))
	imshape = hf['original'].shape
	hf.configure_raster(None,None,100,50,3,4, -0.5)
	hf.make_raster_points()
	print('saved test mrc imagings in current directory')
	hf.configure_ice(i0=133, tmin=0.0)
	hf.configure_convolve(conv_vect=[(0,0),])
	hf.configure_sample(classes=2, samples=40, category='thickness-mean')
	hf.find_holes()
	print('first holes of',len(hf['holes']),hf['holes'][0].stats)
	print('first holes2 of',len(hf['holes2']),hf['holes2'][0].stats)
