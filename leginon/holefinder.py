#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata, version
from leginon import jahcfinder
import targetfinder
import holefinderback
from pyami import imagefun, ordereddict
import threading
import ice
import instrument
import os.path
import math
import gui.wx.HoleFinder
import itertools

default_template = os.path.join(version.getInstalledLocation(),'hole_edge_template.mrc')

class HoleFinder(jahcfinder.JAHCFinder):
	panelclass = gui.wx.HoleFinder.Panel
	settingsclass = leginondata.HoleFinderSettingsData
	defaultsettings = dict(jahcfinder.JAHCFinder.defaultsettings)
	defaultsettings.update({
		'edge lpf': {
			'sigma': 1.0,
		},
		'edge': True,
		'edge type': 'sobel',
		'edge log size': 9,
		'edge log sigma': 1.4,
		'edge absolute': False,
		'edge threshold': 100.0,
	})
	extendtypes = ['off', 'full', '3x3']
	targetnames = jahcfinder.JAHCFinder.targetnames
	def __init__(self, id, session, managerlocation, **kwargs):
		jahcfinder.JAHCFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.hf = holefinderback.HoleFinder()
		self.icecalc = ice.IceCalculator()

		self.images.update({
			'Edge': None,
		})
		self.imagetargets.update({
			'Edge': {},
		})
		self.filtertypes = [
			'sobel',
			'laplacian3',
			'laplacian5',
			'laplacian-gaussian'
		]
		# ...

		if self.__class__ == HoleFinder:
			self.start()

	def findEdges(self):
		self.logger.info('find edges')
		n = self.settings['edge log size']
		sig = self.settings['edge log sigma']
		ab = self.settings['edge absolute']
		edges = self.settings['edge']
		filt = self.settings['edge type']
		lpfsettings = self.settings['edge lpf']
		lowpasssig = lpfsettings['sigma']
		edgethresh = self.settings['edge threshold']
		self.hf.configure_edges(filter=filt, size=n, sigma=sig, absvalue=ab, lpsig=lowpasssig, thresh=edgethresh, edges=edges)
		try:
			self.hf.find_edges()
		except Exception, e:
			self.logger.error(e)
			return
		# convert to Float32 to prevent seg fault
		self.setImage(self.hf['edges'], 'Edge')

	def everything(self):
		# find edges
		self.findEdges()
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

	def _getHolePrefs(self, imagedata):
		hfprefs = super(HoleFinder, self)._getHolePrefs(imagedata)
		hfprefs.update({
			'edge-lpf-sigma': self.settings['edge lpf']['sigma'],
			'edge-filter-type': self.settings['edge type'],
			'edge-threshold': self.settings['edge threshold'],
		})
		return hfprefs

