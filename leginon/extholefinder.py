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
import extholefinderback
from pyami import ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.ExtHoleFinder
import version
import itertools

invsqrt2 = math.sqrt(2.0)/2.0

class ExtHoleFinder(targetfinder.TargetFinder):
	'''
	Hole Finder that uses external program to get holes but
	calculate stats and filter by ice thickness like JAHCFinder.
	'''
	panelclass = gui.wx.ExtHoleFinder.Panel
	settingsclass = leginondata.ExtHoleFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'command': '',
		'hole diameter': 40,
		'lattice spacing': 150.0,
		'lattice hole radius': 15.0,
		'lattice zero thickness': 1000.0,
		'lattice extend': 'off',
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
	})
	targetnames = targetfinder.TargetFinder.targetnames + ['ExtHoles']
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		# load backend
		self.hf = extholefinderback.HoleFinder()
		# make it possible to use logger in the backend.
		self.hf.logger = self.logger
		self.icecalc = ice.IceCalculator()

		# ...

		self.focustypes = ['Off', 'Any Hole', 'Good Hole', 'Center']
		self.userpause = threading.Event()

		self.foc_counter = itertools.count()
		self.foc_activated = False

		self.start()

	def readImage(self, filename):
		self.hf['original'] = targetfinder.TargetFinder.readImage(self, filename)

	def holeStatsTargets(self, holes):
		'''
		Convert stats of holes to a list of target dictionaries.
		'''
		# targets are set to the node gui with setTarget function.
		targets = []
		for hole in holes:

			mean = float(hole.stats['hole_mean'])
			tmean = self.icecalc.get_thickness(mean)
			std = float(hole.stats['hole_std'])
			tstd = self.icecalc.get_stdev_thickness(std, mean)

			# Each target is a dictionary
			target = {}
			target['x'] = hole.stats['center'][1]
			target['y'] = hole.stats['center'][0]
			# These are shown in gui target panel when cursor hover around the coordinate.
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Mean Intensity'] = mean
			target['stats']['Mean Thickness'] = tmean
			target['stats']['S.D. Intensity'] = std
			target['stats']['S.D. Thickness'] = tstd
			targets.append(target)
		return targets

	def runExtHoles(self):
		'''
		Set configuration and then run the external program
		'''
		self.logger.info('run external hole finding command')
		diameter = self.settings['hole diameter']
		cmd = self.settings['command']
		self.hf.configure_extholes(diameter, cmd)
		try:
			self.hf.run_extholes()
		except Exception, e:
			self.logger.error(e)
			return
		targets = self.holeToTargets(self.hf['extholes'])
		self.setTargets(targets, 'ExtHoles')

	def holeToTargets(self, holes):
		'''
		Convert only center of each hole object to target dictionary.
		'''
		targets = []
		for hole in holes:
			target = {}
			target['x'] = hole.stats['center'][1] # hole = (r,c)
			target['y'] = hole.stats['center'][0]
			targets.append(target)
		return targets

	def fitLattice(self):
		'''
		This replaces fitLattice in JAHCFinder. It does not really
		fit lattice poinrt.  Just map extholes to holes so that stats
		are calculated from them.
		'''
		self.logger.info('convert to lattice with hole stats')
		r = self.settings['lattice hole radius']
		i0 = self.settings['lattice zero thickness']
		self.icecalc.set_i0(i0)

		# No fitting is done.  This is needed only to minimize
		# changes
		try:
			self.hf.extholes_to_holes()
		except Exception, e:
			self.logger.error(e)
			return
		targets = self. getTargetsWithStats(r)
		if targets is not None:
			self.logger.info('Number of lattice positions: %s' % (len(targets),))
			self.setTargets(targets, 'Lattice')

	def getTargetsWithStats(self, stats_radius):
		'''
		Get targets with holestats within a radius
		'''
		self.hf.configure_holestats(radius=stats_radius)
		try:
			self.hf.calc_holestats()
		except Exception, e:
			self.logger.error(e)
			return
		holes = self.hf['holes']
		targets = self.holeStatsTargets(holes)
		return targets

	def ice(self):
		'''
		Filter holes with ice thickness and other filters and processing.
		'''
		orig_holes = self.hf['holes']
		centers, focus_points = self.filterIceForFocus()
		acq_points, focus_points = self.makeConvolvedPoints(centers, focus_points)
		all_acq_numbers = len(acq_points) # (x,y)
		if self.settings['filter ice on convolved']:
			# self.hf['holes'] are changed to acq_points in iceOnConvolved.
			acq_points = self.iceOnConvolved(acq_points)
		# display and save preferences and hole stats
		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)
		self.logger.info('Acquisition Targets: %s' % (len(acq_points),))
		self.logger.info('Focus Targets: %s' % (len(focus_points),))
		if type(self.currentimagedata) == type(leginondata.AcquisitionImageData()):
			hfprefs = self.storeHoleFinderPrefsData(self.currentimagedata)
			self.storeHoleStatsData(hfprefs)
		if self.settings['filter ice on convolved']:
			# return self.hf['holes'] to lattice result so that it can be reused for adjusting
			# parameters
			self.hf.updateHoles(orig_holes)

	def filterIce(self):
		'''
		Filter hf['holes'] by ice thickness stats.  The results are in
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
			self.hf.calc_ice()
		except Exception, e:
			self.logger.error(e)
			return

	def blobCenters(self, blobs):
		'''
		Return centers in (x,y) of blob or holes.
		'''
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def filterIceForFocus(self):
		self.filterIce()
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

		if not self.settings['filter ice on convolved']:
			self.logger.info('Holes with good ice: %s' % (len(centers),))
			return centers, focus_points
		else:
			return allcenters, focus_points

	def makeConvolvedPoints(self, centers, focus_points):
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
		return acq_points, focus_points

	def iceOnConvolved(self, centers):
		'''
		Filter target centers with ice thickness threshold.
		'''
		sw_centers = self.hf.swapxy(centers) # input centers are in (x,y) but self.hf operates in (r,c)
		holes = self.hf.points_to_extholes(sw_centers)
		self.hf.updateHoles(holes)
		r = self.settings['lattice hole radius']
		targets = self. getTargetsWithStats(r)
		if targets is not None:
			self.logger.info('Potential targets with stats: %s' % (len(targets),))
			self.setTargets(targets, 'acquisition')
		self.filterIce()
		goodholes = self.hf['holes2']
		targets = self.holeStatsTargets(goodholes)
		self.logger.info('Convolved acquisition targets rejected: %d' % (len(centers)-len(targets),))
		return targets

	def centerCarbon(self, points):
		temppoints = points
		centerhole = self.focus_on_hole(temppoints, temppoints, False)
		closexdist = 1.0e10
		closeydist = 1.0e10
		xdist = 0.0
		ydist = 0.0
		for point in points:
			dist = math.hypot(point[0]-centerhole[0], point[1]-centerhole[1])
			#find nearest lattice points and get the components
			if dist > 1.8*self.settings['lattice spacing']:
				continue
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
		## find centroid
		cx = cy = 0.0
		for point in points:
			cx += point[0]
			cy += point[1]
		cx /= len(points)
		cy /= len(points)
		return cx,cy

	def focus_on_hole(self, good, all, apply_offset=False):
		cx,cy = self.centroid(all)
		focpoint = None

		## make a list of the bad holes
		bad = []
		for point in all:
			if point not in good:
				bad.append(point)

		## if there are bad holes, use one
		if bad:
			point = bad[0]
			closest_dist = math.hypot(point[0]-cx, point[1]-cy)
			closest_point = point
			for point in bad:
				dist = math.hypot(point[0]-cx, point[1]-cy)
				if dist < closest_dist:
					closest_dist = dist
					closest_point = point
			if apply_offset:
				closest_point = self.offsetFocus(closest_point)
			return closest_point

		## now use a good hole for focus
		point = good[0]
		closest_dist = math.hypot(point[0]-cx,point[1]-cy)
		closest_point = point
		for point in good:
			dist = math.hypot(point[0]-cx,point[1]-cy)
			if dist < closest_dist:
				closest_dist = dist
				closest_point = point
		good.remove(closest_point)
		if apply_offset:
			closest_point = self.offsetFocus(closest_point)
		return closest_point

	def offsetFocus(self, point):
			return point[0]+self.settings['focus offset col'],point[1]+self.settings['focus offset row']

	def bypass(self):
		self.setTargets([], 'ExtHoles', block=True)
		self.setTargets([], 'Lattice', block=True)
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)
		self.setTargets([], 'preview', block=True)

	def applyTargetTemplate(self, centers):
		self.logger.info('apply template')
		imshape = self.hf['original'].shape
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
					tstdmin = self.settings['focus min stdev thickness']
					tstdmax = self.settings['focus max stdev thickness']
					if tstdmin is None:
						tstdmin = 0.0
					coord = target[1], target[0]
					stats = self.hf.get_hole_stats(self.hf['original'], coord, rad)
					if stats is None:
						self.logger.info('skipping template point %s:  stats region out of bounds' % (vect,))
						continue
					tm = self.icecalc.get_thickness(stats['mean'])
					ts = self.icecalc.get_stdev_thickness(stats['std'], stats['mean'])
					self.logger.info('template point %s stats:  mean: %s, stdev: %s' % (vect, tm, ts))
					if (tmin <= tm <= tmax) and (ts >= tstdmin) and (ts < tstdmax):
						self.logger.info('template point %s passed thickness test' % (vect,))
						newtargets['focus'].append(target)
						break
				else:
					newtargets['focus'].append(target)
		return newtargets

	def everything(self):
		# find holes or blobs
		self.runExtHoles()
		# lattice
		self.fitLattice()
		# ice
		self.ice()

	def storeHoleStatsData(self, prefs):
		holes = self.hf['holes']
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
		'''
		HoleFinderPrefsData is shared between HoleFinder, JAHCFinder, and this.
		'''
		hfprefs = leginondata.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'lattice-spacing': self.settings['lattice spacing'],
			'stats-radius': self.settings['lattice hole radius'],
			'ice-zero-thickness': self.settings['lattice zero thickness'],

			'ice-min-thickness': self.settings['ice min mean'],
			'ice-max-thickness': self.settings['ice max mean'],
			'ice-max-stdev': self.settings['ice max std'],
			'ice-min-stdev': self.settings['ice min std'],
			'template-on': self.settings['target template'],
			'template-focus': self.settings['focus template'],
			'template-acquisition': self.settings['acquisition template'],

		})

		self.publish(hfprefs, database=True)
		return hfprefs

	def findTargets(self, imdata, targetlist):
		'''
		Creating targets from input AcquisitionImageData instance, imdata.
		Resulting targets are published as part of targetlist associated with imdata.
		'''
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.hf['original'] = imdata['image']
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
				raise
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
