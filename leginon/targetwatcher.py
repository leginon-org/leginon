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

class TargetWatcher(watcher.Watcher):
	'''
	TargetWatcher will watch for TargetLists
	It is also initialized with a specific type of target that it can
	process.  All other targets are republished in another target list.
	'''

	eventinputs = watcher.Watcher.eventinputs + [event.TargetListDoneEvent,
																						event.ImageTargetListPublishEvent,
																						event.ImageTargetShiftPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.TargetListDoneEvent,
																							event.ImageTargetListPublishEvent,
																							event.NeedTargetShiftEvent]

	def __init__(self, id, session, nodelocations, target_type='acquisition',
								**kwargs):
		watchfor = [event.ImageTargetListPublishEvent]
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor,
															**kwargs)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.addEventInput(event.ImageTargetShiftPublishEvent,
												self.handleTargetShift)

		self.abort = threading.Event()
		self.pause = threading.Event()
		self.cont = threading.Event()
		self.newtargetshift = threading.Event()
		self.target_type = target_type
		self.targetlistevents = {}
		self.driftedimages = {}

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)

		self.targetwatcherlog = uidata.MessageLog('Messages')

		pausemethod = uidata.Method('Pause', self.pauseTargetListLoop)
		continuemethod = uidata.Method('Continue',
																		self.continueTargetListLoop)
		abortmethod = uidata.Method('Abort', self.abortTargetListLoop)

		targetcontainer = uidata.Container('Target Processing')
		targetcontainer.addObjects((pausemethod, continuemethod, abortmethod))

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((targetcontainer,))

		container = uidata.LargeContainer('Target Watcher')
		container.addObjects((self.targetwatcherlog, controlcontainer,))

		self.uiserver.addObject(container)

	def handleTargetShift(self, ev):
		print 'Handling target shift'
		dataid = ev['dataid']
		driftdata = self.researchByDataID(dataid)
		self.driftedimages = driftdata['shifts']
		print 'Drifted images:', self.driftedimages
		# may be waiting for a requested image shift
		req = driftdata['requested']
		if req:
			self.newtargetshift.set()

	def processData(self, newdata):
		if not isinstance(newdata, data.ImageTargetListData):
			return

		# separate the good targets from the rejects
		targetlist = newdata['targets']
		goodtargets = []
		rejects = []
		for target in targetlist:
			if target['type'] == self.target_type:
				goodtargets.append(target)
			else:
				rejects.append(target)

		print '%s received %d targets, processing %d, passing on %d' \
						% (self.id[-1], len(targetlist), len(goodtargets), len(rejects))

		# republish the rejects and wait for them to complete
		if rejects:
			#print self.id, 'PUBLISHING REJECTS', len(rejects)
			newtargetlist = data.ImageTargetListData(id=self.ID(), targets=rejects)
			self.passTargets(newtargetlist)
			print 'Waiting for passed targets to be processed...'
			rejectstatus = self.waitForRejects()

			# decide whether or not to continue doing the
			# good targets based on result of reject targets
			if rejectstatus != 'success':
				## report my status as reject status
				## may not be a good idea all the time
				## This means if rejects were aborted
				## then this whole target list was aborted
				print 'Passed targets not processed, aborting current target list'
				self.reportTargetListDone(newdata['id'], rejectstatus)
				return

			print 'Passed targets processed, processing current target list'

		# process the good ones
		self.abort.clear()
		self.pause.clear()
		self.cont.clear()
		targetliststatus = 'success'
		ntargets = len(goodtargets)
		for target in goodtargets:
			# abort
			if self.abort.isSet():
				print 'Aborting current target list'
				targetliststatus = 'aborted'
				break

			# if this target is done, skip it
			#print 'TARGET STATUS', target['status']
			if target['status'] == 'done':
				print 'Skipping done target', target['id']
				continue

			print 'Processing target', target['id'],

			try:
				imageid = target['image']['id']
				print 'from source image', imageid
			except (KeyError, TypeError):
				imageid = None
				print

			adjustedtarget = data.AcquisitionImageTargetData(initializer=target,
																												status='processing')
			self.publish(adjustedtarget, database=True, dbforce=True)

			# this while loop allows target to repeat
			process_status = 'repeat'
			while process_status == 'repeat':
				# check if this imageid needs update
				if imageid in self.driftedimages:
					print 'Target has drifted'
#					if self.driftedimages[imageid]:
#						print 'ALREADY HAVE ADJUST'
#					else:
					if not self.driftedimages[imageid]:
						# need to have drift manager do it
						self.newtargetshift.clear()
						ev = event.NeedTargetShiftEvent(imageid=imageid)
						print 'Waiting for adjustment value...',
						self.outputEvent(ev)
						self.newtargetshift.wait()
						print 'done.'
					adjust = self.driftedimages[imageid]
					# perhaps flip
					print 'Adjusting target by (%d, %d)...' % (adjust['rows'],
																											adjust['columns']),
				
					## create new adjusted target from old
					adjustedtarget = \
						data.AcquisitionImageTargetData(initializer=adjustedtarget)
					adjustedtarget['version'] += 1
					adjustedtarget['delta row'] = target['delta row'] + adjust['rows']
					adjustedtarget['delta column'] = target['delta column'] \
																														+ adjust['columns']
					self.publish(adjustedtarget, database=True, dbforce=True)
					print 'done.'
#				else:
#					print 'NOT DRIFTED TARGET'

				# now have processTargetData work on it
				try:
					process_status = self.processTargetData(adjustedtarget)
				except:
					self.printException()
					process_status = 'exception'
				print 'Target processed with status:', process_status

				# pause
				if self.pause.isSet():
					messagestr = 'Pausing current target list...'
					print messagestr
					message = self.targetwatcherlog.information(messagestr)
					self.cont.clear()
					self.cont.wait()
					self.pause.clear()
					print 'done.'
					message.clear()

				# abort
				if self.abort.isSet():
					print 'Aborting current target list'
					break

				# end of target repeat loop

			donetarget = data.AcquisitionImageTargetData(initializer=adjustedtarget,
																										status='done')
			self.publish(donetarget, database=True, dbforce=True)

		self.reportTargetListDone(newdata['id'], targetliststatus)

	def reportTargetListDone(self, listid, status):
		e = event.TargetListDoneEvent(id=self.ID(), targetlistid=listid,
																	status=status)
		self.outputEvent(e)

	def passTargets(self, targetlistdata):
		self.targetlistevents[targetlistdata['id']] = {}
		self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['status'] = 'waiting'
		self.publish(targetlistdata, pubevent=True)

	def waitForRejects(self):
		# wait for focus target list to complete
		#print 'Waiting for passed targets to be processed...'
		for tid, teventinfo in self.targetlistevents.items():
			teventinfo['received'].wait()
		#print 'Done waiting for rejected targets'

		## check status of all target lists
		## all statuses must be success in order for complete success
		status = 'success'
		for tid, teventinfo in self.targetlistevents.items():
			if teventinfo['status'] in ('failed', 'aborted'):
				status = teventinfo['status']
				break
		self.targetlistevents.clear()
		
		return status

	def handleTargetListDone(self, targetlistdoneevent):
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		print 'Got notification target list', targetlistid, 'is done'
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		print 'Aborting current target list after current target is processed'
		self.abort.set()

	def pauseTargetListLoop(self):
		print 'Pausing current target list after current target is processed'
		self.pause.set()

	def continueTargetListLoop(self):
		print 'Continuing processing of current target list'
		self.cont.set()

