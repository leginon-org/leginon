#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import time
import sys
import node
import data
import uidata
import event
import threading
import Queue

class TestCommunications(object):
	def __init__(self):
		self.Signal0 = 1
		self.Signal1 = 1
		self.Signal2 = 1
		self.Signal3 = 1
		self.Signal4 = 1
		self.Signal5 = 1
		self.Signal6 = 1
		self.Signal7 = 1
		self.Signal8 = 1
		self.gridNumber = -1

class RobotException(Exception):
	pass

class GridException(Exception):
	pass

class GridQueueEmpty(GridException):
	pass

class GridLoadException(GridException):
	pass

class GridUnloadException(GridException):
	pass

class ScopeException(Exception):
	pass

def validateGridNumber(gridnumber):
	if gridnumber >= 1 and gridnumber <= 96:
		return True
	else:
		return False

class GridQueue(Queue.Queue):
  def __init__(self, callback, maxsize=0):
    self.callback = callback
    Queue.Queue.__init__(self, maxsize)

  def _put(self, item):
    Queue.Queue._put(self, item)
    if callable(self.callback):
      self.callback(self.queue)

  def _get(self):
    item = Queue.Queue._get(self)
    if callable(self.callback):
      self.callback(self.queue)
    return item

  def pause(self):
    self.mutex.acquire()

  def resume(self):
    self.mutex.release()

  def clear(self):
    if not self.esema.acquire(0):
      return
    self.mutex.acquire()
    was_full = self._full()
    self.queue = []
    if callable(self.callback):
      self.callback(self.queue)
    if was_full:
      self.fsema.release()
    self.mutex.release()

class RobotNode(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.statushistory = []
		self.statusindex = -1
		self.statuslength = 50
		self.abort = False
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

	def waitScope(self, parameter, value, interval=-1.0, timeout=0.0):
		parametervalue = self.getScope(parameter)
		elapsed = 0.0
		if interval >= 0.0:
			while parametervalue != value:
				time.sleep(interval)
				if timeout > 0.0:
					elapsed += interval
					if elapsed > timeout:
						raise ScopeException('parameter is not set to value')
				parametervalue = self.getScope(parameter)
		else:
			if parametervalue != value:
				raise ScopeException('parameter is not set to value')

	def getScope(self, key):
		parameterdata = self.researchByDataID((key,))
		if parameterdata is None:
			raise ScopeException('cannot get parameter value')
		print key, parameterdata[key]
		return parameterdata[key]

	def setScope(self, key, value):
		scopedata = data.AllEMData()
		scopedata['id'] = ('scope',)
		scopedata[key] = value
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			raise ScopeException('cannot set parameter to value')

	def setStatus(self, message):
		self.statushistory.append(message)
		if len(self.statushistory) > self.statuslength:
			try:
				self.statushistory = self.statushistory[-self.statuslength:]
			except IndexError:
				pass
		self.statuslabel.set(message)

if sys.platform == 'win32':
	sys.coinit_flags = 0
	import pythoncom
	import win32com.client
	import pywintypes
	class RobotControl(RobotNode):
		eventinputs = RobotNode.eventinputs + [event.ExtractGridEvent,
																						event.InsertGridEvent,]
		eventoutputs = RobotNode.eventoutputs + [event.GridInsertedEvent,
																							event.GridExtractedEvent]
		def __init__(self, id, session, nodelocations, **kwargs):
			RobotNode.__init__(self, id, session, nodelocations, **kwargs)
			self.gridqueue = GridQueue(self.gridQueueCallback)
			self.gridnumber = None
	
			#self.communication = TestCommunications()

			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
			try:
				self.communication = win32com.client.Dispatch(
																									'RobotCommunications.Signal')
			except pywintypes.com_error, e:
				raise RuntimeError('Cannot initialized robot communications')
	
			self.addEventInput(event.InsertGridEvent, self.handleInsert)
			self.addEventInput(event.ExtractGridEvent, self.handleExtract)

			self.defineUserInterface()
			self.start()

		def __del__(self):
			self.communication = None

		def zeroStage(self):
			self.setScopeStatusMessage('Zeroing stage position')
			self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
			self.setScopeStatusMessage('Stage position is zeroed')

		def holderNotInScope(self):
			self.setScopeStatusMessage('Verifying there is no holder inserted')
			self.waitScope('holder status', 'not inserted')
			self.setScopeStatusMessage('No holder currently inserted')

		def holderInScope(self):
			self.setScopeStatusMessage('Verifying there is no holder inserted')
			self.waitScope('holder status', 'inserted')
			self.setScopeStatusMessage('No holder currently inserted')

		def vacuumReady(self):
			self.setScopeStatusMessage('Verifying vacuum is ready')
			self.waitScope('vacuum status', 'ready', 0.5, 600)
			self.setScopeStatusMessage('Vacuum is ready')

		def closeColumnValves(self):
			self.setScopeStatusMessage('Closing column valves')
			self.setScope('column valves', 'closed')
			self.setScopeStatusMessage('Verifying column valves are closed')
			self.waitScope('column valves', 'closed', 0.5, 15)
			self.setScopeStatusMessage('Column valves are closed')

		def turboPumpOn(self):
			self.setScopeStatusMessage('Turning on turbo pump')
			self.setScope('turbo pump', 'on')
			self.setScopeStatusMessage('Verifying turbo pump is on')
			self.waitScope('turbo pump', 'on', 0.5, 300)
			self.setScopeStatusMessage('Turbo pump is on')

		def stageReady(self):
			self.setScopeStatusMessage('Waiting for stage to be ready')
			self.waitScope('stage status', 'ready', 0.5, 600)
			self.setScopeStatusMessage('Stage is ready')

		def setHolderType(self):
			self.setScopeStatusMessage('Setting holder type to single tilt')
			self.setScope('holder type', 'single tilt')
			self.setScopeStatusMessage('Verifying holder type is set to single tilt')
			self.waitScope('holder type', 'single tilt', 0.5, 60)
			self.setScopeStatusMessage('Holder type is set to single tilt')

		def scopeReadyForInsertion1(self):
			self.setScopeStatusMessage('Readying microscope for insertion step 1')
			self.zeroStage()
			self.holderNotInScope()
			self.vacuumReady()
			self.closeColumnValves()
			self.turboPumpOn()
			self.stageReady()
			self.setScopeStatusMessage('Microscope ready for insertion step 1')

		def scopeReadyForInsertion2(self):
			self.setScopeStatusMessage('Readying microscope for insertion step 2')
			self.setHolderType()
			self.stageReady()
			self.setScopeStatusMessage('Microscope ready for insertion step 2')

		def scopeReadyForExtraction(self):
			self.setScopeStatusMessage('Readying microscope for extraction')
			self.zeroStage()
			self.holderInScope()
			self.vacuumReady()
			self.closeColumnValves()
			self.stageReady()
			self.setScopeStatusMessage('Microscope ready for extraction')

		def signalRobotToInsert1(self):
			self.setRobotStatusMessage('Signaling robot to begin insertion step 1')
			self.communication.Signal1 = 1
			self.setRobotStatusMessage('Signaled robot to begin insertion step 1')

		def signalRobotToInsert2(self):
			self.setRobotStatusMessage('Signaling robot to begin insertion step 2')
			self.communication.Signal3 = 1
			self.setRobotStatusMessage('Signaled robot to begin insertion step 2')

		def signalRobotToExtract(self):
			self.setRobotStatusMessage('Signaling robot to begin extraction')
			self.communication.Signal6 = 1
			self.setRobotStatusMessage('Signaled robot to begin extraction')

		def waitForRobotGridLoad(self):
			self.setRobotStatusMessage('Verifying robot is ready for insertion')
			while not self.communication.Signal0:
				if self.communication.Signal8:
					self.setRobotStatusMessage('Robot failed to extract grid from tray')
					self.communication.Signal8 = 0
					raise GridLoadException
				time.sleep(0.5)
			self.communication.Signal0 = 0
			self.setRobotStatusMessage('Robot is ready for insertion')

		def waitForRobotToInsert1(self):
			self.setRobotStatusMessage(
															'Waiting for robot to complete insertion step 1')
			while not self.communication.Signal2:
				time.sleep(0.5)
			self.communication.Signal2 = 0
			self.setRobotStatusMessage('Robot has completed insertion step 1')

		def waitForRobotToInsert2(self):
			self.setRobotStatusMessage(
															'Waiting for robot to complete insertion step 2')
			while not self.communication.Signal4:
				time.sleep(0.5)
			self.communication.Signal4 = 0
			self.setRobotStatusMessage('Robot has completed insertion step 2')

		def robotReadyForExtraction(self):
			self.setRobotStatusMessage('Verifying robot is ready for extraction')
			while not self.communication.Signal5:
				time.sleep(0.5)
			self.communication.Signal5 = 0
			self.setRobotStatusMessage('Robot is ready for extraction')

		def waitForRobotToExtract(self):
			self.setRobotStatusMessage('Waiting for robot to complete extraction')
			while not self.communication.Signal7:
				time.sleep(0.5)
			self.communication.Signal7 = 0
			self.setRobotStatusMessage('Robot has completed extraction')

		def getGridNumber(self):
			gridnumber = -1
			while not validateGridNumber(gridnumber):
				try:
					gridnumber = self.gridqueue.get(block=False)
				except Queue.Empty:
					raise GridQueueEmpty
			return gridnumber

		def selectGrid(self):
			try:
				self.gridnumber = self.getGridNumber()
			except GridQueueEmpty:
				self.uicurrentgridnumber.set(None)
				raise
			else:
				self.uicurrentgridnumber.set(self.gridnumber)
				self.communication.gridNumber = self.gridnumber

		def robotReadyForInsertion(self):
			selectgrid = True
			while(selectgrid):
				try:
					self.selectGrid()
				except GridQueueEmpty:
					self.setStatusMessage('Grid queue is empty')
					raise
				try:
					self.waitForRobotGridLoad()
				except GridLoadException:
					selectgrid = True
				else:
					selectgrid = False

		def outputGridInsertedEvent(self):
			self.setStatusMessage('Sending notification the holder is inserted')
			evt = event.GridInsertedEvent()
			evt['grid number'] = self.gridnumber
			self.outputEvent(evt)
			self.setStatusMessage('Sent notification the holder is inserted')

		def outputGridExtractedEvent(self):
			self.setStatusMessage('Sending notification the holder is extracted')
			evt = event.GridExtractedEvent()
			evt['grid number'] = self.gridnumber
			self.gridnumber = None
			self.uicurrentgridnumber.set(None)
			self.outputEvent(evt)
			self.setStatusMessage('Sent notification the holder is extracted')

		def insert(self):
			self.insertmethod.disable()
			self.setStatusMessage('Inserting holder into microscope')

			try:
				self.robotReadyForInsertion()
			except GridQueueEmpty:
				self.insertmethod.enable()
				return

			try:
				self.scopeReadyForInsertion1()
			except ScopeException:
				self.insertmethod.enable()
				return
			self.signalRobotToInsert1()
			self.waitForRobotToInsert1()

			try:
				self.scopeReadyForInsertion2()
			except ScopeException:
				self.insertmethod.enable()
				return
			self.signalRobotToInsert2()
			self.waitForRobotToInsert2()

			self.outputGridInsertedEvent()

			self.setScopeStatusMessage('')
			self.setRobotStatusMessage('')
			self.setStatusMessage('Insertion of holder successfully completed')
			#self.insertmethod.enable()

		def extract(self):
			self.setStatusMessage('Extracting holder from microscope')

			self.robotReadyForExtraction()
			try:
				self.scopeReadyForExtraction()
			except ScopeException:
				return
			self.signalRobotToExtract()
			self.waitForRobotToExtract()

			self.outputGridExtractedEvent()

			self.setScopeStatusMessage('')
			self.setRobotStatusMessage('')
			self.setStatusMessage('Extraction of holder successfully completed')

		def handleInsert(self, ievent):
			self.insert()

		def handleExtract(self, ievent):
			self.extract()

		def gridQueueCallback(self, value):
			gridstring = str(value[0])
			lastvalue = value[0]
			c = False
			for i in value[1:]:
				if i - lastvalue == 1:
					c = True
				else:
					if c:
						gridstring += '-'
						gridstring += str(lastvalue)
						c = False
					gridstring += ', '
					gridstring += str(i)
				lastvalue = i

			if c:
				gridstring += '-'
				gridstring += str(lastvalue)

			self.uigridstring.set(gridstring)

		def uiAddGrid(self):
			gridnumber = self.uigridnumber.get()
			if validateGridNumber(gridnumber):
				self.gridqueue.put(gridnumber)

		def uiAddGridRange(self):
			try:
				gridrange = range(self.uigridrangestart.get(),
													self.uigridrangestop.get() + 1)
			except:
				return
			for gridnumber in gridrange:
				if validateGridNumber(gridnumber):
					self.gridqueue.put(gridnumber)

		def uiDeleteGrid(self):
			try:
				self.gridqueue.get(block=False)
			except Queue.Empty:
				pass

		def uiClearGridQueue(self):
			self.gridqueue.clear()

		def setStatusMessage(self, message):
			self.uistatusmessage.set(message)

		def setRobotStatusMessage(self, message):
			self.uirobotstatusmessage.set(message)

		def setScopeStatusMessage(self, message):
			self.uiscopestatusmessage.set(message)
		
		def defineUserInterface(self):
			RobotNode.defineUserInterface(self)

			self.uigridstring = uidata.String('Grids', [])
			griddeletemethod = uidata.Method('Delete', self.uiDeleteGrid)
			gridclearmethod = uidata.Method('Clear', self.uiClearGridQueue)

			self.uigridnumber = uidata.Integer('Grid Number', None, 'rw')
			gridaddmethod = uidata.Method('Add', self.uiAddGrid)

			self.uigridrangestart = uidata.Integer('From Grid Number', None, 'rw')
			self.uigridrangestop = uidata.Integer('To Grid Number', None, 'rw')
			gridaddrangemethod = uidata.Method('Add Range', self.uiAddGridRange)

			gridcontainer = uidata.Container('Grids')
			gridcontainer.addObjects((self.uigridstring,
																griddeletemethod, gridclearmethod,
																self.uigridnumber, gridaddmethod,
																self.uigridrangestart, self.uigridrangestop,
																gridaddrangemethod))

			self.uistatusmessage = uidata.String('Status', '', 'r')
			self.uiscopestatusmessage = uidata.String('Microscope Status', '', 'r')
			self.uirobotstatusmessage = uidata.String('Robot Status', '', 'r')
			self.uicurrentgridnumber = uidata.Integer('Current grid number',
																								None, 'r')
			statuscontainer = uidata.Container('Status')
			statuscontainer.addObjects((self.uistatusmessage,
																	self.uiscopestatusmessage,
																	self.uirobotstatusmessage,
																	self.uicurrentgridnumber))

			self.insertmethod = uidata.Method('Process Grids', self.insert)
			controlcontainer = uidata.Container('Control')
			controlcontainer.addObjects((self.insertmethod,))

			rccontainer = uidata.LargeContainer('Robot Control')
			rccontainer.addObjects((gridcontainer, statuscontainer, controlcontainer))
			self.uiserver.addObject(rccontainer)

class RobotNotification(RobotNode):
	eventinputs = RobotNode.eventinputs + [event.GridInsertedEvent,
																					event.GridExtractedEvent,
																					event.MosaicDoneEvent]
	eventoutputs = RobotNode.eventoutputs + [event.ExtractGridEvent,
																						event.InsertGridEvent,
																						event.PublishSpiralEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		RobotNode.__init__(self, id, session, nodelocations, **kwargs)

		self.addEventInput(event.GridInsertedEvent, self.handleGridInserted)
		self.addEventInput(event.GridExtractedEvent, self.handleGridExtracted)
		self.addEventInput(event.MosaicDoneEvent, self.handleGridDataCollectionDone)

		self.defineUserInterface()
		self.start()

	def handleGridInserted(self, ievent):
		self.setStatus('Grid inserted (event received)')

		self.setStatus('Checking vacuum')
		self.waitScope('vacuum status', 'ready', 0.5, 600)
		self.setStatus('Vacuum ready')

		self.setStatus('Checking column pressure')
		while self.getScope('column pressure') > 3.5e-5:
			time.sleep(2.0)
		self.setStatus('Column pressure ready')

		self.setStatus('Opening column valves')
		time.sleep(5.0)
		self.setScope('column valves', 'open')
		self.setStatus('Column valves open')

		self.setStatus('Checking camera is retracted')
		self.waitScope('inserted', False, 0.5, 60)
		self.setStatus('Camera is retracted')

		self.setStatus('Inserting camera')
		self.setScope('inserted', True)

		self.setStatus('Checking camera is inserted')
		self.waitScope('inserted', True, 0.5, 600)
		self.setStatus('Camera is inserted')

		self.setStatus('Outputting data collection event')
		self.outputEvent(event.PublishSpiralEvent())
		self.setStatus('Data collection event outputted')

	def handleGridDataCollectionDone(self, ievent):
		self.setStatus('Data collection finished (event received)')

		self.setStatus('Zeroing stage position')
		self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
		self.setStatus('Stage position zeroed')

		self.setStatus('Closing column valves')
		self.setScope('column valves', 'closed')
		self.setStatus('Column valves closed')

		self.setStatus('Retracting camera')
		self.setScope('inserted', False)

		self.setStatus('Checking camera is retracted')
		self.waitScope('inserted', False, 0.5, 600)
		self.setStatus('Camera is retracted')

		self.setStatus('Outputting grid extract event')
		self.outputEvent(event.ExtractGridEvent())
		self.setStatus('Grid extract event outputted')

	def handleGridExtracted(self, ievent):
		self.setStatus('Outputting grid insert event')
		evt = event.InsertGridEvent()
		evt['grid number'] = -1
		self.outputEvent(evt)
		self.setStatus('Grid insert event outputted')

	def defineUserInterface(self):
		RobotNode.defineUserInterface(self)

		self.statuslabel = uidata.String('Current Operation', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statuslabel,))

		container = uidata.LargeContainer('Robot Notification')
		container.addObjects((statuscontainer,))
		self.uiserver.addObject(container)

