import node
import datahandler
import scopedict
import cameradict
import threading
import data
import event
import sys
import imp
import cPickle
if sys.platform == 'win32':
	import pythoncom

class DataHandler(datahandler.DataBinder):
	def __init__(self, id, EMnode):
		datahandler.DataBinder.__init__(self, id)
		self.EMnode = EMnode

	def query(self, id):
		print 'getting stuff'
		stuff = self.EMnode.getEM([id])
		print 'done getting stuff'
		result = data.EMData(self.ID(), stuff)
		return result

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		else:
			self.EMnode.setEM(idata.content)

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class EM(node.Node):
	def __init__(self, id, nodelocations, scope = None, camera = None, **kwargs):
		# internal
		self.lock = threading.Lock()
		# external
		self.nodelock = threading.Lock()
		self.locknodeid = None

		# very temporary
		if scope is None:
			scope = ('tecnai', 'tecnai')
		if camera is None:
			camera = ('gatan', 'gatan')
		self.setEMclasses(scope, camera)

		node.Node.__init__(self, id, nodelocations, DataHandler, (self,), **kwargs)

		self.addEventInput(event.LockEvent, self.doLock)
		self.addEventInput(event.UnlockEvent, self.doUnlock)

		self.defineUserInterface()
		self.start()

	def setEMclasses(self, scope, camera):
		self.scope = self.camera = {}
		if scope[0]:
			fp, pathname, description = imp.find_module(scope[0])
			scopemodule = imp.load_module(scope[0], fp, pathname, description)
			if scope[1]:
				self.scope = scopedict.factory(scopemodule.__dict__[scope[1]])()
		if camera[0]:
			fp, pathname, description = imp.find_module(camera[0])
			cameramodule = imp.load_module(camera[0], fp, pathname, description)
			if camera[1]:
				self.camera = cameradict.factory(cameramodule.__dict__[camera[1]])()

	def main(self):
		self.addEventOutput(event.ListPublishEvent)
		ids = ['scope', 'camera', 'camera no image data', 'all']
		ids += self.scope.keys()
		ids += self.camera.keys()
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

	def exit(self):
		node.Node.exit(self)
		self.scope.exit()
		self.camera.exit()

	def doLock(self, ievent):
		if ievent.id[-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent.id[-1]
		self.confirmEvent(ievent)

	def doUnlock(self, ievent):
		if ievent.id[-1] == self.locknodeid:
			self.locknodeid = None
			self.nodelock.release()

	def getEM(self, withkeys=None, withoutkeys=None):
		self.lock.acquire()
		result = {}
		if withkeys is not None:
			for EMkey in withkeys:
				if EMkey in self.scope:
					try:
						result[EMkey] = self.scope[EMkey]
					except:	
						print "failed to get '%s'" % EMkey
				elif EMkey in self.camera:
					try:
						result[EMkey] = self.camera[EMkey]
					except:	
						print "failed to get '%s'" % EMkey
				elif EMkey == 'scope':
					result.update(self.scope)
				elif EMkey == 'camera no image data':
					for camerakey in self.camera:
						if camerakey != 'image data':
							result[camerakey] = self.camera[camerakey]
				elif EMkey == 'camera':
					result.update(self.camera)
				elif EMkey == 'all':
					result.update(self.scope)
					result.update(self.camera)
		elif withoutkeys is not None:
			if not ('scope' in withoutkeys or 'all' in withoutkeys):
				for EMkey in self.scope:
					if not EMkey in withoutkeys:
						try:
							result[EMkey] = self.scope[EMkey]
						except:	
							print "failed to get '%s'" % EMkey
			if not ('camera' in withoutkeys or 'all' in withoutkeys):
				for EMkey in self.camera:
					if not EMkey in withoutkeys:
						try:
							result[EMkey] = self.camera[EMkey]
						except:	
							print "failed to get '%s'" % EMkey
		else:
			result.update(self.scope)
			result.update(self.camera)

		self.lock.release()
		return result

	def setEM(self, EMstate):
		self.lock.acquire()
		for EMkey in EMstate:
			if EMkey in self.scope:
				try:
					self.scope[EMkey] = EMstate[EMkey]
				except:	
					print "failed to set '%s' to" % EMkey, EMstate[EMkey]
			elif EMkey in self.camera:
				try:
					self.camera[EMkey] = EMstate[EMkey]
				except:	
					print "failed to set '%s' to" % EMkey, EMstate[EMkey]
		self.lock.release()

	def save(self, filename):
		print "Saving state to file: %s..." % filename,
		try:
			f = file(filename, 'w')
			savestate = self.getEM(withoutkeys=['image data'])
			cPickle.dump(savestate, f)
			f.close()
		except:
			print "Error: failed to save EM state"
			raise
		else:
			print "done."
		return ''

	def load(self, filename):
		print "Loading state from file: %s..." % filename,
		try:
			f = file(filename, 'r')
			loadstate = cPickle.load(f)
			self.setEM(loadstate)
			f.close()
		except:
			print "Error: failed to load EM state"
			raise
		else:
			print "done."
		return ''

	def uiCallback(self, value=None):
		if value is not None:
			return self.setEM(value)
		else:
			return self.getEM(withoutkeys=['image data'])

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		statespec = self.registerUIData('EM State', 'struct', permissions='rw', callback=self.uiCallback)

		argspec = (self.registerUIData('Filename', 'string'),)
		savespec = self.registerUIMethod(self.save, 'Save', argspec)
		loadspec = self.registerUIMethod(self.load, 'Load', argspec)

		filespec = self.registerUIContainer('File', (savespec, loadspec))

		self.registerUISpec('EM', (statespec, filespec, nodespec))

