#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import targetfinder
import threading
import gui.wx.RegionFinder
import libCVwrapper
import raster
import polygon
import math

class RegionFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.RegionFinder.Panel
	settingsclass = leginondata.RegionFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'image filename': '',
		'min region area': 0.01,
		'max region area': 0.8,
		've limit': 50,
		'raster spacing': 50,
		'raster angle': 0,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.rasterpoints = None
		self.polygonrasterpoints = None

		self.userpause = threading.Event()
		self.start()

	def findRegions(self):
		imshape = self.currentimagedata['image'].shape
		minsize = self.settings['min region area']
		maxsize = self.settings['max region area']
		velimit = self.settings['ve limit']
		regions,image = libCVwrapper.FindRegions(self.currentimagedata['image'], minsize, maxsize)
		self.regionarrays = []
		displaypoints = []
		for i,region in enumerate(regions):
			regionarray = region['regionBorder']
			self.logger.info('Region %d has %d points' % (i, regionarray.shape[1]))
			## reduce to 20 points
			regionarray = libCVwrapper.PolygonVE(regionarray, velimit)
			regionarray.transpose()
			self.regionarrays.append(regionarray)

			regiondisplaypoints = self.transpose_points(regionarray)
			displaypoints.extend(regiondisplaypoints)

		self.setTargets(displaypoints, 'Perimeter', block=False)

	def testFindRegions(self):
		self.findRegions()

	def makeRaster(self):
		shape = self.currentimagedata['image'].shape
		spacing = self.settings['raster spacing']
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		rasterpoints = raster.createRaster(shape, spacing, anglerad)
		regionrasters = []
		fullrasterset = set()
		for region in self.regionarrays:
			regionraster = polygon.pointsInPolygon(rasterpoints, region)
			regionrasters.append(regionraster)
			fullrasterset = fullrasterset.union(regionraster)
		# set is unordered, so use original rasterpoints for order
		self.fullraster = []
		for point in rasterpoints:
			if point in fullrasterset:
				self.fullraster.append(point)

		fullrasterdisplay = self.transpose_points(self.fullraster)
		self.setTargets(fullrasterdisplay, 'acquisition', block=False)

	def publishRasterTargets(self):
		pass

	def testMakeRaster(self):
		self.makeRaster()
		#self.splitRegions()

	def splitRegions(self):
		regionpieces = []
		for regionarray in self.regionarrays:
			pieces = libCVwrapper.PolygonACD(regionarray, 0.05)
			if pieces is None:
				print 'PolygonACD FAIL'
				self.logger.warning('PolygonACD failed')
			else:
				print 'PolygonACD SUCCESS'
				regionpieces.append(pieces)
		
		self.setTargets('acquisition', tt, block=False)

	def findTargets(self, imdata, targetlist):
		## display image
		self.setImage(imdata['image'], 'Original')

		## automated part
		self.currentimagedata = imdata

		self.findRegions()
		self.makeRaster()
		#self.split()

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
		#if self.settings['publish polygon']:
		#	self.publishTargets(imdata, 'Polygon Vertices', targetlist)
