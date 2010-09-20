# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/testtargetfinder.py,v $
# $Revision: 1.8 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-21 23:17:17 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import os.path
import threading
import leginondata
from pyami import mrc
import targetfinder
import gui.wx.TestTargetFinder

class TestTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.TestTargetFinder.Panel
	settingsclass = leginondata.TestTargetFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'test image': '',
	})
	def __init__(self, *args, **kwargs):
		self.userpause = threading.Event()
		targetfinder.TargetFinder.__init__(self, *args, **kwargs)
		self.image = None
		self.start()

	def readImage(self, filename=''):
		if filename:
			self.image = mrc.read(filename)
		self.setImage(self.image, 'Image')

	def testFindTargets(self):
		focus_targets_on_image = []
		acquisition_targets_on_image = []

		# Put your function call here:
		# such as
		# focus_targets_on_image, acquisition_targets_on_image = your_targetfinder(self.image)

		# here is an example of the output
		focus_targets_on_image = [(50,20)]
		acquisition_targets_on_image = [(100,100),(200,100)]

		self.setTargets(acquisition_targets_on_image, 'acquisition')
		self.setTargets(focus_targets_on_image, 'focus')
		import time
		time.sleep(1)

		if self.settings['user check']:
			self.panel.foundTargets()

	def findTargets(self, imdata, targetlist):
		image = imdata['image']

		self.setImage(image, 'Image')

		self.image = image
		self.testFindTargets()

		if self.settings['user check']:
			# user now clicks on targets
			self.notifyUserSubmit()
			self.userpause.clear()
			self.setStatus('user input')
			self.userpause.wait()

		self.setStatus('processing')

		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)

		self.logger.info('Targets have been submitted')

	def targetTestImage(self):
		usercheck = self.settings['user check']
		self.settings['user check'] = False
		filename = self.settings['test image']
		try:
			image = mrc.read(filename)
		except:
			self.logger.error('Failed to load test image')
			raise
			return
		self.setImage(image, 'Image')

		self.image = image
		self.testFindTargets()

		self.settings['user check'] = usercheck
