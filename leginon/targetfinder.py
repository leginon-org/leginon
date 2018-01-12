#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import calibrationclient
from leginon import leginondata
import event
import instrument
import imagewatcher
import mosaic
import threading
import node
import targethandler
import appclient
import remoteserver
from pyami import convolver, imagefun, mrc, numpil
from pyami import ordereddict
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
		'check method': 'local',
		'queue drift': True,
		'sort target': False,
		'allow append': False,
		'multifocus': False,
		'allow no focus': False,
	}
	eventinputs = imagewatcher.ImageWatcher.eventinputs \
									+ [event.AcquisitionImagePublishEvent] \
									+ targethandler.TargetWaitHandler.eventinputs
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs \
									+ targethandler.TargetWaitHandler.eventoutputs
	targetnames = ['acquisition','focus','preview','reference','done']
	checkmethods = ['local', 'remote']

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
												calibrationclient.ModeledStageCalibrationClient(self),
			'beam size':
												calibrationclient.BeamSizeCalibrationClient(self)
		}
		self.parent_imageid = None
		self.current_image_pixelsize = None
		self.focusing_targetlist = None
		self.last_acq_node = None
		self.next_acq_node = None
		self.targetimagevector = (0,0)
		self.targetbeamradius = 0
		self.resetLastFocusedTargetList(None)
		self.remote = remoteserver.RemoteServerMaster(self.logger, session, self)
		self.remote.targets.setTargetNames(self.targetnames)
		self.onQueueCheckBox(self.settings['queue'])
		# assumes needing focus. Overwritten by subclasses
		self.foc_activated = True

	def onInitialized(self):
		super(TargetFinder, self).onInitialized()
		# self.panel is now made
		combined_state = self.settings['user check'] and not self.settings['queue']
		self.setUserVerificationStatus(combined_state)

	def handleApplicationEvent(self,evt):
		'''
		Find the Acquisition class or its subclass instance bound
		to this node upon application loading.
		'''
		app = evt['application']
		self.last_acq_node = appclient.getLastNodeThruBinding(app,self.name,'AcquisitionImagePublishEvent','Acquisition')
		self.next_acq_node = appclient.getNextNodeThruBinding(app,self.name,'ImageTargetListPublishEvent','Acquisition')

	def checkSettings(self,settings):
		'''
		Check that depth-first tree travelsal won't break
		'''
		if self.last_acq_node:
			settingsclassname = self.last_acq_node['class string']+'SettingsData'
			results= self.reseachDBSettings(getattr(leginondata,settingsclassname),self.last_acq_node['alias'])
			if not results:
				# default acquisition settings waiting is False. However, admin default
				# should be o.k.
				return []
			else:
				last_acq_wait = results[0]['wait for process']
			if not settings['queue'] and not last_acq_wait:
				return [('error','"%s" node "wait for process" setting must be True when queue is not activated in this node' % (self.last_acq_node['alias'],))]
		return []

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

	def getCheckMethods(self):
		return self.checkmethods

	def waitForInteraction(self,imagedata=None):
		'''
		Wait for user interaction either locally or remotely.
		'''
		# Rule about z height retention to the target selected
		# when z height is changed during interaction:
		# If the target will be in a queue, the z will be the z of the parent image.
		# If the target will not be in a queue, the z will be the value it happens
		# to be at the time of its processing, i.e., afected by z adjustment during
		# and after the interaction.
		valid_selection = False
		while not valid_selection:
			if self.settings['check method'] == 'remote':
				self.waitForRemoteCheck(imagedata)
			else:
				# default
				self.waitForUserCheck()
			if not self.settings['allow no focus']:
				has_aqu = self.hasTargetTypeOnPanel('acquisition')
				has_foc = self.hasTargetTypeOnPanel('focus')
				if not has_aqu or has_foc:
					valid_selection = True
				else:
					self.logger.error('Must have a focus target')
			else:
				break

	def hasTargetTypeOnPanel(self, typename):
		targets = self.panel.getTargetPositions(typename)
		return len(targets) > 0
		
	def waitForUserCheck(self):
		'''
		Local gui user target confirmation
		'''
		self.setStatus('user input')
		self.beep()
		self.logger.info('Waiting for user to check targets...')
		self.panel.submitTargets()
		self.userpause.clear()
		self.userpause.wait()
		self.setStatus('processing')

	def waitForRemoteCheck(self,imdata):
		'''
		Remote service target confirmation
		'''
		if imdata is None:
			return
		self.setStatus('user input')
		self.twobeeps()
		xytargets = self.getPanelTargets(imdata['image'].shape)
		# put stuff in OutBox
		self.remote.targets.setImage(imdata)
		self.remote.targets.setOutTargets(xytargets)
		# wait and get stuff from InBox
		targetfile = self.remote.targets.getInTargetFilePath()
		self.logger.info('Waiting for targets in data file %s' % targetfile)
		self.setStatus('processing')
		# targetxys are target coordinates in x, y grouped by targetnames
		targetxys = self.remote.targets.getInTargets()
		print 'remote targets',targetxys

		self.displayRemoteTargetXYs(targetxys)
		preview_targets = self.panel.getTargetPositions('preview')
		if not preview_targets:
			self.remote.targets.unsetImage(imdata)
		self.setStatus('idle')

	def getPanelTargets(self,imageshape):
		'''
		Get xy target positions for all target types on ImagePanel in
		a dictionary.
		'''
		xytargets = {}
		for typename in self.targetnames:
			try:
				xys = self.getTargetsFromPanel(typename, imageshape)
				xytargets[typename] = xys
			except ValueError:
				pass
			except:
				raise
		return xytargets

	def displayRemoteTargetXYs(self,xys):
		'''
		Display all xytargets from remote target server on ImagePanel.
		'''
		for name in self.targetnames:
			self.setTargets(xys[name], name, block=True)

	def processPreviewTargets(self, imdata, targetlist):
			preview_targets = self.panel.getTargetPositions('preview')
			if preview_targets:
				self.publishTargets(imdata, 'preview', targetlist)
				self.setTargets([], 'preview', block=True)
				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, database=True, dbforce=True, pubevent=True)
				self.waitForTargetListDone()
				status = True
				if self.settings['check method'] == 'remote':
					# change status fo False if failed
					status = self.resetRemoteToListen()
				self.logger.info('Preview targets processed. Go back to waiting')
			return preview_targets and status

	def resetRemoteToListen(self):
		status = True
		try:
			# clear targetis set from the server
			self.remote.targets.resetTargets()
		except Exception, e:
			# assumes no preview targets
			self.logger.error(e)
			status = False
		if not status:
			# clear all targets displayed so that target server can set them again
			self.clearAllTargets()

	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return

		querydata = leginondata.AcquisitionImageData(list=imagelistdata)
		## research, but don't read images until later
		images = self.research(querydata, readimages=False)
		targetlist = self.newTargetList(queue=self.settings['queue'])

		if self.settings['allow append']:
			self.logger.info("will append targets")
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
		bestorder, bestscore, messages = shortpath.sortPoints(targetlist, numiter=3, maxeval=70000)
		for msg in messages:
			self.logger.info(msg)
		if bestorder is None or len(bestorder) < 3:
			self.logger.info("skipping sort targets")
			return targetlist
		sortedtargetlist = []
		for i in bestorder:
			sortedtargetlist.append(targetlist[i])
		self.logger.info("returning sorted targets")
		return sortedtargetlist
		
	def resetLastFocusedTargetList(self,targetlist):
		self.last_focused = None
		self.focusing_targetlist = targetlist

	def setLastFocusedTargetList(self,targetlist):
		# z may change if this targetfinder produces focus target
		if 'focus' in self.panel.getSelectionToolNames() and self.panel.getTargetPositions('focus'):
			# Issue #4331
			self.resetLastFocusedTargetList(targetlist)
		# Issue #3794 atlas targetlist, manual image, and simulated target need to reset last focused targetlist
		elif targetlist['image'] is None or targetlist['image']['target'] is None or targetlist['image']['target']['type'] == 'simulated':
			# parent image is from simulated target
			self.resetLastFocusedTargetList(targetlist)
		else:
			self.last_focused = self.focusing_targetlist

	def getTargetsFromPanel(self, typename, imageshape):
		'''
		Get xy coordinates of the targets of a specified type from ImagePanel.
		'''
		imagetargets = self.panel.getTargetPositions(typename)
		if typename == 'focus' and self.settings['multifocus'] is not True:
			imagetargets = self.getCenterTargets(imagetargets, imageshape)
		return imagetargets

	#--------------------
	def publishTargets(self, imagedata, typename, targetlist):
		'''
		Publish specific type of targets on ImagePanel bound to an 
		AcquisitionImageData and TargetListData
		'''
		imagearray = imagedata['image']
		imageshape = imagearray.shape
		imagetargets = self.getTargetsFromPanel(typename, imageshape)

		if not imagetargets:
			return
		if self.settings['sort target']:
			imagetargets = self.sortTargets(imagetargets)
		# advance to next target number
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imageshape[0]/2
			dcol = column - imageshape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number,last_focused=self.last_focused)
			self.publish(targetdata, database=True)
			number += 1

	def getCenterTargets(self, imagetargets, imageshape):
		'''
		return the image target closest to the center of the image in a list
		'''
		if len(imagetargets) <= 1:
			return imagetargets
		else:
			self.logger.warning('Publish only the focus target closest to the center')
			deltas = map((lambda x: math.hypot(x[1]-imageshape[0]/2,x[0]-imageshape[1]/2)),imagetargets)
			return [imagetargets[deltas.index(min(deltas))],]

	def displayPreviousTargets(self, targetlistdata):
		'''
		Display targets belongs to a TargetListData.
		'''
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

		self.setTargetImageVector(imagedata)
		self.setImageTiltAxis(imagedata)

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

	def clearAllTargets(self):
		for name in self.targetnames:
			self.clearTargets(name)

	def isFromNewParentImage(self, imdata):
		'''
		Determine if the parent image of the given imdata is new. This is used to reset foc_counter for automated hole finders.
		'''
		is_new = True
		if imdata['target']:
			targetcopy = imdata['target']
			while True:
				# get the original target
				if targetcopy['fromtarget'] is None:
					break
				targetcopy = targetcopy['fromtarget']
			if targetcopy['image']:
				if targetcopy['image'].dbid == self.parent_imageid:
					is_new = False
				self.parent_imageid = targetcopy['image'].dbid
			else:
				self.parent_imageid = None
		else:
			self.parent_imageid = None
		return is_new

	def setTargetImageVector(self,imagedata):
		try:
			cam_length_on_image,beam_diameter_on_image = self.getAcquisitionTargetDimensions(imagedata)
			self._setTargetImageVector(cam_length_on_image,beam_diameter_on_image)
		except:
			pass

	def _setTargetImageVector(self,cam_length_on_image,beam_diameter_on_image):
		self.targetbeamradius = beam_diameter_on_image / 2
		self.targetimagevector = (cam_length_on_image,0)

	def setImageTiltAxis(self, imagedata):
		try:
			tem = imagedata['scope']['tem']
			ccdcamera = imagedata['camera']['ccdcamera']
			ht = imagedata['scope']['high tension']
			mag = imagedata['scope']['magnification']
			thetax, thetay = self.calclients['stage position'].getAngles(tem, ccdcamera, 'stage position', ht, mag, None)
			self.panel.onNewTiltAxis(thetax)
		except NoMatrixCalibrationError, e:
			self.logger.warning('No stage position matrix. Can not show tilt axis')
		except:
			raise

	def getTargetImageVector(self):
		return self.targetimagevector

	def getTargetBeamRadius(self):
		return self.targetbeamradius

	def uiRefreshTargetImageVector(self):
		'''
		refresh target image vector and beam size when ui exposure target panel tool
		is toggled on.
		'''
		if not self.current_image_pixelsize:
			self.logger.error('No image to calculate exposure area')
			return
		cam_length_on_image,beam_diameter_on_image = self._getAcquisitionTargetDimensions(self.current_image_pixelsize)
		self._setTargetImageVector(cam_length_on_image,beam_diameter_on_image)

	def getAcquisitionTargetDimensions(self,imagedata):
		'''
		Get next acquisition target image size and beam diameter displayed on imagedata
		'''
		if not self.next_acq_node:
			return 0,0
		image_pixelsize = self.calclients['image shift'].getImagePixelSize(imagedata)
		self.current_image_pixelsize = image_pixelsize
		return self._getAcquisitionTargetDimensions(image_pixelsize)

	def _getAcquisitionTargetDimensions(self,image_pixelsize):
		try:
			# get settings for the next Acquisition node
			settingsclassname = self.next_acq_node['class string']+'SettingsData'
			results= self.reseachDBSettings(getattr(leginondata,settingsclassname),self.next_acq_node['alias'])
			acqsettings = results[0]
			# use first preset in preset order for display
			presetlist = acqsettings['preset order']
			presetname = presetlist[0]
			# get image dimension of the target preset
			acq_dim = self.presetsclient.getPresetImageDimension(presetname)
			dim_on_image = []
			for axis in ('x','y'):
				dim_on_image.append(int(acq_dim[axis]/image_pixelsize[axis]))
			# get Beam diameter on image
			acq_presetdata = self.presetsclient.getPresetFromDB(presetname)
			beam_diameter = self.calclients['beam size'].getBeamSize(acq_presetdata)
			if beam_diameter is None:
				# handle no beam size calibration
				beam_diameter = 0
			beam_diameter_on_image = int(beam_diameter/min(image_pixelsize.values()))
			return max(dim_on_image), beam_diameter_on_image
		except:
			# Set Length to 0 in case of any exception
			return 0,0

	def onQueueCheckBox(self, state):
		'''
		Start queue click tool tracking.
		'''
		if self.settings['check method'] == 'remote':
			if state is True:
				self.remote.toolbar.addClickTool('queue','publishQueue','process queue')
			else:
				if 'queue' in self.remote.toolbar.tools:
					self.remote.toolbar.tools['queue'].deActivate()

	def blobStatsTargets(self, blobs):
		targets = []
		for blob in blobs:
			target = {}
			target['x'] = blob.stats['center'][1]
			target['y'] = blob.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Size'] = blob.stats['n']
			target['stats']['Mean'] = blob.stats['mean']
			target['stats']['Std. Dev.'] = blob.stats['stddev']
			targets.append(target)
		return targets

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
			self.waitForInteraction(imdata)
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
		self.logger.info('all targets published')
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

