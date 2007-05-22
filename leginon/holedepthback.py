#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

# this is python Numeric version of -radial_image (mon_radial_image)

import numpy
from pyami import imagefun, correlator, peakfinder, convolver, mrc, arraystats
import ice

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

class OvalMaskCreator(object):
	def __init__(self):
		self.masks = {}

	def get(self, shape, center, minradius, maxradius,angle,tltaxis):
		'''
		create binary mask of a oval centered at 'center'
		'''
		## use existing oval mask
		key = (shape, center, minradius, maxradius,angle,tltaxis)
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
	
		def oval(indices0,indices1):
			## this shifts and wraps the indices
			i0 = numpy.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = numpy.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			j0 = i0*numpy.cos(tltaxis)+i1*numpy.sin(tltaxis)
			j1 = -i0*numpy.sin(tltaxis)+i1*numpy.cos(tltaxis)
			rsq = j0*j0+j1*j1/(numpy.cos(angle)*numpy.cos(angle))
			c = numpy.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c.astype(numpy.int8)
		temp = numpy.fromfunction(oval, shape)
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
		hf.configure_pickhole(hole_center)
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
			'holes': None,
			'markedholes': None,
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('edges',),
			'edges': ('correlation',),
			'template': ('correlation',),
			'correlation': ('threshold',),
			'threshold': ('blobs',),
			'blobs': (),
			'holes': ('markedholes',),
			'markedholes': (),
		}

		## other necessary components
		self.edgefinder = convolver.Convolver()
		self.peakfinder = peakfinder.PeakFinder()
		self.circle = CircleMaskCreator()
		self.oval = OvalMaskCreator()
		self.icecalc = ice.IceCalculator()

		## some default configuration parameters
		self.save_mrc = False
		self.edges_config = {'filter': 'sobel', 'size': 9, 'sigma': 1.4, 'abs': False, 'lp':True, 'lpsig':1.0, 'thresh':100.0, 'edges': True}
		self.template_config = {'ring_list': [(25,30)],'tilt_axis':0.0}
		self.correlation_config = {'cortype': 'cross', 'corfilt': (1.0,)}
		self.threshold = 3.0
		self.blobs_config = {'border': 20, 'maxblobsize': 50, 'maxblobs':100}
		self.makeblobs_config = {'center_list': [(100,100)]}
		self.dist_config = {'binned_pixel': 2e-10}
		self.pickhole_config = {'center_list': [(100,100)]}
		self.holestats_config = {'radius': 20}

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
		filt = self.edges_config['filter']
		sigma = self.edges_config['sigma']
		ab = self.edges_config['abs']
		lpsig = self.edges_config['lpsig']
		edgethresh = self.edges_config['thresh']
		edgesflag = self.edges_config['edges']

		kernel = convolver.gaussian_kernel(lpsig)
		n = len(kernel)
		self.edgefinder.setKernel(kernel)
		smooth = self.edgefinder.convolve(image=sourceim)

		if not edgesflag:
			edges = smooth
		elif filt == 'laplacian3':
			kernel = convolver.laplacian_kernel3
			self.edgefinder.setKernel(kernel)
			edges = self.edgefinder.convolve(image=smooth)
		elif filt == 'laplacian5':
			kernel = convolver.laplacian_kernel5
			self.edgefinder.setKernel(kernel)
			edges = self.edgefinder.convolve(image=smooth)
		elif filt == 'laplacian-gaussian':
			kernel = convolver.laplacian_of_gaussian_kernel(n,sigma)
			self.edgefinder.setKernel(kernel)
			edges = self.edgefinder.convolve(image=smooth)
		elif filt == 'sobel':
			self.edgefinder.setImage(smooth)
			kernel1 = convolver.sobel_row_kernel
			kernel2 = convolver.sobel_col_kernel
			edger = self.edgefinder.convolve(kernel=kernel1)
			edgec = self.edgefinder.convolve(kernel=kernel2)
			edges = numpy.hypot(edger,edgec)
			## zero the image edge effects
			edges[:n] = 0
			edges[:,:n] = 0
			edges[:,-n:] = 0
			edges[-n:] = 0
		else:
			raise RuntimeError('no such filter type: %s' % (filt,))

		if ab and edgesflag:
			edges = numpy.absolute(edges)

		if edgethresh and edgesflag:
			edges = imagefun.threshold(edges, edgethresh)

		self.__update_result('edges', edges)
		if self.save_mrc:
			mrc.write(edges, 'edges.mrc')

	def configure_template(self, ring_list=None,tilt_axis=None,tilt_angle=None):
		if ring_list is not None:
			self.template_config['ring_list'] = ring_list
		if tilt_axis is not None:
			self.template_config['tilt_axis'] = tilt_axis
		if tilt_angle is not None:
			self.template_config['tilt_angle'] = tilt_angle

	## for test1, test1: 30, 37
	## for test3, test4: 22, 30
	def create_template(self, ring_list=None,tilt_axis=None,tilt_angle=None):
		'''
		This creates the template image that will be correlated
		with the edge image.  This will fail if there is no
		existing edge image, which is necessary to determine the
		size of the template.
		'''
		fromimage = 'edges'
		if self.__results[fromimage] is None:
			raise RuntimeError('need image %s before creating template' % (fromimage,))
		self.configure_template(ring_list,tilt_axis,tilt_angle)
		shape = self.__results[fromimage].shape
		center = (0,0)
		ring_list = self.template_config['ring_list']
		template = numpy.zeros(shape, numpy.int8)
		tilt_axis = self.template_config['tilt_axis']
		tltangle = self.template_config['tilt_angle']
		tltaxis=(tilt_axis*numpy.pi/180)
		for ring in ring_list:
			temp = self.oval.get(shape, center, ring[0], ring[1],tltangle,tltaxis)
			template = template | temp
		template = template.astype(numpy.float32)
		#template = imagefun.zscore(template)
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
		#cc = imagefun.zscore(smooth)
		#cc = imagefun.zscore(cc)
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
		t = imagefun.threshold(cc, self.threshold)
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

	def configure_makeblobs(self, center_list=None):
		if center_list is not None:
			self.makeblobs_config['center_list'] = center_list

	def make_blobs(self):
		'''
		This adds hole stats to holes.
		'''
		if self.__results['original'] is None:
			raise RuntimeError('need original to make dummy blobs')
		im = self.__results['original']
		blobs = []
		realblobs = self.makeblobs_config['center_list']
		for realblob in realblobs:
			coord = [realblob[1],realblob[0]]
		        blob = imagefun.Blob(im,None,None,coord,None,None)
			blobs.append(blob)
		self.__results['blobs']=blobs
		
	def configure_distance(self, binned_pixel=None):
		if binned_pixel is not None:
			self.dist_config['binned_pixel'] = binned_pixel

	def find_distance(self):
		if None in (self.__results['blobs'],):
			raise RuntimeError('need blobs to calc hole depth')
		blobnumber = 0
		blobcoord = []
		holedepth = {}
		binnedpixel=self.dist_config['binned_pixel']
		tiltangle = self.template_config['tilt_angle']
		tilt_axis = self.template_config['tilt_axis']
		tiltaxis=(tilt_axis*numpy.pi/180)
		for blob in self.__results['blobs']:
			blobcoord.append(blob.stats['center'])
			blobnumber = blobnumber+1
		if (blobnumber != 2):
			if (blobnumber != 1):
				print 'only 1 or 2 blobs allowed'
				blobdist=0
				blobtilt=0
			else:
				print 'unresolved'
				blobdist=1.0
				blobtilt=tiltaxis
		else:
			blobdx=blobcoord[0][0]-blobcoord[1][0]
			blobdy=blobcoord[0][1]-blobcoord[1][1]
			blobdist = numpy.sqrt(blobdx**2+blobdy**2)
			blobtilt = -numpy.arctan(float(blobdx)/blobdy)
		holedepth['depth'] = binnedpixel*blobdist/numpy.abs(numpy.sin(tiltangle))
		holedepth['tilt'] = blobtilt
		return holedepth

	def configure_pickhole(self, center_list=None):
		if center_list is not None:
			self.pickhole_config['center_list'] = center_list

	def calc_holestats(self, radius=None):
		'''
		This adds hole stats to holes.
		'''
		if self.__results['original'] is None:
			raise RuntimeError('need original to calculate picked hole stats')
		self.configure_holestats(radius=radius)
		im = self.__results['original']
		r = self.holestats_config['radius']
		holes = []
		realholes = self.pickhole_config['center_list']
		for realhole in realholes:
			coord = [realhole[1],realhole[0]]
			holestats = self.get_hole_stats(im, coord, r)
			'''
			First create a dummy blob from the coordinate then fill in the stats
			'''
		        hole = imagefun.Blob(im,None,None,coord,None,None)
			hole.stats['n'] = holestats['n']
			hole.stats['hole_mean'] = holestats['mean']
			hole.stats['hole_std'] = holestats['std']
			holes.append(hole)
		self.__results['holes']=holes
		
	def shift_holes(self,I_image=None,I0_image=None):
		I=I_image
		I0=I0_image
		cc = correlator.cross_correlate(I, I0)
		self.peakfinder.setImage(cc)
		peak=self.peakfinder.pixelPeak()
		delta = correlator.wrap_coord(peak, cc.shape)
		delta_transposed=(delta[1],delta[0])
		return delta_transposed
		

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

	def find_holes(self):
		self.find_edges()
		self.create_template()
		self.correlate_template()
		self.threshold_correlation()
		self.find_blobs()
		self.mark_holes()
		self.calc_holestats()

if __name__ == '__main__':
	#hf = HoleFinder(9,1.4)
	hf = HoleFinder()
	hf['original'] = mrc.read('03sep16a/03sep16a.001.mrc')
	hf.threshold = 1.6
	hf.configure_template(min_radius=23, max_radius=29)
	hf.configure_pickhole(center_list=None)
	hf.find_holes()
