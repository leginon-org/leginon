#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import os
import math
import numpy
import threading
import itertools
from scipy import ndimage
#leginon
import ice
import version
import targetfinder
import jahcfinderback
import voronoiWrapper
from leginon import leginondata
import gui.wx.DoGFinder
from pyami import imagefun
from pyami import ordereddict

invsqrt2 = math.sqrt(2.0)/2.0
default_template = os.path.join(version.getInstalledLocation(),'holetemplate.mrc')

class DoGFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.DoGFinder.Panel
	settingsclass = leginondata.DoGFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'dog diameter': 100,
		'dog invert': False,
		'dog k-factor': 1.3,
		'threshold': 1.0,
		'threshold method': "Threshold = mean + A * stdev",
		'blobs border': 20,
		'blobs max': 100,
		'blobs max size': 10000,
		'blobs min size': 100,
		'lattice hole radius': 15.0,
		'lattice zero thickness': 1000.0,
		'ice min mean': 0.0,
		'ice max mean': 0.6,
		'ice max std': 0.2,
		'focus hole': 'Central Voronoi',
		'target template': False,
		'focus template': [(0, 0)],
		'acquisition template': [(0, 0)],
		'focus template thickness': False,
		'focus stats radius': 10,
		'focus min mean thickness': 0.05,
		'focus max mean thickness': 0.5,
		'focus max stdev thickness': 0.5,
		'focus interval': 1,
		'focus offset row': 0,
		'focus offset col': 0,
	})
	extendtypes = ['off', 'full', '3x3']
	targetnames = targetfinder.TargetFinder.targetnames + ['Blobs']
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.icecalc = ice.IceCalculator()
		self.circle = jahcfinderback.CircleMaskCreator()

		self.theshImage = None
		self.dogmap = None
		self.blobs = None
		self.holes = None
		self.goodholes = None

		self.images = {
			'Original': None,
			'DoG': None,
			'Threshold': None,
			'Blobs': None,
			'Final': None,
		}
		self.imagetargets = {
			'Original': {},
			'DoG': {},
			'Threshold': {},
			'Blobs': {},
			'Final': {},
		}

		self.focustypes = ['Off', 'Central Voronoi', 'Good Voronoi', 'Any Hole', 'Good Hole', 'Center', ]
		self.userpause = threading.Event()
		self.foc_counter = itertools.count()
		self.foc_activated = False
		self.start()

	def readImage(self, filename):
		self.original = targetfinder.TargetFinder.readImage(self, filename)

	def dogFilter(self):
		'''
		Set configuration and then create template and correlate
		'''
		self.logger.info('apply difference of Gaussians filter')
		# convert diameters to radii
		pixel_diameter = self.settings['dog diameter']
		invert = self.settings['dog invert']
		kfactor = self.settings['dog k-factor']

		self.logger.info('DoG: pixel diameter: %d, k-factor: %.3f'%(pixel_diameter, kfactor))

		if invert is False:
			imgarray0 = -1.0 * self.original
		else:
			imgarray0 = self.original

		# find xi (E) function of k
		Ek = math.sqrt( (kfactor**2 - 1.0) / (2.0 * kfactor**2 * math.log(kfactor)) )

		# convert pixel diameter to sigma1
		# 0.6 is extra adjustment factor that is not in DoG picker
		sigma1 = Ek * pixel_diameter/2.0 * 0.6

		# find sigmaprime
		sigmaprime = sigma1 * math.sqrt(kfactor**2 - 1.0)

		#do the blurring
		#first blur
		imgarray1 = ndimage.gaussian_filter(imgarray0, sigma=sigma1, mode='reflect')
		# double blur of first blur
		imgarray2 = ndimage.gaussian_filter(imgarray1, sigma=sigmaprime, mode='reflect')

		#subtract
		self.dogmap = imgarray2 - imgarray1

		self.dogmap = numpy.where(self.dogmap < 0, 0, self.dogmap)

		self.setImage(self.dogmap, 'DoG')

	def threshold(self):
		self.logger.info('Thresholding map')
		tvalue = self.settings['threshold']
		tmeth = self.settings['threshold method']
		cc = self.dogmap.copy()
		mean = numpy.mean(cc)
		std = numpy.std(cc)
		if tmeth == "Threshold = mean + A * stdev":
			thresh = mean + tvalue * std
		else:
			thresh = tvalue
		self.theshImage = imagefun.threshold(cc, thresh)
		t = self.theshImage
		pixelcount = t.sum()
		percent = pixelcount / float(t.shape[0] * t.shape[1])
		self.logger.info('thresholded %d percent of the image'%(percent*100))
		self.setImage(t, 'Threshold')

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def blobStatsTargets(self, blobs):
		targets = []
		for blob in blobs:
			target = {}
			target['x'] = blob.stats['center'][1]
			target['y'] = blob.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Size'] = blob.stats['n']
			target['stats']['Mean'] = blob.stats['mean']
			target['stats']['Std. Dev.'] = blob.stats['stddev']
			targets.append(target)
		return targets

	def findBlobs(self):
		'''
		find blobs on a thresholded image
		'''
		self.logger.info('find blobs')
		border = self.settings['blobs border']
		maxblobsize = self.settings['blobs max size']
		minblobsize = self.settings['blobs min size']
		maxblobs = self.settings['blobs max']
		if self.theshImage is None or self.dogmap is None:
			raise RuntimeError('need correlation image and threshold image to find blobs')
		im = self.dogmap
		mask = self.theshImage
		self.blobs = imagefun.find_blobs(im, mask, border, maxblobs, maxblobsize, minblobsize)
		targets = self.blobStatsTargets(self.blobs)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')

	def holeStatsTargets(self, holes):
		targets = []
		holes = self.blobs #self.getTargets('Blobs')
		for hole in holes:
			mean = float(hole.stats['hole_mean'])
			tmean = self.icecalc.get_thickness(mean)
			std = float(hole.stats['hole_std'])
			tstd = self.icecalc.get_stdev_thickness(std, mean)

			target = {}
			target['x'] = hole.stats['center'][1]
			target['y'] = hole.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Mean Intensity'] = mean
			target['stats']['Mean Thickness'] = tmean
			target['stats']['S.D. Intensity'] = std
			target['stats']['S.D. Thickness'] = tstd
			targets.append(target)
		return targets

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
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.circle.get(subimage.shape, center, 0, radius)
		im = numpy.ravel(subimage)
		mask = numpy.ravel(mask)
		roi = numpy.compress(mask, im)
		mean = numpy.mean(roi)
		std = numpy.std(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}

	def calc_holestats(self):
		'''
		This adds hole stats to holes.
		'''
		if self.blobs is None:
			raise RuntimeError('need blobs to calculate hole stats')
		im = self.original
		r = self.settings['lattice hole radius']
		blobs = self.blobs
		holes = []
		for blob in blobs:
			coord = blob.stats['center']
			holestats = self.get_hole_stats(im, coord, r)
			if holestats is None:
				continue
			blob.stats['hole_stat_radius'] = r
			blob.stats['hole_n'] = holestats['n']
			blob.stats['hole_mean'] = holestats['mean']
			blob.stats['hole_std'] = holestats['std']
			holes.append(blob)
		return holes

	def calc_ice(self, i0=None, tmin=None, tmax=None, tstd=None):
		self.holes = self.calc_holestats()
		if self.holes is None:
			raise RuntimeError('need holes to calculate ice')
		holes = self.holes
		goodholes = []
		self.icecalc.set_i0(i0)
		thicknesses = []
		stdevthicks = []
		for hole in holes:
			if 'hole_mean' not in hole.stats:
				## no mean was calculated
				continue
			mean = hole.stats['hole_mean']
			std = hole.stats['hole_std']
			tm = self.icecalc.get_thickness(mean)
			hole.stats['thickness-mean'] = tm
			thicknesses.append(tm)
			ts = self.icecalc.get_stdev_thickness(std, mean)
			stdevthicks.append(ts)
			hole.stats['thickness-stdev'] = ts
			if (tmin <= tm <= tmax) and (ts < tstd):
				goodholes.append(hole)
				hole.stats['good'] = True
			else:
				hole.stats['good'] = False
		self.logger.info('hole thinkness-mean: %.3f +/- %.3f'%(numpy.mean(thicknesses), numpy.std(thicknesses)))
		self.logger.info('hole thinkness-stdev: %.3f +/- %.3f'%(numpy.mean(stdevthicks), numpy.std(stdevthicks)))
		self.logger.info('%d of %d blobs are good holes'%(len(goodholes), len(self.blobs)))
		self.holes = goodholes

	def ice(self):
		self.logger.info('limit holes by thickness')
		i0 = self.settings['lattice zero thickness']
		tmin = self.settings['ice min mean']
		tmax = self.settings['ice max mean']
		tstd = self.settings['ice max std']
		try:
			self.calc_ice(i0=i0, tmin=tmin, tmax=tmax, tstd=tstd)
		except Exception, e:
			self.logger.error(e)
			return
		goodholes = self.holes
		centers = self.blobCenters(goodholes)
		allcenters = self.blobCenters(self.blobs)

		# activate if counter is at a multiple of interval
		interval = self.settings['focus interval']
		if interval and not (self.foc_counter.next() % interval):
			self.foc_activated = True
		else:
			self.foc_activated = False

		focus_points = []

		if self.foc_activated:
			## replace an acquisition target with a focus target
			onehole = self.settings['focus hole']
			if centers and onehole != 'Off':
				## if only one hole, this is useless
				if len(allcenters) < 2:
					self.logger.info('need more than one hole if you want to focus on one of them')
					centers = []
				elif onehole == 'Central Voronoi':
					fpoint = self.centralVoronoiFocus(allcenters)
					focus_points.append(fpoint)
				elif onehole == 'Good Voronoi':
					fpoint = self.goodVoronoiFocus(allcenters)
					focus_points.append(fpoint)
				elif onehole == 'Center':
					focus_points.append(self.centerCarbon(allcenters))
				elif onehole == 'Any Hole':
					fochole = self.focus_on_hole(centers, allcenters, True)
					focus_points.append(fochole)
				elif onehole == 'Good Hole':
					if len(centers) < 2:
						self.logger.info('need more than one good hole if you want to focus on one of them')
						centers = []
					else:
						## use only good centers
						fochole = self.focus_on_hole(centers, centers, True)
						focus_points.append(fochole)

		self.logger.info('Holes with good ice: %s' % (len(centers),))
		# takes x,y instead of row,col
		if self.settings['target template']:
			newtargets = self.applyTargetTemplate(centers)
			acq_points = newtargets['acquisition']
			focus_points.extend(newtargets['focus'])
		else:
			acq_points = centers
		# need just one focus point
		if len(focus_points) > 1 and self.settings['focus template thickness']:
			focpoint = self.focus_on_hole(focus_points,focus_points, False)
			focus_points = [focpoint]
		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)
		self.logger.info('Acquisition Targets: %s' % (len(acq_points),))
		self.logger.info('Focus Targets: %s' % (len(focus_points),))
		if type(self.currentimagedata) == type(leginondata.AcquisitionImageData()):
			hfprefs = self.storeHoleFinderPrefsData(self.currentimagedata)
			self.storeHoleStatsData(hfprefs)

	def calc_focus_stats(self, focus_points):
		im = self.original
		r = self.settings['focus stats radius']
		focus_spots= []
		self.icecalc.set_i0(self.settings['lattice zero thickness'])
		for coord in focus_points:
			focus_stats = self.get_hole_stats(im, coord, r)
			if focus_stats is None:
				continue
			focus_spot = {'coord': coord}
			focus_spot['hole_stat_radius'] = r
			focus_spot['hole_n'] = focus_stats['n']
			focus_spot['hole_mean'] = focus_stats['mean']
			focus_spot['hole_std'] = focus_stats['std']
			mean = float(focus_stats['mean'])
			focus_spot['thickness-mean'] = self.icecalc.get_thickness(mean)
			std = float(focus_stats['std'])
			focus_spot['thickness-stdev'] = self.icecalc.get_stdev_thickness(std, mean)
			focus_spots.append(focus_spot)
		return focus_spots

	def goodVoronoiFocus(self, target_points):
		focus_points = voronoiWrapper.pointsToVoronoiPoints(target_points)
		focus_points = voronoiWrapper.filterVoronoiPoints(target_points, focus_points)
		self.setTargets(focus_points, 'Voronoi')
		focus_spots = self.calc_focus_stats(focus_points)
		if len(focus_spots) < 1:
			self.logger.error('failed to find any focus spots')
			return None

		tmin = self.settings['focus min mean thickness']
		tmax = self.settings['focus max mean thickness']
		tstd = self.settings['focus max stdev thickness']
		good_focus_points = []
		thicknesses = []
		stdevthicks = []
		for focus_spot in focus_spots:
			if 'hole_mean' not in focus_spot:
				## no mean was calculated
				continue
			tm = focus_spot['thickness-mean']
			ts = focus_spot['thickness-stdev']
			thicknesses.append(tm)
			stdevthicks.append(ts)
			if (tmin <= tm <= tmax) and (ts < tstd):
				good_focus_points.append(focus_spot['coord'])

		self.logger.info('focus thinkness-mean: %.3f +/- %.3f'%(numpy.mean(thicknesses), numpy.std(thicknesses)))
		self.logger.info('focus thinkness-stdev: %.3f +/- %.3f'%(numpy.mean(stdevthicks), numpy.std(stdevthicks)))
		self.logger.info('%d of %d Voronoi points are good focus spots'%(len(good_focus_points), len(focus_points)))

		if len(good_focus_points) < 1:
			self.logger.warning('failed to find any good focus spots, using central spot')
			middle_point = self.centralPoint(focus_points)
			return middle_point

		middle_point = self.centralPoint(good_focus_points)
		return middle_point

	def centralVoronoiFocus(self, target_points):
		focus_points = voronoiWrapper.pointsToVoronoiPoints(target_points)
		focus_points = voronoiWrapper.filterVoronoiPoints(target_points, focus_points)
		self.setTargets(focus_points, 'Voronoi')
		middle_point = self.centralPoint(focus_points)
		return middle_point

	def centralPoint(self, points):
		numpypoints = numpy.array(points)
		print numpypoints.shape
		xavg = (numpypoints[:,0]).mean()
		yavg = (numpypoints[:,1]).mean()
		a = numpy.array((xavg, yavg))
		print a
		mindist = 1e10
		for p in points:
			dist = numpy.power(a - p, 2).mean()
			if dist < mindist:
				minpoint = p
				mindist = dist
		return minpoint

	def centerCarbon(self, points):
		temppoints = points
		centerhole = self.focus_on_hole(temppoints, temppoints, False)
		closexdist = 1.0e10
		closeydist = 1.0e10
		xdist = 0.0
		ydist = 0.0
		for point in points:
			#find nearest points and get the components
			xdist = abs(point[0]-centerhole[0])
			if xdist < closexdist:
				closexdist = xdist
			ydist = abs(point[1]-centerhole[1])
			if ydist < closeydist:
				closeydist = ydist
		centercarbon = tuple(
			(int(centerhole[0] + xdist/2.0),
			int(centerhole[1] + ydist/2.0),)
		)
		return centercarbon

	def centroid(self, points):
		numpypoints = numpy.array(points)
		cx = (numpypoints[:,0]).mean()
		cy = (numpypoints[:,1]).mean()
		return cx,cy

	def focus_on_hole(self, good, all, apply_offset=False):
		## make a list of the bad holes
		allset = set(all)
		goodset = set(good)
		badset = allset - goodset
		bad = list(badset)

		## if there are bad holes, use one
		if bad:
			closest_point = self.centralPoint(bad)
			if apply_offset:
				closest_point = self.offsetFocus(closest_point)
			return closest_point

		## now use a good hole for focus
		closest_point = self.centralPoint(good)
		good.remove(closest_point)
		if apply_offset:
			closest_point = self.offsetFocus(closest_point)
		return closest_point

	def offsetFocus(self, point):
		return point[0]+self.settings['focus offset col'],point[1]+self.settings['focus offset row']

	def bypass(self):
		self.setTargets([], 'Blobs', block=True)
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)
		self.setTargets([], 'preview', block=True)

	def applyTargetTemplate(self, centers):
		self.logger.info('apply template')

		imshape = self.original.shape
		acq_vect = self.settings['acquisition template']
		foc_vect = self.settings['focus template']
		newtargets = {'acquisition':[], 'focus':[]}

		focuscenters = centers

		for vect in acq_vect:
			for center in centers:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				newtargets['acquisition'].append(target)
		if not self.foc_activated:
			return newtargets
		for vect in foc_vect:
			for center in focuscenters:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				## check if target has good thickness
				if self.settings['focus template thickness']:
					rad = self.settings['focus stats radius']
					tmin = self.settings['focus min mean thickness']
					tmax = self.settings['focus max mean thickness']
					tstd = self.settings['focus max stdev thickness']
					coord = target[1], target[0]
					stats = self.get_hole_stats(self.original, coord, rad)
					if stats is None:
						self.logger.info('skipping template point %s:  stats region out of bounds' % (vect,))
						continue
					tm = self.icecalc.get_thickness(stats['mean'])
					ts = self.icecalc.get_stdev_thickness(stats['std'], stats['mean'])
					self.logger.info('template point %s stats:  mean: %s, stdev: %s' % (vect, tm, ts))
					if (tmin <= tm <= tmax) and (ts < tstd):
						self.logger.info('template point %s passed thickness test' % (vect,))
						newtargets['focus'].append(target)
						break
				else:
					newtargets['focus'].append(target)
		return newtargets

	def everything(self):
		# correlate template
		self.dogFilter()
		# threshold
		self.threshold()
		# find blobs
		self.findBlobs()
		# ice
		self.ice()

	def storeHoleStatsData(self, prefs):
		holes = self.holes
		for hole in holes:
			stats = hole.stats
			holestats = leginondata.HoleStatsData(session=self.session, prefs=prefs)
			holestats['row'] = stats['center'][0]
			holestats['column'] = stats['center'][1]
			holestats['mean'] = stats['hole_mean']
			holestats['stdev'] = stats['hole_std']
			holestats['thickness-mean'] = stats['thickness-mean']
			holestats['thickness-stdev'] = stats['thickness-stdev']
			holestats['good'] = stats['good']
			self.publish(holestats, database=True)

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = leginondata.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'threshold-value': self.settings['threshold'],
			'threshold-method': self.settings['threshold method'],
			'blob-border': self.settings['blobs border'],
			'blob-max-number': self.settings['blobs max'],
			'blob-max-size': self.settings['blobs max size'],
			'blob-min-size': self.settings['blobs min size'],
			'stats-radius': self.settings['lattice hole radius'],
			'ice-zero-thickness': self.settings['lattice zero thickness'],

			'ice-min-thickness': self.settings['ice min mean'],
			'ice-max-thickness': self.settings['ice max mean'],
			'ice-max-stdev': self.settings['ice max std'],
			'template-on': self.settings['target template'],
			'template-focus': self.settings['focus template'],
			'template-acquisition': self.settings['acquisition template'],

			## these are in JAHCFinder only
			'dog-diameter': self.settings['dog diameter'],
			'dog-invert': self.settings['dog invert'],
			'dog-k-factor': self.settings['dog k-factor'],
		})
		self.publish(hfprefs, database=True)
		return hfprefs

	def findTargets(self, imdata, targetlist):
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.original = imdata['image']
		self.currentimagedata = imdata
		self.setImage(imdata['image'], 'Original')
		if not self.settings['skip']:
			if self.isFromNewParentImage(imdata):
				self.logger.debug('Reset focus counter')
				self.foc_counter = itertools.count()
				self.resetLastFocusedTargetList(targetlist)
			autofailed = False
			try:
				self.everything()
			except Exception, e:
				self.logger.error('auto target finder failed: %s' % (e,))
				autofailed = True

		## user part
		if self.settings['user check'] or autofailed:
			while True:
				self.waitForInteraction(imdata)
				if not self.processPreviewTargets(imdata, targetlist):
					break
			self.panel.targetsSubmitted()
		self.setStatus('idle')
