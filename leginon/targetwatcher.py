#!/usr/bin/env python

import event, data
import watcher

class TargetWatcher(watcher.Watcher):
	def __init__(self, id, nodelocations, **kwargs):
		watchfor = event.ImageTargetListPublishEvent
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking=0, **kwargs)

	def processData(self, newdata):
		targetlist = newdata.content
		for target in targetlist:
			self.processTargetData(target)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def defineUserInterface(self):
		return watcher.Watcher.defineUserInterface(self)


