import leginonconfig
import node
import datahandler
import scopedict
import cameradict
import threading
import data
import event
import sys
import imp
import strictdict
import copy
import time
import uidata
import Queue
import emregistry

#if sys.platform == 'win32':
#	sys.coinit_flags = 0
#	import pythoncom

# These keys are not included in a get all parameters
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
	'holder type',
	'holder status',
	'stage status',
	'vacuum status',
	'column valves',
	'turbo pump',
	'column pressure',
	'inserted',
)

def unique(s):
	n = len(s)
	if n == 0:
		return []

	u = {}
	try:
		for x in s:
			u[x] = 1
	except TypeError:
		del u  # move on to the next method
	else:
		return u.keys()

	try:
		t = list(s)
		t.sort()
	except TypeError:
		del t  # move on to the next method
	else:
		assert n > 0
		last = t[0]
		lasti = i = 1
		while i < n:
			if t[i] != last:
				t[lasti] = last = t[i]
				lasti += 1
			i += 1
		return t[:lasti]

	u = []
	for x in s:
		if x not in u:
			u.append(x)
	return u

class DataHandler(node.DataHandler):
	def query(self, id):
		emkey = id[0]
		self.node.statelock.acquire()
		done_event = threading.Event()
		self.node.requestqueue.put(Request(done_event, [emkey]))
		done_event.wait()
		stuff = self.node.state

		if emkey == 'scope':
			result = data.ScopeEMData(id=('scope',))
			result.friendly_update(stuff)
		elif emkey in ('camera', 'camera no image data'):
			result = data.CameraEMData(id=('camera',))
			# this is a fix for the bigger problem of always 
			# setting defocus
			result.friendly_update(stuff)
		elif emkey == 'all em':
			result = data.AllEMData(id=('all em',))
			result.friendly_update(stuff)
		else:
			### could be either CameraEMData or ScopeEMData
			newid = self.ID()
			trydatascope = data.ScopeEMData(id=('scope',))
			trydatacamera = data.CameraEMData(id=('camera',))
			for trydata in (trydatascope, trydatacamera):
				try:
					trydata.update(stuff)
					result = trydata
					break
				except KeyError:
					result = None

		self.node.uiUpdate()
		self.node.statelock.release()
		return result

	def insert(self, idata):
		if isinstance(idata, data.EMData):
			self.node.statelock.acquire()
			done_event = threading.Event()
			#self.node.requestqueue.put(Request(done_event, idata['em']))
			# this converts Data to a dict, and deletes items
			# that are None.  This saves us some time because
			# queueHandler will not only setEM, but getEM on
			# all keys we give it, even if values are None
			d = idata.toDict(noNone=True)
			# also delete these, which are not understood by
			# pyScope, or are read only
			for key in ('id','session','system time', 'image data'):
				try:
					del d[key]
				except KeyError:
					pass

			self.node.requestqueue.put(Request(done_event, d))
			done_event.wait()
			self.node.uiUpdate()
			self.node.statelock.release()
		else:
			node.DataHandler.insert(self, idata)


class Request(object):
	def __init__(self, ievent, value):
		self.event = ievent
		self.value = value

class EM(node.Node):
	eventinputs = node.Node.eventinputs + [event.LockEvent, event.UnlockEvent]
	eventoutputs = node.Node.eventoutputs + [event.ListPublishEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		# the queue of requests to get and set parameters
		self.requestqueue = Queue.Queue()

		# external lock for nodes keep EM for themself
		self.nodelock = threading.Lock()
		self.locknodeid = None

		node.Node.__init__(self, id, session, nodelocations,
												datahandler=DataHandler, **kwargs)

		# get the scope module and class from the database
		try:
			scopename = self.session['instrument']['scope']
		except (TypeError, KeyError):
			# no scope is associated with this session
			print 'no scope is associated with this session'
			scopename = None

		# get the camera module and class from the database
		try:
			cameraname = self.session['instrument']['camera']
		except (TypeError, KeyError):
			# no camera is associated with this session
			print 'no camera is associated with this session'
			cameraname = None

		# add event inputs for locking and unlocking EM from a node
		self.addEventInput(event.LockEvent, self.doLock)
		self.addEventInput(event.UnlockEvent, self.doUnlock)

		# state tracks always keeps the current (known by EM) and compares
		# to changes in the UI state in order to only change parameters that
		# the user has modified (to save time)
		self.statelock = threading.RLock()
		self.state = {}

		# the handler thread waits for queue requests and processes them
		# scope and camera are typically COM objects and need to be intialized
		# in this thread
		self.handlerthread = threading.Thread(name='EM handler thread',
																					target=self.handler,
																					args=(scopename, cameraname))
		self.handlerthread.setDaemon(1)
		self.handlerthread.start()

		self.start()

	def handler(self, scopename, cameraname):
		self.scope = {}
		self.camera = {}

		if scopename is not None:
			self.setScopeType(scopename)
		if cameraname is not None:
			self.setCameraType(cameraname)

		ids = ['scope', 'camera', 'camera no image data', 'all em']
		ids += self.scope.keys()
		ids += self.camera.keys()
		for i in range(len(ids)):
			ids[i] = (ids[i],)

		self.uistate = {}
		self.defineUserInterface()

		self.state = self.getEM(self.uiscopedict.keys() + self.uicameradict.keys())
		self.uiUpdate()

		e = event.ListPublishEvent(id=self.ID(), idlist=ids)
		self.outputEvent(e, wait=True)
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))

		self.queueHandler()

	def getClass(self, modulename, classname):
		if modulename and classname:
			fp, pathname, description = imp.find_module(modulename)
			module = imp.load_module(modulename, fp, pathname, description)
			try:
				return module.__dict__[classname]
			except:
				pass
		return None

	def setScopeType(self, scopename):
		modulename, classname, d = emregistry.getScopeInfo(scopename)
		try:
			scopeclass = self.getClass(modulename, classname)
			self.scope = scopedict.factory(scopeclass)()
		except Exception, e:
			print 'cannot set scope to type', scopename
			print e

	def setCameraType(self, cameraname):
		modulename, classname, d = emregistry.getCameraInfo(cameraname)
		try:
			cameraclass = self.getClass(modulename, classname)
			self.camera = cameradict.factory(cameraclass)()
		except Exception, e:
			print 'cannot set camera to type', cameraname
			print e

	def main(self):
		pass

	def exit(self):
		try:
			self.scope.exit()
		except AttributeError:
			pass
		try:
			self.camera.exit()
		except AttributeError:
			pass
		node.Node.exit(self)

	def doLock(self, ievent):
		if ievent['id'][:-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent['id'][:-1]
		self.confirmEvent(ievent)

	def doUnlock(self, ievent):
		if ievent['id'][:-1] == self.locknodeid:
			self.locknodeid = None
			self.nodelock.release()
		self.confirmEvent(ievent)

	def getEM(self, withkeys=[], withoutkeys=[]):
		result = {}

		if not withkeys and withoutkeys:
			withkeys = ['all em']

		for key in withkeys:
			if key == 'scope':
				withkeys.remove(key)
				scopekeys = self.scope.keys()
				for prunekey in prunekeys:
					try:
						scopekeys.remove(prunekey)
					except ValueError:
						pass
				withkeys += scopekeys
			elif key == 'camera':
				withkeys.remove(key)
				withkeys += self.camera.keys()
			elif key == 'camera no image data':
				withkeys.remove(key)
				keys = self.camera.keys()
				try:
					keys.remove('image data')
				except ValueError:
					pass
				withkeys += keys
			elif key == 'all em':
				withkeys.remove(key)
				withkeys += self.scope.keys()
				withkeys += self.camera.keys()

		withkeys = unique(withkeys)

		for key in withoutkeys:
			if key == 'scope':
				withoutkeys.remove(key)
				withoutkeys += self.scope.keys()
			elif key == 'camera':
				withoutkeys.remove(key)
				withoutkeys += self.camera.keys()
			elif key == 'camera no image data':
				withoutkeys.remove(key)
				keys = self.camera.keys()
				try:
					keys.remove('image data')
				except KeyError:
					pass
				withoutkeys += keys
			elif key == 'all em':
				withoutkeys.remove(key)
				withoutkeys += self.scope.keys()
				withoutkeys += self.camera.keys()

		for key in withoutkeys:
			try:
				withkeys.remove(key)
			except ValueError:
				pass

		scopekeys = self.scope.keys()
		camerakeys = self.camera.keys()
		for key in withkeys:
			if key in scopekeys:
				result[key] = self.scope[key]
			elif key in camerakeys:
				result[key] = self.camera[key]
			else:
				pass

		result['system time'] = time.time()

		return result

	def sortEMdict(self, emdict):
		'''
		sort items in em dict for proper setting order
		'''
		olddict = copy.deepcopy(emdict)
		newdict = strictdict.OrderedDict()

		# The order of the following keys matters
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

		# the rest don't matter
		newdict.update(olddict)
		return newdict

	def setEM(self, emstate):
		# order the items in emstate
		ordered = self.sortEMdict(emstate)

		scopekeys = self.scope.keys()
		camerakeys = self.camera.keys()
		for emkey, emvalue in ordered.items():
			if emvalue is not None:
				if emkey in scopekeys:
					try:
						self.scope[emkey] = emvalue
					except:	
						print "failed to set '%s' to %s" % (emkey, emvalue)
						self.printException()
				elif emkey in camerakeys:
					try:
						self.camera[emkey] = emvalue
					except:	
						print "failed to set '%s' to" % EMkey, EMstate[EMkey]
						self.printException()

	# needs to have statelock locked
	def uiUpdate(self):
		self.uiSetDictData(self.uiscopedict, self.state)
		self.uistate.update(self.uiGetDictData(self.uiscopedict))
		self.uiSetDictData(self.uicameradict, self.state)
		self.uistate.update(self.uiGetDictData(self.uicameradict))

	def uiSetState(self, setdict):
		request = {}
		for key in setdict:
			if key not in self.uistate or self.uistate[key] != setdict[key]:
				request[key] = setdict[key]

		if not request:
			return

		self.statelock.acquire()
		done_event = threading.Event()
		self.requestqueue.put(Request(done_event, request))
		done_event.wait()
		self.statelock.release()

	def queueHandler(self):
		while True:
			request = self.requestqueue.get()
			if isinstance(request.value, dict):
				self.setEM(request.value)
				self.state = self.getEM(request.value.keys())
			else:
				self.state = self.getEM(request.value)
			self.uiUpdate()
			request.event.set()

	def uiUnlock(self):
		self.locknodeid = None
		self.nodelock.release()

	def uiResetDefocus(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		self.uiSetState({'reset defocus': 1})
		self.statelock.acquire()
		done_event = threading.Event()
		self.requestqueue.put(Request(done_event, ['defocus']))
		done_event.wait()
		self.statelock.release()
		self.cameracontainer.enable()
		self.scopecontainer.enable()

	def uiToggleMainScreen(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		try:
			uiscreenposition = self.uiscopedict['screen position'].get()
		except KeyError:
			return
		if uiscreenposition == 'down':
			self.uiSetState({'screen position': 'up'})
		elif uiscreenposition == 'up':
			self.uiSetState({'screen position': 'down'})
		self.cameracontainer.enable()
		self.scopecontainer.enable()

	def uiRefreshScope(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		self.statelock.acquire()
		done_event = threading.Event()
		request = self.uiGetDictData(self.uiscopedict).keys()
		self.requestqueue.put(Request(done_event, request))
		done_event.wait()
		self.statelock.release()
		self.cameracontainer.enable()
		self.scopecontainer.enable()

	def uiSetScope(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		scopedict = self.uiGetDictData(self.uiscopedict)
		updatedstate = self.uiSetState(scopedict)
		self.cameracontainer.enable()
		self.scopecontainer.enable()

	def uiSetCamera(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		cameradict = self.uiGetDictData(self.uicameradict)
		updatedstate = self.uiSetState(cameradict)
		self.cameracontainer.enable()
		self.scopecontainer.enable()

	def uiGetDictData(self, uidict):
		uidictdata = {}
		for key, value in uidict.items():
			if isinstance(value, uidata.Data):
				uidictdata[key] = value.get()
#			elif isinstance(value, dict):
			else:
				uidictdata[key] = self.uiGetDictData(value)
		return uidictdata

	def uiSetDictData(self, uidict, dictdata):
		for key, value in uidict.items():
			if key in dictdata:
				if isinstance(value, uidata.Data):
					value.set(dictdata[key])
#				elif isinstance(value, dict):
				else:
					self.uiSetDictData(value, dictdata[key])

	def getDictStructure(self, dictionary):
		return self.keys()

	def cameraInterface(self):
		self.camera.keys()
		self.uicameradict = {}
		cameraparameterscontainer = uidata.Container('Parameters')

		parameters = [('exposure time', 'Exposure time', uidata.Float, 'rw')]

		for key, name, datatype, permissions in parameters:
			self.uicameradict[key] = datatype(name, None, permissions)
			cameraparameterscontainer.addObject(self.uicameradict[key])

		pairs = [('dimension', 'Dimension', ['x', 'y'], uidata.Integer),
							('offset', 'Offset', ['x', 'y'], uidata.Integer),
							('binning', 'Binning', ['x', 'y'], uidata.Integer)]

		for key, name, axes, datatype in pairs:
			self.uicameradict[key] = {}
			container = uidata.Container(name)
			for axis in axes:
				self.uicameradict[key][axis] = datatype(axis, 0, 'rw')
				container.addObject(self.uicameradict[key][axis])
			cameraparameterscontainer.addObject(container)

		self.cameracontainer = uidata.MediumContainer('Camera')
		self.cameracontainer.addObject(cameraparameterscontainer)

		setcamera = uidata.Method('Set', self.uiSetCamera)
		self.cameracontainer.addObject(setcamera)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		# scope

		self.uiscopedict = {}
		scopeparameterscontainer = uidata.Container('Parameters')

		parameters = [('magnification', 'Magnification', uidata.Number, 'rw'),
									('intensity', 'Intensity', uidata.Float, 'rw'),
									('defocus', 'Defocus', uidata.Float, 'rw'),
									('spot size', 'Spot Size', uidata.Integer, 'rw'),
									('screen position', 'Main Screen', uidata.String, 'r')]

		for key, name, datatype, permissions in parameters:
			print key, name, datatype
			self.uiscopedict[key] = datatype(name, None, permissions)
			scopeparameterscontainer.addObject(self.uiscopedict[key])

		togglemainscreen = uidata.Method('Toggle Main Screen',
																			self.uiToggleMainScreen)
		resetdefocus = uidata.Method('Reset Defocus', self.uiResetDefocus)
		scopeparameterscontainer.addObject(togglemainscreen)
		scopeparameterscontainer.addObject(resetdefocus)

		pairs = [('stage position', 'Stage Position',
								['x', 'y', 'z', 'a'], uidata.Float),
							('image shift', 'Image Shift', ['x', 'y'], uidata.Float),
							('beam tilt', 'Beam Tilt', ['x', 'y'], uidata.Float),
							('beam shift', 'Beam Shift', ['x', 'y'], uidata.Float)]
		for key, name, axes, datatype in pairs:
			self.uiscopedict[key] = {}
			container = uidata.Container(name)
			for axis in axes:
				self.uiscopedict[key][axis] = datatype(axis, None, 'rw')
				container.addObject(self.uiscopedict[key][axis])
			scopeparameterscontainer.addObject(container)

		self.uiscopedict['stigmator'] = {}
		stigmatorcontainer = uidata.Container('Stigmators')
		pairs = [('condenser', 'Condenser'), ('objective', 'Objective'),
							('diffraction', 'Diffraction')]
		for key, name in pairs:
			self.uiscopedict['stigmator'][key] = {}
			container = uidata.Container(name)
			for axis in ['x', 'y']:
				self.uiscopedict['stigmator'][key][axis] = uidata.Float(axis, None, 'rw')
				container.addObject(self.uiscopedict['stigmator'][key][axis])
			stigmatorcontainer.addObject(container)

		scopeparameterscontainer.addObject(stigmatorcontainer)

		self.scopecontainer = uidata.MediumContainer('Microscope')
		self.scopecontainer.addObject(scopeparameterscontainer)

		refreshscope = uidata.Method('Refresh', self.uiRefreshScope)
		setscope = uidata.Method('Set', self.uiSetScope)
		self.scopecontainer.addObject(refreshscope)
		self.scopecontainer.addObject(setscope)

		# camera

		self.uicameradict = {}
		cameraparameterscontainer = uidata.Container('Parameters')

		parameters = [('exposure time', 'Exposure time', uidata.Float, 'rw')]

		for key, name, datatype, permissions in parameters:
			self.uicameradict[key] = datatype(name, None, permissions)
			cameraparameterscontainer.addObject(self.uicameradict[key])

		pairs = [('dimension', 'Dimension', ['x', 'y'], uidata.Integer),
							('offset', 'Offset', ['x', 'y'], uidata.Integer),
							('binning', 'Binning', ['x', 'y'], uidata.Integer)]

		for key, name, axes, datatype in pairs:
			self.uicameradict[key] = {}
			container = uidata.Container(name)
			for axis in axes:
				self.uicameradict[key][axis] = datatype(axis, 0, 'rw')
				container.addObject(self.uicameradict[key][axis])
			cameraparameterscontainer.addObject(container)

		self.cameracontainer = uidata.MediumContainer('Camera')
		self.cameracontainer.addObject(cameraparameterscontainer)

		setcamera = uidata.Method('Set', self.uiSetCamera)
		self.cameracontainer.addObject(setcamera)

		container = uidata.MediumContainer('EM')
		container.addObjects((self.scopecontainer, self.cameracontainer))
		self.uiserver.addObject(container)

