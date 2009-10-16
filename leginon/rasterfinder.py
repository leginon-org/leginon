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
import ice
import numpy
import math
import pyami.quietscipy
from scipy import ndimage
from pyami import arraystats
import gui.wx.RasterFinder
import polygon

class RasterFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.RasterFinder.Panel
	settingsclass = leginondata.RasterFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
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
		self.start()

	def autoSpacingAngle(self):
		try:
			imageid = self.currentimagedata.dbid
		except:
			self.logger.warning('Image not in database')
			return None, None
		imagedata = self.currentimagedata

		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		ht = imagedata['scope']['high tension']

		# transforming from target mag
		targetpresetname = self.settings['raster preset']
		targetpreset = self.presetsclient.getPresetByName(targetpresetname)
		mag1 = targetpreset['magnification']
		dim1 = targetpreset['dimension']['x']
		bin1 = targetpreset['binning']['x']
		fulldim = dim1 * bin1
		p1 = (0,fulldim)

		# transforming into mag of atlas
		mag2 = imagedata['scope']['magnification']
		bin2 = imagedata['camera']['binning']['x']

		movetype = self.settings['raster movetype']
		p2 = self.calclients[movetype].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
		spacing = numpy.hypot(*p2)
		angle = numpy.arctan2(*p2)
		angle = math.degrees(angle)
		
		return spacing, angle

	def createRaster(self):
		"""
		from center of image, generate a raster of points
		"""
		#print "xy raster"
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
			x0 = imageshape[0]/2.0
			y0 = imageshape[1]/2.0
		else:
			x0 = float(self.settings['raster center x'])
			y0 = float(self.settings['raster center y'])
		points = []

		#new stuff
		xlist = numpy.asarray(range(xpoints), dtype=numpy.float32)
		xlist -= ndimage.mean(xlist)
		ylist = numpy.asarray(range(ypoints), dtype=numpy.float32)
		ylist -= ndimage.mean(ylist)

		for xt in xlist:
			xshft = xt * xspacing
			for yt in ylist:
				print 'old',xt,yt
				yshft = yt * yspacing
				xrot = xshft * numpy.cos(radians) - yshft * numpy.sin(radians) 
				yrot = yshft * numpy.cos(radians) + xshft * numpy.sin(radians)
				x = int(xrot + x0)
				y = int(yrot + y0)
				if x < 0 or x >= imageshape[0]: continue
				if y < 0 or y >= imageshape[1]: continue
				print 'rotated',x,y
				points.append( (x,y) )

		#old stuff
		self.setTargets(points, 'Raster')
		self.rasterpoints = points
		self.logger.info('Full raster has %s points' % (len(points),))

	def createRasterOld(self):
		'''
		from center of image, generate a raster of points
		'''
		print "normal raster"
		imageshape = self.currentimagedata['image'].shape
		spacing = self.settings['raster spacing']
		limit = self.settings['raster limit']
		radians = 3.14159 * self.settings['raster angle'] / 180
		if self.settings['raster center on image']:
			rcenter = imageshape[0]/2
			ccenter = imageshape[1]/2
		else:
			ccenter = self.settings['raster center x']
			rcenter = self.settings['raster center y']
		points = []
		for rlayer in range(-limit, limit+1):
			r = rlayer * spacing
			for clayer in range(-limit, limit+1):
				c = clayer * spacing
				rr = -1 * c * numpy.sin(radians) + r * numpy.cos(radians)
				cc =  c * numpy.cos(radians) + r * numpy.sin(radians)
				rr = int(rr + rcenter)
				cc = int(cc + ccenter)
				if rr < 0 or rr >= imageshape[0]: continue
				if cc < 0 or cc >= imageshape[1]: continue
				points.append((int(rr),int(cc)))

		self.setTargets(self.transpose_points(points), 'Raster')
		self.rasterpoints = points
		self.logger.info('Full raster has %s points' % (len(points),))

	def waitForPolygon(self):
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
		vertices = self.panel.getTargetPositions('Polygon Vertices')
		if len(vertices) < 3:
			self.polygonrasterpoints = self.rasterpoints
		else:
			self.polygonrasterpoints = polygon.pointsInPolygon(self.rasterpoints, vertices)
		self.setTargets(self.polygonrasterpoints, 'Polygon Raster')

	def get_box_stats(self, image, coord, boxsize):
		## select the region of interest
		b2 = boxsize / 2
		rmin = int(coord[1]-b2)
		rmax = int(coord[1]+b2)
		cmin = int(coord[0]-b2)
		cmax = int(coord[0]+b2)
		## beware of boundaries
		if rmin < 0:  rmin = 0
		if rmax >= image.shape[0]:  rmax = image.shape[0]-1
		if cmin < 0:  cmin = 0
		if cmax >= image.shape[1]:  cmax = image.shape[1]-1

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		roi = numpy.ravel(subimage)
		mean = arraystats.mean(roi)
		std = arraystats.std(roi)
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
		if self.polygonrasterpoints is None:
			self.polygonrasterpoints= []
		for rasterpoint in self.polygonrasterpoints:
			box_stats = self.get_box_stats(self.currentimagedata['image'], rasterpoint, boxsize)
			t = self.icecalc.get_thickness(box_stats['mean'])
			ts = self.icecalc.get_stdev_thickness(box_stats['std'], box_stats['mean'])
			if (tmin <= t <= tmax) and (ts < tstd):
				goodpoints.append(rasterpoint)
				mylist.append( (rasterpoint, t, ts))

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

		self.setTargets(acq_points, 'acquisition', block=True)
		self.setTargets(focus_points, 'focus', block=True)

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
		self.waitForPolygon()
		# ice
		self.ice()

	def findTargets(self, imdata, targetlist):
		## display image
		self.setImage(imdata['image'], 'Original')

		## automated part
		self.currentimagedata = imdata
		if not self.settings['skip']:
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
		if self.settings['publish polygon']:
			self.publishTargets(imdata, 'Polygon Vertices', targetlist)



