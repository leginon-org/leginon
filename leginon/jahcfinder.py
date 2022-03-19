#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
import targetfinder, icetargetfinder
import jahcfinderback
from pyami import imagefun, ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.JAHCFinder
import version
import itertools

invsqrt2 = math.sqrt(2.0)/2.0
default_template = os.path.join(version.getInstalledLocation(),'holetemplate.mrc')

class JAHCFinder(icetargetfinder.IceTargetFinder):
	panelclass = gui.wx.JAHCFinder.Panel
	settingsclass = leginondata.JAHCFinderSettingsData
	defaultsettings = dict(icetargetfinder.IceTargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'template diameter': 40,
		'template filename': default_template,
		'file diameter': 168,
		'template image min':0.0,
		'template invert': False,
		'template type': 'cross',
		'template lpf': {
			'sigma': 1.0,
		},
		'template multiple':1,
		'multihole angle':0.0,
		'multihole spacing':200.0,
		'threshold': 3.0,
		'threshold method': "Threshold = mean + A * stdev",
		'blobs border': 20,
		'blobs max': 300,
		'blobs max size': 1000,
		'blobs min size': 10,
		'blobs min roundness': 0.8,
		'lattice spacing': 150.0,
		'lattice tolerance': 0.1,
		'lattice hole radius': 15.0,
		'lattice zero thickness': 1000.0,
		'lattice extend': 'off',
	})
	extendtypes = ['off', 'full', '3x3']
	targetnames = icetargetfinder.IceTargetFinder.targetnames + ['Lattice','Blobs']
	targetnames.remove('Hole')
	def __init__(self, id, session, managerlocation, **kwargs):
		icetargetfinder.IceTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = jahcfinderback.HoleFinder()
		self.hf.logger = self.logger
		self.icecalc = ice.IceCalculator()

		self.images = {
			'Original': None,
			'Template': None,
			'Threshold': None,
			'Blobs': None,
			'Lattice': None,
			'Final': None,
		}
		self.imagetargets = {
			'Original': {},
			'Template': {},
			'Threshold': {},
			'Blobs': {},
			'Lattice': {},
			'Final': {},
		}
		self.filtertypes = [
			'sobel',
			'laplacian3',
			'laplacian5',
			'laplacian-gaussian'
		]
		# ...

		self.cortypes = ['cross', 'phase']
		self.focustypes = ['Off', 'Any Hole', 'Good Hole', 'Center']
		self.userpause = threading.Event()

		self.foc_counter = itertools.count()
		self.foc_activated = False

		self.start()

	def correlateTemplate(self):
		'''
		Set configuration and then create template and correlate
		'''
		self.logger.info('correlate ring template')
		# convert diameters to radii
		diameter = self.settings['template diameter']
		filediameter = self.settings['file diameter']
		invert = self.settings['template invert']
		multiple = self.settings['template multiple']
		spacing = self.settings['multihole spacing']
		angle = self.settings['multihole angle']
		if self.settings['template filename'] != '':
			if os.path.isfile(self.settings['template filename']):
				filename = self.settings['template filename']
			else:
				self.logger.warning('Specified template not found. Use default')
				filename = default_template
		else:
			filename = default_template
		self.hf.configure_template(diameter, filename, filediameter, invert, multiple, spacing, angle)
		try:
			self.hf.create_template()
		except Exception, e:
			self.logger.error(e)
			return
		cortype = self.settings['template type']
		cor_image_min = self.settings['template image min']
		lpfsettings = self.settings['template lpf']
		corsigma = lpfsettings['sigma']
		if cortype == 'phase' and corsigma:
			corfilt = (corsigma,)
		else:
			corfilt = None
		self.hf.configure_correlation(cortype, corfilt,cor_image_min)
		try:
			self.hf.correlate_template()
		except Exception, e:
			self.logger.error(e)
			return
		self.setImage(self.hf['correlation'], 'Template')

	def threshold(self):
		self.logger.info('threshold')
		tvalue = self.settings['threshold']
		tmeth = self.settings['threshold method']
		self.hf.configure_threshold(tvalue, tmeth)
		try:
			self.hf.threshold_correlation()
		except Exception, e:
			self.logger.error(e)
			return
		# convert to Float32 to prevent seg fault
		self.setImage(self.hf['threshold'], 'Threshold')

	def blobCenters(self, blobs):
		centers = []
		for blob in blobs:
			c = tuple(blob.stats['center'])
			centers.append((c[1],c[0]))
		return centers

	def findBlobs(self):
		self.logger.info('find blobs')
		border = self.settings['blobs border']
		blobsize = self.settings['blobs max size']
		minblobsize = self.settings['blobs min size']
		maxblobs = self.settings['blobs max']
		minblobroundness = self.settings['blobs min roundness']   #wjr
		self.hf.configure_blobs(border=border, maxblobsize=blobsize, maxblobs=maxblobs, minblobsize=minblobsize, minblobroundness=minblobroundness)   #wjr
		try:
			self.hf.find_blobs()
		except Exception, e:
			self.logger.error(e)
			self.logger.error('was in FindBlobs')
			return
		blobs = self.hf['blobs']
		targets = self.blobStatsTargets(blobs)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')

	def usePickedBlobs(self):
		self.logger.info('find blobs')
		picks = self.panel.getTargetPositions('Blobs')
		try:
			self.hf.find_blobs(picks)
		except Exception, e:
			self.logger.error(e)
			return
		blobs = self.hf['blobs']
		targets = self.blobStatsTargets(blobs)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')

	def holeStatsTargets(self, holes):
		targets = []
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

	def fitLattice(self):
		self.logger.info('fit lattice')
		latspace = self.settings['lattice spacing']
		lattol = self.settings['lattice tolerance']
		r = self.settings['lattice hole radius']
		i0 = self.settings['lattice zero thickness']
		extend = self.settings['lattice extend']
		self.icecalc.set_i0(i0)

		self.hf.configure_lattice(spacing=latspace, tolerance=lattol, extend=extend)
		try:
			self.hf.blobs_to_lattice()
		except Exception, e:
			self.logger.error(e)
			self.setTargets([], 'Lattice')
			return
		self.calcHoleStats()
		targets = self. getTargetsWithStats(input_name='holes')
		if targets is not None:
			self.logger.info('Number of lattice blobs: %s' % (len(targets),))
			self.setTargets(targets, 'Lattice')

	def bypass(self):
		self.setTargets([], 'Blobs', block=True)
		self.setTargets([], 'Lattice', block=True)
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)
		self.setTargets([], 'preview', block=True)

	def everything(self):
		# correlate template
		self.correlateTemplate()
		# threshold
		self.threshold()
		# find blobs
		self.findBlobs()
		# lattice
		self.fitLattice()
		# ice
		self.ice()

	def storeHoleFinderPrefsData(self, imagedata):
		hfprefs = leginondata.HoleFinderPrefsData()
		hfprefs.update({
			'session': self.session,
			'image': imagedata,
			'user-check': self.settings['user check'],
			'skip-auto': self.settings['skip'],
			'queue': self.settings['queue'],

			'template-correlation-type': self.settings['template type'],
			'template-lpf': self.settings['template lpf']['sigma'],

			'threshold-value': self.settings['threshold'],
			'threshold-method': self.settings['threshold method'],
			'blob-border': self.settings['blobs border'],
			'blob-max-number': self.settings['blobs max'],
			'blob-max-size': self.settings['blobs max size'],
			'blob-min-size': self.settings['blobs min size'],
#			'blob-min-roundness': self.settings['blobs min roundness'],    # wjr don not store yet in database
			'lattice-spacing': self.settings['lattice spacing'],
			'lattice-tolerance': self.settings['lattice tolerance'],
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

			## these are in JAHCFinder only
			'template-diameter': self.settings['template diameter'],
			'file-diameter': self.settings['file diameter'],
			'template-filename': self.settings['template filename'],
		})

		self.publish(hfprefs, database=True)
		return hfprefs

	def blobsChanged(self):
			# if blobs have changed, return true
			newblobs = self.panel.getTargetPositions('Blobs')
			if not newblobs:
				return False
			if self.settings['lattice extend'] == 'off':
				return False
			for point in self.oldblobs:
				if point not in newblobs:
					self.logger.info('Lattice extension is on and blobs changed.')
					return True
			if len(newblobs) == len(self.oldblobs):
				return False
			else:
				self.logger.info('Lattice extension is on and some blob added.')
				return True

	def findTargets(self, imdata, targetlist):
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
		#
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
				self.oldblobs = self.panel.getTargetPositions('Blobs')
				self.waitForInteraction(imdata)
				ptargets = self.processPreviewTargets(imdata, targetlist)
				newblobs = self.blobsChanged()
				if newblobs:
					try:
						self.logger.info('Autofinder rerun starting from Lattice fitting')
						self.usePickedBlobs()
						self.fitLattice()
						self.ice()
						self.logger.info('Autofinder rerun due to blob editing finished')
					except Exception, e:
						raise
						self.logger.error('Failed: %s' % (e,))
						continue
				if not ptargets and not newblobs:
					break
				self.panel.targetsSubmitted()
		self.setStatus('idle')

