#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import event, data
import watcher
import threading
import uidata
import targethandler
import node
import player

class TargetWatcher(watcher.Watcher, targethandler.TargetHandler):
	'''
	TargetWatcher will watch for TargetLists
	It is also initialized with a specific type of target that it can
	process.  All other targets are republished in another target list.
	'''

	eventinputs = watcher.Watcher.eventinputs + targethandler.TargetHandler.eventinputs + [event.TargetListDoneEvent,
																						event.ImageTargetListPublishEvent,
																						event.ImageTargetShiftPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + targethandler.TargetHandler.eventoutputs + [event.TargetListDoneEvent, event.NeedTargetShiftEvent]

	def __init__(self, id, session, managerlocation, target_types=('acquisition',),
								**kwargs):
		watchfor = [event.ImageTargetListPublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor,
															**kwargs)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.addEventInput(event.ImageTargetShiftPublishEvent,
												self.handleTargetShift)

		self.player = player.Player(callback=self.panel.playerEvent)
		self.panel.playerEvent(self.player.state())
		self.newtargetshift = threading.Event()
		self.target_types = target_types
		self.targetlistevents = {}
		self.driftedimages = {}

	def handleTargetShift(self, ev):
		driftdata = ev['data']
		self.driftedimages = driftdata['shifts']
		self.logger.debug('HANDLING TARGET SHIFT ' + str(self.driftedimages))
		# may be waiting for a requested image shift
		req = driftdata['requested']
		if req:
			self.logger.debug('TARGET SHIFT WAS REQUESTED')
			self.newtargetshift.set()
		else:
			self.logger.debug('TARGET SHIFT NOT REQUESTED')

	def processData(self, newdata):
		if not isinstance(newdata, data.ImageTargetListData):
			return

		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist),listid))

		# separate the good targets from the rejects
		goodtargets = []
		rejects = []

		for target in targetlist:
			im = target['image']
			if im is not None:
				imageid = target['image'].dbid
			else:
				imageid = None
			self.logger.debug('IMAGEID ' + str(imageid))
			if target['type'] in self.target_types:
				goodtargets.append(target)
			else:
				rejects.append(target)

		self.logger.debug('%d process, %d pass, %d total' % (len(goodtargets), len(rejects), len(targetlist)))

		# republish the rejects and wait for them to complete
		waitrejects = rejects and self.settings['wait for rejects']
		if waitrejects:
			rejectstatus = self.rejectTargets(rejects)
			if rejectstatus != 'success':
				## report my status as reject status
				## may not be a good idea all the time
				## This means if rejects were aborted
				## then this whole target list was aborted
				self.logger.warning('Passed targets not processed, aborting current target list')
				self.reportTargetListDone(newdata.dmid, rejectstatus)
				return

			self.logger.info('Passed targets processed, processing current target list')

		# process the good ones
		targetliststatus = 'success'
		for i, target in enumerate(goodtargets):
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# abort
			if self.player.state() == 'stop':
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				donetarget = data.AcquisitionImageTargetData(initializer=target, status='aborted')
				#self.publish(donetarget, database=True, dbforce=True)
				## Why use force????????????
				self.publish(donetarget, database=True)
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			#'TARGET STATUS', target['status']
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				continue

			### generate a focus target
			if self.settings['duplicate targets']:
				focustarget = data.AcquisitionImageTargetData(initializer=target)
				focustarget['type'] = self.settings['duplicate target type']
				self.publish(focustarget, database=True)
				tlist = [focustarget]
				self.rejectTargets(tlist)

			self.logger.debug('creating processing target')
			adjustedtarget = data.AcquisitionImageTargetData(initializer=target,
																												status='processing')
			#self.publish(adjustedtarget, database=True, dbforce=True)
			## Why force???
			self.logger.debug('publishing processing target')
			self.publish(adjustedtarget, database=True)
			self.logger.debug('processing target published')

			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1
				# check if this imageid needs update
				self.logger.debug('DRIFTED IMAGES ' + str(self.driftedimages))
				if imageid in self.driftedimages:
					self.logger.debug('THIS IS DRIFTED')
					#if self.driftedimages[imageid]:
					#	'ALREADY HAVE ADJUST'
					#else:
					if not self.driftedimages[imageid]:
						# need to have drift manager do it
						self.newtargetshift.clear()
						ev = event.NeedTargetShiftEvent(imageid=imageid)
						self.logger.debug('SENDING NEEDTARGETSHIFTEVENT AND WAITING ' + str(imageid))
						self.outputEvent(ev)
						self.newtargetshift.wait()
						self.logger.debug('DONE WAITING')
						# 'done.'
					adjust = self.driftedimages[imageid]
					# perhaps flip
					## create new adjusted target from old
					adjustedtarget = \
						data.AcquisitionImageTargetData(initializer=adjustedtarget)
					adjustedtarget['version'] += 1
					adjustedtarget['delta row'] = target['delta row'] + adjust['rows']
					adjustedtarget['delta column'] = target['delta column'] \
																														+ adjust['columns']
					#self.publish(adjustedtarget, database=True, dbforce=True)
					## Why force???
					self.publish(adjustedtarget, database=True )
					# 'done.'
				#else:
				#	 'NOT DRIFTED TARGET'

				# now have processTargetData work on it
				try:
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except node.PublishError, e:
					self.logger.info('Pausing...')
					self.player.pause()
					self.logger.exception('Saving image failed: %s' % e)
					process_status = 'repeat'
				except Exception, e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'

				# pause
				if self.player.state() == 'pause':
					self.logger.info('Paused')
					self.player.wait()

				# abort
				if self.player.state() == 'stop':
					self.logger.info('Aborted')
					break

				# end of target repeat loop

			self.logger.debug('creating done target')
			donetarget = data.AcquisitionImageTargetData(initializer=adjustedtarget,
																										status='done')
			#self.publish(donetarget, database=True, dbforce=True)
			## Why force???
			self.logger.debug('publishing done target')
			self.publish(donetarget, database=True)
			self.logger.debug('done target published')

		self.reportTargetListDone(newdata.dmid, targetliststatus)

	def reportTargetListDone(self, listid, status):
		self.logger.info('%s done with target list ID: %s, status: %s' % (self.name, listid, status))
		e = event.TargetListDoneEvent(targetlistid=listid, status=status)
		self.outputEvent(e)

	def waitForRejects(self):
		# wait for focus target list to complete
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

	def rejectTargets(self, targets):
		self.logger.info('Publishing reject targets')
		rejectlist = self.newTargetList()
		self.publish(rejectlist, database=True, dbforce=True)
		for target in targets:
			reject = data.AcquisitionImageTargetData(initializer=target)
			reject['list'] = rejectlist
			self.publish(reject, database=True)
		tlistid = rejectlist.dmid
		self.targetlistevents[tlistid] = {}
		self.targetlistevents[tlistid]['received'] = threading.Event()
		self.targetlistevents[tlistid]['status'] = 'waiting'
		self.publish(rejectlist, pubevent=True)
		self.logger.info('Waiting for reject targets to be processed...')
		rejectstatus = self.waitForRejects()
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

