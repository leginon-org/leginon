#!/usr/bin/env python

import imagewatcher

class ImViewer(imagewatcher.ImageWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		imwatch = imagewatcher.ImageWatcher.defineUserInterface(self)
		print 'imwatch', imwatch
		myspec = self.registerUISpec('ImViewer', ())
		print 'myspec', myspec
		myspec += imwatch
