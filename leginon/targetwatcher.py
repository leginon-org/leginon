#!/usr/bin/env python

import event, data
import watcher
import threading

class TargetWatcher(watcher.Watcher):
	def __init__(self, id, session, nodelocations, targetclass=data.ImageTargetData, **kwargs):
		watchfor = event.ImageTargetListPublishEvent
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, lockblocking=0, **kwargs)

		## moved here from acquisition, hope this doesn't break it
		self.addEventInput(event.TargetDoneEvent, self.handleTargetDone)

		self.abort = threading.Event()
		self.targetclass = targetclass
		self.targetevents = {}

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
		goodtargets = []
		rejects = []
		for target in targetlist:
			if target.__class__ is self.targetclass:
				goodtargets.append(target)
			else:
				rejects.append(target)

		### republish the rejects
		if rejects:
			newtargetlist = data.ImageTargetListData(self.ID(), targets=rejects)
			self.passTargets(newtargetlist)

		### process the good ones
		self.abort.clear()
		for target in goodtargets:
			print 'python id', id(target)
			print 'target id', target['id']
			print 'target id id', id(target['id'])
			self.processTargetData(target)
			e = event.TargetDoneEvent(self.ID(), targetid=target['id'])
			self.outputEvent(e)
			print 'checking abort'
			if self.abort.isSet():
				print 'breaking from targetlist loop'
				break
			print 'not aborted'

	def passTargets(self, targetlistdata):
		## create an event watcher for each target we pass
		for target in targetlistdata['targets']:
			targetid = target['id']
			## maybe should check if already waiting on this target?
			self.targetevents[targetid] = threading.Event()
			print 'publishing focustargetdata', targetid
			self.publish(targetlistdata, pubevent=True)

	def handleTargetDone(self, targetdoneevent):
		targetid = targetdoneevent['targetid']
		print 'got targetdone event, setting threading event', targetid
		if targetid in self.targetevents:
			self.targetevents[targetid].set()
		self.confirmEvent(targetdoneevent)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		print 'will abort target list loop after current target'
		self.abort.set()
