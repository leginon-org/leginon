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
import dbdatakeeper
import strictdict
import copy
import time

if sys.platform == 'win32':
	import pythoncom

#class DataHandler(datahandler.DataBinder):
class DataHandler(node.DataHandler):
	def query(self, id):
		emkey = id[0]
		stuff = self.node.getEM([emkey])

		if emkey == 'scope':
			result = data.ScopeEMData(self.ID(), initializer=stuff)
		elif emkey == 'camera':
			result = data.CameraEMData(self.ID(), initializer=stuff)
		elif emkey == 'all':
			result = data.AllEMData(self.ID(), initializer=stuff)
		else:
			### could be either CameraEMData or ScopeEMData
			newid = self.ID()
			for dataclass in (data.ScopeEMData,data.CameraEMData):
				tryresult = dataclass(newid)
				try:
					tryresult.update(stuff)
					result = tryresult
					break
				except KeyError:
					result = None
		return result

	def insert(self, idata):
		if isinstance(idata, data.EMData):
			print idata['id'][:-1], 'attempting to set EM'
			self.node.setEM(idata)
			print idata['id'][:-1], 'EM set'
		else:
			node.DataHandler.insert(self, idata)
			

class EM(node.Node):
	def __init__(self, id, session, nodelocations,
								scope = None, camera = None, **kwargs):
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

		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

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
		for i in range(len(ids)):
			ids[i] = (ids[i],)
		e = event.ListPublishEvent(self.ID(), idlist=ids)
		self.outputEvent(e, wait=True)
		self.outputEvent(event.NodeInitializedEvent(self.ID()))

	def exit(self):
		node.Node.exit(self)
		self.scope.exit()
		self.camera.exit()

	def doLock(self, ievent):
		print 'EM do lock'
		if ievent['id'][:-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent['id'][:-1]
			print self.locknodeid, 'acquired EM lock'
		self.confirmEvent(ievent)

	def doUnlock(self, ievent):
		print 'EM do unlock'
		if ievent['id'][:-1] == self.locknodeid:
			print self.locknodeid, 'releasing EM lock'
			self.locknodeid = None
			self.nodelock.release()

	### now this is handled by EMData
	def OLDpruneEMdict(self, emdict):
		'''
		restrict access to certain scope parameters
		'''
		prunekeys = (
			'gun shift',
			'gun tilt',
			'high tension',
			'beam blank',
			'dark field mode',
			'diffraction mode',
			'low dose',
			'low dose mode',
			'screen current',
		)

		for key in prunekeys:
			try:
				del emdict[key]
			except KeyError:
				pass

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
		#self.pruneEMdict(result)
		result['system time'] = time.time()
		return result

	def OLDsortEMdict(self, emdict):
		'''
		sort items in em dict for proper setting order
		'''
		olddict = copy.deepcopy(emdict)
		newdict = strictdict.OrderedDict()

		### I care about these, the rest don't matter
		order = (
			'magnification',
			'spot size',
			'image shift',
			'beam shift',
			'defocus',
			'reset defocus',
			'intensity',
		)
		for key in order:
			try:
				newdict[key] = olddict[key]
				del olddict[key]
			except KeyError:
				pass

		## the rest don't matter
		newdict.update(olddict)
		return newdict

	def setEM(self, emstate):
		self.lock.acquire()

		### order the items in EMstate
		#ordered = self.sortEMdict(EMstate)

		#for EMkey in ordered.keys():
		for emkey, emvalue in emstate.items():
			if emvalue is None:
				continue
			if emkey in self.scope:
				try:
					self.scope[emkey] = emvalue
				except:	
					print "failed to set '%s' to %s" % (emkey, emvalue)
					pass
			elif emkey in self.camera:
				try:
					self.camera[emkey] = emvalue
				except:	
					#print "failed to set '%s' to" % EMkey, EMstate[EMkey]
					pass
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
			if self.uistate is not None:
				for key in self.uistate.keys():
					if key in value and value[key] != self.uistate[key]:
						print 'setting', key
						self.setEM({key: value[key]})
			else:
				self.setEM(value)
		emdict = self.getEM(withoutkeys=['image data'])
		self.uistate = self.sortEMdict(emdict)
		return emdict

	def uiUnlock(self):
		self.locknodeid = None
		self.nodelock.release()

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.uistate = None
		statespec = self.registerUIData('EM State', 'struct', permissions='rw', callback=self.uiCallback)

		argspec = (self.registerUIData('Filename', 'string'),)
		savespec = self.registerUIMethod(self.save, 'Save', argspec)
		loadspec = self.registerUIMethod(self.load, 'Load', argspec)

		filespec = self.registerUIContainer('File', (savespec, loadspec))
		unlockspec = self.registerUIMethod(self.uiUnlock, 'Unlock', ())

		myspec = self.registerUISpec('EM', (statespec, unlockspec, filespec))
		myspec += nodespec
		return myspec
