#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import numpy
import pyami.quietscipy
import scipy.ndimage
from pyami import imagefun, peakfinder, convolver, correlator, mrc, arraystats
import ice
import lattice

class CircleMaskCreator(object):
	def __init__(self):
		self.masks = {}

	def get(self, shape, center, minradius, maxradius):
		'''
		create binary mask of a circle centered at 'center'
		'''
		## use existing circle mask
		key = (shape, center, minradius, maxradius)
		if self.masks.has_key(key):
			return self.masks[key]

		## set up shift and wrapping of circle on image
		halfshape = shape[0] / 2.0, shape[1] / 2.0
		cutoff = [0.0, 0.0]
		lshift = [0.0, 0.0]
		gshift = [0.0, 0.0]
		for axis in (0,1):
			if center[axis] < halfshape[axis]:
				cutoff[axis] = center[axis] + halfshape[axis]
				lshift[axis] = 0
				gshift[axis] = -shape[axis]
			else:
				cutoff[axis] = center[axis] - halfshape[axis]
				lshift[axis] = shape[axis]
				gshift[axis] = 0
		minradsq = minradius*minradius
		maxradsq = maxradius*maxradius
		def circle(indices0,indices1):
			## this shifts and wraps the indices
			i0 = numpy.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = numpy.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			rsq = i0*i0+i1*i1
			c = numpy.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c.astype(numpy.int8)
		temp = numpy.fromfunction(circle, shape)
		self.masks[key] = temp
		return temp

### Note:  we should create a base class ImageProcess
### which defines the basic idea of a series of operations on 
### an image or a pipeline of operations.
### In subclasses such as HoleFinder, we would just have to define
### the steps and the dependencies.  The dependency checking and result
### management would be taken care of by the base class.
class HoleFinder(object):
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
	def __init__(self):
		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None,
			'edges': None,
			'template': None,
			'correlation': None,
			'threshold': None,
			'blobs': None,
			'vector': None,
			'lattice': None,
			'holes': None,
			'markedholes': None,
			'holes2': None,
			'markedholes2': None,
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
			'threshold': ('blobs','vector'),
			'blobs': ('lattice',),
			'vector': ('lattice',),
			'lattice': ('holes',),
			'holes': ('holes2','markedholes'),
			'markedholes': (),
			'holes2': ('markedholes2',),
			'markedholes2': (),
		}

		## other necessary components
		self.edgefinder = convolver.Convolver()
		self.peakfinder = peakfinder.PeakFinder()
		self.circle = CircleMaskCreator()
		self.icecalc = ice.IceCalculator()

		## some default configuration parameters
		self.save_mrc = False
		self.edges_config = {'filter': 'sobel', 'size': 9, 'sigma': 1.4, 'abs': False, 'lp':True, 'lpsig':1.0, 'thresh':100.0, 'edges': True}
		self.template_config = {'ring_list': [(25,30)]}
		self.correlation_config = {'cortype': 'cross', 'corfilt': (1.0,)}
		self.threshold = 3.0
		self.blobs_config = {'border': 20, 'maxblobsize': 50, 'maxblobs':100}
		self.lattice_config = {'tolerance': 0.1, 'vector': 100.0, 'minspace': 20}
		self.holestats_config = {'radius': 20}
		self.ice_config = {'i0': None, 'min': 0.0, 'max': 0.1, 'std': 0.05}

	def __getitem__(self, key):
		return self.__results[key]

	def __setitem__(self, key, value):
		## only some images are allowed to be set externally
		## (right now, only original)
		if key in ('original',):
			self.__update_result(key, value)

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
		if self.__results['original'] is None:
			raise RuntimeError('no original image to find edges on')

		sourceim = self.__results['original']
		sigma = self.edges_config['lpsig']
		edgethresh = self.edges_config['thresh']

		smooth = scipy.ndimage.gaussian_filter(sourceim, sigma)
		mrc.write(smooth, 'smooth.mrc')

		edges = scipy.ndimage.generic_gradient_magnitude(smooth, derivative=scipy.ndimage.sobel)

		if edgethresh:
			edges = imagefun.threshold(edges, edgethresh)

		self.__update_result('edges', edges)
		if self.save_mrc:
			mrc.write(edges, 'edges.mrc')

	def configure_template(self, ring_list=None):
		if ring_list is not None:
			self.template_config['ring_list'] = ring_list

	## for test1, test1: 30, 37
	## for test3, test4: 22, 30
	def create_template(self, ring_list=None):
		'''
		This creates the template image that will be correlated
		with the edge image.  This will fail if there is no
		existing edge image, which is necessary to determine the
		size of the template.
		'''
		fromimage = 'edges'
		if self.__results[fromimage] is None:
			raise RuntimeError('need image %s before creating template' % (fromimage,))
		self.configure_template(ring_list)
		shape = self.__results[fromimage].shape
		center = (0,0)
		ring_list = self.template_config['ring_list']
		template = numpy.zeros(shape, numpy.int8)
		for ring in ring_list:
			temp = self.circle.get(shape, center, ring[0], ring[1])
			template = template | temp
		template = template.astype(numpy.float32)
		self.__update_result('template', template)
		if self.save_mrc:
			mrc.write(template, 'template.mrc')

	def configure_correlation(self, cortype=None, corfilt=None):
		if cortype is not None:
			self.correlation_config['cortype'] = cortype
		self.correlation_config['corfilt'] = corfilt

	def correlate_template(self):
		fromimage = 'edges'
		if None in (self.__results[fromimage], self.__results['template']):
			raise RuntimeError('need image %s and template before correlation' % (fromimage,))
		edges = self.__results[fromimage]
		template = self.__results['template']
		cortype = self.correlation_config['cortype']
		corfilt = self.correlation_config['corfilt']
		if cortype == 'cross':
			cc = correlator.cross_correlate(edges, template)
		elif cortype == 'phase':
			cc = correlator.phase_correlate(edges, template, zero=False)
		else:
			raise RuntimeError('bad correlation type: %s' % (cortype,))
		cc = numpy.absolute(cc)

		if corfilt is not None:
			kernel = convolver.gaussian_kernel(*corfilt)
			self.edgefinder.setKernel(kernel)
			cc = self.edgefinder.convolve(image=cc)
		self.__update_result('correlation', cc)
		if self.save_mrc:
			mrc.write(cc, 'correlation.mrc')

	def configure_threshold(self, threshold=None):
		if threshold is not None:
			self.threshold = threshold

	def threshold_correlation(self, threshold=None):
		'''
		Threshold the correlation image.
		'''
		if self.__results['correlation'] is None:
			raise RuntimeError('need correlation image to threshold')
		self.configure_threshold(threshold)
		cc = self.__results['correlation']
		mean = arraystats.mean(cc)
		std = arraystats.std(cc)
		thresh = mean + self.threshold * std
		t = imagefun.threshold(cc, thresh)
		self.__update_result('threshold', t)
		if self.save_mrc:
			mrc.write(t, 'threshold.mrc')

	def configure_blobs(self, border=None, maxblobs=None, maxblobsize=None):
		if border is not None:
			self.blobs_config['border'] = border
		if maxblobsize is not None:
			self.blobs_config['maxblobsize'] = maxblobsize
		if maxblobs is not None:
			self.blobs_config['maxblobs'] = maxblobs

	def find_blobs(self):
		'''
		find blobs on a thresholded image
		'''
		if None in (self.__results['threshold'],self.__results['correlation']):
			raise RuntimeError('need correlation image and threshold image to find blobs')
		im = self.__results['correlation']
		mask = self.__results['threshold']
		border = self.blobs_config['border']
		maxsize = self.blobs_config['maxblobsize']
		maxblobs = self.blobs_config['maxblobs']
		blobs = imagefun.find_blobs(im, mask, border, maxblobs, maxsize)
		self.__update_result('blobs', blobs)

	def configure_lattice(self, tolerance=None, spacing=None, minspace=None):
		if tolerance is not None:
			self.lattice_config['tolerance'] = tolerance
		if spacing is not None:
			self.lattice_config['spacing'] = spacing
		if minspace is not None:
			self.lattice_config['minspace'] = minspace

	def blobs_to_lattice(self, tolerance=None, spacing=None, minspace=None):
		if self.__results['blobs'] is None:
			raise RuntimeError('need blobs to create lattice')
		self.configure_lattice(tolerance=tolerance,spacing=spacing,minspace=minspace)

		blobs = self.__results['blobs']
		tolerance = self.lattice_config['tolerance']
		spacing = self.lattice_config['spacing']
		# make make list of blob coords:
		points = []
		pointdict = {}
		for blob in blobs:
			point = tuple(blob.stats['center'])
			points.append(point)
			pointdict[point] = blob
		
		best_lattice = lattice.pointsToLattice(points, spacing, tolerance)
		if best_lattice is None:
			best_lattice = []
		else:
			best_lattice = best_lattice.points
		holes = [pointdict[tuple(point)] for point in best_lattice]

		self.__update_result('lattice', best_lattice)
		if best_lattice is None:
			self.__update_result('holes', [])
		else:
			self.__update_result('holes', holes)

	def mark_holes(self):
		if None in (self.__results['holes'], self.__results['original']):
			raise RuntimeError('need original image and holes before marking holes')
		image = self.__results['original']
		im = image.copy()
		value = arraystats.min(im)
		for hole in self.__results['holes']:
			coord = hole.stats['center']
			imagefun.mark_image(im, coord, value)
		self.__update_result('markedholes', im)
		if self.save_mrc:
			mrc.write(im, 'markedholes.mrc')

	def get_hole_stats(self, image, coord, radius):
		## select the region of interest
		rmin = int(coord[0]-radius)
		rmax = int(coord[0]+radius)
		cmin = int(coord[1]-radius)
		cmax = int(coord[1]+radius)
		## beware of boundaries
		if rmin < 0 or rmax >= image.shape[0] or cmin < 0 or cmax > image.shape[1]:
			return None

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		if self.save_mrc:
			mrc.write(subimage, 'hole.mrc')
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.circle.get(subimage.shape, center, 0, radius)
		if self.save_mrc:
			mrc.write(mask, 'holemask.mrc')
		im = numpy.ravel(subimage)
		mask = numpy.ravel(mask)
		roi = numpy.compress(mask, im)
		mean = arraystats.mean(roi)
		std = arraystats.std(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}

	def configure_holestats(self, radius=None):
		if radius is not None:
			self.holestats_config['radius'] = radius

	def calc_holestats(self, radius=None):
		'''
		This adds hole stats to holes.
		'''
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate hole stats')
		self.configure_holestats(radius=radius)
		im = self.__results['original']
		r = self.holestats_config['radius']
		holes = list(self.__results['holes'])
		for hole in holes:
			coord = hole.stats['center']
			holestats = self.get_hole_stats(im, coord, r)
			if holestats is None:
				self.__results['holes'].remove(hole)
				continue
			hole.stats['hole_stat_radius'] = r
			hole.stats['hole_n'] = holestats['n']
			hole.stats['hole_mean'] = holestats['mean']
			hole.stats['hole_std'] = holestats['std']

	def configure_ice(self, i0=None, tmin=None, tmax=None, tstd=None):
		if i0 is not None:
			self.ice_config['i0'] = i0
		if tmin is not None:
			self.ice_config['tmin'] = tmin
		if tmax is not None:
			self.ice_config['tmax'] = tmax
		if tstd is not None:
			self.ice_config['tstd'] = tstd

	def calc_ice(self, i0=None, tmin=None, tmax=None):
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax)
		holes = self.__results['holes']
		holes2 = []
		i0 = self.ice_config['i0']
		tmin = self.ice_config['tmin']
		tmax = self.ice_config['tmax']
		tstd = self.ice_config['tstd']
		self.icecalc.set_i0(i0)
		for hole in holes:
			if 'hole_mean' not in hole.stats:
				## no mean was calculated
				continue
			mean = hole.stats['hole_mean']
			std = hole.stats['hole_std']
			tm = self.icecalc.get_thickness(mean)
			hole.stats['thickness-mean'] = tm
			ts = self.icecalc.get_stdev_thickness(std, mean)
			hole.stats['thickness-stdev'] = ts
			if (tmin <= tm <= tmax) and (ts < tstd):
				holes2.append(hole)
				hole.stats['good'] = True
			else:
				hole.stats['good'] = False
		self.__update_result('holes2', holes2)

	def find_holes(self):
		self.find_edges()
		self.create_template()
		self.correlate_template()
		self.threshold_correlation()
		self.find_blobs()
		self.blobs_to_lattice()
		self.mark_holes()
		self.calc_holestats()
		#self.calc_ice()

if __name__ == '__main__':
	#hf = HoleFinder(9,1.4)
	hf = HoleFinder()
	hf['original'] = mrc.read('03sep16a/03sep16a.001.mrc')
	hf.threshold = 1.6
	hf.configure_template(min_radius=23, max_radius=29)
	hf.configure_lattice(tolerance=0.08, spacing=122)
	hf.find_holes()
