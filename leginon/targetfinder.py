#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import leginondata
import event
import instrument
import imagewatcher
import mosaic
import threading
import node
import targethandler
from pyami import convolver, imagefun, mrc, numpil
import numpy
import pyami.quietscipy
import scipy.ndimage as nd
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.MosaicClickTargetFinder
import os
import shortpath
import math
import polygon
import raster
import presets
import time
import version

try:
	set = set
except NameError:
	import sets
	set = sets.Set

class TargetFinder(imagewatcher.ImageWatcher, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetFinder.Panel
	settingsclass = leginondata.TargetFinderSettingsData
	defaultsettings = {
		'queue': False,
		'wait for done': True,
		'ignore images': False,
		'user check': False,
		'queue drift': True,
		'sort target': False,
		'allow append': False,
	}
	eventinputs = imagewatcher.ImageWatcher.eventinputs \
									+ [event.AcquisitionImagePublishEvent] \
									+ targethandler.TargetWaitHandler.eventinputs
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs \
									+ targethandler.TargetWaitHandler.eventoutputs
	targetnames = ['acquisition','focus','preview','reference','done']
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation,
																				**kwargs)
		targethandler.TargetWaitHandler.__init__(self)
		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.presetsclient = presets.PresetsClient(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}

	def readImage(self, filename):
		imagedata = None
		if filename:
			imagedata = self.getImageFromDB(filename)
		if imagedata is None:
			if filename == '':
				if self.name in ['Hole Targeting','Subsquare Targeting']:
					filename = os.path.join(version.getInstalledLocation(),'sq_example.jpg')
				elif self.name in ['Square Targeting']:
					filename = os.path.join(version.getInstalledLocation(),'gr_example.jpg')
				else:
					filename = os.path.join(version.getInstalledLocation(),'hl_example.jpg')
			try:
				orig = mrc.read(filename)
			except Exception, e:
				try:
					orig = numpil.read(filename)
				except:
					self.logger.exception('Read image failed: %s' % e[-1])
					return
			self.currentimagedata = {'image':orig} 
		else:
			orig = imagedata['image']
			self.currentimagedata = imagedata

		self.setImage(orig, 'Original')
		return orig

	def getImageFromDB(self, filename):
		# only want filename without path and extension
		filename = os.path.split(filename)[1]
		filename = '.'.join(filename.split('.')[:-1])
		q = leginondata.AcquisitionImageData(filename=filename)
		results = self.research(datainstance=q)
		if not results:
			return None
		imagedata = results[0]
		return imagedata

	def findTargets(self, imdata, targetlist):
		'''
		Virtual function, inheritting classes implement creating targets
		'''
		raise NotImplementedError()

	def waitForUserCheck(self):
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.setStatus('processing')

	def processPreviewTargets(self, imdata, targetlist):
			preview_targets = self.panel.getTargetPositions('preview')
			if preview_targets:
				self.publishTargets(imdata, 'preview', targetlist)
				self.setTargets([], 'preview', block=True)
				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, database=True, dbforce=True, pubevent=True)
				self.waitForTargetListDone()
			return preview_targets

	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return

		querydata = leginondata.AcquisitionImageData(list=imagelistdata)
		## research, but don't read images until later
		images = self.research(querydata, readimages=False)
		targetlist = self.newTargetList(queue=self.settings['queue'])

		if self.settings['allow append']:
			print "will find targets"
			for imagedata in images:
				self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		if self.settings['queue']:
			self.logger.info('Queue is on... not generating event')
			pubevent=False
		else:
			self.logger.info('Queue is off... generating event')
			pubevent=True
		self.publish(targetlist, database=True, dbforce=True, pubevent=pubevent)
		if self.settings['wait for done'] and pubevent:
			self.setStatus('waiting')
			self.waitForTargetListDone()
			self.setStatus('processing')

	def targetsFromClickImage(self, clickimage, typename, targetlist):
		imagedata = clickimage.imagedata
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in clickimage.getTargetType(typename):
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			self.publish(targetdata, database=True)
			number += 1

	#--------------------
	def sortTargets(self, targetlist):
		"""
		input: list of (x,y) tuples
		output: sorted list of  (x,y) tuples
		"""
		if len(targetlist) < 3:
			self.logger.info("skipping sort targets")
			return targetlist
		#print "targets=",targetlist
		bestorder, bestscore, messages = shortpath.sortPoints(targetlist, numiter=3, maxeval=70000)
		for msg in messages:
			self.logger.info(msg)
		#print "bestorder=",bestorder
		if bestorder is None or len(bestorder) < 3:
			self.logger.info("skipping sort targets")
			return targetlist
		sortedtargetlist = []
		for i in bestorder:
			sortedtargetlist.append(targetlist[i])
		#print "sortedtargets=",sortedtargets
		self.logger.info("returning sorted targets")
		return sortedtargetlist
		
	#--------------------
	def publishTargets(self, imagedata, typename, targetlist):
		imagetargets = self.panel.getTargetPositions(typename)

		if not imagetargets:
			return
		if self.settings['sort target']:
			imagetargets = self.sortTargets(imagetargets)
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			self.publish(targetdata, database=True)
			number += 1

	def displayPreviousTargets(self, targetlistdata):
		targets = self.researchTargets(list=targetlistdata)
		done = []
		acq = []
		foc = []
		halfrows = targetlistdata['image']['camera']['dimension']['y'] / 2
		halfcols = targetlistdata['image']['camera']['dimension']['x'] / 2
		for target in targets:
			drow = target['delta row']
			dcol = target['delta column']
			x = dcol + halfcols
			y = drow + halfrows
			disptarget = x,y
			if target['status'] in ('done', 'aborted'):
				done.append(disptarget)
			elif target['type'] == 'acquisition':
				acq.append(disptarget)
			elif target['type'] == 'focus':
				foc.append(disptarget)
		self.setTargets(acq, 'acquisition', block=True)
		self.setTargets(foc, 'focus', block=True)
		self.setTargets(done, 'done', block=True)

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image leginondata.
		'''
		if self.settings['ignore images']:
			return

		for target_name in self.targetnames:
			self.setTargets([], target_name, block=True)
		# check if there is already a target list for this image
		# or any other versions of this image (all from same target/preset)
		# exclude sublists (like rejected target lists)
		qtarget = imagedata['target']
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

	def publishQueue(self):
		if self.settings['queue drift']:
			self.declareDrift('submit queue')
		queue = self.getQueue()
		self.publish(queue, pubevent=True)

	def notifyUserSubmit(self):
		message = 'Waiting for user to submit targets...'
		self.logger.info(message)
		self.beep()

	def submitTargets(self):
		self.userpause.set()

	def clearTargets(self,targettype):
		self.setTargets([], targettype, block=False)

class ClickTargetFinder(TargetFinder):
	targetnames = ['preview', 'reference', 'focus', 'acquisition']
	panelclass = gui.wx.ClickTargetFinder.Panel
	eventoutputs = TargetFinder.eventoutputs + [event.ReferenceTargetPublishEvent]
	settingsclass = leginondata.ClickTargetFinderSettingsData
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.start()

	def findTargets(self, imdata, targetlist):
		# display image
		self.setImage(imdata['image'], 'Image')
		while True:
			self.waitForUserCheck()
			if not self.processPreviewTargets(imdata, targetlist):
				break
		self.panel.targetsSubmitted()
		self.setStatus('processing')
		self.logger.info('Publishing targets...')
		for i in self.targetnames:
			if i == 'reference':
				self.publishReferenceTarget(imdata)
			else:
				self.publishTargets(imdata, i, targetlist)
		self.setStatus('idle')

	def publishReferenceTarget(self, image_data):
		try:
			column, row = self.panel.getTargetPositions('reference')[-1]
		except IndexError:
			return
		rows, columns = image_data['image'].shape
		delta_row = row - rows/2
		delta_column = column - columns/2
		reference_target = self.newReferenceTarget(image_data, delta_row, delta_column)
		try:
			self.publish(reference_target, database=True, pubevent=True)
		except node.PublishError, e:
			self.logger.error('Submitting reference target failed')
		else:
			self.logger.info('Reference target submitted')

