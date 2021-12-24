# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
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
from leginon import leginondata
from pyami import mrc
import targetfinder
import gui.wx.TestTargetFinder

class TestTargetFinder(targetfinder.TargetFinder):
	'''
	Example TargetFinder subclass.
	'''
	panelclass = gui.wx.TestTargetFinder.Panel
	settingsclass = leginondata.TestTargetFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'test image': '',
	})
	def __init__(self, *args, **kwargs):
		targetfinder.TargetFinder.__init__(self, *args, **kwargs)
		# needed for user pause
		self.userpause = threading.Event()
		# numpy array to find targets on
		self.image = None
		self.start()

	def readImage(self, filename=''):
		'''
		Read test mrc image
		'''
		if filename:
			# set self.image to this numpy array
			self.image = mrc.read(filename)
		# display this image
		self.setImage(self.image, 'Image')

	def testFindTargets(self, from_refresh=False):
		'''
		Make targets from your function call and set them on the image.
		'''
		focus_targets_on_image = []
		acquisition_targets_on_image = []

		self.logger.info('create example targets')
		# Put your function call here:
		# such as
		# focus_targets_on_image, acquisition_targets_on_image = your_targetfinder(self.image)

		# here is an example of the output
		focus_targets_on_image = [(50,20)]
		acquisition_targets_on_image = [(100,100),(200,100)]

		# Set targets on the gui image panel
		self.setTargets(acquisition_targets_on_image, 'acquisition')
		self.setTargets(focus_targets_on_image, 'focus')

		if from_refresh:
			# activate refresh to try again.
			self.panel.foundTargets()

	def findTargets(self, imdata, targetlist):
		'''
		Creating targets from input AcquisitionImageData instance, imdata.
		Resulting targets are published as part of targetlist associated with imdata.
		'''
		# set node processing status to processing so that the gui spins its wheel
		self.setStatus('processing')
		# image item in imdata is a numpy array representing the image.
		image = imdata['image']
		# give this image array to the gui image panel named "Image" to display		
		self.setImage(image, 'Image')
		# set self.image
		self.image = image
		self.testFindTargets()

		# user interaction part.  This allows user to modify the targets found
		# either locally or remotely
		if self.settings['user check']:
			while True:
				self.current_interaction = self.settings['check method']
				self.terminated_remote = False
				self.waitForInteraction(imdata)
				# process preview targets the user added to this image and then back to interaction again.
				if not self.processPreviewTargets(imdata, targetlist):
					break
		# tell gui panel to change tool activation states after submission
		self.panel.targetsSubmitted()

		# set node processing status to idle so that the gui goes back to standby and remote is not blocked.
		self.setStatus('idle')

	def targetTestImage(self):
		'''
		Testing target finder from gui tool. Read test image and find targets.
		'''
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
		# activate refresh to try again.
		self.panel.foundTargets()

