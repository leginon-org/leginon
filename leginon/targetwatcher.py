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
import time

class PauseRepeatException(Exception):
	'''Raised within processTargetData method if the target should be
	repeated after a user pause'''
	pass

class PauseRestartException(Exception):
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
		'park after list': False,
		'clear beam path': False,
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
		self.is_firstimage = False

	def processData(self, newdata):
		if isinstance(newdata, leginondata.ImageTargetListData):
			self.clearBeamPath()
			self.setStatus('processing')
			self.startTimer('processTargetList')
			self.processTargetList(newdata)
			self.stopTimer('processTargetList')
			self.player.play()
			self.setStatus('idle')
			if self.settings['reset tilt']:
				self.resetTiltStage()
		if isinstance(newdata, leginondata.QueueData):
			self.processTargetListQueue(newdata)

	def processTargetListQueue(self, newdata):
		self.targetlistqueue = newdata
		self.queueupdate.set()

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
			# pause and abort check before reference and rejected targets are sent away
			if self.player.state() == 'pause':
				self.setStatus('user input')
			state = self.player.wait()
			self.setStatus('processing')
			if state in ('stop', 'stopqueue'):
				targetliststatus = 'aborted'
				# If I report targets done then rejected target are also done.  Which make
				# them unrestartable What to do???????
				self.reportTargetListDone(newdata, targetliststatus)
				self.setStatus('idle')
				return

			# initialize is_first-image
			self.is_firstimage = True
			#tilt the stage first
			if self.settings['use parent tilt']:
				state1 = leginondata.ScopeEMData()
				parentimage = newdata.special_getitem('image', True, readimages=False)
				state1['stage position'] = {'a':parentimage['scope']['stage position']['a']}
				self.instrument.setData(state1)
			# start conditioner
			self.setStatus('waiting')
			self.fixCondition()
			self.setStatus('processing')
			# This is only for beamfixer now and it does not need preset_name
			preset_name = None
			original_position = self.instrument.tem.getStagePosition()
			if self.settings['wait for reference']:
				self.setStatus('waiting')
				self.processReferenceTarget()
				self.setStatus('processing')
			# start alignment manager.  May replace reference in the future
			self.setStatus('waiting')
			self.fixAlignment()
			self.setStatus('processing')
			self.instrument.tem.setStagePosition({'z':original_position['z']})
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
			self.logger.info('Passed targets processed, processing current target list')

		########## THIS IS EXPERIMENTAL AND SHOULD NOT BE USED ###############
		use_it_anyway = False
		if use_it_anyway:
			import random
			import os.path
			homedir = os.path.expanduser('~')
			filename = os.path.join(homedir, 'settings_list.txt')
			try:
				f = open(filename)
			except:
				print '****** No ~/settings_list.txt'
				pass
			else:
				lines = f.readlines()
				f.close()
				node_name = lines[0].strip()
				if node_name == self.name:
					idlines = lines[1:]
					ids_strings = map(str.strip, idlines)
					ids_ints = map(int, ids_strings)
					id = random.choice(ids_ints)
					print '************** Loading new settings:', id
					self.loadSettingsByID(id)
		#####################################################################

		# process the good ones
		targetliststatus = 'success'
		for i, target in enumerate(goodtargets):
			self.goodnumber = i
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# ...
			if self.player.state() == 'pause':
				self.setStatus('user input')
			state = self.clearBeamPath()
			self.setStatus('processing')
			# abort
			if state in ('stop', 'stopqueue'):
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				self.reportTargetStatus(target, 'aborted')
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				continue

			adjustedtarget = self.reportTargetStatus(target, 'processing')

			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1

				# now have processTargetData work on it
				self.startTimer('processTargetData')
				try:
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except PauseRestartException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then resubmit targets from previous step to repeat')
					self.beep()
					process_status = 'repeat'
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

				if process_status == 'repeat':
					# Do not report targetstatus so that it can repeat even if
					# restart Leginon
					pass
				elif process_status != 'exception':
					self.reportTargetStatus(adjustedtarget, 'done')
				else:
					# set targetlist status to abort if exception not user fixable
					targetliststatus = 'aborted'
					self.reportTargetStatus(adjustedtarget, 'aborted')

				# pause check after a good target processing
				if self.player.state() == 'pause':
					self.setStatus('user input')
				state = self.player.wait()
				self.setStatus('processing')
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborted')
					break

				# end of target repeat loop
			# next target is not a first-image
			self.is_firstimage = False

		self.reportTargetListDone(newdata, targetliststatus)
		if self.settings['park after list']:
			self.park()
		self.setStatus('idle')

	def park(self):
		self.logger.info('parking...')
		self.instrument.tem.ColumnValvePosition = 'closed'
		self.instrument.tem.StagePosition = {'x': 0, 'y': 0, 'a': 0}
		self.logger.warning('column valves closed and stage reset')

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
	
	def fixAlignment(self):
		raise NotImplementedError()

	def fixCondition(self):
		raise NotImplementedError()

	def clearBeamPath(self):
		'''
		Check column valve and any other obsticles for the beam
		to reach the camera.  This is a work around for some scopes
		that closes column valve that senses a tiny spike in pressure
		that is recoverable.
		'''
		# This should be set to be long enough for scope to respond
		# if the vacuum is really bad.
		valve_opening_wait_time_seconds = 5

		if not self.settings['clear beam path']:
			return self.player.state()
		# Check column valve
		if self.instrument.tem.ColumnValvePosition == 'closed':
			self.logger.info('found column valve closed')
			if self.player.state() == 'stopqueue':
				return self.player.state()
			# Try to reopen the column
			self.logger.info('Opening column valve....')
			self.instrument.tem.ColumnValvePosition = 'open'
			# Test if the opening is successful
			time.sleep(valve_opening_wait_time_seconds)
			if self.instrument.tem.ColumnValvePosition == 'closed':
				# Pause if the scope closes the column valve again
				self.logger.warning('column valve failed to open')
				if self.player.state() == 'play':
					self.player.pause()
					self.setStatus('user input')
				return self.player.wait()
			else:
				self.logger.info('column valve opened successfully')
				return self.player.state()
