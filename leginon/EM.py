#!/usr/bin/env python
import node
import datahandler
import scopedict
import cameradict
import threading
import data
import event
import sys
if sys.platform == 'win32':
	import pythoncom

class DataHandler(datahandler.DataBinder):
	def __init__(self, id, lock, scope, camera, EMnode):
		datahandler.DataBinder.__init__(self, id)
		self.lock = lock
		self.scope = scope
		self.camera = camera
		self.EMnode = EMnode

	def query(self, id):
		self.lock.acquire()
		if self.scope and self.scope.has_key(id):
			result = data.EMData(self.ID(), {id : self.scope[id]})
		elif self.camera and self.camera.has_key(id):
			result = data.EMData(self.ID(), {id : self.camera[id]})
		elif self.scope and id == 'scope':
			result = data.EMData(self.ID(), self.scope)
		elif self.camera and id == 'camera':
			result = data.EMData(self.ID(), self.camera)
		elif id == 'all':
			result = data.EMData(self.ID(), {})
			if self.scope:
				result.content.update(self.scope)
			if self.camera:
				result.content.update(self.camera)
		else:
			result = None

		self.lock.release()
		return result

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			self.lock.acquire()
			for id in idata.content:
				if self.scope and self.scope.has_key(id):
					print id, idata.content
					self.scope[id] = idata.content[id]
				elif self.camera and self.camera.has_key(id):
					self.camera[id] = idata.content[id]
			self.lock.release()

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class EM(node.Node):
	def __init__(self, id, managerloc, scopeclass = None, cameraclass = None):
		# internal
		self.lock = threading.Lock()
		# external
		self.nodelock = threading.Lock()
		self.locknodeid = None

		if scopeclass:
			self.scope = scopedict.factory(scopeclass)()
		else:
			self.scope = None
		if cameraclass:
			self.camera = cameradict.factory(cameraclass)()
		else:
			self.camera = None

		node.Node.__init__(self, id, managerloc, DataHandler, (self.lock, self.scope, self.camera, self))

		self.addEventInput(event.LockEvent, self.lock)
		self.addEventInput(event.UnlockEvent, self.unlock)

		self.start()

	def main(self):
		self.addEventOutput(event.ListPublishEvent)
		ids = []
		if self.scope:
			ids.append('scope')
			ids += self.scope.keys()
		if self.camera:
			ids.append('camera')
			ids += self.camera.keys()
		if self.scope and self.camera:
			ids.append('all')

		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

	def lock(self, ievent):
		if ievent.id[-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent.id[-1]
		self.confirmEvent(ievent)

	def unlock(self, ievent):
		if ievent.id[-1] == self.locknodeid:
			self.locknodeid = None
			self.nodelock.release()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		argspec = (
			{'name': 'parameter', 'alias': 'Parameter', 'type': {'test': 2, 'foo': {'bar': 1}}},)
		self.registerUIFunction(self.foo, argspec, 'Foo')

	def foo(self):
		pass

if __name__ == '__main__':
	import time
	import tecnai
	import tietz

	foo = EM('myEM', {'hostname' : 'cronus1', 'TCP port' : 49152}, tecnai.tecnai, tietz.tietz)
	while(1):
		time.sleep(.01)

