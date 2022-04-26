#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
from leginon import icetargetfinder
from leginon import rasterfinderback
import threading
import numpy
import math
import pyami.quietscipy
import gui.wx.RasterFinder
import polygon
import itertools

class RasterFinder(icetargetfinder.IceTargetFinder):
	panelclass = gui.wx.RasterFinder.Panel
	settingsclass = leginondata.RasterFinderSettingsData
	defaultsettings = dict(icetargetfinder.IceTargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'publish polygon': False,
		'image filename': '',
		'raster movetype': None,
		'raster preset': None,
		'raster overlap': 0.0,
		'raster spacing': 100,
		'raster spacing asymm': None,
		'raster angle': 0,
		'raster center x': 0,
		'raster center y': 0,
		'raster center on image': True,
		'raster limit': 5,
		'raster limit asymm': None,
		'raster symmetric': True,
		'select polygon': False,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		icetargetfinder.IceTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = rasterfinderback.HoleFinder()
		self.hf.logger = self.logger

		self.rasterpoints = None
		self.polygonrasterpoints = None
		self.lattice_matrix = self.hf.lattice_matrix

		self.userpause = threading.Event()
		self.images = {
			'Original': None,
		}
		self.imagetargets = {
			'Original': {},
			'Raster': {},
			'Polygon': {},
			'Final': {},
		}

		if self.__class__ == RasterFinder:
			self.start()


	def autoSpacingAngle(self):
		try:
			imageid = self.currentimagedata.dbid
		except:
			self.logger.warning('Image not in database')
			return None, None
		imagedata = self.currentimagedata

		ht = imagedata['scope']['high tension']

		# transforming from target mag
		targetpresetname = self.settings['raster preset']
		targetpreset = self.presetsclient.getPresetByName(targetpresetname)
		tem1 = targetpreset['tem']
		cam1 = targetpreset['ccdcamera']
		mag1 = targetpreset['magnification']
		dim1 = targetpreset['dimension']['x']
		bin1 = targetpreset['binning']['x']
		fulldim = dim1 * bin1
		p1 = (0,fulldim)

		# transforming into mag of atlas
		tem2 = imagedata['scope']['tem']
		cam2 = imagedata['camera']['ccdcamera']
		mag2 = imagedata['scope']['magnification']
		bin2 = imagedata['camera']['binning']['x']

		movetype = self.settings['raster movetype']
		try:
			p2 = self.calclients[movetype].pixelToPixel(tem1, cam1, tem2, cam2, ht, mag1, mag2, p1)
		except RuntimeError, e:
					self.logger.exception('Raster conversion failed: %s' % e)
					return self.settings['raster spacing'], self.settings['raster angle']
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
		spacing = numpy.hypot(*p2)
		angle = numpy.arctan2(*p2)
		angle = math.degrees(angle) # +x to +y is positive
		
		return spacing, angle

	def createRaster(self):
		"""
		from center of image, generate a raster of points
		"""
		try:
			imageshape = self.currentimagedata['image'].shape
		except:
			imageshape = (512,512)
		xspacing = float(self.settings['raster spacing'])
		xpoints = int(self.settings['raster limit'])

		if self.settings['raster symmetric']:
			yspacing = xspacing
			ypoints = xpoints
		else:
			yspacing = float(self.settings['raster spacing asymm'])
			ypoints = int(self.settings['raster limit asymm'])

		radians = math.pi * self.settings['raster angle'] / 180.0
		if self.settings['raster center on image']:
			x0 = imageshape[1]/2.0
			y0 = imageshape[0]/2.0
		else:
			x0 = float(self.settings['raster center x'])
			y0 = float(self.settings['raster center y'])
		self.hf.configure_raster(x0,y0,xspacing,yspacing,xpoints,ypoints, radians)
		self.hf.make_raster_points()
		#old stuff
		points = self.hf['raster']
		self.setTargets(points, 'Raster')
		self.rasterpoints = points
		self.logger.info('Full raster has %s points' % (len(points),))

	def waitForPolygon(self):
		'''
		Wait for polygon selection if desired, and then set the polygon for filtering.
		'''
		## user part
		if self.settings['select polygon']:
			self.setTargets([], 'Polygon Vertices')
			self.setStatus('user input')
			self.logger.info('Waiting for user to select polygon...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.panel.targetsSubmitted()
			self.setStatus('processing')

		self.setPolygon()

	def setPolygon(self):
		'''
		Use polygon to filter raster points. Stats are calculated and set for
		display.  This is called from test button.
		'''
		vertices = self.panel.getTargetPositions('Polygon Vertices')
		if len(vertices) < 3:
			self.polygonrasterpoints = self.hf['raster']
		else:
			self.polygonrasterpoints = polygon.pointsInPolygon(self.hf['raster'], vertices)
		self.hf.points_to_holes(self.polygonrasterpoints)
		self.calcHoleStats()
		targets = self. getTargetsWithStats(input_name='holes')
		if targets is not None:
			self.logger.info('Number of polygon raster: %s' % (len(targets),))
			self.setTargets(targets, 'Polygon Raster')

	def everything(self):
		self.createRaster()
		self.waitForPolygon()
		self.ice()

	def _publishFoundTargets(self, imdata, targetlist):
		super(RasterFinder, self)._publishFoundTargets(imdata, targetlist)
		if self.settings['publish polygon']:
			self.publishTargets(imdata, 'Polygon Vertices', targetlist)

