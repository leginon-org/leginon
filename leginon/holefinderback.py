#!/usr/bin/env python
# this is python Numeric version of -radial_image (mon_radial_image)

import Numeric
import Mrc
import imagefun
import peakfinder
import LinearAlgebra

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
			i0 = Numeric.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = Numeric.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			rsq = i0*i0+i1*i1
			c = Numeric.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c
		temp = Numeric.fromfunction(circle, shape)
		self.masks[key] = temp
		return temp

class Lattice(object):
	def __init__(self, firstblob, spacing, tolerance=0.1):
		self.blobs = []
		self.lattice_points_blob = {}
		self.lattice_points_err = {}
		self.center = None

		self.tolerance = tolerance
		## spacing is either given as a distance or a vector
		spacingarray = Numeric.array(spacing, Numeric.Float32)
		if len(spacingarray) == 1:
			self.spacing = spacingarray
			self.vector = None
		elif len(spacingarray) == 2:
			self.spacing = None
			self.vector = spacingarray

		self.add_first_blob(firstblob)

	def add_blob(self, newblob):
		num = len(self.blobs)
		if num == 0:
			self.add_first_blob(newblob)
		elif num == 1:
			self.add_second_blob(newblob)
		else:
			self.add_any_blob(newblob)

	def add_first_blob(self, firstblob):
		self.blobs.append(firstblob)
		self.lattice_points_blob[(0,0)] = firstblob
		self.lattice_points_err[(0,0)] = 0.0
		self.center = firstblob.stats['center']

	def add_second_blob(self, secondblob):
		'''
		If the lattice vector still needs to be determined,
		see if this blob is at proper spacing, then add it
		and calculate vector.

		If the lattice vector is already known, treat this blob
		like any other.
		'''
		## check if vector is known
		if self.vector is None:
			## check if spacing is within tolerance
			c1 = self.center
			c2 = secondblob.stats['center']
			v = float(c2[0]-c1[0]), float(c2[1]-c1[1])
			dist = Numeric.hypot(v[0],v[1])
			nf = dist / self.spacing
			n = int(round(nf))
			if n == 0:
				## we can only have one blob at (0,0)
				return
			err = Numeric.absolute(nf - n)
			if err < self.tolerance:
				point = (n,0)
				self.vector = (v[0]/n, v[1]/n)
				self.lattice_points_blob[point] = secondblob
				## I am trusting that my new calculated
				## vector is more reliable than the first
				## guess for spacing, otherwise I could set
				## error to be err instead of 0.0
				self.lattice_points_err[point] = 0.0
				self.blobs.append(secondblob)
		else:
			self.add_any_blob(secondblob)

	def add_any_blob(self, blob):
		'''
		this checks to see if a blob falls on a lattice
		point, within a certain tolerance
		'''
		a = Numeric.zeros((2,2), Numeric.Float32)
		a[:,0] = self.vector
		a[:,1] = (-self.vector[1], self.vector[0])
		b = blob.stats['center'] - self.center
		c = LinearAlgebra.solve_linear_equations(a,b)
		closest = int(round(c[0])), int(round(c[1]))
		err = c - closest
		err = Numeric.hypot(err[0], err[1])

		if err < self.tolerance:
			## if already have blob at this lattice point,
			## use the one with least error
			if closest in self.lattice_points_err:
				if self.lattice_points_err[closest] > err:
					## replace existing blob
					self.blobs.remove(self.lattice_points_blob[closest])
					self.blobs.append(blob)
					self.lattice_points_blob[closest] = blob
					self.lattice_points_err[closest] = err
			else:
				self.lattice_points_blob[closest] = blob
				self.lattice_points_err[closest] = err
				self.blobs.append(blob)


class IceCalculator(object):
	def __init__(self, i0=None):
		self.i0 = i0

	def set_i0(self, i0):
		self.i0 = i0

	def get_intensity(self, thickness):
		return self.i0 / Numeric.exp(thickness)

	def get_thickness(self, intensity):
		return Numeric.log(self.i0 / intensity)

	def get_stdev_thickness(self, stdev_intensity, mean_intensity):
		if stdev_intensity >= mean_intensity:
			std = imagefun.inf
		else:
			std = Numeric.log(mean_intensity / (mean_intensity-stdev_intensity))
		return std

	def get_stdev_intensity(self, stdev_thickness, mean_thickness):
		### figure this out later
		pass


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
		#self.edgefinder = imagefun.LaplacianFilter(0.4)
		#self.edgefinder = imagefun.LaplacianGaussianFilter(n, sigma)
		self.peakfinder = peakfinder.PeakFinder()
		self.circle = CircleMaskCreator()
		self.icecalc = IceCalculator()

		## some default configuration parameters
		self.save_mrc = True
		self.edges_config = {'filter': 'laplacian', 'size': 9, 'sigma': 1.4, 'abs': False}
		self.template_config = {'min_radius': 25, 'max_radius': 30}
		self.correlation_config = {'cortype': 'cross correlation'}
		self.threshold = 3.0
		self.blobs_config = {'border': 20}
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

	def configure_edges(self, filter=None, size=None, sigma=None, absvalue=None):
		if filter is not None:
			self.edges_config['filter'] = filter
		if size is not None:
			self.edges_config['size'] = size
		if sigma is not None:
			self.edges_config['sigma'] = sigma
		if absvalue is not None:
			self.edges_config['abs'] = absvalue

	def find_edges(self):
		'''
		find edges on the original image
		'''
		if self.__results['original'] is None:
			raise RuntimeError('no original image to find edges on')

		print 'creating edge filter'
		sourceim = self.__results['original']
		n = self.edges_config['size']
		filt = self.edges_config['filter']
		sigma = self.edges_config['sigma']
		ab = self.edges_config['abs']

		if filt == 'laplacian':
			edgefinder = imagefun.LaplacianFilter()
		elif filt == 'laplacian-gaussian':
			edgefinder = imagefun.LaplacianGaussianFilter(n,sigma)
		else:
			raise RuntimeError('no such filter type: %s' % (filt,))

		print 'finding edges'
		edges = edgefinder.run(sourceim)
		if ab:
			edges = Numeric.absolute(edges)

		self.__update_result('edges', edges)
		if self.save_mrc:
			Mrc.numeric_to_mrc(edges, 'edges.mrc')

	def configure_template(self, min_radius=None, max_radius=None):
		if min_radius is not None:
			self.template_config['min_radius'] = min_radius
		if max_radius is not None:
			self.template_config['max_radius'] = max_radius

	## for test1, test1: 30, 37
	## for test3, test4: 22, 30
	def create_template(self, min_radius=None, max_radius=None):
		'''
		This creates the template image that will be correlated
		with the edge image.  This will fail if there is no
		existing edge image, which is necessary to determine the
		size of the template.
		'''
		if self.__results['edges'] is None:
			raise RuntimeError('need edge image before creating template')
		print 'creating template'
		self.configure_template(min_radius, max_radius)
		shape = self.__results['edges'].shape
		center = (0,0)
		rmin = self.template_config['min_radius']
		rmax = self.template_config['max_radius']
		template = self.circle.get(shape, center, rmin, rmax)
		template = imagefun.zscore(template)
		self.__update_result('template', template)
		if self.save_mrc:
			Mrc.numeric_to_mrc(template, 'template.mrc')

	def configure_correlation(self, cortype=None):
		if cortype is not None:
			self.correlation_config['cortype'] = cortype

	def correlate_template(self):
		if None in (self.__results['edges'], self.__results['template']):
			raise RuntimeError('need edge image and template before correlation')
		print 'correlating template'
		edges = self.__results['edges']
		template = self.__results['template']
		cortype = self.correlation_config['cortype']
		if cortype == 'cross correlation':
			cc = imagefun.cross_correlate(edges, template)
		elif cortype == 'phase correlation':
			cc = imagefun.phase_correlate(edges, template)
		else:
			raise RuntimeError('bad correlation type: %s' % (cortype,))
		cc = imagefun.zscore(cc)
		self.__update_result('correlation', cc)
		if self.save_mrc:
			Mrc.numeric_to_mrc(cc, 'correlation.mrc')

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
		print 'thresholding correlation'
		cc = self.__results['correlation']
		t = imagefun.threshold(cc, self.threshold)
		self.__update_result('threshold', t)
		if self.save_mrc:
			Mrc.numeric_to_mrc(t, 'threshold.mrc')

	def configure_blobs(self, border=None):
		if border is not None:
			self.blobs_config['border'] = border

	def find_blobs(self):
		'''
		find blobs on a thresholded image
		'''
		if None in (self.__results['threshold'],self.__results['correlation']):
			raise RuntimeError('need correlation image and threshold image to find blobs')
		print 'finding blobs'
		im = self.__results['correlation']
		mask = self.__results['threshold']
		border = self.blobs_config['border']
		blobs = imagefun.find_blobs(im, mask, border)
		self.__update_result('blobs', blobs)

	def configure_lattice(self, tolerance=None, spacing=None, minspace=None):
		if tolerance is not None:
			self.lattice_config['tolerance'] = tolerance
		if spacing is not None:
			self.lattice_config['spacing'] = spacing
		if minspace is not None:
			self.lattice_config['minspace'] = minspace

	def find_lattice_vector(self, minspace=None):
		if self.__results['threshold'] is None:
			raise RuntimeError('need threshold image to find vector')
		self.configure_lattice(minspace=minspace)

		## autocorrelation
		mask = self.__results['threshold']
		ac = imagefun.cross_correlate(mask, mask)
		minspace = self.lattice_config['minspace']

		## zero out circle around the minimum 
		tmp = self.circle.get(ac.shape, (0,0), minspace, max(ac.shape))
		ac[:minspace,:minspace] *= tmp[:minspace,:minspace]
		ac[:minspace,-minspace:] *= tmp[:minspace,-minspace:]

		## only need top half
		newrows,newcols = mask.shape[0]/2, mask.shape[1]
		ac = ac[:newrows, :newcols]
		
		self.peakfinder.setImage(ac)
		p = self.peakfinder.subpixelPeak()
		v = list(p)
		# wrap columns
		if p[1] > mask.shape[1]/2:
			v[1] = p[1] - mask.shape[1]
		self.__update_result('vector', v)

	def blobs_to_lattice(self, tolerance=None, spacing=None, minspace=None):
		if self.__results['blobs'] is None:
			raise RuntimeError('need blobs to create lattice')
		self.configure_lattice(tolerance=tolerance,spacing=spacing,minspace=minspace)

		## if spacing is empty vector, fill in vector now
		if self.lattice_config['spacing'] is ():
			self.find_lattice_vector()
			s = self.__results['vector']
		else:
			s = self.lattice_config['spacing']
			
		blobs = self.__results['blobs']
		lattices = []
		tolerance = self.lattice_config['tolerance']

		# create a lattice for every blob
		for blob in blobs:
			lattices.append(Lattice(blob, s, tolerance))
		# see which blobs fit in which lattices
		for blob in blobs:
			#found_lattice = False
			for lat in lattices:
				lat.add_blob(blob)
		# find the best lattice
		maxblobs = 0
		best_lattice = None
		for lat in lattices:
			if len(lat.blobs) > maxblobs:
				maxblobs = len(lat.blobs)
				best_lattice = lat
		print 'best lattice has %s blobs' % (maxblobs,)
		self.__update_result('lattice', best_lattice)
		self.__update_result('holes', best_lattice.blobs)

	def mark_holes(self):
		if None in (self.__results['holes'], self.__results['original']):
			raise RuntimeError('need original image and holes before marking holes')
		image = self.__results['original']
		im = Numeric.array(image)
		value = imagefun.min(im)
		for hole in self.__results['holes']:
			coord = hole.stats['center']
			imagefun.mark_image(im, coord, value)
		self.__update_result('markedholes', im)
		if self.save_mrc:
			Mrc.numeric_to_mrc(im, 'markedholes.mrc')

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
		Mrc.numeric_to_mrc(subimage, 'hole.mrc')
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.circle.get(subimage.shape, center, 0, radius)
		Mrc.numeric_to_mrc(mask, 'holemask.mrc')
		im = Numeric.ravel(subimage)
		mask = Numeric.ravel(mask)
		roi = Numeric.compress(mask, im)
		mean = imagefun.mean(roi)
		std = imagefun.stdev(roi)
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
			t = self.icecalc.get_thickness(hole.stats['hole_mean'])
			ts = self.icecalc.get_stdev_thickness(hole.stats['hole_std'], hole.stats['hole_mean'])
			if (tmin <= t <= tmax) and (ts < tstd):
				holes2.append(hole)
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
	import Mrc
	#hf = HoleFinder(9,1.4)
	hf = HoleFinder()
	hf['original'] = Mrc.mrc_to_numeric('03sep16a/03sep16a.001.mrc')
	hf.threshold = 1.6
	hf.configure_template(min_radius=23, max_radius=29)
	hf.configure_lattice(tolerance=0.08, spacing=122)
	hf.find_holes()
