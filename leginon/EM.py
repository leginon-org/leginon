#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import datatransport
import emregistry
import event
import imp
import methoddict
import node
import Numeric
import Queue
import threading
import time
import uidata
import unique

watch_set = (
'magnification',
'focus',
'defocus',
'resetdefocus',
'stigmator',
'beam tilt',
'stage position',
)

class DataHandler(node.DataHandler):
	def query(self, id):
		if id == 'UI server':
			return node.DataHandler.query(self, id)
		emkey = id[0]
		self.node.statelock.acquire()
		try:
			done_event = threading.Event()
			self.node.requestqueue.put(GetRequest(done_event, [emkey]))
			done_event.wait()
			state = self.node.state

			if emkey == 'scope':
				result = data.ScopeEMData(id=('scope',))
				result.friendly_update(state)
			elif emkey in ('camera', 'camera no image data'):
				result = data.CameraEMData(id=('camera',))
				# this is a fix for the bigger problem of always 
				# setting defocus
				result.friendly_update(state)
			elif emkey == 'all em':
				result = data.AllEMData(id=('all em',))
				result.friendly_update(state)
			else:
				### could be either CameraEMData or ScopeEMData
				trydatascope = data.ScopeEMData(id=('scope',))
				trydatacamera = data.CameraEMData(id=('camera',))
				for trydata in (trydatascope, trydatacamera):
					try:
						trydata.update(state)
						result = trydata
						break
					except KeyError:
						result = None
		finally:
			self.node.statelock.release()
		return result

	def insert(self, idata):
		if isinstance(idata, data.EMData):
			self.node.statelock.acquire()
			try:
				done_event = threading.Event()
				d = idata.toDict(noNone=True)
				for key in ['id', 'session', 'system time', 'image data']:
					try:
						del d[key]
					except KeyError:
						pass
				self.node.requestqueue.put(SetRequest(done_event, d))
				done_event.wait()
			finally:
				self.node.statelock.release()
		else:
			node.DataHandler.insert(self, idata)

class Request(object):
	pass

class GetRequest(Request):
	def __init__(self, ievent, value):
		self.event = ievent
		self.value = value

class SetRequest(Request):
	def __init__(self, ievent, value):
		self.event = ievent
		self.value = value

class SetInstrumentRequest(Request):
	def __init__(self, type, name):
		self.type = type
		self.name = name

class EM(node.Node):
	eventinputs = node.Node.eventinputs + [event.LockEvent, event.UnlockEvent]
	eventoutputs = node.Node.eventoutputs + [event.ListPublishEvent]
	def __init__(self, id, session, nodelocations, tcpport=None, **kwargs):

		self.messagelog = uidata.MessageLog('Message Log')

		# These keys are not included in a get all parameters
		self.prunekeys = [
			'gun shift',
			'gun tilt',
			'beam blank',
			'dark field mode',
			'diffraction mode',
			'low dose',
			'low dose mode',
			'holder type',
			'holder status',
			'stage status',
			'vacuum status',
			'column valves',
			'turbo pump',
			'column pressure',
			'inserted',
		]

		## if many of these are changed in one call, do them in this order
		self.order = [
			'magnification',
			'spot size',
			'image shift',
			'beam shift',
			'focus',
			'defocus',
			'reset defocus',
			'intensity',
			'offset'
			'dimension',
			'binning',
			'exposure time',
			'exposure type'
		]

		## if any of these are changed, follow up with the specified pause
		## these pauses are just a guess in order to allow for normalizations and such
		self.pauses = {
			'magnification':  1.5,
			'spot size': 0.4,
			'image shift': 0.2,
			'beam shift': 0.1,
			'defocus': 0.4,
			'focus': 0.4,
			'intensity': 0.1,
		}

		self.permissions = {
			'high tension': 'r',
			'temperature': 'r',
#			'column valves': 'r',
			'gun shift': '',
			'gun tilt': '',
			'beam blank': '',
			'dark field mode': '',
			'diffraction mode': '',
			'low dose': '',
			'low dose mode': '',
			'screen current': 'r',
#			'holder type': '',
#			'holder status': '',
#			'stage status': '',
#			'vacuum status': '',
#			'turbo pump': '',
#			'column pressure': '',
		}

		# the queue of requests to get and set parameters
		self.requestqueue = Queue.Queue()

		# external lock for nodes keep EM for themself
		self.nodelock = threading.Lock()
		self.locknodeid = None

		# state tracks always keeps the current (known by EM) and compares
		# to changes in the UI state in order to only change parameters that
		# the user has modified (to save time)
		self.statelock = threading.RLock()
		self.state = {}

		self.datahandler = DataHandler(self)
		self.server = datatransport.Server(self.datahandler, tcpport)
		kwargs['datahandler'] = None

		node.Node.__init__(self, id, session, nodelocations, **kwargs)

		# get the scope module and class from the database
		try:
			scopename = self.session['instrument']['scope']
		except (TypeError, KeyError):
			# no scope is associated with this session
			self.messagelog.warning('no scope is associated with this session')
			scopename = None

		# get the camera module and class from the database
		try:
			cameraname = self.session['instrument']['camera']
		except (TypeError, KeyError):
			# no camera is associated with this session
			self.messagelog.warning('no camera is associated with this session')
			cameraname = None

		# add event inputs for locking and unlocking EM from a node
		self.addEventInput(event.LockEvent, self.doLock)
		self.addEventInput(event.UnlockEvent, self.doUnlock)

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
		self.scope = None
		self.camera = None

		if scopename is not None:
			self.setScopeType(scopename)
		if cameraname is not None:
			self.setCameraType(cameraname)

		for key, permissions in self.permissions.items():
			try:
				if self.scope is not None:
					self.scope.setPermissions(key, permissions)
			except KeyError:
				try:
					if self.camera is not None:
						self.camera.setPermissions(key, permissions)
				except KeyError:
					pass

		ids = []
		if self.scope is not None:
			ids += ['scope']
			ids += self.scope.keys()
		if self.camera is not None:
			ids += ['camera', 'camera no image data']
			ids += self.camera.keys()
		if self.scope is not None and self.camera is not None:
			ids += ['all em']
		for i in range(len(ids)):
			ids[i] = (ids[i],)

		self.uistate = {}
		self.defineUserInterface()

		self.state = self.getEM(self.uiscopedict.keys() + self.uicameradict.keys())
		self.uiUpdate()
		self.scopecontainer.enable()
		self.cameracontainer.enable()

		if ids:
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
		scopeinfo = emregistry.getScopeInfo(scopename)
		if scopeinfo is None:
			raise RuntimeError('EM node unable to get scope info')
		modulename, classname, d = scopeinfo
		try:
			scopeclass = self.getClass(modulename, classname)
			self.scope = methoddict.factory(scopeclass)()
		except Exception, e:
			self.messagelog.error('cannot set scope to type ' + str(scopename))

	def setCameraType(self, cameraname):
		modulename, classname, d = emregistry.getCameraInfo(cameraname)
		try:
			cameraclass = self.getClass(modulename, classname)
			self.camera = methoddict.factory(cameraclass)()
		except Exception, e:
			self.messagelog.error('cannot set camera to type ' + str(cameraname))

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
		self.server.exit()

	def location(self):
		location = node.Node.location(self)
		location['data transport'] = self.server.location()
		return location

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
				if self.scope is not None:
					scopekeys = self.scope.keys()
					for prunekey in self.prunekeys:
						try:
							scopekeys.remove(prunekey)
						except ValueError:
							pass
					withkeys += scopekeys
			elif key == 'camera':
				withkeys.remove(key)
				if self.camera is not None:
					withkeys += self.camera.keys()
			elif key == 'camera no image data':
				withkeys.remove(key)
				keys = self.camera.keys()
				if self.camera is not None:
					try:
						keys.remove('image data')
					except ValueError:
						pass
					withkeys += keys
			elif key == 'all em':
				withkeys.remove(key)
				if self.scope is not None:
					withkeys += self.scope.keys()
				if self.camera is not None:
					withkeys += self.camera.keys()

		withkeys = unique.unique(withkeys)

		for key in withoutkeys:
			if key == 'scope':
				withoutkeys.remove(key)
				if self.scope is not None:
					withoutkeys += self.scope.keys()
			elif key == 'camera':
				withoutkeys.remove(key)
				if self.camera is not None:
					withoutkeys += self.camera.keys()
			elif key == 'camera no image data':
				withoutkeys.remove(key)
				if self.camera is not None:
					keys = self.camera.keys()
					try:
						keys.remove('image data')
					except KeyError:
						pass
					withoutkeys += keys
			elif key == 'all em':
				withoutkeys.remove(key)
				if self.scope is not None:
					withoutkeys += self.scope.keys()
				if self.camera is not None:
					withoutkeys += self.camera.keys()

		for key in withoutkeys:
			try:
				withkeys.remove(key)
			except ValueError:
				pass

		if self.scope is not None:
			scopekeys = self.scope.keys()
		else:
			scopekeys = []
		if self.camera is not None:
			camerakeys = self.camera.keys()
		else:
			camerakeys = []
		for key in withkeys:
			if key in scopekeys:
				result[key] = self.scope[key]
			elif key in camerakeys:
				result[key] = self.camera[key]
			else:
				pass

		result['system time'] = time.time()

		return result

	def cmpEM(self, a, b):
		ain = a in self.order
		bin = b in self.order

		if ain and bin:
			return cmp(self.order.index(a), self.order.index(b))
		elif ain and not bin:
			return -1
		elif not ain and bin:
			return 1
		elif not ain and not bin:
			return 0

	def setEM(self, state):
		orderedkeys = state.keys()
		orderedkeys.sort(self.cmpEM)

		if self.scope is not None:
			scopekeys = self.scope.writekeys()
		else:
			scopekeys = []
		if self.camera is not None:
			camerakeys = self.camera.writekeys()
		else:
			camerakeys = []

		if 'focus' in orderedkeys and 'defocus' in orderedkeys:
			self.messagelog.warning('Focus and defocus changed at the same time defocus ' + str(state['focus']) +  ' focus ' + str(state['defocus']))

		#print 'setEM'
		for key in orderedkeys:
			value = state[key]
			#if key in watch_set:
			#	print '%s\t\t%s' % (key, value)
			if value is not None:
				if key in scopekeys:
					try:
						self.scope[key] = value
					except:	
						self.messagelog.error("failed to set '%s' to %s" % (key, value))
						print "failed to set '%s' to %s" % (key, value)
						self.printException()
				elif key in camerakeys:
					try:
						self.camera[key] = value
					except:	
						self.messagelog.error("failed to set '%s' to %s"
																	% (key, state[key]))
						print "failed to set '%s' to" % key, state[key]
						self.printException()

			if self.uipauses.get() and (key in self.pauses):
				p = self.pauses[key]
				time.sleep(p)

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
		try:
			done_event = threading.Event()
			self.requestqueue.put(SetRequest(done_event, request))
			done_event.wait()
		finally:
			self.statelock.release()

	def queueHandler(self):
		while True:
			request = self.requestqueue.get()
			if isinstance(request, SetRequest):
				self.setEM(request.value)
				self.state = self.getEM(request.value.keys())
			elif isinstance(request, GetRequest):
				self.state = self.getEM(request.value)
			elif isinstance(request, SetInstrumentRequest):
				pass
			else:
				raise TypeError('invalid EM request')
			self.uiUpdate()
			request.event.set()

	def uiUnlock(self):
		self.locknodeid = None
		self.nodelock.release()

	def uiRefreshScope(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			request = self.uiGetDictData(self.uiscopedict).keys()
			self.requestqueue.put(GetRequest(done_event, request))
			done_event.wait()
		finally:
			self.statelock.release()
			self.cameracontainer.enable()
			self.scopecontainer.enable()

	def uiRefreshCamera(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			request = self.uiGetDictData(self.uicameradict).keys()
			self.requestqueue.put(GetRequest(done_event, request))
			done_event.wait()
		finally:
			self.statelock.release()
			self.cameracontainer.enable()
			self.scopecontainer.enable()

	def uiSetScope(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		try:
			scopedict = self.uiGetDictData(self.uiscopedict)
			updatedstate = self.uiSetState(scopedict)
		finally:
			self.cameracontainer.enable()
			self.scopecontainer.enable()

	def uiSetCamera(self):
		self.scopecontainer.disable()
		self.cameracontainer.disable()
		try:
			cameradict = self.uiGetDictData(self.uicameradict)
			updatedstate = self.uiSetState(cameradict)
		finally:
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

	def interfaceObjectFromKey(self, obj, key):
		try:
			permissions = ''
			if obj.readable(key):
				permissions += 'r'
			if obj.writable(key):
				permissions += 'w'
		except (KeyError, AttributeError):
			raise ValueError('cannot get permission for "%s" from object' % key)
		if not permissions:
			raise ValueError('permissions of "%s" do not allow object creation' % key)
		try:
			return self.interfaceObjectFromTypeInfo(key, obj.typemapping[key],
																								permissions)
		except (AttributeError, KeyError):
			raise ValueError('no typemap for "%s"' % key)

	def interfaceObjectFromTypeInfo(self, key, typeinfodict, permissions):
		datatype = typeinfodict['type']
		if datatype == int:
			interfaceclass = uidata.Integer
			value = None
		elif datatype == float:
			interfaceclass = uidata.Float
			value = None
		elif datatype == str:
			interfaceclass = uidata.String
			value = ''
		elif datatype == list:
			interfaceclass = uidata.Sequence
			value = []
		elif datatype == bool:
			interfaceclass = uidata.Boolean
			value = False
		elif datatype == Numeric.arraytype:
			raise ValueError('currently not displaying images')
			interfaceclass = uidata.Image
			value = None
		elif datatype == dict:
			interfaceclass = uidata.Container

		try:
			range = typeinfodict['range']
		except KeyError:
			pass

		try:
			values = typeinfodict['values']
			if datatype == dict:
				mapping = {}
				objects = []
				for subkey in values:
					try:
						subinterface, submapping = self.interfaceObjectFromTypeInfo(subkey,
																														values[subkey],
																														permissions)
						objects.append(subinterface)
						if submapping is None:
							mapping[subkey] = subinterface
						else:
							mapping[subkey] = submapping
					except (AttributeError, KeyError, ValueError):
						pass
				interface = interfaceclass(key)
				interface.addObjects(objects)
				return interface, mapping
		except KeyError:
			if datatype == dict:
				return interfaceclass(key), None

		return interfaceclass(key, value, permissions=permissions), None

	def interfaceFromObject(self, obj):
		if obj is None:
			return uidata.Container('Parameters'), {}
		orderedkeys = obj.keys()
		orderedkeys.sort(self.cmpEM)
		interfaceobjects = []
		mapping = {}
		for key in orderedkeys:
			try:
				interfaceobject, submapping = self.interfaceObjectFromKey(obj, key)
				interfaceobjects.append(interfaceobject)
				if submapping is None:
					mapping[key] = interfaceobject
				else:
					mapping[key] = submapping
			except ValueError, e:
				pass
		container = uidata.Container('Parameters')
		container.addObjects(interfaceobjects)
		return container, mapping

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.uipauses = uidata.Boolean('Do Pauses', True, permissions='rw',
																		persist=True)

		# scope
		scopeinterface, self.uiscopedict = self.interfaceFromObject(self.scope)
		refreshscope = uidata.Method('Refresh', self.uiRefreshScope)
		setscope = uidata.Method('Set', self.uiSetScope)
		self.scopecontainer = uidata.LargeContainer('Microscope')
		self.scopecontainer.addObjects((self.uipauses, scopeinterface,
																		refreshscope, setscope))
		self.scopecontainer.disable()

		# camera
		camerainterface, self.uicameradict = self.interfaceFromObject(self.camera)
		self.cameracontainer = uidata.LargeContainer('Camera')
		refreshcamera = uidata.Method('Refresh', self.uiRefreshCamera)
		setcamera = uidata.Method('Set', self.uiSetCamera)
		self.cameracontainer.addObjects((camerainterface, refreshcamera, setcamera))
		self.cameracontainer.disable()

		container = uidata.LargeContainer('EM')
		container.addObject(self.messagelog)
		if self.scope is not None:
			container.addObject(self.scopecontainer)
		if self.camera is not None:
			container.addObject(self.cameracontainer)
		self.uicontainer.addObject(container)

