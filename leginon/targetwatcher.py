#!/usr/bin/env python

import event, data
import watcher
import threading

class TargetWatcher(watcher.Watcher):
	'''
	TargetWatcher will watch for TargetLists
	It is also initialized with a specific type of target that it can
	process.  All other targets are republished in another target list.
	'''
	def __init__(self, id, session, nodelocations, targetclass=data.ImageTargetData, **kwargs):
		watchfor = event.ImageTargetListPublishEvent
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, lockblocking=0, **kwargs)

		## moved here from acquisition, hope this doesn't break it
		self.addEventInput(event.TargetDoneEvent, self.handleTargetDone)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

		self.abort = threading.Event()
		self.targetclass = targetclass
		#self.targetevents = {}
		self.targetlistevents = {}

	def processData(self, newdata):
		'''
		accepts either ImageTargetData or ImageTargetListData
		'''
		print '###############################################################################'
		print '###############################################################################'
		if not isinstance(newdata, data.ImageTargetListData):
			return 

		### separate the good targets from the rejects
		targetlist = newdata['targets']
		print self.id, 'RECEIVED TARGET LIST', len(targetlist)
		goodtargets = []
		rejects = []
		for target in targetlist:
			if target.__class__ is self.targetclass:
				goodtargets.append(target)
			else:
				rejects.append(target)

		### republish the rejects
		if rejects:
			print self.id, 'PUBLISHING REJECTS', len(rejects)
			newtargetlist = data.ImageTargetListData(id=self.ID(), targets=rejects)
			self.passTargets(newtargetlist)

		### process the good ones
		self.abort.clear()
		print self.id, 'PROCESSING GOOD', len(goodtargets)
		for target in goodtargets:
			print 'STARTING NEW TARGET', target['id']
			print 'python id', id(target)
			print 'target id', target['id']
			print 'target id id', id(target['id'])
			newstatus = self.processTargetData(target)
			print 'NEWSTATUS', newstatus
			e = event.TargetDoneEvent(id=self.ID(), targetid=target['id'], status=newstatus)
			self.outputEvent(e)
			print 'checking abort'
			if self.abort.isSet():
				print 'breaking from targetlist loop'
				break
			print 'not aborted'

	def passTargets(self, targetlistdata):
		## create an event watcher for each target we pass
		#for target in targetlistdata['targets']:
		#	targetid = target['id']
		#	## maybe should check if already waiting on this target?
		#	self.targetevents[targetid] = {}
		#	self.targetevents[targetid]['received'] = threading.Event()
		#	self.targetevents[targetid]['status'] = 'waiting'

		self.targetlistevents[targetlistdata['id']['received'] = threading.Event()
		self.targetlistevents[targetlistdata['id']]['stats'] = 'waiting'
		print 'publishing focustargetdata', targetid
		self.publish(targetlistdata, pubevent=True)

	def OLDhandleTargetDone(self, targetdoneevent):
		targetid = targetdoneevent['targetid']
		status = targetdoneevent['status']
		print 'got targetdone event, setting threading event', targetid
		if targetid in self.targetevents:
			self.targetevents[targetid]['status'] = status
			self.targetevents[targetid]['received'].set()
		self.confirmEvent(targetdoneevent)

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
