import dataserver
import datahandler
import scopedict
import cameradict
import clientpush
import clientpull
import threading
# this is so the COM stuff will work
# I don't know if this is a good place for it, perhaps the caller is
import sys
if sys.platform == 'win32':
	sys.coinit_flags = 0
	import pythoncom

class DataHandler(datahandler.DataBinder):
	def __init__(self, scope, camera, lock):
		datahandler.DataBinder.__init__(self)
		self.scope = scope
		self.camera = camera
		self.lock = lock

	def query(self, id):
		self.lock.acquire()
		if(self.scope.has_key(id)):
			result = self.scope[id]
		elif(self.camera.has_key(id)):
		  result = self.camera[id]
		else:
			result = None
		self.lock.release()
		return result

	def insert(self, newdata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			self.lock.acquire()
			if(self.scope.has_key(newdata.id)):
				self.scope[newdata.id] = newdata.content
			elif(self.camera.has_key(newdata.id)):
				self.camera[newdata.id] = newdata.content
			self.lock.release()

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class DataServer(dataservernode.DataServerNode):
	def __init__(self, nodeid, managerloc, scopeclass, cameraclass):
		self.lock = threading.Lock()
		self.scope = scopedict.factory(scopeclass)()
		self.camera = cameradict.factory(cameraclass)()

		dataserver.DataServer.__init__(self, nodeid, managerloc, DataHandler, (self.scope, self.camera, self.lock))

