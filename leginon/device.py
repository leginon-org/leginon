import data
import event
import node
import uidata
import threading
import Queue
import datahandler

class DeviceClient(object):
	dataclass = data.DeviceData
	eventinputs = [event.DevicePublishEvent]
	eventoutputs = [event.DeviceLockEvent,
									event.DeviceUnlockEvent,
									event.DeviceGetPublishEvent,
									event.DevicePublishEvent]
	def __init__(self, node):
		self.node = node
		self.node.addEventInput(event.DevicePublishEvent, self.handleDevicePublish)
		self.geteventwaits = {}
		self.getdata = {}

	def lock(self, wait=True, timeout=None):
		self.node.outputEvent(event.DeviceLockEvent(), wait, timeout)

	def unlock(self, wait=False, timeout=None):
		self.node.outputEvent(event.DeviceUnlockEvent(), wait, timeout)

	def handleDevicePublish(self, ievent):
		dataid = ievent['get data ID']
		if dataid in self.geteventwaits:
			self.getdata[dataid] = self.node.researchPublishedData(ievent)
			self.geteventwaits[dataid].set()

	def get(self, keys):
		getdata = data.DeviceGetData()
		getdata['id'] = self.node.ID()
		getdata['keys'] = keys
		self.geteventwaits[getdata['id']] = threading.Event()
		self.node.publish(getdata, pubeventclass=event.DeviceGetPublishEvent,
											pubevent=True)
		self.geteventwaits[getdata['id']].wait()
		gotdata = self.getdata[getdata['id']]
		del self.getdata[getdata['id']]
		return gotdata

	def set(self, setdata):
		setdata = self.dataclass(initializer=setdata)
		setdata['id'] = self.node.ID()
		self.node.publish(setdata, pubeventclass=event.DevicePublishEvent,
											pubevent=True, confirm=True, wait=True)

class DeviceEventQueue(Queue.Queue):
	def __init__(self):
		self.lockedby = None
		Queue.Queue.__init__(self, 0)
		self.mutex = threading.Condition()

	def lock(self, id):
		self.mutex.acquire()
		if self.lockedby is None:
			self.lockedby = id
		elif self.lockedby != id:
			self.mutex.wait()
			was_empty = self._empty()
			self.lockedby = id
			if was_empty and not self._empty():
				self.esema.release()
			elif self._empty() and not was_empty:
				self.esema.acquire()
		self.mutex.release()

	def unlock(self, id):
		self.mutex.acquire()
		if self.lockedby == id:
			was_empty = self._empty()
			self.lockedby = None
			if was_empty and not self._empty():
				self.esema.release()
			self.mutex.notify()
		self.mutex.release()

	def _get(self):
		if self.lockedby is None:
			return Queue.Queue._get(self)
		else:
			for i, item in enumerate(self.queue):
				if item['id'][-2] == self.lockedby:
					return self.queue.pop(i)
		raise RuntimeError

	def _empty(self):
		if self.lockedby is None:
			return Queue.Queue._empty(self)
		else:
			for item in self.queue:
				if item['id'][-2] == self.lockedby:
					return False
			return True

	# jorg
	def put(self, item, block=True, timeout=None):
		if block:
			if timeout is None:
				self.fsema.acquire()
			elif timeout >= 0:
				delay = 0.0005 # 500 us -> initial delay of 1 ms
				endtime = _time() + timeout
				while True:
					if self.fsema.acquire(0):
						break
					remaining = endtime - _time()
					if remaining <= 0:  #time is over and no slot was free
						raise Full
					delay = min(delay * 2, remaining, .05)
					_sleep(delay)	   #reduce CPU usage by using a sleep
			else:
				raise ValueError("'timeout' must be a positive number")
		elif not self.fsema.acquire(0):
			raise Full
		self.mutex.acquire()
		release_fsema = True
		try:
			was_empty = self._empty()
			self._put(item)
			if was_empty and not self._empty():
				self.esema.release()
			release_fsema = not self._full()
		finally:
			if release_fsema:
				self.fsema.release()
			self.mutex.release()


class DeviceDataBinder(datahandler.DataBinder):
	def __init__(self, threaded=False, queueclass=DeviceEventQueue):
		datahandler.DataBinder.__init__(self, id, session, threaded, queueclass)

class DeviceDataHandler(node.DataHandler):
	def __init__(self, mynode, databinderclass=DeviceDataBinder):
		node.DataHandler.__init__(self, id, session, mynode,
															databinderclass=databinderclass)

class Device(node.Node):
	dataclass = data.DeviceData
	eventinputs = node.Node.eventinputs + [event.DeviceLockEvent,
																					event.DeviceUnlockEvent,
																					event.DeviceGetPublishEvent,
																					event.DevicePublishEvent]
	eventoutputs = node.Node.eventinputs + [event.DevicePublishEvent]

	def __init__(self, id, session, nodelocations,
								datahandler=DeviceDataHandler, **kwargs):
		node.Node.__init__(self, id, session, nodelocations,
												datahandler=datahandler, **kwargs)
		self.addEventInput(event.DeviceLockEvent, self.handleLock)
		self.addEventInput(event.DeviceUnlockEvent, self.handleUnlock)
		self.addEventInput(event.DeviceGetPublishEvent, self.handleGet)
		self.addEventInput(event.DevicePublishEvent, self.handleSet)
		self.defineUserInterface()
		self.start()

	def lock(self, id=None):
		if id is None:
			id = self
		self.datahandler.databinder.queue.lock(id)

	def unlock(self, id=None):
		if id is None:
			id = self
		self.datahandler.databinder.queue.unlock(id)

	def handleLock(self, ievent):
		self.lock(ievent['id'][-2])
		self.confirmEvent(ievent)

	def handleUnlock(self, ievent):
		self.unlock(ievent['id'][-2])
		self.confirmEvent(ievent)

	def _get(self, keys):
		return {}

	def get(self, keys):
		self.lock()
		self._get(keys)
		self.unlock()

	def _set(self, value):
		pass

	def set(self, value):
		self.lock()
		self._set(value)
		self.unlock()

	def handleGet(self, ievent):
		getdata = self.researchPublishedData(ievent)

		initializer = self._get(getdata['keys'])
		initializer['id'] = self.ID()

		publisheventinstance = event.DevicePublishEvent()
		publisheventinstance['dataid'] = initializer['id']
		publisheventinstance['get data ID'] = getdata['id']

		self.publish(self.dataclass(initializer=initializer),
									publisheventinstance=publisheventinstance)

	def handleSet(self, ievent):
		setdata = self.researchPublishedData(ievent)
		self._set(setdata)
		self.confirmEvent(ievent)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

'''
import time
class TestDeviceClient(node.Node):
	eventinputs = node.Node.eventinputs + DeviceClient.eventinputs
	eventoutputs = node.Node.eventoutputs + DeviceClient.eventoutputs
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.deviceclient = DeviceClient(self)
		self.defineUserInterface()
		self.start()

	def testLock(self):
		self.deviceclient.lock()

	def testUnlock(self):
		self.deviceclient.unlock()

	def testGet(self):
		t = time.time()
		print 'test get value =', self.deviceclient.get([])
		print 'test get time =', time.time() - t

	def testSet(self):
		t = time.time()
		self.deviceclient.set({})
		print 'test set time =', time.time() - t

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		testlockmethod = uidata.Method('Test Lock', self.testLock)
		testunlockmethod = uidata.Method('Test Unlock', self.testUnlock)
		testgetmethod = uidata.Method('Test Get', self.testGet)
		testsetmethod = uidata.Method('Test Set', self.testSet)
		container = uidata.LargeContainer('Test Device')
		container.addObjects((testlockmethod, testunlockmethod,
													testgetmethod, testsetmethod))

		self.uiserver.addObject(container)
'''

