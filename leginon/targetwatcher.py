#!/usr/bin/env python

import event, data
import watcher
import threading

class TargetWatcher(watcher.Watcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = event.ImageTargetListPublishEvent
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, lockblocking=0, **kwargs)
		self.abort = threading.Event()

	def processData(self, newdata):
		'''
		accepts either ImageTargetData or ImageTargetListData
		'''
		print '###############################################################################'
		print '###############################################################################'
		if not isinstance(newdata, data.ImageTargetListData):
			return 

		targetlist = newdata['targets']
		self.abort.clear()
		for target in targetlist:
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

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		print 'will abort target list loop after current target'
		self.abort.set()
