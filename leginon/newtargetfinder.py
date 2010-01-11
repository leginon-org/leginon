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
from pyami import ordereddict
import threading
import os.path
import math
import gui.wx.NewTargetFinder
import version
import targetingsteps

invsqrt2 = math.sqrt(2.0)/2.0
default_template = os.path.join(version.getInstalledLocation(),'holetemplate.mrc')

newworkflow = targetingsteps.templatefinder
newsettingsclass = targetingsteps.makeSettingsClass('NewTargetFinderSettingsData', newworkflow)
newdefaultsettings = targetingsteps.makeDefaultSettings(newworkflow)

class NewTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.NewTargetFinder.Panel
	settingsclass = newsettingsclass
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update(newdefaultsettings)
	#targetnames = targetfinder.TargetFinder.targetnames + ['Blobs']
	workflow = newworkflow
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		#self.images = {
		#self.imagetargets = {

		self.userpause = threading.Event()
		self.start()

	def readImage(self, filename):
		self.hf['original'] = targetfinder.TargetFinder.readImage(self, filename)

	def bypass(self):
		self.setTargets([], 'Blobs', block=True)
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

	def findTargets(self, imdata, targetlist):
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.hf['original'] = imdata['image']
		self.currentimagedata = imdata
		self.setImage(imdata['image'], 'Original')
		if not self.settings['skip']:
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
				self.waitForUserCheck()
				ptargets = self.processPreviewTargets(imdata, targetlist)
				newblobs = self.blobsChanged()
				if newblobs:
					try:
						self.usePickedBlobs()
						self.fitLattice()
						self.ice()
					except Exception, e:
						raise
						self.logger.error('Failed: %s' % (e,))
						continue
				if not ptargets and not newblobs:
					break
				self.panel.targetsSubmitted()

		self.logger.info('Publishing targets...')
		### publish targets from goodholesimage
		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)
		self.setStatus('idle')

