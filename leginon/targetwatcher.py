#!/usr/bin/env python

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

	eventinputs = watcher.Watcher.eventinputs + [event.TargetListDoneEvent, event.ImageTargetListPublishEvent, event.ImageTargetShiftPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.TargetListDoneEvent, event.ImageTargetListPublishEvent, event.NeedTargetShiftEvent]

	def __init__(self, id, session, nodelocations, targetclass=data.AcquisitionImageTargetData, **kwargs):
		watchfor = [event.ImageTargetListPublishEvent]
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, **kwargs)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.addEventInput(event.ImageTargetShiftPublishEvent, self.handleTargetShift)

		self.abort = threading.Event()
		self.pause = threading.Event()
		self.cont = threading.Event()
		self.newtargetshift = threading.Event()
		self.driftedimages = {}
		self.targetclass = targetclass
		#self.targetevents = {}
		self.targetlistevents = {}
		self.driftedimages = {}

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)

		pausemethod = uidata.Method('Pause', self.pauseTargetListLoop)
		continuemethod = uidata.Method('Continue',
																		self.continueTargetListLoop)
		abortmethod = uidata.Method('Abort', self.abortTargetListLoop)

		targetcontainer = uidata.Container('Target Processing')
		targetcontainer.addObjects((pausemethod, continuemethod, abortmethod))

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((targetcontainer,))

		container = uidata.MediumContainer('Target Watcher')
		container.addObjects((controlcontainer,))

		self.uiserver.addObject(container)

	def handleTargetShift(self, ev):
		print 'HANDLING TARGET SHIFT'
		dataid = ev['dataid']
		driftdata = self.researchByDataID(dataid)
		self.driftedimages = driftdata['shifts']
		print 'DRIFTED IMAGES', self.driftedimages
		# may be waiting for a requested image shift
		req = driftdata['requested']
		if req:
			self.newtargetshift.set()

	def processData(self, newdata):
		if not isinstance(newdata, data.ImageTargetListData):
			return 

		### separate the good targets from the rejects
		targetlist = newdata['targets']
		print self.id, 'RECEIVED TARGET LIST', len(targetlist)
		goodtargets = []
		rejects = []
		for target in targetlist:
			if target.__class__ is self.targetclass:
				print 'GOOD', target['id'], target.__class__
				goodtargets.append(target)
			else:
				print 'REJECT', target['id'], target.__class__
				rejects.append(target)

		### republish the rejects and wait for them to complete
		if rejects:
			print self.id, 'PUBLISHING REJECTS', len(rejects)
			newtargetlist = data.ImageTargetListData(id=self.ID(), targets=rejects)
			self.passTargets(newtargetlist)
			rejectstatus = self.waitForRejects()

			# decide whether or not to continue doing the
			# good targets based on result of reject targets
			if rejectstatus is not 'success':
				## report my status as reject status
				## may not be a good idea all the time
				## This means if rejects were aborted
				## then this whole target list was aborted
				self.reportTargetListDone(newdata['id'], rejectstatus)
				return

		### process the good ones
		self.abort.clear()
		self.pause.clear()
		self.cont.clear()
		targetliststatus = 'success'
		ntargets = len(goodtargets)
		for target in goodtargets:
			print 'STARTING NEW TARGET', target['id']
			print 'python id', id(target)
			print 'target id', target['id']
			print 'target id id', id(target['id'])
			try:
				imageid = target['image']['id']
				print 'TARGET SOURCE IMAGE', imageid
			except (KeyError, TypeError):
				imageid = None

			while 1:
				## check if this imageid needs update
				if imageid in self.driftedimages:
					print 'DRIFTED IMAGE TARGET'
					if self.driftedimages[imageid]:
						adjust = self.driftedimages[imageid]
						print 'ALREADY HAVE ADJUST', adjust
					else:
						## need to have drift manager do it
						self.newtargetshift.clear()
						ev = event.NeedTargetShiftEvent(imageid=imageid)
						print 'NEED ADJUST'
						self.outputEvent(ev)
						self.newtargetshift.wait()
						adjust = self.driftedimages[imageid]
						print 'GOT ADJUST', adjust
				else:
					adjust = {'rows':0, 'columns':0}
					print 'NOT DRIFTED TARGET', adjust
	
				## apply updated
				print 'TARGET WAS R,C', target['delta row'], target['delta column']
				target['delta row'] += adjust['rows']
				target['delta column'] += adjust['columns']

				print 'TARGET IS NOW R,C', target['delta row'], target['delta column']
	
				try:
					process_status = self.processTargetData(target)
				except:
					self.printException()
					process_status = 'exception'
	
				print 'TARGET FINISHED STATUS', process_status
				print 'checking pause'
				if self.pause.isSet():
					print 'pausing'
					self.cont.clear()
					self.cont.wait()
					self.pause.clear()
					print 'done pausing'
				print 'checking abort'
				if self.abort.isSet():
					print 'breaking from repeat loop'
					break
				print 'not aborted'

				if process_status != 'repeat':
					break

			if self.abort.isSet():
				print 'breaking from targetlist loop'
				targetliststatus = 'aborted'
				break

		self.reportTargetListDone(newdata['id'], targetliststatus)

	def reportTargetListDone(self, listid, status):
		e = event.TargetListDoneEvent(id=self.ID(), targetlistid=listid, status=status)
		self.outputEvent(e)

	def passTargets(self, targetlistdata):
		## create an event watcher for each target we pass
		#for target in targetlistdata['targets']:
		#	targetid = target['id']
		#	## maybe should check if already waiting on this target?
		#	self.targetevents[targetid] = {}
		#	self.targetevents[targetid]['received'] = threading.Event()
		#	self.targetevents[targetid]['status'] = 'waiting'

		self.targetlistevents[targetlistdata['id']] = {}
		self.targetlistevents[targetlistdata['id']]['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['status'] = 'waiting'
		self.publish(targetlistdata, pubevent=True)

	def waitForRejects(self):
		# wait for focus target list to complete
		print 'waiting for rejected targets to complete...'
		for tid, teventinfo in self.targetlistevents.items():
			teventinfo['received'].wait()
		print 'done waiting for rejected targets'

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
		print 'got targetlistdone event, setting threading event', targetlistid
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		print 'will abort target list loop after current target'
		self.abort.set()

	def pauseTargetListLoop(self):
		print 'will pause target list loop after current target'
		self.pause.set()

	def continueTargetListLoop(self):
		print 'continuing loop'
		self.cont.set()
