#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
from pyScope import registry, methoddict
import event
import imp
import node
try:
	import numarray as Numeric
except:
	import Numeric
import Queue
import threading
import time
import unique
import copy
import gui.wx.Instrument
import instrument

watch_set = (
'magnification',
'focus',
'defocus',
'resetdefocus',
'stigmator',
'beam tilt',
'stage position',
)

## if a stage position movement is requested that is less than the following,
## then ignore it
minimum_stage = {
	'x': 5e-8,
	'y': 5e-8,
	'z': 5e-8,
	'a': 6e-5,
}

class EMUnavailable(Exception):
	pass
class ScopeUnavailable(EMUnavailable):
	pass
class CameraUnavailable(EMUnavailable):
	pass

class EMClient(object):
	eventinputs = [event.ScopeEMPublishEvent,
									event.CameraEMPublishEvent,
									event.CameraImageEMPublishEvent]
	eventoutputs = [event.SetScopeEvent, event.SetCameraEvent]
	def __init__(self, node):
		self.node = node
		## for referencing the scope and camera
		## will eventually need to handle multiple scopes/cameras
		self.scoperef = None
		self.cameraref = None
		self.cameraimageref = None
		self.scopeavailable = threading.Event()
		self.cameraavailable = threading.Event()
		self.cameraimageavailable = threading.Event()
		self.node.addEventInput(event.ScopeEMPublishEvent, self.handleScopePublish)
		self.node.addEventInput(event.CameraEMPublishEvent, self.handleCameraPublish)
		self.node.addEventInput(event.CameraImageEMPublishEvent, self.handleCameraImagePublish)

	def handleScopePublish(self, ievent):
		self.scoperef = ievent
		self.scopeavailable.set()

	def handleCameraPublish(self, ievent):
		self.cameraref = ievent
		self.cameraavailable.set()

	def handleCameraImagePublish(self, ievent):
		self.cameraimageref = ievent
		self.cameraimageavailable.set()

	def wait_for_scope(self, timeout=None):
		self.scopeavailable.wait(timeout=timeout)

	def wait_for_camera(self, timeout=None):
		self.cameraavailable.wait(timeout=timeout)

	def wait_for_image(self, timeout=None):
		self.cameraimageavailable.wait(timeout=timeout)

	def getScope(self, key=None):
		if self.scoperef is None:
			raise ScopeUnavailable()
		## still has to get whole ScopeEMData just to get one key
		dat = self.scoperef['data']
		if key is None:
			## return copy to avoid referencing problem
			return copy.copy(dat)
		else:
			return dat[key]

	def getCamera(self, key=None):
		if self.cameraref is None:
			raise ScopeUnavailable()
		## still has to get whole CameraEMData just to get one key
		dat = self.cameraref['data']
		self.node.logger.debug('getCamera dat dmid: %s' % (dat.dmid,))
		if key is None:
			## return copy to avoid referencing problem
			return copy.copy(dat)
		else:
			return dat[key]

	def getImage(self, key=None):
		if self.cameraimageref is None:
			raise CameraUnavailable()
		self.node.logger.debug('GET IMAGE REF: %s' % (self.cameraimageref.special_getitem('data', dereference=False),))
		dat = self.cameraimageref['data']
		if key is None:
			## return copy to avoid referencing problem
			## this looks funny, but keeps datamanager from
			## thinking it is using a lot of memory
			im = dat['image data']
			dat['image data'] = None
			dat = copy.copy(dat)
			dat['image data'] = im
			return dat
		else:
			return dat[key]

	def setScope(self, value):
		value = copy.copy(value)
		self.node.logger.debug('setScope: %s' % (value, ))
		setevent = event.SetScopeEvent(data=value)
		try:
			self.node.outputEvent(setevent, wait=True)
		except node.ConfirmationNoBinding:
			self.node.logger.debug('Cannot set scope parameter (no event binding)')
			raise

	def setCamera(self, value):
		value = copy.copy(value)
		self.node.logger.debug('setCamera: %s' % (value, ))
		setevent = event.SetCameraEvent(data=value)
		try:
			self.node.outputEvent(setevent, wait=True)
		except node.ConfirmationNoBinding:
			self.node.logger.debug('Cannot set camera parameter (no event binding)')
			raise

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

class ExitRequest(Request):
	pass

class EM(node.Node):
	panelclass = gui.wx.Instrument.Panel
	eventinputs = node.Node.eventinputs + [event.LockEvent, event.UnlockEvent, event.SetScopeEvent, event.SetCameraEvent]
	def __init__(self, name, session, managerlocation, tcpport=None, **kwargs):

		self.tems = []
		self.ccdcameras = []

		self.typemap = {}

		# These keys are not included in a get all parameters
		self.prunekeys = [
			'gun shift',
			'gun tilt',
			'beam blank',
			'dark field mode',
			'diffraction mode',
			'low dose',
			#'low dose mode',
			# comment out below for robot
			'holder type',
			'holder status',
			'stage status',
			'vacuum status',
			'column valves',
			'turbo pump',
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
			'main screen position': 1.0,
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
#			'low dose': '',
#			'low dose mode': '',
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
		self.locknode = None

		# state tracks always keeps the current (known by EM) and compares
		# to changes in the UI state in order to only change parameters that
		# the user has modified (to save time)
		self.statelock = threading.RLock()
		self.state = {}

		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		# get the scope module and class from the database
		try:
			scopename = self.session['instrument']['scope']
		except (TypeError, KeyError):
			# no scope is associated with this session
			self.logger.warning('no scope is associated with this session')
			scopename = None

		# get the camera module and class from the database
		try:
			cameraname = self.session['instrument']['camera']
		except (TypeError, KeyError):
			# no camera is associated with this session
			self.logger.warning('no camera is associated with this session')
			cameraname = None

		try:
			description = self.session['instrument']['description']
		except (TypeError, KeyError):
			description = 'Unknown instrument'

		# add event inputs for locking and unlocking EM from a node
		self.addEventInput(event.LockEvent, self.doLock)
		self.addEventInput(event.UnlockEvent, self.doUnlock)

		# watch for SetScopeEvent and SetCameraEvent
		self.addEventInput(event.SetScopeEvent, self.handleSet)
		self.addEventInput(event.SetCameraEvent, self.handleSet)

		# the handler thread waits for queue requests and processes them
		# scope and camera are typically COM objects and need to be initialized
		# in this thread
		args = (scopename, cameraname, description)
		self.handlerthread = threading.Thread(name='EM handler thread',
																					target=self.handler,
																					args=args)
		self.handlerthread.setDaemon(1)
		self.handlerthread.start()

	def getScope(self):
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			self.requestqueue.put(GetRequest(done_event, ['scope']))
			done_event.wait()
			state = self.state
		finally:
			self.statelock.release()
		newdata = data.ScopeEMData()
		newdata.friendly_update(state)
		return newdata

	def getCamera(self):
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			self.requestqueue.put(GetRequest(done_event, ['camera no image data']))
			done_event.wait()
			state = self.state
		finally:
			self.statelock.release()
		newdata = data.CameraEMData()
		newdata.friendly_update(state)
		return newdata

	def getImage(self):
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			self.requestqueue.put(GetRequest(done_event, ['camera']))
			done_event.wait()
			state = self.state
		finally:
			self.statelock.release()
		newdata = data.CameraEMData()
		newdata.friendly_update(state)
		return newdata

	def handleSet(self, setevent):
		try:
			scopedata = setevent['data']
		except ValueError:
			print '-------------------------------------------------------'
			print 'THIS IS THE MYSTERY EXCEPTION...'
			print 'SETEVENT', setevent
			print 'SOMETHING IS WRONG WITH THE FOLLOWING DATA REFERENCE:'
			print 'DATA REF', setevent.special_getitem('data', False)
			print '--------------- ACTUAL EXCEPTION: ---------------------'
			raise
		self.logger.debug('handleSet: %s' % (scopedata,))
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			d = scopedata.toDict(noNone=True)
			for key in ['session', 'system time', 'image data']:
				try:
					del d[key]
				except KeyError:
					pass
			self.requestqueue.put(SetRequest(done_event, d))
			done_event.wait()
		finally:
			self.statelock.release()
			self.confirmEvent(setevent)

	def publishData(self):
		### data handlers that will be hosted here:
		if self.scope is not None:
			self.scopedata = data.DataHandler(data.ScopeEMData,
																				getdata=self.getScope)
			self.publish(self.scopedata,
										pubevent=True,
										pubeventclass=event.ScopeEMPublishEvent,
										broadcast=True)

		if self.camera is not None:
			self.cameradata = data.DataHandler(data.CameraEMData,
																					getdata=self.getCamera)
			self.publish(self.cameradata,
										pubevent=True,
										pubeventclass=event.CameraEMPublishEvent,
										broadcast=True)

			self.imagedata = data.DataHandler(data.CameraEMData,
																				getdata=self.getImage)
			self.publish(self.imagedata,
										pubevent=True,
										pubeventclass=event.CameraImageEMPublishEvent,
										broadcast=True)


	def handler(self, scopename, cameraname, description):
		self.scope = None
		self.camera = None

		if scopename is not None:
			self.setScopeType(scopename, description)
		if cameraname is not None:
			self.setCameraType(cameraname, description)

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

		self.panel.initParameters(self.typemap, self.session)

		keys = []
		if self.scope is not None:
			keys += self.scope.keys()
		if self.camera is not None:
			keys += self.camera.keys()
		if keys:
			self.state = self.getEM(keys, withoutkeys=['image data',
																									'vacuum status',
																									'column valves'])

		self.start()
		self.publishData()
		self.queueHandler()

	def setScopeType(self, scopename, description):
		try:
			scopeclass = registry.getClass(scopename)
			if scopeclass is None:
				raise RuntimeError
			class ScopeClass(scopeclass, instrument.TEM):
				def __init__(self):
					scopeclass.__init__(self)
					instrument.TEM.__init__(self)
			self.scope = methoddict.factory(ScopeClass)()
			self.typemap.update(self.scope.typemapping)
			name = '%s on %s' % (scopename, description)
			self.objectservice._addObject(name, self.scope)
		except Exception, e:
			self.logger.exception('Initializing scope type %s failed: %s'
															% (scopename, e))

	def setCameraType(self, cameraname, description):
		try:
			cameraclass = registry.getClass(cameraname)
			if cameraclass is None:
				raise RuntimeError
			class CameraClass(cameraclass, instrument.CCDCamera):
				def __init__(self):
					cameraclass.__init__(self)
					instrument.CCDCamera.__init__(self)
			self.camera = methoddict.factory(CameraClass)()
			self.typemap.update(self.camera.typemapping)
			name = '%s on %s' % (cameraname, description)
			self.objectservice._addObject(name, self.camera)
		except Exception, e:
			self.logger.exception('Initializing camera type %s failed: %s'
															% (cameraname, e))

	def main(self):
		pass

	def exit(self):
		node.Node.exit(self)
		#self.server.exit()
		self.requestqueue.put(ExitRequest())

	def doLock(self, ievent):
		if ievent['node'] != self.locknode:
			self.nodelock.acquire()
			self.locknode = ievent['node']
		self.confirmEvent(ievent)

	def doUnlock(self, ievent):
		if ievent['node'] == self.locknode:
			self.locknode = None
			self.nodelock.release()
		self.confirmEvent(ievent)

	def getEM(self, withkeys=[], withoutkeys=[]):
		result = {}

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
			try:
				if key in scopekeys:
					result[key] = self.scope[key]
				elif key in camerakeys:
					result[key] = self.camera[key]
				else:
					pass
			except:
				self.logger.exception('Cannot get value of \'%s\'' % key)

		self.panel.setParameters(result)

		result['system time'] = time.time()
		result['session'] = self.session

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

	def checkStagePosition(self, state):
		'''
		ignore small stage movements
		'''
		if 'stage position' not in state or state['stage position'] is None:
			return
		current = self.scope['stage position']
		requested = state['stage position']
		bigenough = {}
		for axis in ('x','y','z','a'):
			if axis in requested:
				delta = abs(requested[axis]-current[axis])
				if delta > minimum_stage[axis]:
					bigenough[axis] = requested[axis]
				else:
					self.logger.debug('requested stage %s=%s is within %s of current: %s' % (axis, requested[axis], minimum_stage[axis], current[axis]))
		if bigenough:
			state['stage position'] = bigenough
		else:
			state['stage position'] = None

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
			self.logger.warning('Focus and defocus changed at the same time defocus ' + str(state['focus']) +  ' focus ' + str(state['defocus']))
		self.checkStagePosition(state)

		for key in orderedkeys:
			value = state[key]
			if key in watch_set:
				self.logger.info('Set \'%s\' %s' % (key, value))
			if value is not None:
				if key in scopekeys:
					try:
						self.scope[key] = value
					except:	
						self.logger.exception('Set \'%s\' %s failed' % (key, value))
				elif key in camerakeys:
					try:
						self.camera[key] = value
					except:	
						self.logger.exception('Set \'%s\' %s failed' % (key, value))

			if self.pause and (key in self.pauses):
				p = self.pauses[key]
				time.sleep(p)

	def setState(self, setdict):
		self.statelock.acquire()
		try:
			done_event = threading.Event()
			self.requestqueue.put(SetRequest(done_event, setdict))
		finally:
			self.statelock.release()

	def appendDependencies(self, keys):
		if self.scope is not None:
			for key, value in self.scope.parameterdependencies.items():
				if key in keys:
					keys += value
		return keys

	def queueHandler(self):
		while True:
			request = self.requestqueue.get()
			if isinstance(request, SetRequest):
				self.setStatus('processing')
				try:
					self.setEM(request.value)
					keys = request.value.keys()
					keys = self.appendDependencies(keys)
					self.state = self.getEM(keys)
				finally:
					self.setStatus('idle')
			elif isinstance(request, GetRequest):
				self.setStatus('processing')
				try:
					self.state = self.getEM(request.value)
				finally:
					self.setStatus('idle')
			elif isinstance(request, SetInstrumentRequest):
				pass
			elif isinstance(request, ExitRequest):
				try:
					self.scope.exit()
				except AttributeError:
					pass
				try:
					self.camera.exit()
				except AttributeError:
					pass
				break
			else:
				raise TypeError('invalid EM request')
			request.event.set()

	def refresh(self):
		self.statelock.acquire()
		try:
			request = []
			if self.scope is not None:
				request += self.scope.keys()
			if self.camera is not None:
				request += self.camera.keys()
			if request:
				done_event = threading.Event()
				self.requestqueue.put(GetRequest(done_event, request))
		finally:
			self.statelock.release()

	def getDictStructure(self, dictionary):
		return self.keys()

