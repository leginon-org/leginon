#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#
import time
import sys
import node
import data
import event
import threading
import emailnotification
import project
import EM
import Image
import gui.wx.Robot

# ...
def seconds2str(seconds):
	seconds = int(seconds)
	minute = 60
	hour = 60*minute
	day = 24*hour
	week = 7*day

	weeks = seconds / week
	string = ''
	if weeks:
		if weeks == 1:
			value = ''
		else:
			value = 's'
		string += '%i week%s, ' % (weeks, value)
	seconds %= week

	days = seconds / day
	if days or string:
		if days == 1:
			value = ''
		else:
			value = 's'
		string += '%i day%s, ' % (days, value)
	seconds %= day

	hours = seconds / hour
	if hours or string:
		if hours == 1:
			value = ''
		else:
			value = 's'
		string += '%i hour%s, ' % (hours, value)
	seconds %= hour

	minutes = seconds / minute
	if minutes or string:
		if minutes == 1:
			value = ''
		else:
			value = 's'
		string += '%i minute%s, ' % (minutes, value)
	seconds %= minute

	if seconds or string:
		if seconds == 1:
			value = ''
		else:
			value = 's'
		string += '%i second%s' % (seconds, value)
	return string

class TestCommunication(object):
	def __init__(self):
		self.gridNumber = -1
		for i in range(11):
			setattr(self, 'Signal' + str(i), 0)

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

class RobotNode(node.Node):
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.abort = False
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)

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
		parameterdata = self.emclient.getScope(key)
		if parameterdata is None:
			raise ScopeException('cannot get parameter value')
		self.logger.info('Get scope %s, %s' % (key, parameterdata))
		return parameterdata

	def setScope(self, key, value):
		scopedata = data.ScopeEMData()
		scopedata[key] = value
		try:
			self.emclient.setScope(scopedata)
		except:
			raise ScopeException('cannot set parameter to value')

class Request(object):
	def __init__(self):
		self.event = threading.Event()

class InsertRequest(Request):
	pass

class ExtractRequest(Request):
	pass

class ExitRequest(Request):
	pass

if sys.platform == 'win32':
	import pythoncom
	import win32com.client
	import pywintypes
	import Queue

class RobotControl(RobotNode):
	panelclass = gui.wx.Robot.ControlPanel
	eventinputs = RobotNode.eventinputs + [event.ExtractGridEvent,
																					event.InsertGridEvent,]
	eventoutputs = RobotNode.eventoutputs + [event.GridInsertedEvent,
																						event.GridExtractedEvent,
																						event.EmailEvent]
	def __init__(self, id, session, managerlocation, **kwargs):

		self.simulate = False
		#self.simulate = True

		RobotNode.__init__(self, id, session, managerlocation, **kwargs)
		self.gridnumber = None
		self.griddata = None
		self.timings = {}
		self.gridcleared = threading.Event()

		self.emailclient = emailnotification.EmailClient(self)

		# if label is same, kinda screwed
		self.gridtrayids = {}
		projectdata = project.ProjectData()
		gridboxes = projectdata.getGridBoxes()
		for i in gridboxes.getall():
			self.gridtrayids[i['label']] = i['gridboxId']

		self.queue = Queue.Queue()
		threading.Thread(name='robot control queue handler thread',
											target=self._queueHandler).start()

		self.addEventInput(event.InsertGridEvent, self.handleInsert)
		self.addEventInput(event.ExtractGridEvent, self.handleExtract)

		self.start()

	def _queueHandler(self):
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		if self.simulate:
				self.communication = TestCommunication()
		else:
			try:
				self.communication = win32com.client.Dispatch(
																								'RobotCommunications.Signal')
			except pywintypes.com_error, e:
				raise RuntimeError('Cannot initialized robot communications')

		while True:
			request = self.queue.get()
			if isinstance(request, InsertRequest):
				self._insert()
			elif isinstance(request, ExtractRequest):
				self._extract()
			elif isinstance(request, ExitRequest):
				request.event.set()
				break
			else:
				self.logger.error('Invalid request put in queue')
			request.event.set()
		del self.communication

	def exit(self):
		request = ExitRequest()
		self.queue.put(request)
		request.event.wait()
		RobotNode.exit(self)

	def zeroStage(self):
		self.logger.info('Zeroing stage position')
		self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
		self.logger.info('Stage position is zeroed')

	def holderNotInScope(self):
		self.logger.info('Verifying there is no holder inserted')
		self.waitScope('holder status', 'not inserted')
		self.logger.info('No holder currently inserted')

	def holderInScope(self):
		self.logger.info('Verifying holder is inserted')
		self.waitScope('holder status', 'inserted')
		self.logger.info('No holder currently inserted')

	def vacuumReady(self):
		self.logger.info('Verifying vacuum is ready')
		self.waitScope('vacuum status', 'ready', 0.5, 600)
		self.logger.info('Vacuum is ready')

	def closeColumnValves(self):
		self.logger.info('Closing column valves')
		self.setScope('column valves', 'closed')
		self.logger.info('Verifying column valves are closed')
		self.waitScope('column valves', 'closed', 0.5, 15)
		self.logger.info('Column valves are closed')

	def turboPumpOn(self):
		self.logger.info('Turning on turbo pump')
		self.setScope('turbo pump', 'on')
		self.logger.info('Verifying turbo pump is on')
		self.waitScope('turbo pump', 'on', 0.5, 300)
		self.logger.info('Turbo pump is on')

	def stageReady(self):
		self.logger.info('Waiting for stage to be ready')
		self.waitScope('stage status', 'ready', 0.5, 600)
		self.logger.info('Stage is ready')

	def setHolderType(self):
		self.logger.info('Setting holder type to single tilt')
		self.setScope('holder type', 'single tilt')
		self.logger.info('Verifying holder type is set to single tilt')
		self.waitScope('holder type', 'single tilt', 0.5, 60)
		self.logger.info('Holder type is set to single tilt')

	def scopeReadyForInsertion1(self):
		self.logger.info('Readying microscope for insertion step 1')
		self.zeroStage()
		self.holderNotInScope()
		self.vacuumReady()
		self.closeColumnValves()
		self.turboPumpOn()
		self.stageReady()
		self.logger.info('Microscope ready for insertion step 1')

	def scopeReadyForInsertion2(self):
		self.logger.info('Readying microscope for insertion step 2')
		self.setHolderType()
		self.stageReady()
		self.logger.info('Microscope ready for insertion step 2')

	def scopeReadyForExtraction(self):
		self.logger.info('Readying microscope for extraction')
		self.zeroStage()
		self.holderInScope()
		self.vacuumReady()
		self.closeColumnValves()
		self.stageReady()
		self.logger.info('Microscope ready for extraction')

	def signalRobotToInsert1(self):
		self.logger.info('Signaling robot to begin insertion step 1')
		self.communication.Signal1 = 1
		self.logger.info('Signaled robot to begin insertion step 1')

	def signalRobotToInsert2(self):
		self.logger.info('Signaling robot to begin insertion step 2')
		self.communication.Signal3 = 1
		self.logger.info('Signaled robot to begin insertion step 2')

	def signalRobotToExtract(self):
		self.logger.info('Signaling robot to begin extraction')
		self.communication.Signal6 = 1
		self.logger.info('Signaled robot to begin extraction')

	def emailGridClear(self):
		if self.gridnumber is None:
			gridnumber = '(unknown)'
		else:
			gridnumber = self.gridnumber
		subject = 'Grid #%s failed to be removed from specimen holder properly' % gridnumber
		text = 'Reply to this message if grid is no longer in the specimen holder.\nImage of the specimen holder is attached.'
		time.sleep(5.0)
		try:
			raise NotImplemetedError
			image = Image.open(imagefilename)
			imagestring = emailnotification.PILImage2String(image)
		except:
			imagestring = None
		self.emailclient.sendAndSet(self.gridcleared, subject, text, imagestring)

	def waitForGridClear(self):
		self.gridcleared.clear()
		self.logger.warning('Waiting for confirmation that grid is clear')
		self.setStatus('user input')
		self.emailGridClear()
		self.gridcleared.wait()
		self.gridcleared = threading.Event()
		self.setStatus('idle')
		self.logger.info('Resuming operation')
		self.communication.Signal10 = 1

	def gridCleared(self):
		self.gridcleared.set()

	def waitForRobotGridLoad(self):
		self.logger.info('Verifying robot is ready for insertion')
		while not self.communication.Signal0:
			if self.communication.Signal8:
				self.logger.warning('Robot failed to extract grid from tray')
				self.communication.Signal8 = 0
				raise GridLoadException
			time.sleep(0.5)
		self.communication.Signal0 = 0
		self.logger.info('Robot is ready for insertion')

	def waitForRobotToInsert1(self):
		self.logger.info('Waiting for robot to complete insertion step 1')
		while not self.communication.Signal2:
			time.sleep(0.5)
		self.communication.Signal2 = 0
		self.logger.info('Robot has completed insertion step 1')

	def waitForRobotToInsert2(self):
		self.logger.info('Waiting for robot to complete insertion step 2')
		while not self.communication.Signal4:
			time.sleep(0.5)
		self.communication.Signal4 = 0
		self.logger.info('Robot has completed insertion step 2')

	def robotReadyForExtraction(self):
		self.logger.info('Verifying robot is ready for extraction')
		while not self.communication.Signal5:
			time.sleep(0.5)
		self.communication.Signal5 = 0
		self.logger.info('Robot is ready for extraction')

	def waitForRobotToExtract(self):
		self.logger.info('Waiting for robot to complete extraction')
		while not self.communication.Signal7:
			if self.communication.Signal9:
				self.logger.warning('Robot failed to remove grid from specimen holder')
				self.communication.Signal9 = 0
				self.waitForGridClear()
			time.sleep(0.5)
		self.communication.Signal7 = 0
		self.logger.info('Robot has completed extraction')

	def getGridNumber(self):
		gridnumber = -1
		while not validateGridNumber(gridnumber):
			gridnumber = self.panel.getNextGrid()
			if gridnumber is None:
				raise GridQueueEmpty
		return gridnumber

	def newGrid(self, gridboxid, gridnumber):
		projectdata = project.ProjectData()
		return projectdata.newGrid('Robot #%d' % gridnumber, -1, gridnumber,
																gridboxid, gridnumber)

	def getGridID(self, gridboxid, gridnumber):
		projectdata = project.ProjectData()
		gridlocations = projectdata.getGridLocations()
		gridboxidindex = gridlocations.Index(['gridboxId'])
		gridlocations = gridboxidindex[gridboxid].fetchall()
		for gridlocation in gridlocations:
			if gridlocation['location'] == gridnumber:
				return gridlocation['gridId']
		return self.newGrid(gridboxid, gridnumber)

	def selectGrid(self):
		try:
			self.gridnumber = self.getGridNumber()
			gridid = self.getGridID(self.gridtrayid, self.gridnumber)
			initializer = {'grid ID': gridid}
			self.griddata = data.GridData(initializer=initializer)
		except GridQueueEmpty:
			raise
		else:
			self.logger.info('Current grid: %d' % self.gridnumber)
			self.communication.gridNumber = self.gridnumber

	def robotReadyForInsertion(self):
		selectgrid = True
		while(selectgrid):
			try:
				self.selectGrid()
			except GridQueueEmpty:
				self.logger.info('Grid queue is empty')
				raise
			if self.simulate:
				return
			try:
				self.waitForRobotGridLoad()
			except GridLoadException:
				selectgrid = True
			else:
				selectgrid = False

	def outputGridInsertedEvent(self):
		self.logger.info('Sending notification the holder is inserted')
		evt = event.GridInsertedEvent()
		evt['grid'] = self.griddata
		self.outputEvent(evt)
		self.logger.info('Sent notification the holder is inserted')

	def outputGridExtractedEvent(self):
		self.logger.info('Sending notification the holder is extracted')
		evt = event.GridExtractedEvent()
		evt['grid'] = self.griddata
		self.outputEvent(evt)
		self.gridnumber = None
		self.griddata = None
		self.logger.info('Sent notification the holder is extracted')

	def estimateTimeLeft(self):
		if 'insert' not in self.timings:
			self.timings['insert'] = []
		self.timings['insert'].append(time.time())

		timestring = ''
		ntimings = len(self.timings['insert']) - 1
		if ntimings > 0:
			first = self.timings['insert'][0]
			last = self.timings['insert'][-1]
			ngridsleft = self.panel.getGridQueueSize()
			secondsleft = (last - first)/ntimings*ngridsleft
			timestring = seconds2str(secondsleft)
		if timestring:
			self.logger.info(timestring + ' remaining')

	def _insert(self):
		if self.simulate:
			#self.insertmethod.disable()
			self.estimateTimeLeft()
			try:
				self.robotReadyForInsertion()
			except GridQueueEmpty:
				#self.insertmethod.enable()
				return
			self.outputGridInsertedEvent()
			return

		#self.insertmethod.disable()
		self.estimateTimeLeft()

		self.logger.info('Inserting holder into microscope')

		try:
			self.robotReadyForInsertion()
		except GridQueueEmpty:
			#self.insertmethod.enable()
			return

		try:
			self.scopeReadyForInsertion1()
		except ScopeException:
			#self.insertmethod.enable()
			return
		self.signalRobotToInsert1()
		self.waitForRobotToInsert1()

		try:
			self.scopeReadyForInsertion2()
		except ScopeException:
			#self.insertmethod.enable()
			return
		self.signalRobotToInsert2()
		self.waitForRobotToInsert2()

		self.outputGridInsertedEvent()

		self.logger.info('Insertion of holder successfully completed')

	def _extract(self):
		if self.simulate:
			self.outputGridExtractedEvent()
			return

		self.logger.info('Extracting holder from microscope')

		self.robotReadyForExtraction()
		try:
			self.scopeReadyForExtraction()
		except ScopeException:
			return
		self.signalRobotToExtract()
		self.waitForRobotToExtract()

		self.outputGridExtractedEvent()

		self.logger.info('Extraction of holder successfully completed')

	def insert(self):
		request = InsertRequest()
		self.queue.put(request)
		request.event.wait()

	def extract(self):
		request = ExtractRequest()
		self.queue.put(request)
		request.event.wait()

	def handleInsert(self, ievent):
		self.insert()

	def handleExtract(self, ievent):
		self.extract()

	def gridQueueCallback(self, value):
		'''
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
		'''

		self.uigridtray.set(value)

	def getTrayLabels(self):
		return self.gridtrayids.keys()

	def setTray(self, traylabel):
		try:
			self.gridtrayid = self.gridtrayids[traylabel]
		except KeyError:
			raise ValueError('unknown tray label')
	
	def getGridLocations(self, traylabel):
		try:
			gridboxid = self.gridtrayids[traylabel]
		except KeyError:
			raise ValueError('unknown tray label')
		projectdata = project.ProjectData()
		gridlocations = projectdata.getGridLocations()
		gridboxidindex = gridlocations.Index(['gridboxId'])
		gridlocations = gridboxidindex[gridboxid].fetchall()
		return [int(i['location']) for i in gridlocations]

class RobotNotification(RobotNode):
	panelclass = gui.wx.Robot.NotificationPanel
	eventinputs = RobotNode.eventinputs + [event.GridInsertedEvent,
																					event.GridExtractedEvent,
																					event.MosaicDoneEvent,
																					event.TargetListDoneEvent]
	eventoutputs = RobotNode.eventoutputs + [event.ExtractGridEvent,
																						event.InsertGridEvent,
																						event.MakeTargetListEvent]
	def __init__(self, id, session, managerlocation, **kwargs):

		self.simulate = False
		#self.simulate = True

		RobotNode.__init__(self, id, session, managerlocation, **kwargs)

		self.addEventInput(event.GridInsertedEvent, self.handleGridInserted)
		self.addEventInput(event.GridExtractedEvent, self.handleGridExtracted)
		self.addEventInput(event.MosaicDoneEvent, self.handleGridDataCollectionDone)
		self.addEventInput(event.TargetListDoneEvent,
												self.handleGridDataCollectionDone)

		self.start()

	def handleGridInserted(self, ievent):
		if self.simulate:
			evt = event.MakeTargetListEvent()
			evt['grid'] = ievent['grid']
			self.outputEvent(evt)
			return

		self.logger.info('Grid inserted (event received)')

		self.logger.info('Checking vacuum')
		self.waitScope('vacuum status', 'ready', 0.5, 600)
		self.logger.info('Vacuum ready')

		self.logger.info('Checking column pressure')
		while self.getScope('column pressure') > 3.5e-5:
			time.sleep(2.0)
		self.logger.info('Column pressure ready')

		self.logger.info('Opening column valves')
		time.sleep(5.0)
		self.setScope('column valves', 'open')
		self.logger.info('Column valves open')

		'''
		self.logger.info('Checking camera is retracted')
		self.waitScope('inserted', False, 0.5, 60)
		self.logger.info('Camera is retracted')

		self.logger.info('Inserting camera')
		self.setScope('inserted', True)

		self.logger.info('Checking camera is inserted')
		self.waitScope('inserted', True, 0.5, 600)
		self.logger.info('Camera is inserted')
		'''

		self.logger.info('Outputting data collection event')
		evt = event.MakeTargetListEvent()
		evt['grid'] = ievent['grid']
		self.outputEvent(evt)
		self.logger.info('Data collection event outputted')

	def handleGridDataCollectionDone(self, ievent):
		self.extract()

	def extract(self):
		if self.simulate:
			self.outputEvent(event.ExtractGridEvent())
			return

		self.logger.info('Data collection finished (event received)')

		self.logger.info('Zeroing stage position')
		self.setScope('stage position', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0})
		self.logger.info('Stage position zeroed')

		self.logger.info('Closing column valves')
		self.setScope('column valves', 'closed')
		self.logger.info('Column valves closed')

		'''
		self.logger.info('Retracting camera')
		self.setScope('inserted', False)

		self.logger.info('Checking camera is retracted')
		self.waitScope('inserted', False, 0.5, 600)
		self.logger.info('Camera is retracted')
		'''

		self.logger.info('Outputting grid extract event')
		self.outputEvent(event.ExtractGridEvent())
		self.logger.info('Grid extract event outputted')

	def handleGridExtracted(self, ievent):
		self.insert()

	def insert(self):
		self.logger.info('Outputting grid insert event')
		evt = event.InsertGridEvent()
		self.outputEvent(evt)
		self.logger.info('Grid insert event outputted')

