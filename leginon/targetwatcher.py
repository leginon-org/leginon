#!/usr/bin/env python

import event, data
import watcher
import threading

class TargetWatcher(watcher.Watcher):
	def __init__(self, id, nodelocations, **kwargs):
		watchfor = event.ImageTargetListPublishEvent
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking=0, **kwargs)
		self.abort = threading.Event()

	def processData(self, newdata):
		'''
		accepts either ImageTargetData or ImageTargetListData
		'''
		if isinstance(newdata, data.ImageTargetData):
			self.processTargetData(newdata)
		elif isinstance(newdata, data.ImageTargetListData):
			targetlist = newdata.content
			print 'TARGETLIST len', len(targetlist)
			self.abort.clear()
			for target in targetlist:
				print 'targetid', target.id
				self.processTargetData(target)
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
