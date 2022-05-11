#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import threading
import time
import math
import event, leginondata
import watcher
import targethandler
import node
import player
import remoteserver

class PauseRepeatException(Exception):
	'''Raised within processTargetData method if the target should be
	repeated after a user pause'''
	pass

class PauseRestartException(Exception):
	'''Raised within processTargetData method if the target should be
	repeated after a user pause'''
	pass

class BypassException(Exception):
	'''Raised within processTargetData method if the target should be
	bypassed'''
	pass

class BypassWarningException(Exception):
	'''Raised within processTargetData method if the target should be
	bypassed but not log as error'''
	pass

class FakeQueueNode(object):
	def __init__(self,name):
		self.name = '_'.join(name.split())

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
		parentimage = self.getTargetListParentImageWithStagePosition(targetlistdata, recent=True)
		try:
			scope = parentimage['scope']
			z = scope['stage position']['z']
			tem = scope['tem']
		except:
			self.logger.warning('Error retrieving z from most recent parent from targetlist of image id=%d' % parentimage.dbid)
		filename = parentimage['filename']
		self.logger.info('returning %s to z=%.4e of parent image %s' % (tem['name'], z, filename,))
		self.instrument.setTEM(tem['name'])
		self.instrument.tem.StagePosition = {'z': z}
		self.logger.info('z change done')


	def getTargetListParentImageWithStagePosition(self, targetlistdata, recent=False):
		'''
		This function is used for restoring z or alpha tilt of the targetlist.
		Target list may not have parent or the parent may not have stage position.
		If none of the potential parents have stage position, it will return None.
		'''
		imageref = targetlistdata.special_getitem('image', dereference=False)
		if hasattr(imageref,'dbid'):
			imageid = imageref.dbid
			# This is the version 0 of the parent when the imagetargetlist was created.
			imagedata0 = self.researchDBID(leginondata.AcquisitionImageData, imageid, readimages=False)
		else:
			imagedata0 = None
		if not imagedata0:
				# grid atlas targetlist (one targetlist for all image tiles)
				# has no parent image but targets in that list has parent image.
				#	HACK: Use the most recent target to get the parent image
				result_t = leginondata.AcquisitionImageTargetData(list=targetlistdata).query(results=1)
				try:
					# parent image must have ScopeEMData reference
					stage = result_t[0]['image']['scope']['stage position']
					imagedata0 = result_t[0]['image']
					self.logger.info('Found target parent image (id=%d) through a target of the targetlist' % imagedata0.dbid)
				except:
					# No parent image in any way.
					return None
		# look for a more recent version of this image
		if recent:
			target = imagedata0['target']
			if target:
				#this will go very wrong if the image comes from no target
				# Fortunately only manual or uploaded images have no target.
				imquery = leginondata.AcquisitionImageData(target=target)
				allversions = imquery.query(readimages=False)
				self.logger.info('%d versions found from parent target id %d' % (len(allversions), target.dbid))
				imagedata = allversions[0]
				try:
					# parent image must have ScopeEMData reference.  True for all images.
					stage = imagedata['scope']['stage position']
					self.logger.info('Found most recent target parent image (id=%d)' % imagedata.dbid)
				except Exception, e:
					# This should never happen unless there is database error
					self.logger.error(str(e))
			else:
				imagedata = imagedata0
		else:
			imagedata = imagedata0
		return imagedata

	def getTiltForList(self, targetlistdata):
		original_position = self.instrument.tem.getStagePosition()
		parent_tilt = original_position['a']
		#tilt the stage first
		if self.settings['use parent tilt']:
			# FIX ME: Do we have to use most the recent version of the parent image ?
			parentimage = self.getTargetListParentImageWithStagePosition(targetlistdata, recent=False)
			if parentimage :
				parent_tilt = parentimage['scope']['stage position']['a']
				self.logger.info('Found targetlist parent image stage tilt at %.2f degrees.' % (parent_tilt*180.0/math.pi))
			else:
				parent_tilt = original_position['a']
		return parent_tilt

	def sortTargetsByType(self, targetlist, mytargettype):
		# separate the good targets from the rejects
		completed_targets = []
		good_targets = []
		rejects = []
		#ignored = []

		for target in targetlist:
			if target['status'] in ('done', 'aborted'):
				completed_targets.append(target)
			elif target['type'] == mytargettype:
				good_targets.append(target)
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
		return completed_targets, good_targets, rejects

	def postQueueCount(self, count):
		if not hasattr(self, 'remote_queue_count'):
			if self.remote:
				# when targetwatcher is first initiated, getQueue may fail if application
				# is loaded out of order.  Safer to do it here.
				queue = self.getQueue()
				# queue_node_class only needs name and logger attribute.
				queue_node_class = FakeQueueNode(queue['label'])
				# routing logger to self
				queue_node_class.logger = self.logger
				self.remote_queue_count = remoteserver.RemoteQueueCount(self.logger, self.session, queue_node_class, self.remote.leginon_base)
			else:
				# remoteserver.NO_REQUESTS=True
				self.remote_queue_count = None
		if self.remote_queue_count:
			self.remote_queue_count.setQueueCount(count)

	def processTargetList(self, newdata):
		self.setStatus('processing')
		mytargettype = self.settings['process target type']
		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist), listid))
		completed_targets, good_targets, rejects = self.sortTargetsByType(targetlist, mytargettype)

		# There may not be good targets but only rejected
		# or reference targets causing self.targetlist_reset_tilt undefined.
		# define it now regardless.
		original_position = self.instrument.tem.getStagePosition()
		self.targetlist_reset_tilt = original_position['a']
		if self.settings['set aperture']:
			# get aperture selection only if need to avoid error in accessing info.
			try:
				self.logger.info('Getting current aperture selection so we can restore....')
				self.obj_aperture_reset_value = self.instrument.tem.getApertureSelection('objective')
				self.c2_aperture_reset_value = self.instrument.tem.getApertureSelection('condenser')
			except Exception, e:
				self.logger.error(e)
				self.logger.error('Please set aperture manually and continue')
				self.player.pause()
				self.obj_aperture_reset_value = 'unknown'
				self.c2_aperture_reset_value = 'unknown'
			
		if good_targets:
			# Things to do before reject targets are published.
			# pause and abort check before reference and rejected targets are sent away
			state = self.pauseCheck('paused before reject targets are published')
			self.setStatus('processing')
			if state in ('stop', 'stopqueue'):			# When user stops at this node
				targetliststatus = 'aborted'
				# If I report targets done then rejected target are also done.  Which make
				# them unrestartable What to do???????
				self.reportTargetListDone(newdata, targetliststatus)
				self.setStatus('idle')
				return

			# initialize is_first-image
			self.is_firstimage = True
			self.targetlist_reset_tilt = self.getTiltForList(newdata)
			# There was a set self.targetlist_reset_tilt in the old code.
			# start conditioner
			condition_status = 'repeat'					# don't need a target
			while condition_status == 'repeat':
				if self.remote_pmlock:
					self.remote_pmlock.setLock()
				try:
					self.setStatus('waiting')
					self.fixCondition()
					self.setStatus('processing')
					condition_status = 'success'
				except PauseRepeatException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then press play to repeat target')
					condition_status = 'repeat'
				except Exception, e:
					self.logger.error('Conditioning failed. Continue without it')
					condition_status = 'abort'
				self.beep()
				if self.remote_pmlock:
					self.remote_pmlock.setUnlock()
			# pause but not stop
			state = self.pauseCheck('paused after fix condition')

			# processReference.  FIX ME, when it comes back, need to move more
			# accurately than just send the position.
			if self.settings['wait for reference']:				#For example ZLP alignment
				self.setStatus('waiting')
				if self.remote_pmlock:
					self.remote_pmlock.setLock()
				self.processReferenceTarget()
				if self.remote_pmlock:
					self.remote_pmlock.setUnlock()
				self.setStatus('processing')
			# pause but not stop
			state = self.pauseCheck('paused after reference processing')
			# start alignment manager.  May replace reference in the future
			self.setStatus('waiting')
			if self.remote_pmlock:
				self.remote_pmlock.setLock()
			self.fixAlignment()
			if self.remote_pmlock:
				self.remote_pmlock.setUnlock()
			self.setStatus('processing')
			# pause but not stop
			state = self.pauseCheck('paused after fix alignment')
			# This will bright z to the value before reference targets and alignment
			# fixing.
			self.logger.info('Setting z to original z of %.2f um' % (original_position['z']*1e6))
			try:
				self.setStatus('processing')
				self.instrument.tem.setStagePosition({'z':original_position['z']})
			except Exception as e:
				self.logger.error('Failed to return z position %s' % str(e))
				self.logger.error('Please check tem')
			self.logger.info('Processing %d %s targets...' % (len(good_targets), mytargettype))
		# republish the rejects and wait for them to complete
		
		waitrejects = rejects and self.settings['wait for rejects']
		if waitrejects:

			# FIX ME: If autofocus involves stage tilt and self.targetlist_reset_tilt
			# is at high tilt, it is better not to tilt first but if autofocus does
			# not involve that, it needs to be tilted now.
			if self.remote_pmlock:
				self.remote_pmlock.setLock()
			rejectstatus = self.rejectTargets(newdata) # will stay until node gives back a done
			if self.remote_pmlock:
				self.remote_pmlock.setUnlock()
			if rejectstatus != 'success':
				## report my status as reject status may not be a good idea
				## all the time. This means if rejects were aborted
				## then this whole target list was aborted
				self.logger.debug('Passed targets not processed, aborting current target list')
				self.reportTargetListDone(newdata, rejectstatus)
				self.setStatus('idle')
				# Anchi, at focus node, if it fails, I think it still reports success since 
				# line ~ 324 is always true. This is a bit dangerous for tomo.
				# If focusing fails, there is not reason to move on, since tracking with likely
				# be very off. 
				if rejectstatus != 'aborted':	 
					return
			self.logger.info('Passed targets processed, processing current target list')
			# pause but not stop
			state = self.pauseCheck('paused after waiting for processing rejected targets')

		self.logger.info('Original tilt %.2f degrees.' % (original_position['a']*180.0/math.pi))
		self.logger.info('Parent tilt %.2f degrees.' % (self.targetlist_reset_tilt*180.0/math.pi))
		# process the good ones
		retract_successful = False
		if self.isNeedSetApertures(good_targets):
			retract_successful = self.setApertures()

		targetliststatus = 'success'
		if good_targets:
			targetliststatus = self.processGoodTargets(good_targets)

		self.reportTargetListDone(newdata, targetliststatus)
		if retract_successful:
			self.putBackApertures()

		if self.settings['park after list']:
			self.park()
		self.setStatus('idle')

	def isNeedSetApertures(self,good_targets):
		want_to = good_targets and self.settings['set aperture']
		if not want_to:
			return False
		obj_to_set = self.settings['objective aperture']
		c2_to_set = self.settings['c2 aperture']
		if self.obj_aperture_reset_value == 'unknown' or self.obj_aperture_reset_value == 'unknown':
			self.logger.warning('Objective aperture not in a restorable state. Skip setting aperture')
			return False
		can_do = self.obj_aperture_reset_value not in (obj_to_set,) or self.c2_aperture_reset_value != c2_to_set
		return can_do

	def setApertures(self):
		set_ap_successful = False
		new_obj_ap = self.settings['objective aperture']
		new_c2_ap = self.settings['c2 aperture']
		self.logger.info('Setting apertures....')
		try:
			state1 = self.instrument.tem.setApertureSelection('objective',new_obj_ap)
			self.logger.info('Objective aperture set to %s' % new_obj_ap)
			state2 = self.instrument.tem.setApertureSelection('condenser',new_c2_ap)
			self.logger.info('Condenser aperture set to %s' % new_c2_ap)
			set_ap_successful = state1 and state2
		except Exception, e:
			self.logger.error(e)
		return set_ap_successful

	def putBackApertures(self):
		self.logger.info('Inserting objective aperture....')
		new_obj_ap = self.obj_aperture_reset_value
		new_c2_ap = self.c2_aperture_reset_value
		try:
			state1 = self.instrument.tem.setApertureSelection('objective',new_obj_ap)
			self.logger.info('objective aperture set to %s' % (new_obj_ap,))
			state2 = self.instrument.tem.setApertureSelection('condenser',new_c2_ap)
			self.logger.info('Condenser aperture set to %s' % new_c2_ap)
		except Exception, e:
			self.logger.error(e)

	def getIsResetTiltInList(self):
		'''
		Determine whether to reset tilt before the first target is processed.
		Subclasses like RCT and TiltListAlternator
		'''
		return self.settings['use parent tilt']

	def pauseCheck(self, msg):
		'''
		Check if need pause.  During pause z might change from
		other nodes.  Restore the z when resume.
		'''
		if self.player.state() == 'pause':
			self.logger.info(msg)
			self.setStatus('user input')
			try:
				self.z_now = self.instrument.tem.getStagePosition()['z']
			except Exception as e:
				# catch for display but not stopping the workflow
				# since this unlikely to be fatal.
				self.logger.error(e)
		else:
			self.z_now = None
		state = self.player.wait()
		if self.z_now is not None:
			try:
				self.instrument.tem.StagePosition={'z':self.z_now}
			except Exception as e:
				# catch for display but not stopping the workflow
				# since this unlikely to be fatal.
				# we will let other place to handle the cause of this error.
				self.logger.error(e)
		return state

	def makeTargetIndexOrder(self, good_targets):
		'''
		Return the order of the good_targets within a targetlist
		expressed in its target numbers. Use database values if present.
		'''
		if not good_targets:
			return [] # nothing to reorder
		targetlist = good_targets[0]['list']
		# get target order from db. This may include done targets not
		# in good_targets if leginon was restarted in the mid of processing.
		try:
			target_order = leginondata.TargetOrderData(session=self.session, list=targetlist).query(results=1)[0]['order']
		except IndexError:
			return range(len(good_targets))
		target_numbers = map((lambda x: x['number']),good_targets)
		# this filter makes sure that returned index_order only contains only those
		# of the good_targets.
		valid_order = filter((lambda x: x in target_numbers), target_order)
		index_order = map((lambda x:target_numbers.index(x)), valid_order)
		return index_order

	def processGoodTargets(self, good_targets):
		good_target_count = len(good_targets)
		# Approach 1: order targets 
		remaining_targets = good_targets
		targetliststatus = 'success'
		while True:
			index_order = self.makeTargetIndexOrder(remaining_targets)
			if index_order:
				i = index_order[0]
				target = remaining_targets[i]
			elif remaining_targets:
				# abort the targets
				targetliststatus = 'aborted'
				for t in good_targets:
					self.reportTargetStatus(t, 'aborted')
				break
			else:
				# end of good targets
				break
			# target adjustment may have changed the tilt.
			if self.getIsResetTiltInList() and self.is_firstimage:
				# ? Do we need to reset on every target ?
				self.logger.info('Tilting to %.2f degrees on first good target.' % (self.targetlist_reset_tilt*180.0/math.pi))
				self.instrument.tem.setDirectStagePosition({'a':self.targetlist_reset_tilt})
			self.goodnumber = i
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# ...
			if self.player.state() == 'pause':
				self.logger.info('paused after resetTiltInList')
				self.setStatus('user input')
				# FIX ME: if player does not wait, why should it pause ?
			state = self.clearBeamPath()
			self.setStatus('processing')
			# abort
			if state in ('stop', 'stopqueue'):
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				self.reportTargetStatus(target, 'aborted')
				del remaining_targets[i]
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				del remaining_targets[i]
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
					self.logger.info('Processing target id %d' % adjustedtarget.dbid)
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except BypassException, e:
					# for example Image Acquisition error
					self.logger.error(str(e) + '... Bypass this target and continue to the next')
					process_status = 'bypass'
				except BypassWarningException, e:
					# for example invalid stage position error
					self.logger.warning(str(e) + '... Bypass this target and continue to the next')
					process_status = 'bypass'
				except PauseRestartException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then resubmit targets from previous step to repeat')
					self.beep()
					process_status = 'repeat'
				except PauseRepeatException, e:
					#TODO: NoMoveCalibration is a subclass of this. It is not handled now.
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
				finally:
					is_failed = self.resetComaCorrection()
					if is_failed is True:
						self.logger.warning('Failure here will repeat process target. Might double expose')
						self.player.pause()
						process_status = 'repeat'
				self.stopTimer('processTargetData')

				if process_status == 'repeat':
					# Do not report targetstatus so that it can repeat even if
					# restart Leginon
					pass
				elif process_status == 'bypass':
					# abort just the target
					self.reportTargetStatus(adjustedtarget, 'aborted')
				elif process_status != 'exception':
					# normal status
					self.reportTargetStatus(adjustedtarget, 'done')
				else:
					# set targetlist status to abort if exception not user fixable
					targetliststatus = 'aborted'
					self.reportTargetStatus(adjustedtarget, 'aborted')

				# pause check after a good target processing
				state =  self.pauseCheck('paused after processTargetData')
				self.setStatus('processing')
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborted')
					break # break repeat
				if state in ('stoptarget',):
					self.logger.info('Aborted this target. continue to next')
					self.reportTargetStatus(adjustedtarget, 'aborted')
					self.player.play()

				# end of target repeat loop
			# next target is not a first-image
			del remaining_targets[i]
			self.is_firstimage = False
		return targetliststatus

	def park(self):
		self.logger.info('parking...')
		try:
			self.instrument.tem.ColumnValvePosition = 'closed'
			self.instrument.tem.StagePosition = {'x': 0, 'y': 0}
			self.logger.warning('column valves closed and stage reset')
		except Exception as e:
			self.logger.error('Parking error: %s' % e )

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
		elif state == 'stoptarget':
			infostr += 'Aborting single target...'
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
