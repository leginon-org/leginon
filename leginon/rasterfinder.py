#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import targetfinder
import Mrc
import threading
import ice
try:
	import numarray as Numeric
except:
	import Numeric
import imagefun
import gui.wx.RasterFinder

class RasterFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.RasterFinder.Panel
	settingsclass = data.RasterFinderSettingsData
	defaultsettings = {
		'wait for done': True,
		'ignore images': False,
		'user check': False,
		'image filename': '',
		'raster spacing': 100,
		'raster limit': 5,
		'ice box size': 15.0,
		'ice thickness': 1000.0,
		'ice min mean': 0.05,
		'ice max mean': 0.2,
		'ice max std': 0.2,
		'focus convolve': False,
		'focus convolve template': [],
		'focus constant template': [],
		'acquisition convolve': False,
		'acquisition convolve template': [],
		'acquisition constant template': [],
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.icecalc = ice.IceCalculator()
		self.rasterpoints = None

		self.userpause = threading.Event()
		self.images = {
			'Original': None,
		}
		self.imagetargets = {
			'Original': {},
			'Raster': {},
			'Final': {},
		}
		self.start()

	def readImage(self, filename):
		orig = Mrc.mrc_to_numeric(filename)
		self.original = orig
		self.setImage(orig, 'Original')

	def transpose_points(self, points):
		newpoints = []
		for point in points:
			newpoints.append((point[1],point[0]))
		return newpoints

	def createRaster(self):
		'''
		from center of image, generate a raster of points
		'''
		imageshape = self.original.shape
		spacing = self.settings['raster spacing']
		limit = self.settings['raster limit']
		rcenter = imageshape[0]/2
		ccenter = imageshape[1]/2
		points = []
		for rlayer in range(-limit, limit+1):
			r = int(rcenter + rlayer * spacing)
			if r < 0 or r >= imageshape[0]: continue
			for clayer in range(-limit, limit+1):
				c = int(ccenter + clayer * spacing)
				if c < 0 or c >= imageshape[1]: continue
				points.append((r,c))

		self.setTargets(self.transpose_points(points), 'Raster')
		self.rasterpoints = points
		self.logger.info('Full raster has %s points' % (len(points),))

	def get_box_stats(self, image, coord, boxsize):
		## select the region of interest
		b2 = boxsize / 2
		rmin = int(coord[0]-b2)
		rmax = int(coord[0]+b2)
		cmin = int(coord[1]-b2)
		cmax = int(coord[1]+b2)
		## beware of boundaries
		if rmin < 0:  rmin = 0
		if rmax >= image.shape[0]:  rmax = image.shape[0]-1
		if cmin < 0:  cmin = 0
		if cmax >= image.shape[1]:  cmax = image.shape[1]-1

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		roi = Numeric.ravel(subimage)
		mean = imagefun.mean(roi)
		std = imagefun.stdev(roi, known_mean=mean)
		n = len(roi)
		stats = {'mean':mean, 'std': std, 'n':n}
		return stats

	def ice(self):
		i0 = self.settings['ice thickness']
		tmin = self.settings['ice min mean']
		tmax = self.settings['ice max mean']
		tstd = self.settings['ice max std']
		boxsize = self.settings['ice box size']

		self.icecalc.set_i0(i0)

		## calculate stats around each raster point
		goodpoints = []
		mylist = []
		for rasterpoint in self.rasterpoints:
			box_stats = self.get_box_stats(self.original, rasterpoint, boxsize)
			t = self.icecalc.get_thickness(box_stats['mean'])
			ts = self.icecalc.get_stdev_thickness(box_stats['std'], box_stats['mean'])
			if (tmin <= t <= tmax) and (ts < tstd):
				goodpoints.append(rasterpoint)
				mylist.append( (rasterpoint, t, ts))
				stat_str = 'OK:  '
			else:
				stat_str = 'BAD: '
			ice_stat = '  mean: %.4f,     std: %.4f' % (t,ts)
			stat_str = stat_str + str(rasterpoint) + ice_stat
			self.logger.info(stat_str)

		goodpoints = self.transpose_points(goodpoints)
		self.logger.info('%s points with good ice' % (len(goodpoints),))

		### run template convolution
		# takes x,y instead of row,col
		if self.settings['focus convolve']:
			focus_points = self.applyTargetTemplate(goodpoints, 'focus')
		else:
			focus_points = []
		if self.settings['acquisition convolve']:
			acq_points = self.applyTargetTemplate(goodpoints, 'acquisition')
		else:
			acq_points = goodpoints

		## add constant targets
		const_foc = self.settings['focus constant template']
		focus_points.extend(const_foc)
		const_acq = self.settings['acquisition constant template']
		acq_points.extend(const_acq)

		self.setTargets(acq_points, 'acquisition')
		self.setTargets(focus_points, 'focus')

	def applyTargetTemplate(self, centers, type):
		if type == 'focus':
			vects = self.settings['focus convolve template']
		elif type == 'acquisition':
			vects = self.settings['acquisition convolve template']
		newtargets = []
		for center in centers:
			for vect in vects:
				target = center[0]+vect[0], center[1]+vect[1]
				newtargets.append(target)
		return newtargets

	def everything(self):
		self.createRaster()
		# ice
		self.ice()

	def findTargets(self, imdata, targetlist):
		## check if targets already found on this image
		previous = self.researchTargets(image=imdata)
		if previous:
			return

		## display image
		self.setImage(imdata['image'], 'Original')

		## automated part
		self.original = imdata['image']
		self.everything()

		## user part
		if self.settings['user check']:
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.panel.targetsSubmitted()
			self.setStatus('processing')

		## the new way
		self.logger.info('Publishing targets...')
		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)

	def submit(self):
		self.userpause.set()
