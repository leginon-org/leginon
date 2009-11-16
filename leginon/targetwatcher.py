#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import event, leginondata
import watcher
import threading
import targethandler
import node
import player

class PauseRepeatException(Exception):
	'''Raised within processTargetData method if the target should be
	repeated after a user pause'''
	pass

class TargetWatcher(watcher.Watcher, targethandler.TargetHandler):
	'''
	TargetWatcher will watch for TargetLists
	It is also initialized with a specific type of target that it can
	process.  All other targets are republished in another target list.
	'''

	settingsclass = leginondata.TargetWatcherSettingsData
	defaultsettings = {
		'process target type': 'acquisition',
	}

	eventinputs = watcher.Watcher.eventinputs + targethandler.TargetHandler.eventinputs + [event.TargetListDoneEvent,
																						event.ImageTargetListPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + targethandler.TargetHandler.eventoutputs + [event.TargetListDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.ImageTargetListPublishEvent, event.QueuePublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor,
															**kwargs)
		targethandler.TargetHandler.__init__(self)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.targetlistevents = {}
		self.startQueueProcessor()

	def processData(self, newdata):
		if isinstance(newdata, leginondata.ImageTargetListData):
			self.setStatus('processing')
			self.startTimer('processTargetList')
			self.processTargetList(newdata)
			self.stopTimer('processTargetList')
			self.player.play()
			self.setStatus('idle')
		if isinstance(newdata, leginondata.QueueData):
			self.processTargetListQueue(newdata)

	def processTargetListQueue(self, newdata):
		self.targetlistqueue = newdata
		self.queueupdate.set()

	def setZ(self, targetdata):
		parentimage = targetdata.special_getitem('image', readimages=False)
		if parentimage is None:
			return
		parenttarget = parentimage['target']
		if parenttarget is None:
			## only query targets from this image
			imquery = parentimage
		else:
			## query targets from all image descendents of parenttarget
			imquery = leginondata.AcquisitionImageData(target=parenttarget)
		## query focus corrections made on parent image
		targetquery = leginondata.AcquisitionImageTargetData(image=imquery)
		focusquery = leginondata.FocuserResultData(target=targetquery)
		siblingresults = focusquery.query(results=1)
		# use z from focus result or from parent image
		if siblingresults:
			z = siblingresults[0]['scope']['stage position']['z']
			self.logger.info('setting Z from focus result')
		else:
			z = parentimage['scope']['stage position']['z']
			self.logger.info('setting Z from parent image')
		self.instrument.tem.StagePosition = {'z': z}
		self.logger.info('Z set to %f' % (z,))

	def revertTargetListZ(self, targetlistdata):
		'''use the z position of the target list parent image'''
		imageref = targetlistdata.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		imagedata = self.researchDBID(leginondata.AcquisitionImageData, imageid, readimages=False)

		# look for a more recent version of this image
		target = imagedata['target']
		imquery = leginondata.AcquisitionImageData(target=target)
		allversions = imquery.query(readimages=False)
		imagedata = allversions[0]

		scope = imagedata['scope']
		z = scope['stage position']['z']
		tem = scope['tem']
		filename = imagedata['filename']
		self.logger.info('returning %s to z=%.4e of parent image %s' % (tem['name'], z, filename,))
		self.instrument.setTEM(tem['name'])
		self.instrument.tem.StagePosition = {'z': z}
		self.logger.info('z change done')

	def processTargetList(self, newdata):
		self.setStatus('processing')
		mytargettype = self.settings['process target type']

		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist), listid))

		# separate the good targets from the rejects
		completed_targets = []
		goodtargets = []
		rejects = []
		#ignored = []

		for target in targetlist:
			if target['status'] in ('done', 'aborted'):
				completed_targets.append(target)
			elif target['type'] == mytargettype:
				goodtargets.append(target)
			#elif not rejects:
				## this only allows one reject
			else:
				rejects.append(target)
			#else:
			#	ignored.append(target)

		self.logger.info('%d target(s) in the list' % len(targetlist))
		if completed_targets:
			self.logger.info('%d target(s) have already been processed' % len(completed_targets))
		if rejects:
			self.logger.info('%d target(s) will be rejected based on type' % len(rejects))
		#if ignored:
		#	self.logger.info('%d target(s) will be ignored' % len(ignored))
		if goodtargets:
			#tilt the stage first
			if self.settings['use parent tilt']:
				state1 = leginondata.ScopeEMData()
				parentimage = newdata.special_getitem('image', True, readimages=False)
				state1['stage position'] = {'a':parentimage['scope']['stage position']['a']}
				self.instrument.setData(state1)
			# This is only for beamfixer now and it does not need preset_name
			preset_name = None
			if self.settings['wait for reference']:
				self.setStatus('waiting')
				self.processReferenceTarget(preset_name)
				self.setStatus('processing')
			self.logger.info('Processing %d %s targets...' % (len(goodtargets), mytargettype))

		# republish the rejects and wait for them to complete
		waitrejects = rejects and self.settings['wait for rejects']
		if waitrejects:
			rejectstatus = self.rejectTargets(newdata)
			if rejectstatus != 'success':
				## report my status as reject status
				## may not be a good idea all the time
				## This means if rejects were aborted
				## then this whole target list was aborted
				self.logger.debug('Passed targets not processed, aborting current target list')
				self.reportTargetListDone(newdata, rejectstatus)
				self.setStatus('idle')
				if rejectstatus != 'aborted':
					return
			self.markTargetsDone(rejects)
			self.logger.info('Passed targets processed, processing current target list')

		# process the good ones
		targetliststatus = 'success'
		for i, target in enumerate(goodtargets):
			self.goodnumber = i
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# ...
			if self.player.state() == 'pause':
				self.setStatus('user input')
			state = self.player.wait()
			self.setStatus('processing')
			# abort
			if state in ('stop', 'stopqueue'):
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				donetarget = leginondata.AcquisitionImageTargetData(initializer=target, status='aborted')
				self.publish(donetarget, database=True)
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				continue

			self.logger.debug('Creating processing target...')
			adjustedtarget = leginondata.AcquisitionImageTargetData(initializer=target,
																												status='processing')
			self.logger.debug('Publishing processing target...')
			self.publish(adjustedtarget, database=True)
			self.logger.debug('Processing target published')

			#self.setZ(adjustedtarget)
			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1

				# now have processTargetData work on it
				self.startTimer('processTargetData')
				try:
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except PauseRepeatException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then press play to repeat target')
					self.beep()
					process_status = 'repeat'
				except node.PublishError, e:
					self.player.pause()
					self.logger.exception('Saving image failed: %s' % e)
					process_status = 'repeat'
				except Exception, e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'
				self.stopTimer('processTargetData')

				# pause
				# ...
				if self.player.state() == 'pause':
					self.setStatus('user input')
				state = self.player.wait()
				self.setStatus('processing')
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborted')
					break

				# end of target repeat loop

			self.logger.debug('Creating done target...')
			donetarget = leginondata.AcquisitionImageTargetData(initializer=adjustedtarget,
																										status='done')
			#self.publish(donetarget, database=True, dbforce=True)
			## Why force???
			self.logger.debug('Publishing done target...')
			self.publish(donetarget, database=True)
			self.logger.debug('Done target published')

		# (Hack removed: Sometimes we are processing an empty
		# target list. The TargetListDone event still has to go
		# back to the other node or else application hangs.
		self.reportTargetListDone(newdata, targetliststatus)
		self.setStatus('idle')

	def waitForRejects(self):
		# wait for other targets to complete
		for tid, teventinfo in self.targetlistevents.items():
			teventinfo['received'].wait()

		## check status of all target lists
		## all statuses must be success in order for complete success
		status = 'success'
		for tid, teventinfo in self.targetlistevents.items():
			if teventinfo['status'] in ('failed', 'aborted'):
				status = teventinfo['status']
				break
		self.targetlistevents.clear()
		
		return status

	def rejectTargets(self, targetlist):
		self.logger.info('Publishing rejected targets')
		rejectlist = targetlist
		tlistid = rejectlist.dbid
		self.targetlistevents[tlistid] = {}
		self.targetlistevents[tlistid]['received'] = threading.Event()
		self.targetlistevents[tlistid]['status'] = 'waiting'
		self.publish(rejectlist, pubevent=True)
		self.logger.info('Waiting for rejected targets to be processed...')
		self.setStatus('waiting')
		rejectstatus = self.waitForRejects()
		self.setStatus('processing')
		return rejectstatus

	def handleTargetListDone(self, targetlistdoneevent):
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		self.player.stop()

	def pauseTargetListLoop(self):
		self.player.pause()

	def continueTargetListLoop(self):
		self.player.play()

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += 'Continuing...'
		elif state == 'pause':
			infostr += 'Pausing...'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)
	def processReferenceTarget(self,presetname):
		raise NotImplementedError()
