#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
ma = numpy.ma
import math
from pyami import imagefun, mrc, arraystats, correlator, convolver
import pyami.circle
import os

from leginon import icefinderback, statshole, holetemplatemaker, lattice

###################
### Because of the use of __result, the subclass should define update_result and get_result
###################
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
			'correlation': None,
			'threshold': None,
			'blobs': None,
			'vector': None,
			'lattice': None,
			'holes': None,  # holes with stats
			'markedholes': None,
			'holes2': None, # good holes to use after convolution, ice filtering etc.
			'markedholes2': None,
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('correlation',),
			'template': ('correlation',),
			'correlation': ('threshold','blobs'),
			'threshold': ('blobs','vector'),
			'blobs': ('lattice',),
			'vector': ('lattice',),
			'lattice': ('holes',),
			'holes': ('holes2','markedholes'),
			'markedholes': (),
			'holes2': ('markedholes2',),
			'markedholes2': (),
		}

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()
		self.template = holetemplatemaker.HoleTemplateMaker()
		self.convolver = convolver.Convolver()

	def setDefaults(self):
		## some default configuration parameters
		super(HoleFinder, self).setDefaults() # icefinder part
		self.template.setDefaults({'template filename':'', 'template diameter':168, 'file diameter':168, 'invert':False, 'min':0.0, 'multiple':1, 'spacing': 100.0, 'angle':0.0})
		self.correlation_config = {'cortype': 'cross', 'corfilt': (1.0,),'cor_image_min':0.0}
		self.threshold = 3.0
		self.threshold_method = "Threshold = mean + A * stdev"
		self.blobs_config = {'border': 20, 'maxblobsize': 50, 'maxblobs':100, 'minblobsize':0, 'minblobroundness':0.8}  #wjr
		self.lattice_config = {'tolerance': 0.1, 'spacing': 100.0, 'minspace': 20, 'extend': 'off'}
		self.holestats_config = {'radius': 20}
		self.filter_config = {'tmin': -10, 'tmax': 20}
		self.convolve_config = {'conv_vect':None}
		self.save_mrc = False

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

	def updateHoles(self, holes):
		self.__update_result('holes', holes)

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

	def configure_holefinder(self, script=None, job_name='hole', in_path=None, out_dir=None, score_key=None, threshold=None):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		if not in_path and self.get_result('original'):
			self.temp_in_path = '%s.mrc' % job_name
			mrc.write(self.get_result('original'), self.temp_in_path)
			in_path = self.temp_in_path

	def run_holefinder(self):
		'''
		Return external hole finder holes found
		'''
		if self.get_result('original') is None:
			raise RuntimeError('need original image to run hole finding')
		self.create_template()
		self.correlate_template()
		self.threshold_correlation()
		self.find_blobs()
		self.blobs_to_lattice()

	def configure_template(self, diameter=None, filename=None, filediameter=None, invert=False, multiple=1, spacing=100.0, angle=0.0):
		self.template.configure({'template filename':filename, 'template diameter':diameter, 'file diameter':filediameter, 'invert':invert, 'multiple':multiple, 'spacing': spacing, 'angle':angle})

	def create_template(self):
		fromimage = self.correlator_from_result
		if self.get_result(fromimage) is None:
			raise RuntimeError('need image %s before creating template' % (fromimage,))
		template = self.template.create_template(self.im_shape)
		#self.logger.info('invert template for correlation')
		self.update_result('template', template)
		self.saveTestMrc(template, 'template.mrc')

	def configure_correlation(self, cortype=None, corfilt=None,cor_image_min=0):
		if cortype is not None:
			self.correlation_config['cortype'] = cortype
		self.correlation_config['corfilt'] = corfilt
		if cor_image_min is not None:
			# for back compatibility
			self.correlation_config['cor_image_min'] = cor_image_min

	def maskBlack(self, image):
		'''
		Mask area with value lower than cor_image_min and fill it with mean
		of the rest of the area.  Effectively, this reduces the correlation
		produced by the edge produced by the black block.
		'''
		image_min = self.correlation_config['cor_image_min']
		if image_min is None:
			return image
		masked = ma.masked_less(image,image_min)
		return masked.filled(masked.mean())

	def correlate_template(self):
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

	def configure_threshold(self, threshold=None, threshold_method=None):
		if threshold is not None:
			self.threshold = threshold
		if threshold_method is not None:
			self.threshold_method = threshold_method

	def threshold_correlation(self):
		'''
		Threshold the correlation image.
		'''
		if self.get_result('correlation') is None:
			raise RuntimeError('need correlation image to threshold')
		cc = self.get_result('correlation')

		meth = self.threshold_method
		if meth == "Threshold = mean + A * stdev":
			mean = arraystats.mean(cc)
			std = arraystats.std(cc)
			thresh = mean + self.threshold * std
		elif meth == "Threshold = A":
			thresh = self.threshold

		t = imagefun.threshold(cc, thresh)
		self.update_result('threshold', t)
		self.saveTestMrc(t, 'threshold.mrc')

	def configure_blobs(self, border=None, maxblobs=None, maxblobsize=None, minblobsize=None, minblobroundness=None):
		if border is not None:
			self.blobs_config['border'] = border
		if maxblobsize is not None:
			self.blobs_config['maxblobsize'] = maxblobsize
		if minblobsize is not None:
			self.blobs_config['minblobsize'] = minblobsize
		if maxblobs is not None:
			self.blobs_config['maxblobs'] = maxblobs
		if minblobroundness is not None:
			self.blobs_config['minblobroundness'] = minblobroundness   #wjr

	def find_blobs(self, picks=None):
		'''
		find blobs on a thresholded image
		'''
		if picks is None:
			if self.get_result('threshold') is None or self.get_result('correlation') is None:
				raise RuntimeError('need correlation image and threshold image to find blobs')
			im = self.get_result('correlation')
			mask = self.get_result('threshold')
			border = self.blobs_config['border']
			maxsize = self.blobs_config['maxblobsize']
			minsize = self.blobs_config['minblobsize']
			maxblobs = self.blobs_config['maxblobs']
			minroundness = self.blobs_config['minblobroundness']
			blobs = imagefun.find_blobs(im, mask, border, maxblobs, maxsize, minsize, minroundness)   #wjr
		else:
			picks = self.swapxy(picks)
			blobs = self.points_to_blobs(picks)
		self.update_result('blobs', blobs)

	def configure_lattice(self, tolerance=None, spacing=None, minspace=None, extend=None):
		if tolerance is not None:
			self.lattice_config['tolerance'] = tolerance
		if spacing is not None:
			self.lattice_config['spacing'] = spacing
		if minspace is not None:
			self.lattice_config['minspace'] = minspace
		if extend is not None:
			self.lattice_config['extend'] = extend
		l = self.lattice_config['spacing']

	def points_to_blobs(self, points):
			blobs = []
			for point in points:
				blob = imagefun.Blob(None, None, 1, point, 1.0, 1.0, 1.0, 1.0)
				blobs.append(blob)
			return blobs

	def points_to_stats_holes(self, points):
		holes = []
		for n,point in enumerate(points):
			h = {'center':point,'convolved':False}
			holes.append(statshole.StatsHole(h, n, h.keys())) # (row, col)
		return holes

	def convolve3x3WithBlobPoints(self,points):
		if len(points) < 2:
			self.logger.warning('Need at least 2 point to determine 3x3 patter orientation')
			return []
		shape = self.get_result('original').shape
		tolerance = self.lattice_config['tolerance']
		spacing = self.lattice_config['spacing']
		total_lattice_points = []
		# Use the first two points to get the rotation of the 3x3 holes
		vector = (points[1][0]-points[0][0],points[1][1]-points[0][1])
		vector_length = math.hypot(vector[0],vector[1])
		# scaling the 3x3 pattern to have the spacing of the lattice_config
		scaled_vector = map((lambda x: x*spacing/vector_length),vector)
		def shiftpoint(point,vector):
			return (point[0]+vector[0],point[1]+vector[1])
		for point in points:
			newpoints = [point,shiftpoint(point,scaled_vector)]
			best_lattice = lattice.pointsToLattice(newpoints, spacing, tolerance, first_is_center=True)
			best_lattice_points = best_lattice.raster(shape, layers=1)
			total_lattice_points.extend(best_lattice_points)
		self.lattice_matrix = best_lattice.matrix
		return total_lattice_points

	def blobs_to_lattice(self, tolerance=None, spacing=None, minspace=None, extend=None):
		if self.get_result('blobs') is None:
			raise RuntimeError('need blobs to create lattice')
		self.configure_lattice(tolerance=tolerance,spacing=spacing,minspace=minspace, extend=extend)

		shape = self.get_result('original').shape
		blobs = self.get_result('blobs')
		tolerance = self.lattice_config['tolerance']
		spacing = self.lattice_config['spacing']
		extend = self.lattice_config['extend']
		# make make list of blob coords:
		points = []
		pointdict = {}
		if len(blobs) < 2 and extend !='off':
			self.update_result('holes', [])
			return
			
		for blob in blobs:
			point = tuple(blob.stats['center'])
			points.append(point)
			pointdict[point] = blob

		if extend == '3x3':
			# Not to use points to determine Lattice but continue with extension
			best_lattice = True
		else:
			if spacing > 0:
				best_lattice = lattice.pointsToLattice(points, spacing, tolerance)
				accept_all = False
			else:
				# accept all points
				im_center = self.im_shape[0]//2, self.im_shape[1]//2
				points = lattice.sortPointsByDistances(points, center=im_center)
				best_lattice = lattice.pointsToFakeLattice(points)
				accept_all = True

		self.update_result('lattice', best_lattice)
		if best_lattice is None:
			# no valid results
			best_lattice_points = []
			holes = []
			self.update_result('holes', [])
			return
		if extend == 'full':
			if accept_all:
				raise ValueError('Can not extend unspecified lattice to full')
			best_lattice_points = best_lattice.raster(shape)
			best_lattice_points = best_lattice.optimizeRaster(best_lattice_points,best_lattice.points)
			self.lattice_matrix = best_lattice.matrix
		elif extend == '3x3':
			if accept_all:
				raise ValueError('Can not extend unspecified lattice to 3x3')
			best_lattice_points = self.convolve3x3WithBlobPoints(points)
		else:
			best_lattice_points = best_lattice.points
			self.lattice_matrix = best_lattice.matrix
		holes = self.points_to_stats_holes(best_lattice_points)
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
		self.run_holefinder()
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
	hf.threshold = 1.6
	template_file= os.path.join(leginon_dir,'holetemplate.mrc')
	hf.configure_template(diameter=40, filename=template_file, filediameter=168, multiple=1, spacing=200.0,angle=25.0)
	hf.configure_correlation(cortype='cross', corfilt=(2.0,),cor_image_min=0)
	hf.configure_threshold(threshold=2.0, threshold_method="Threshold = mean + A * stdev")
	hf.configure_lattice(tolerance=0.1, spacing=90)
	print('saved test mrc imagings in current directory')
	hf.configure_ice(i0=133, tmin=0.0)
	hf.configure_convolve(conv_vect=[(0,0),])
	hf.configure_sample(classes=2, samples=4, category='thickness-mean')
	hf.find_holes()
	print('first holes of',len(hf['holes']),hf['holes'][0].stats)
	print('first holes2 of',len(hf['holes2']),hf['holes2'][0].stats)
