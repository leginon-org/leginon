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

class DataHandler(datahandler.DataHandler):
	def __init__(self, scope, camera, lock):
		datahandler.DataHandler.__init__(self)
		self.lock = lock
		self.scope = scope
		self.camera = camera

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
		self.lock.acquire()
		if(self.scope.has_key(newdata.id)):
			self.scope[newdata.id] = newdata.content
		elif(self.camera.has_key(newdata.id)):
			self.camera[newdata.id] = newdata.content
		self.lock.release()

class DataServer(dataserver.DataServer):
	def __init__(self, scopeclass, cameraclass):
		dataserver.DataServer.__init__(self)
		self.lock = threading.RLock()
		self.scope = scopedict.factory(scopeclass)()
		self.camera = cameradict.factory(cameraclass)()
		self.pushserver = clientpush.Server(DataHandler, (self.scope, self.camera, self.lock))
		self.pullserver = clientpull.Server(DataHandler, (self.scope, self.camera, self.lock))

