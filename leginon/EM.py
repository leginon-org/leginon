#!/usr/bin/env python
import node
import datahandler
import scopedict
import cameradict
import threading
import data
# this is so the COM stuff will work
# I don't know if this is a good place for it, perhaps the caller is
import sys
if sys.platform == 'win32':
	sys.coinit_flags = 0
	import pythoncom

class DataHandler(datahandler.DataBinder):
	def __init__(self, lock, scope, camera):
		datahandler.DataBinder.__init__(self)
		self.lock = lock
		self.scope = scope
		self.camera = camera

	def query(self, id):
		self.lock.acquire()
		if self.scope and self.scope.has_key(id):
			result = data.EMData({id : self.scope[id]})
		elif self.camera and self.camera.has_key(id):
			result = data.EMData({id : self.camera[id]})
		elif id == 'scope':
			result = data.EMData(self.scope)
		elif id == 'camera':
			result = data.EMData(self.camera)
		elif id == 'all':
			result = data.EMData({})
			result.content.update(self.scope)
			result.content.update(self.camera)
		else:
			result = None
		self.lock.release()
		return result

	def insert(self, newdata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			self.lock.acquire()
			if self.scope and self.scope.has_key(newdata.id):
				self.scope[newdata.id] = newdata.content
			elif self.camera and self.camera.has_key(newdata.id):
				self.camera[newdata.id] = newdata.content
			self.lock.release()

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class EM(node.Node):
	def __init__(self, nodeid, managerloc, scopeclass = None, cameraclass = None):
		self.lock = threading.Lock()
		if scopeclass:
			self.scope = scopedict.factory(scopeclass)()
		else:
			self.scope = None
		if cameraclass:
			self.camera = cameradict.factory(cameraclass)()
		else:
			self.camera = None

		node.Node.__init__(self, nodeid, managerloc, DataHandler, (self.lock, self.scope, self.camera))

if __name__ == '__main__':
	import time
	import tecnai
	import tietz

	foo = EM('myEM', {'hostname' : 'cronus1', 'TCP port' : 49152}, tecnai.tecnai, tietz.tietz)
	while(1):
		time.sleep(.01)

