import time
import sys
import node
import data
import uidata
import event
import threading

#class TestCommunications(object):
#	def __init__(self):
#		self.Signal0 = 1
#		self.Signal1 = 1
#		self.Signal2 = 1
#		self.Signal3 = 1
#		self.Signal4 = 1
#		self.Signal5 = 1
#		self.Signal6 = 1
#		self.Signal7 = 1

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
						raise RuntimeError('parameter is not set to value')
				parametervalue = self.getScope(parameter)
		else:
			if parametervalue != value:
				raise RuntimeError('parameter is not set to value')

	def getScope(self, key):
		parameterdata = self.researchByDataID((key,))
		if parameterdata is None:
			raise RuntimeError('cannot get parameter value')
		print key, parameterdata[key]
		return parameterdata[key]

	def setScope(self, key, value):
		scopedata = data.AllEMData()
		scopedata['id'] = ('scope',)
		scopedata[key] = value
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			raise RuntimeError('cannot set parameter to value')

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
	
			#self.communication = TestCommunications()

			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
	
			try:
				self.communication = win32com.client.Dispatch('RobotCommunications.Signal')
			except pywintypes.com_error, e:
				print e
				raise RuntimeError('Cannot initialized robot communications')
	
			self.addEventInput(event.InsertGridEvent, self.handleInsert)
			self.addEventInput(event.ExtractGridEvent, self.handleExtract)

			self.defineUserInterface()
			self.start()

		def __del__(self):
			self.communication = None

		def insertStage(self):
			self.insertmethod.disable()
			self.extractmethod.disable()
			self.setStatus('Verifying robot is ready for insertion')
			while not self.communication.Signal0:
				time.sleep(0.5)
			self.communication.Signal0 = 0
			self.setStatus('Robot is ready for insertion')
	
			self.setStatus('Zeroing stage position')
			self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
			self.setStatus('Stage position is zeroed')
	
			self.setStatus('Verifying there is no holder inserted')
			self.waitScope('holder status', 'not inserted')
			self.setStatus('No holder currently inserted')

			self.setStatus('Verifying vacuum is ready')
			self.waitScope('vacuum status', 'ready', 0.5, 600)
			self.setStatus('Vacuum is ready')

			self.setStatus('Closing column valves')
			self.setScope('column valves', 'closed')
			self.setStatus('Verifying column valves are closed')
			self.waitScope('column valves', 'closed', 0.5, 15)
			self.setStatus('Column valves are closed')

			self.setStatus('Turning on turbo pump')
			self.setScope('turbo pump', 'on')
			self.setStatus('Verifying turbo pump is on')
			self.waitScope('turbo pump', 'on', 0.5, 300)
			self.setStatus('Turbo pump is on')

			self.setStatus('Waiting for stage to be ready')
			self.waitScope('stage status', 'ready', 0.5, 600)
			self.setStatus('Stage is ready, signaled robot to begin insertion step 1')

			self.communication.Signal1 = 1

			self.setStatus('Waiting for robot to complete insertion step 1')
			while not self.communication.Signal2:
				time.sleep(0.5)
			self.communication.Signal2 = 0
			self.setStatus('Robot has completed insertion step 1')

			self.setStatus('Setting holder type to single tilt')
			self.setScope('holder type', 'single tilt')
			self.setStatus('Verifying holder type is set to single tilt')
			self.waitScope('holder type', 'single tilt', 0.5, 60)
			self.setStatus('Holder type is set to single tilt')

			self.setStatus('Waiting for stage to be ready')
			self.waitScope('stage status', 'ready', 0.5, 600)
			self.setStatus('Stage is ready, signaled robot to begin insertion step 2')

			self.communication.Signal3 = 1

			self.setStatus('Waiting for robot to complete insertion step 2')
			while not self.communication.Signal4:
				time.sleep(0.5)
			self.communication.Signal4 = 0
			self.setStatus('Robot has completed insertion step 2')
			self.insertmethod.enable()
			self.extractmethod.enable()
			self.setStatus('Outputting inserted event')
			evt = event.GridInsertedEvent()
			evt['grid number'] = -1
			self.outputEvent(evt)
			self.setStatus('Robot has completed insertion')

		def handleInsert(self, ievent):
			self.insert()

		def handleExtract(self, ievent):
			self.extract()

		def extractStage(self):
			self.insertmethod.disable()
			self.extractmethod.disable()
			self.setStatus('Verifying robot is ready for extraction')
			while not self.communication.Signal5:
				time.sleep(0.5)
			self.communication.Signal5 = 0
			self.setStatus('Robot is ready for extraction')
	
			self.setStatus('Zeroing stage position')
			self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
			self.setStatus('Stage position is zeroed')

			self.setStatus('Verifying holder is inserted')
			self.waitScope('holder status', 'inserted')
			self.setStatus('Holder is currently inserted')

			self.setStatus('Verifying vacuum is ready')
			self.waitScope('vacuum status', 'ready', 0.5, 600)
			self.setStatus('Vacuum is ready')

			self.setStatus('Closing column valves')
			self.setScope('column valves', 'closed')
			self.setStatus('Verifying column valves are closed')
			self.waitScope('column valves', 'closed', 0.5, 15)
			self.setStatus('Column valves are closed')

			self.setStatus('Waiting for stage to be ready')
			self.waitScope('stage status', 'ready', 0.5, 600)
			self.setStatus('Stage is ready, signaled robot to begin extraction')

			self.communication.Signal6 = 1

			self.setStatus('Waiting for robot to complete extraction')
			while not self.communication.Signal7:
				time.sleep(0.5)
			self.communication.Signal7 = 0

			self.insertmethod.enable()
			self.extractmethod.enable()

			self.setStatus('Outputting extracted event')
			evt = event.GridExtractedEvent()
			evt['grid number'] = -1
			self.outputEvent(evt)
			self.setStatus('Robot has completed extraction')

		def insert(self):
			self.setStatus('Inserting stage')
			try:
				self.insertStage()
			except RuntimeError:
				self.setStatus('Error inserting stage')

		def extract(self):
			self.setStatus('Extracting stage')
			try:
				self.extractStage()
			except RuntimeError:
				self.setStatus('Error extracting stage')
		
		def defineUserInterface(self):
			RobotNode.defineUserInterface(self)

			self.statuslabel = uidata.String('Current Operation', '', 'r')
			statuscontainer = uidata.Container('Status')
			statuscontainer.addObjects((self.statuslabel,))

			self.insertmethod = uidata.Method('Insert', self.insert)
			self.extractmethod = uidata.Method('Extract', self.extract)
			controlcontainer = uidata.Container('Control')
			controlcontainer.addObjects((self.insertmethod, self.extractmethod))
	
			rccontainer = uidata.MediumContainer('Robot Control')
			rccontainer.addObjects((statuscontainer, controlcontainer))
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

		container = uidata.MediumContainer('Robot Notification')
		container.addObjects((statuscontainer,))
		self.uiserver.addObject(container)

class RobotTest(node.Node):
	eventinputs = RobotNode.eventinputs + [event.ExtractGridEvent,
																					event.InsertGridEvent,]
	eventoutputs = RobotNode.eventoutputs + [event.GridInsertedEvent,
																						event.GridExtractedEvent,
																						event.MosaicDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)

		self.addEventInput(event.ExtractGridEvent, self.handleExtract)
		self.addEventInput(event.InsertGridEvent, self.handleInsert)

		self.defineUserInterface()
		self.start()

	def insertStage(self):
		print 'insertStage'
		self.insertmethod.disable()
		self.extractmethod.disable()

		self.insertmethod.enable()
		self.extractmethod.enable()
		print 'insertStage outputting event'
		evt = event.GridInsertedEvent()
		evt['grid number'] = -1
		self.outputEvent(evt)
		print 'insertStage Done'

	def handleInsert(self, ievent):
		self.insert()

	def handleExtract(self, ievent):
		self.extract()

	def extractStage(self):
		print 'extractStage'
		self.insertmethod.disable()
		self.extractmethod.disable()

		self.insertmethod.enable()
		self.extractmethod.enable()

		print 'extractStage, outputting extracted event'
		evt = event.GridExtractedEvent()
		evt['grid number'] = -1
		self.outputEvent(evt)
		print 'extractStage done'

	def insert(self):
		print 'robot insert'
		try:
			self.insertStage()
		except RuntimeError:
			pass

	def extract(self):
		print 'robot extract'
		try:
			self.extractStage()
		except RuntimeError:
			pass

	def mosaicDone(self):
		evt = event.MosaicDoneEvent()
		self.outputEvent(evt)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.insertmethod = uidata.Method('Insert', self.insert)
		self.extractmethod = uidata.Method('Extract', self.extract)
		self.mosaicmethod = uidata.Method('Mosaic Done', self.mosaicDone)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.insertmethod, self.extractmethod,
																										self.mosaicmethod))

		rccontainer = uidata.MediumContainer('Robot Test')
		rccontainer.addObjects((controlcontainer,))
		self.uiserver.addObject(rccontainer)

