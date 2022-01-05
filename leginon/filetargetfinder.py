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
import threading
import gui.wx.ClickTargetFinder

class FileTargetFinder(targetfinder.ClickTargetFinder):
	'''
	This is an example TargetFinder class that takes a target as
	center for a mosaic image loaded from a file and associate a
	list of targets with it so they can be submitted and processed.
	'''
	targetnames = ['preview', 'reference', 'focus', 'acquisition']
	panelclass = gui.wx.ClickTargetFinder.Panel
	eventoutputs = targetfinder.ClickTargetFinder.eventoutputs
	settingsclass = leginondata.ClickTargetFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)

	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.start()

	# This is copied from targetfinder.TargetFinder to show an example
	# of selecting one of the image to be used in findTarget.
	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image leginondata.
		'''
		if self.settings['ignore images']:
			return

		for target_name in self.targetnames:
			self.setTargets([], target_name, block=True)

		self.currentimagedata = imagedata
		self.setTargetImageVectors(imagedata)
		# check if there is already a target list for this image
		# or any other versions of this image (all from same target/preset)
		# exclude sublists (like rejected target lists)
		qtarget = imagedata['target']

		# As an example I will fake a way to decide if this is the center imagedata
		# It will return without doing anything further if it is not
		# Here it checks if imagedata comes from the second target of the parent image
		if qtarget['number'] != 2:
			return

		try:
			pname = imagedata['preset']['name']
			qpreset = leginondata.PresetData(name=pname)
		except:
			qpreset = None
		qimage = leginondata.AcquisitionImageData(target=qtarget, preset=qpreset)
		previouslists = self.researchTargetLists(image=qimage, sublist=False)
		if previouslists:
			# I hope you can only have one target list on an image, right?
			targetlist = previouslists[0]
			db = False
			self.logger.info('Existing target list on this image...')
			self.displayPreviousTargets(targetlist)
		else:
			# no previous list, so create one and fill it with targets
			targetlist = self.newTargetList(image=imagedata, queue=self.settings['queue'])
			db = True
		if self.settings['allow append'] or len(previouslists)==0:
			self.findTargets(imagedata, targetlist)
		self.logger.debug('Publishing targetlist...')

		## if queue is turned on, do not notify other nodes of each target list publish
		if self.settings['queue']:
			pubevent = False
		else:
			pubevent = True
		self.publish(targetlist, database=db, pubevent=pubevent)
		self.logger.debug('Published targetlist %s' % (targetlist.dbid,))

		if self.settings['wait for done'] and not self.settings['queue']:
			self.makeTargetListEvent(targetlist)
			self.setStatus('waiting')
			self.waitForTargetListDone()
			self.setStatus('processing')

	# We need center_imdata so that we can copy its scope condition
	# In addition, when this is called, it needs to know which targetlist
	# it should add the targets to which is setup by the function calling it.
	def findTargets(self, center_imdata, targetlist):
		self.setStatus('processing')
		message = 'finding targets'
		self.logger.info(message)

		# Fake image loading
		import numpy
		mosaic_image = numpy.ones((256,256))
		filename = center_imdata['filename']+'_stitch'

		# initializer gives the new imagedata all metadata of the old imdata
		imdata = leginondata.AcquisitionImageData(initializer=center_imdata)

		# CameraEMData referenced in imdata  has to be modified to
		# have it centered at the same place as
		# the original and give the true dimension so that targets on it can
		# go to the stage position or image shift relative to it.
		mosaic_shape = mosaic_image.shape
		camdata0 = center_imdata['camera']
		camdata1 = leginondata.CameraEMData(initializer=camdata0)
		binning = camdata0['binning']
		axes = {'x':1,'y':0}
		for axis in axes.keys():
			camdata1['dimension'][axis] = mosaic_shape[axes[axis]]
			change = camdata0['dimension'][axis]*camdata0['binning'][axis] - camdata1['dimension'][axis]*binning[axis]
			camdata1['offset'][axis] = (camdata0['offset'][axis]*camdata0['binning'][axis]+(change / 2))/binning[axis]

		imdata['camera'] = camdata1
		imdata['image'] = mosaic_image
		imdata['filename'] = filename

		# Note: As is, this can not be used in target adjustment since Leginon can not
		# acquire the whole mosaic image by going to the single scope condition saved.
		# It will take some work to do that.

		# for a simpla case like this, self.publish is the same as insert. Only need one
		# also no need to force	
		imdata.insert()
		
		self.currentimagedata = imdata
		
		# This enough to set image in the gui		
		self.setImage(imdata['image'], 'Image')
		
		goodpoints = []

		# For testing, I just use the same file over and over
		file_path = './test.txt'
		try:
			target_file = open(file_path,'r')

			target_list = target_file.readlines()
			for target in target_list:
				coordinates = target.rstrip().split(',')
				x = float(coordinates[0])
				y = float(coordinates[1])
				goodpoints.append((x,y))
		
		except:
			self.logger.error('Target file %s can not be read' % (file_path))

		self.setTargets(goodpoints, 'acquisition', block=True)
		
		# Copied from targetfinder.ClickTargetFinder		
		while True:
			self.waitForUserCheck()
			if not self.processPreviewTargets(imdata, targetlist):
				break
		self.panel.targetsSubmitted()
		self.setStatus('idle')
