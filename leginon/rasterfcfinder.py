#!/usr/bin/env python

# WVN 10/5/11 - rasterfcfinder.py based on rasterfinder.py
#  The paper describing the use of this Leginon node is:
#  W.V. Nicholson, H. White and J. Trinick (2010) JSB 172, 395-399.
#  "An approach to automated acquisition of cryoEM images from lacey
#  carbon grids."

import leginondata
import targetfinder
# WVN 19/1/08 - changes borrowed from v.1.4.1 rasterfinder.py
# Apart from below changes in imports, other changes were in
# readImage (removed from rasterfinder), transpose_points(removed),
# createRaster (changes in code), get_box_stats (changes),
# findTargets (changes in code)
#  which are inherited from the new
# rasterfinder.py anyway.
# rewrites were required in overridden ice method.
#
import threading
import ice
import numpy
from pyami import arraystats
import gui.wx.RasterFCFinder
import polygon
import itertools

import math

# WVN 12/8/07
import rasterfinder

# WVN 1/4/07 RasterFCFinder - based on RasterFinder

class RasterFCFinder(rasterfinder.RasterFinder):
	panelclass = gui.wx.RasterFCFinder.Panel
	settingsclass = leginondata.RasterFCFinderSettingsData
	defaultsettings = dict(rasterfinder.RasterFinder.defaultsettings)
	defaultsettings.update({
               'focus center x': 0,
               'focus center y': 0,
               'focus radius': 45.0,
               'focus box size': 15.0,
               'focus min mean': 0.05,
               'focus max mean': 0.2,
               'focus min std': 0.0,
               'focus max std': 0.2,
	})

	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.icecalc = ice.IceCalculator()
		self.rasterpoints = None
		self.polygonrasterpoints = None

		self.userpause = threading.Event()
		self.images = {
			'Original': None,
		}
		self.imagetargets = {
			'Original': {},
			'Polygon': {},
			'Raster': {},
			'Final': {},
		}

		self.foc_counter = itertools.count()
		self.foc_activated = False

		self.start()

	def ice(self):
		focusCenterX = self.settings['focus center x']
		focusCenterY = self.settings['focus center y']
		focusRadius = self.settings['focus radius']
		focusBoxSize = self.settings['focus box size']
		focusMinMean = self.settings['focus min mean']
		focusMaxMean = self.settings['focus max mean']
		focusMinSD = self.settings['focus min std']
		focusMaxSD = self.settings['focus max std']

		i0 = self.settings['ice thickness']
		tmin = self.settings['ice min mean']
		tmax = self.settings['ice max mean']
		tstdmax = self.settings['ice max std']
		tstdmin = self.settings['ice min std']
		boxsize = self.settings['ice box size']

		self.icecalc.set_i0(i0)

		# calculate stats around each raster point
		goodpoints = []
		mylist = []
		if self.polygonrasterpoints is None:
			self.polygonrasterpoints= []
		for rasterpoint in self.polygonrasterpoints:
			# WVN 19/1/08 - change borrowed from v.1.4.1 rasterfinder.py
			# box_stats = self.get_box_stats(self.original, rasterpoint, boxsize)
			box_stats = self.get_box_stats(self.currentimagedata['image'], rasterpoint, boxsize)
			t = self.icecalc.get_thickness(box_stats['mean'])
			ts = self.icecalc.get_stdev_thickness(box_stats['std'], box_stats['mean'])
			if (tmin <= t <= tmax) and (tstdmin <= ts <= tstdmax):
				goodpoints.append(rasterpoint)
				mylist.append( (rasterpoint, t, ts))

		self.logger.info('%s points with good ice' % (len(goodpoints),))

		### run template convolution
		# takes x,y instead of row,col

		# activate if counter is at a multiple of interval
		interval = self.settings['focus interval']
		if interval and not (self.foc_counter.next() % interval):
			self.foc_activated = True
		else:
			self.foc_activated = False

		# WVN - focus convolve not used in rasterfcfinder
		# if self.settings['focus convolve']:
	#		focus_points = self.applyTargetTemplate(goodpoints, 'focus')
		# else:
	#		focus_points = []

		if self.settings['acquisition convolve']:
			acq_points = self.applyTargetTemplate(goodpoints, 'acquisition')
		else:
			acq_points = goodpoints

		## add constant targets
		# WVN - focus constant template not used in rasterfcfinder
		# const_foc = self.settings['focus constant template']
		# focus_points.extend(const_foc)

		const_acq = self.settings['acquisition constant template']
		acq_points.extend(const_acq)

		focus_points = []
		if not self.foc_activated:
			# return without focus target search if skip focusing
			self.setTargets(acq_points, 'acquisition', block=True)
			self.setTargets(focus_points, 'focus', block=True)
			return

		# WVN - Find a suitable focus target on the chosen
		# focus "circle"
		circFocusPoints = []
		# WVN - changed to getting max. mean - to target carbon areas
		# rather than "feature-ful" areas
		#circFocusPointsSD = []
		circFocusPointsMean = []
		circPix = 2.0 * math.pi * focusRadius
		angRadStep = 1.0/focusRadius
		# radian step for 1 pixel
		for i in range(int(circPix)):
			omega = angRadStep * i
			# print "angle: ", (omega*180.0/math.pi)
			xPoint = int(focusCenterX + focusRadius*math.cos(omega))
			yPoint = int(focusCenterY + focusRadius*math.sin(omega))
			# coords have to be "transposed" for get_box_stats()
			# box_stats = self.get_box_stats(self.original, (yPoint, xPoint), focusBoxSize)
			# WVN 19/1/08 - change borrowed from v.1.4.1 rasterfinder.py
			box_stats = self.get_box_stats(self.currentimagedata['image'], (yPoint, xPoint), focusBoxSize)
			t = self.icecalc.get_thickness(box_stats['mean'])
			ts = self.icecalc.get_stdev_thickness(box_stats['std'], box_stats['mean'])
			if (focusMinMean <= t <= focusMaxMean) and \
		           (focusMinSD <= ts <= focusMaxSD) :
				circFocusPoints.append((xPoint, yPoint))
				# circFocusPointsSD.append(ts)
				circFocusPointsMean.append(t)

		if len(circFocusPoints) > 0:
			#bestFocusSD = max(circFocusPointsSD)
			bestFocusMean = max(circFocusPointsMean)
			bestFocusIndex = circFocusPointsMean.index(bestFocusMean)
			bestFocusPoint = circFocusPoints[bestFocusIndex]
			focus_points.append(bestFocusPoint)
			print "Best focus point on circle: ", bestFocusPoint
		# WVN - end of my code

		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)
