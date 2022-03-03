#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
import targetfinder
import icefinderback
from pyami import imagefun, ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.IceTargetFinder
import version
import itertools

invsqrt2 = math.sqrt(2.0)/2.0

class IceTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.IceTargetFinder.Panel
	settingsclass = leginondata.IceTargetFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'lattice hole radius': 15.0,
		'lattice zero thickness': 1000.0,
		'ice min mean': 0.05,
		'ice max mean': 0.2,
		'ice max std': 0.2,
		'ice min std': 0.0,
		'focus hole': 'Off',
		'target template': False,
		'focus template': [(0, 0)],
		'acquisition template': [(0, 0)],
		'focus template thickness': False,
		'focus stats radius': 10,
		'focus min mean thickness': 0.05,
		'focus max mean thickness': 0.5,
		'focus min stdev thickness': 0.0,
		'focus max stdev thickness': 0.5,
		'focus interval': 1,
		'focus offset row': 0,
		'focus offset col': 0,
		'filter ice on convolved': False,
		'sampling targets': False,
		'max sampling': 100,
	})
	targetnames = targetfinder.TargetFinder.targetnames + ['Hole']
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = icefinderback.TestIceFinder()
		self.hf.logger = self.logger
		self.icecalc = ice.IceCalculator()

		self.images = {
			'Original': None,
			'Final': None,
		}
		self.imagetargets = {
			'Original': {},
			'Final': {},
		}
		# ...

		self.focustypes = ['Off', 'Any Hole', 'Good Hole', 'Center']
		self.userpause = threading.Event()

		self.foc_counter = itertools.count()
		self.foc_activated = False

		if self.__class__ == IceTargetFinder:
			self.start()

	def readImage(self, filename):
		self.hf['original'] = targetfinder.TargetFinder.readImage(self, filename)

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center']) #(r,c)
			centers.append((c[1],c[0])) # x,y
		return centers

	def findHoles(self):
		'''
		Find holes with subclass self._findHoles, calculate stats and display
		as Holes in gui.
		'''
		self.logger.info('find blobs')
		try:
			# _findHoles is the subclass hole finder.
			self._findHoles()
			self.calcHoleStats()
			targets = self. getTargetsWithStats(input_name='holes')
		except Exception as e:
			self.logger.error(e)
			targets = []
		# set targets found in self._results['holes']
		self.logger.info('Number of holes: %s' % (len(targets),))
		self.setTargets(targets, 'Hole')

	def calcHoleStats(self):
		# now calculate holestats of 'holes' result using the back icecalculator
		r = self.settings['lattice hole radius']
		i0 = self.settings['lattice zero thickness']
		self.icecalc.set_i0(i0)
		self.hf.configure_holestats(radius=r)
		try:
			self.hf.calc_holestats(input_name='holes')
		except Exception as e:
			self.logger.error(e)

	def _findHoles(self):
		'''
		configure and run holefinder in the back module. Raise exception
		to the higher level to handle.
		'''
		self.hf.configure_holefinder()
		self.hf.run_holefinder()
		return

	def holeStatsTargets(self, holes):
		'''
		Return target used to be set to gui.
		'''
		targets = []
		for hole in holes:
			mean = float(hole.stats['hole_mean'])
			tmean = self.icecalc.get_thickness(mean)
			std = float(hole.stats['hole_std'])
			tstd = self.icecalc.get_stdev_thickness(std, mean)
			# target is used for display in gui
			target = {}
			target['x'] = hole.stats['center'][1]
			target['y'] = hole.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Mean Intensity'] = mean
			target['stats']['Mean Thickness'] = tmean
			target['stats']['S.D. Intensity'] = std
			target['stats']['S.D. Thickness'] = tstd
			for key in self._getStatsKeys():
				target['stats'][key] = hole.stats[key]
			targets.append(target)
		return targets

	def getTargetsWithStats(self, input_name='holes'):
		'''
		Return targets with some stats in a dictionary item for displaying in gui
		'''
		holes = self.hf[input_name]
		targets = self.holeStatsTargets(holes)
		return targets

	def sampleTargets(self):
		'''
		Sample holes2
		'''
		holes = self.hf['holes2']
		max_samples = self.settings['max sampling']
		if max_samples < len(self.hf['holes2']):
			self.hf.configure_sample(classes=max_samples, samples=max_samples, category='thickness-mean')
		self.hf.sampling()

	def ice(self):
		'''
		Ice thickness filtering and template convolution.
		'''
		if self.hf['holes'] is None:
			self.logger.error('Must run holefinder to filter them with ice')
			return
		# self.hf['holes'] has holestats such as hole_mean but not i0-related values
		orig_holes = self.hf['holes']
		self.filterIce(input_name='holes')
		self.focus_hole_index = None
		focus_points = self.filterIceForFocus()
		if self.settings['target template']:
			focus_points = self.handleTemplate(focus_points)
		if self.settings['sampling targets']:
			self.sampleTargets()
		r = self.settings['lattice hole radius']
		acq_points = self.getTargetsWithStats('holes2')
		# display and save preferences and hole stats
		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)
		self.logger.info('Acquisition Targets: %s' % (len(acq_points),))
		self.logger.info('Focus Targets: %s' % (len(focus_points),))

		# save to database
		if type(self.currentimagedata) == type(leginondata.AcquisitionImageData()):
			hfprefs = self.storeHoleFinderPrefsData(self.currentimagedata)
			# this saves stats of the points before convolution
			self.storeHoleStatsData(hfprefs,'holes')
			# this saves stats of the points after convolution
			self.storeHoleStatsData(hfprefs,'holes2')

	def filterIce(self, input_name='holes'):
		'''
		Filter hf[input_name] by ice thickness stats.  The results are in
		hf['holes2']
		'''
		self.logger.info('limit thickness')
		i0 = self.settings['lattice zero thickness']
		tmin = self.settings['ice min mean']
		tmax = self.settings['ice max mean']
		tstdmax = self.settings['ice max std']
		tstdmin = self.settings['ice min std']
		self.hf.configure_ice(i0=i0,tmin=tmin,tmax=tmax,tstdmax=tstdmax, tstdmin=tstdmin)
		try:
			self.hf.calc_ice(input_name=input_name)
		except Exception as e:
			self.logger.error(e)
			return

	def filterIceForFocus(self):
		'''
		return focus_points using hole2 statistics.
		'''
		self.focus_hole_index = None
		# calculate ice thickness with good holes saved in holes2
		goodholes = self.hf['holes2']
		centers = self.blobCenters(goodholes)
		allcenters = self.blobCenters(self.hf['holes'])

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
				elif onehole == 'Center':
					focus_points.append(self.centerCarbon(allcenters))
				elif onehole == 'Any Hole':
					fochole, index = self.focus_on_hole(centers, allcenters, True)
					focus_points.append(fochole)
					if index is not False:
						# used one of the good hole since there was no bad ones
						self.hf['holes2'].pop(index)
						self.focus_hole_index = index
				elif onehole == 'Good Hole':
					if len(centers) < 2:
						self.logger.info('need more than one good hole if you want to focus on one of them')
						centers = []
					else:
						## use only good centers
						fochole, index = self.focus_on_hole(centers, centers, True)
						focus_points.append(fochole)
						if index is not False:
							self.hf['holes2'].pop(index)
							self.focus_hole_index = index

		if not self.settings['filter ice on convolved']:
			self.logger.info('Holes with good ice: %s' % (len(centers),))
		return focus_points

	def handleTemplate(self, focus_points):
		'''
		handle both focus and acquistion templates. Does both convolution
		and ice filtering. Input focus_points are pre-existing ones.  The
		returned focus_points includes both pre-existing and convolved ones.
		'''
		self.logger.info('handling target template convolution')
		if not self.foc_activated:
			focus_points = []
		else:
			focus_points = self._handleFocusTemplate(focus_points)
		# acquisition template must be handled after focus because holes2
		# are overwritten in the process, and we want them end up to be
		# acquisition when this function ends.
		self._handleAcquisitionTemplate()
		return focus_points

	def _handleFocusTemplate(self, focus_points):
		'''
		Handle focus templates. Perform convolution
		and ice filtering. Input focus_points are pre-existing ones.  The
		returned focus_points includes both pre-existing and convolved ones.
		'''
		convolved_holes2 = self._makeConvolvedHoles2('focus')
		focus_points = self._holesToCenters(convolved_holes2, focus_points)
		if len(focus_points) > 1 and self.settings['focus template thickness']:
			# need just one focus point
			try:
				focus_points = self.filterFocusTemplateIce(focus_points)
				focpoint, index = self.focus_on_hole(focus_points,focus_points, False)
			except ValueError as e:
				# no good points
				return []
			focus_points = [focpoint,]
		return focus_points

	def _handleAcquisitionTemplate(self):
		'''
		Handle acquisition templates. Perform convolution
		and ice filtering.  Results are saved in holes2
		'''
		if self.settings['filter ice on convolved']:
			self._makeConvolvedHoles2('acquisition','holes')
			self.iceOnConvolved() # results in holes2
		else:
			self.hf.filter_good('holes')
			self._makeConvolvedHoles2('acquisition','holes2')
		return

	def _getStatsKeys(self):
		'''
		Additional stats keys to display in gui.
		'''
		return []

	def _makeConvolvedHoles2(self,acq_type='acquisition', input_name='holes'):
		'''
		Convolve template with holes to save as holes2. Return the centers as
		(x,y) points
		'''
		if self.settings['target template']:
		# takes x,y instead of row,col
			setting_name = '%s template' % acq_type
			# conolve_config conv_vect needs (row, col)
			vect = self.hf.swapxy(self.settings[setting_name])
			self.hf.configure_convolve(conv_vect=vect)
			self.hf.make_convolved(input_name)
		goodholes = self.hf['holes2']
		return goodholes

	def _holesToCenters(self, holes, existing_points):
		acq_points = self.blobCenters(holes)
		acq_points.extend(existing_points)
		return acq_points

	def iceOnConvolved(self):
		'''
		Filter convolved holes with ice thickness threshold.
		The results are in hf['holes2']
		'''
		r = self.settings['lattice hole radius']
		self.hf.configure_holestats(radius=r)
		self.hf.calc_holestats(input_name='holes2')
		n_holes_before = len(list(self.hf['holes2']))
		if self.hf['holes2'] is not None:
			self.logger.info('Potential targets with stats: %d' % n_holes_before)
		self.filterIce(input_name='holes2')

	def centerCarbon(self, points):
		'''
		Return xy tuple half-way between the xypoint closest to the center.
		Minimum of two points as input.
		'''
		if len(points) < 2:
			raise ValueError('need at least two points to center on carbon in between.')
		temppoints = list(points)
		# centerhole is removed from temppoints during focus_on_hole
		centerhole, index = self.focus_on_hole(temppoints, temppoints, False)
		centerhole2, index = self.focus_on_hole(temppoints, temppoints, False)
		centercarbon = tuple(
			(int((centerhole[0] + centerhole2[0])/2.0),
			int((centerhole[1] + centerhole2[1])/2.0),)
		)
		return centercarbon

	def centroid(self, points):
		## find centroid
		cx = cy = 0.0
		for point in points:
			cx += point[0]
			cy += point[1]
		cx /= len(points)
		cy /= len(points)
		return cx,cy

	def focus_on_hole(self, good, all_xy, apply_offset=False):
		'''
		return closest_point through three criteria
		1. the bad hole closes to the centroid
		2. a good hole closes to the centroid
		'''
		if len(all_xy) == 0:
				raise ValueError('no points to choose from')
		if len(all_xy) == 1:
			closest_point = all_xy[0]
			if apply_offset:
				closest_point = self.offsetFocus(closest_point)
			return closest_point, 0
		# Have at least two points to choose from.
		centroid = self.centroid(all_xy)
		closest_point = None

		## make a list of the bad holes
		bad = []
		for point in all_xy:
			if point not in good:
				bad.append(point)

		## if there are bad holes, use one
		if bad:
			closest, bad_index = self.closestToPoint(bad, centroid, apply_offset)
			return closest, False
		else:
			## now use a good hole for focus
			closest, focus_index =  self.closestToPoint(good, centroid, apply_offset)
			return closest, focus_index

	def closestToPoint(self, points, centroid, apply_offset):
		'''
		Return xy point closest to the centroid
		'''
		cx, cy = centroid
		point0 = points[0]
		closest_dist = math.hypot(point0[0]-cx, point0[1]-cy)
		closest_point = point0
		closest_point_index = 0
		for p, point in enumerate(points):
			#offset before checking for closest.
			if apply_offset:
				point = self.offsetFocus(point)
			dist = math.hypot(point[0]-cx, point[1]-cy)
			if dist < closest_dist:
				closest_dist = dist
				closest_point = point
				closest_point_index = p
		# This in-place pop changes the input points
		points.pop(closest_point_index)
		return closest_point, closest_point_index

	def offsetFocus(self, point):
		'''
		Offset xy point with focus offset settings
		'''
		return point[0]+self.settings['focus offset col'],point[1]+self.settings['focus offset row']

	def bypass(self):
		self.setTargets([], 'Hole', block=True)
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)
		self.setTargets([], 'preview', block=True)

	def filterFocusTemplateIce(self, focuspoints):
		'''
		Filter focuscenters to one with its own stats calculation
		parameters.
		'''
		# This function uses its own holestats calculation.
		rc_centers = self.hf.swapxy(focuspoints)
		good_focuscenters = []
		rad = self.settings['focus stats radius']
		tmin = self.settings['focus min mean thickness']
		tmax = self.settings['focus max mean thickness']
		tstdmin = self.settings['focus min stdev thickness']
		tstdmax = self.settings['focus max stdev thickness']
		imshape = self.hf['original'].shape
		for rc_center in rc_centers:
			tarx = rc_center[1]
			tary = rc_center[0]
			vect = (tarx, tary)
			if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
				self.logger.debug('skipping template point %s: out of image bounds' % (vect,))
				continue
			if self.settings['focus template thickness']:
				if tstdmin is None:
					tstdmin = 0.0
				stats = self.hf.calc_center_holestats(rc_center, self.hf['original'], rad)
				if stats is None:
					self.logger.debug('skipping template point %s:  stats region out of bounds' % (vect,))
					continue
				tm = self.icecalc.get_thickness(stats['mean'])
				ts = self.icecalc.get_stdev_thickness(stats['std'], stats['mean'])
				self.logger.debug('template point %s stats:  mean: %s, stdev: %s' % (vect, tm, ts))
				if (tmin <= tm <= tmax) and (ts >= tstdmin) and (ts < tstdmax):
					self.logger.debug('template point %s passed thickness test' % (vect,))
					good_focuscenters.append(rc_center)
		return self.hf.swapxy(good_focuscenters)

	def everything(self):
		# find holes
		self.findHoles()
		# ice
		self.ice()

	def storeHoleStatsData(self, prefs, input_name='holes'):
		holes = self.hf[input_name]
		for hole in holes:
			stats = hole.stats
			holestats = leginondata.HoleStatsData(session=self.session, prefs=prefs)
			holestats['finder-type'] = 'ice'
			holestats['row'] = stats['center'][0] * self.shrink_factor + self.shrink_offset[0]
			holestats['column'] = stats['center'][1] * self.shrink_factor + self.shrink_offset[1]
			holestats['mean'] = stats['hole_mean']
			holestats['stdev'] = stats['hole_std']
			holestats['thickness-mean'] = stats['thickness-mean']
			holestats['thickness-stdev'] = stats['thickness-stdev']
			holestats['good'] = stats['good']
			holestats['hole-number'] = stats['hole_number']
			holestats['convolved'] = stats['convolved']
			self.publish(holestats, database=True)

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = leginondata.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'stats-radius': self.settings['lattice hole radius'],
			'ice-zero-thickness': self.settings['lattice zero thickness'],

			'ice-min-thickness': self.settings['ice min mean'],
			'ice-max-thickness': self.settings['ice max mean'],
			'ice-max-stdev': self.settings['ice max std'],
			'ice-min-stdev': self.settings['ice min std'],
			'template-on': self.settings['target template'],
			'template-focus': self.settings['focus template'],
			'template-acquisition': self.settings['acquisition template'],
			'sampling targets': self.settings['sampling targets'],
			'max sampling': self.settings['max sampling'],
		})

		self.publish(hfprefs, database=True)
		return hfprefs

	def findTargets(self, imdata, targetlist):
		'''
		TargetFinder find targets on image data and publish as part
		of the targetlist.
		'''
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.currentimagedata = imdata
		orig = imdata['image']
		# shrink image in holefinding to save memory usage
		shrunk = imagefun.shrink(orig)
		self.shrink_factor = imagefun.shrink_factor(orig.shape)
		self.shrink_offset = imagefun.shrink_offset(orig.shape)
		self.hf['original'] = shrunk
		self.setImage(shrunk, 'Original')
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
				ptargets = self.processPreviewTargets(imdata, targetlist)
				if not ptargets:
					break
				self.panel.targetsSubmitted()
		self.setStatus('idle')

