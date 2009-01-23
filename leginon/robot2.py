#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#
import Image
import sys
import threading
import time
import data
import emailnotification
import event
import instrument
import node
import project
import gui.wx.Robot
import Queue
import sinedon

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

## these are the names of the robot attributes
robotattrs = ['Signal' + str(i) for i in range(0,13)]
robotattrs.append('gridNumber')

class TestCommunication(object):
	def __init__(self):
		self.gridNumber = -1
		for a in robotattrs:
			setattr(self, a, 0)

robotattrtypemap = [(robotattr, int) for robotattr in robotattrs]
class RobotAttributes(sinedon.Data):
	"sinedon object to contain robot attributes"
	def typemap(cls):
		return sinedon.Data.typemap() + tuple(robotattrtypemap)
	typemap = classmethod(typemap)
	
class DatabaseCommunication(object):
	def __setattr__(self, name, value):
		print 'SET', name, value
		## get current robot attrs from DB
		rattrs = RobotAttributes().query(results=1)
		if rattrs:
			# copy the old one
			rattrs = RobotAttributes(initializer=rattrs[0])
		else:
			# create a new one if
			rattrs = RobotAttributes()
		## update one of the attrs
		rattrs[name] = value
		## store new attrs to DB
		rattrs.insert(force=True)

	def __getattr__(self, name):
		## get current robot attrs from DB
		rattrs = RobotAttributes().query(results=1)
		if rattrs is None:
			return None	
		else:
			return rattrs[0][name]

class RobotException(Exception):
	pass

class GridException(Exception):
	pass

class GridQueueEmpty(GridException):
	pass

class GridLoadError(GridException):
	pass

class GridLoadFromTrayError(GridException):
	pass

class GridUnloadError(GridException):
	pass

def validateGridNumber(gridnumber):
	if not isinstance(gridnumber, int):
		return False
	if gridnumber >= 1 and gridnumber <= 96:
		return True
	else:
		return False

class Request(object):
	def __init__(self):
		self.event = threading.Event()

class ExitRequest(Request):
	pass

class GridRequest(Request):
	def __init__(self, number, gridid=None, node=None, griddata=None):
		Request.__init__(self)
		self.number = number
		self.loaded = False
		self.gridid = gridid
		self.node = node
		self.griddata = griddata

class Robot2(node.Node):
	panelclass = gui.wx.Robot.Panel
	eventinputs = node.Node.eventinputs + [event.TargetListDoneEvent,
																					event.UnloadGridEvent,
																					event.QueueGridEvent,
																					event.QueueGridsEvent,
																					event.MosaicDoneEvent]
	eventoutputs = node.Node.eventoutputs + [event.MakeTargetListEvent,
																						event.GridLoadedEvent,
																						event.EmailEvent]
	settingsclass = data.RobotSettingsData
	defaultsettings = {
		'column pressure threshold': 3.5e-5,
		'default Z position': -140e-6,
		'simulate': False,
		'turbo on': True,
		'pause': False,
		'grid tray': None,
		'grid clear wait': False,
	}
	defaultcolumnpressurethreshold = 3.5e-5
	defaultzposition = -140e-6
	def __init__(self, id, session, managerlocation, **kwargs):


		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session)

		self.timings = {}

		self.gridnumber = None
		self.startevent = threading.Event()
		self.exitevent = threading.Event()
		self.extractinfo = None
		self.extractcondition = threading.Condition()
		self.gridcleared = threading.Event()
		self.usercontinue = threading.Event()

		self.emailclient = emailnotification.EmailClient(self)
		self.simulate = False
		self.startnowait = False

		self.traysFromDB()

		self.queue = Queue.Queue()
		threading.Thread(name='robot control queue handler thread',
											target=self._queueHandler).start()

		self.addEventInput(event.MosaicDoneEvent, self.handleGridDataCollectionDone)
		self.addEventInput(event.TargetListDoneEvent,
												self.handleGridDataCollectionDone)
		self.addEventInput(event.QueueGridEvent, self.handleQueueGrid)
		self.addEventInput(event.QueueGridsEvent, self.handleQueueGrids)
		self.addEventInput(event.UnloadGridEvent, self.handleUnloadGrid)

		self.start()

	def traysFromDB(self):
		# if label is same, kinda screwed
		self.gridtrayids = {}
		self.gridtraylabels = {}
		try:
			projectdata = project.ProjectData()
			gridboxes = projectdata.getGridBoxes()
			for i in gridboxes.getall():
				self.gridtrayids[i['label']] = i['gridboxId']
				self.gridtraylabels[i['gridboxId']] = i['label']
		except Exception, e:
			self.logger.error('Failed to connect to the project database: %s' % e)

	def userContinue(self):
		self.usercontinue.set()

	def handleQueueGrids(self, ievent):
		'''
		Handle queue of grids from another node.
		Wait for user to click start before inserting into the queue.
		'''

		# wait for user to start
		self.logger.info('Grid load request has been made' + ', press \'Start\' button to begin processing')
		self.setStatus('user input')
		self.startevent.clear()
		self.startevent.wait()

		nodename = ievent['node']
		# insert all the grids before handling them
		for gridid in ievent['grid IDs']:
			number = self.getGridNumber(gridid)
			while number is None:
				self.setStatus('idle')
				self.logger.info('Waiting for user to switch tray')
				self.setStatus('user input')
				self.panel.onWaitForTrayChanged()
				self.startevent.clear()
				self.startevent.wait()
				number = self.getGridNumber(gridid)
			request = GridRequest(number, gridid, nodename)
			self.queue.put(request)
		self.startnowait = True
		self._queueHandler()
		
	def handleQueueGrid(self, ievent):
		newevent = {}
		newevent['node'] = ievent['node']
		newevent['grid IDs'] = [ievent['grid ID'],]
		self.handleQueueGrids(newevent)

	def handleUnloadGrid(self, evt):
		gridid = evt['grid ID']
		node = evt['node']
		self.extractcondition.acquire()
		self.extractinfo = (gridid, node)
		self.extractcondition.notify()
		self.extractcondition.release()

	def getCommunication(self):
		if self.settings['simulate']:
			self.simulate = True
			return TestCommunication()
		try:
			com = DatabaseCommunication()
			self.simulate = False
		except:
			com = TestCommunication()
			self.simulate = True
		return com

	def _queueHandler(self):
		self.logger.info('_queueHandler '+str(self.simulate)+' setting'+str(self.settings['simulate']))

		self.communication = self.getCommunication()

		request = None

		self.communication.Signal11 = int(self.settings['grid clear wait'])

		while True:
			### need to wait if something goes wrong
			if not self.startnowait:
				self.usercontinue.clear()
				self.usercontinue.wait()

			if self.exitevent.isSet():
				break

			while True:

				try:
					request = self.queue.get(block=False)
					if isinstance(request, ExitRequest):
						break
				except Queue.Empty:
					request = self.getUserGridRequest()
					if request is None:
						self.startnowait = False
						break

				gridid = request.gridid
				evt = event.GridLoadedEvent()
				evt['request node'] = request.node
				evt['grid'] = data.GridData(initializer={'grid ID': gridid})
				evt['status'] = 'failed'
				gridnumber = request.number
				
				self.selectGrid(gridnumber)
				if gridnumber is None:
					evt['status'] = 'invalid'
					self.outputEvent(evt)
					return

				self.communication = self.getCommunication()

				self.setStatus('processing')
				self.selectGrid(gridnumber)
				self.logger.info('grid selected')
				self.gridnumber = gridnumber

				try:
					griddata = self.insert()
				except GridLoadError:
					self.gridnumber = None
					continue

				except GridLoadFromTrayError:
					self.gridnumber = None
					self.startnowait = True
					self.outputEvent(evt)
					request.event.set()
					continue

				self.setStatus('idle')

				evt['grid'] = griddata

				if griddata is None:
					break

				self.startnowait = False
				if hasattr(request, 'loaded'):
					evt['status'] = 'ok'
				if hasattr(request, 'griddata'):
					request.griddata = griddata


				self.outputEvent(evt)
				request.event.set()

				self.extractcondition.acquire()
				if request.gridid is None and request.node is None:
					self.panel.gridInserted()
				while (self.extractinfo is None
								or self.extractinfo != (request.gridid, request.node)):
					self.extractcondition.wait()

				self.communication = self.getCommunication()

				self.setStatus('processing')
				self.extractinfo = None
				self.extractcondition.release()

				self.extract()
				self.gridnumber = None
				self.setStatus('idle')

			self.setStatus('idle')
			self.panel.gridQueueEmpty()

		del self.communication

	def startProcessing(self):
		self.startevent.set()

	def exit(self):
		self.exitevent.set()
		self.startevent.set()
		node.Node.exit(self)

	def lockScope(self):
		self.logger.info('Locking scope...')
		self.instrument.tem.lock()
		self.logger.info('Scope locked.')

	def unlockScope(self):
		self.logger.info('Unlocking scope...')
		self.instrument.tem.unlock()
		self.logger.info('Scope unlocked.')

	def zeroStage(self):
		while True:
			self.logger.info('Zeroing stage position...')
			self.instrument.tem.StagePosition = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0}
			if self.stageIsZeroed():
				break
			else:
				self.logger.info('Stage is not zeroed, trying again...')
		self.logger.info('Stage position is zeroed.')

	def stageIsZeroed(self, xyzlimit=1e-6, alimit=0.001):
		stage = self.instrument.tem.StagePosition
		x = abs(stage['x'])
		y = abs(stage['y'])
		z = abs(stage['z'])
		a = abs(stage['a'])
		if x<xyzlimit and y<xyzlimit and z<xyzlimit and a<alimit:
			return True
		else:
			return False

	def moveStagePositionZ(self,zval):
		self.logger.info("Move stage position Z to: %s",zval)
		self.instrument.tem.StagePosition = {'z': zval}

	def holderNotInScope(self):
		self.logger.info('Verifying there is no holder inserted...')
		self.waitScope('HolderStatus', 'not inserted')
		self.logger.info('No holder currently inserted.')

	def holderInScope(self):
		self.logger.info('Verifying holder is inserted...')
		self.waitScope('HolderStatus', 'inserted')
		self.logger.info('No holder currently inserted.')

	def vacuumReady(self):
		self.logger.info('Verifying vacuum is ready...')
		self.waitScope('VacuumStatus', 'ready', 0.25)
		self.logger.info('Vacuum is ready.')

	def openColumnValves(self):
		self.logger.info('Opening column valves...')
		self.instrument.tem.ColumnValvePosition = 'open'
		self.logger.info('Verifying column valves are open...')
		self.waitScope('ColumnValvePosition', 'open', 0.25)
		self.logger.info('Column valves are open.')

	def closeColumnValves(self):
		self.logger.info('Closing column valves...')
		self.instrument.tem.ColumnValvePosition = 'closed'
		self.logger.info('Verifying column valves are closed...')
		self.waitScope('ColumnValvePosition', 'closed', 0.25)
		self.logger.info('Column valves are closed.')

	def turboPumpOn(self):
		self.logger.info('Turning on turbo pump...')
		self.instrument.tem.TurboPump = 'on'
		self.logger.info('Verifying turbo pump is on...')
		self.waitScope('TurboPump', 'on', 0.25)
		self.logger.info('Turbo pump is on.')

	def turboPumpOff(self):
		self.logger.info('Turning off turbo pump...')
		self.instrument.tem.TurboPump = 'off'
		#self.logger.info('Verifying turbo pump is off...')
		#self.waitScope('TurboPump', 'off', 0.25)
		self.logger.info('Turbo pump is off.')

	def stageReady(self):
		self.logger.info('Waiting for stage to be ready...')
		self.waitScope('StageStatus', 'ready', 0.25)
		self.logger.info('Stage is ready...')

	def setHolderType(self):
		#type = 'single tilt'
		type = 'cryo'
		self.logger.info('Setting holder type to %s...' % (type,))
		self.instrument.tem.HolderType = type
		self.logger.info('Verifying holder type is set to %s...' % (type,))
		self.waitScope('HolderType', type, 0.25)
		self.logger.info('Holder type is set to %s.' % (type,))

	def getColumnPressureThreshold(self):
		threshold = self.settings['column pressure threshold']
		if threshold is None:
			threshold = self.defaultcolumnpressurethreshold
		return threshold

	def getDefaultZPosition(self):
		defzposition = self.settings['default Z position']
		if defzposition is None:
			defzposition = self.defaultzposition
		return defzposition 


	def checkColumnPressure(self):
		threshold = self.getColumnPressureThreshold()
		self.logger.info('Checking column pressure...')
		while self.instrument.tem.ColumnPressure > threshold:
			time.sleep(0.1)
			threshold = self.getColumnPressureThreshold()
		self.logger.info('Column pressure is below threshold.')

	def checkHighTensionOn(self):
		self.logger.info('Checking high tension state...')
		self.waitScope('HighTensionState', 'on', 0.25)
		self.logger.info('High tension is on.')

	def insertCameras(self):
		ccdcameras = self.instrument.getCCDCameraNames()
		for ccdcamera in ccdcameras:
			self.instrument.setCCDCamera(ccdcamera)
			if self.instrument.ccdcamera.hasAttribute('Inserted'):
				self.logger.info('Inserting %s camera...' % ccdcamera)
				self.instrument.ccdcamera.Inserted = True
				self.waitScope('Inserted', True, 0.25)
				self.logger.info('%s camera is inserted.' % ccdcamera)

	def retractCameras(self):
		ccdcameras = self.instrument.getCCDCameraNames()
		for ccdcamera in ccdcameras:
			self.instrument.setCCDCamera(ccdcamera)
			if self.instrument.ccdcamera.hasAttribute('Inserted'):
				self.logger.info('Retracting %s camera...' % ccdcamera)
				self.instrument.ccdcamera.Inserted = False
				self.waitScope('Inserted', False, 0.25)
				self.logger.info('%s camera is retracted.' % ccdcamera)

	def scopeReadyForInsertion1(self):
		self.logger.info('Readying microscope for insertion step 1...')
		self.zeroStage()
		self.holderNotInScope()
		self.vacuumReady()
		self.closeColumnValves()
		self.stageReady()
		self.logger.info('Microscope ready for insertion step 1.')

	def scopeReadyForInsertion2(self):
		self.logger.info('Readying microscope for insertion step 2...')
		self.setHolderType()
		self.stageReady()
		self.logger.info('Microscope ready for insertion step 2.')

	def scopeReadyForExtraction(self):
		self.logger.info('Readying microscope for extraction...')
		self.closeColumnValves()
		self.retractCameras()
		self.zeroStage()
		self.holderInScope()
		self.vacuumReady()
		self.stageReady()
		self.logger.info('Microscope ready for extraction.')

	def scopeReadyForImaging(self):
		self.logger.info('Readying microscope for imaging...')
		if not self.settings['turbo on']:
			self.turboPumpOff()
		self.insertCameras()
		self.checkHighTensionOn()
		self.vacuumReady()
		zposition = self.getDefaultZPosition()
		if zposition:
			self.moveStagePositionZ(zposition)
		self.checkColumnPressure()
		self.openColumnValves()
		self.logger.info('Microscope ready for imaging.')

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

	def emailGridClear(self, gridnumber):
		m = 'Grid #%s failed to be removed from specimen holder properly'
		subject = m % gridnumber
		text = 'Reply to this message if grid is not in the specimen holder.\n' + \
						'An image of the specimen holder is attached.'
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

		self.emailGridClear(self.gridnumber)

		self.panel.clearGrid()

		self.gridcleared.wait()
		self.gridcleared = threading.Event()

		self.communication.Signal10 = 1

	def autoGridClear(self):
		self.gridcleared.clear()

		self.logger.info('Auto probe clearing')

		self.communication.Signal10 = 1

	def gridCleared(self):
		self.gridcleared.set()

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
			self.communication.Signal11 = int(self.settings['grid clear wait'])
			if self.communication.Signal9:
				self.logger.warning('Robot failed to remove grid from specimen holder')
				if self.communication.Signal11 == 0:
					self.autoGridClear()
				else:
					self.waitForGridClear()
				self.communication.Signal9 = 0
				self.setStatus('processing')
				self.logger.info('Resuming operation')
			time.sleep(0.5)
		self.communication.Signal7 = 0
		self.logger.info('Robot has completed extraction')

	def getUserGridRequest(self):
		gridnumber = -1
		while not validateGridNumber(gridnumber):
			gridnumber = self.panel.getNextGrid()
			if gridnumber is None:
				return None
		return GridRequest(gridnumber)

	def newGrid(self, gridboxid, gridnumber):
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.error('Failed to create grid information: %s' % e)
			return None
		return projectdata.newGrid('Robot Generated Grid #%d' % gridnumber,	
																-1, gridnumber, gridboxid, gridnumber)

	def getGridNumber(self, gridid):
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.error('Failed to find grid information: %s' % e)
			return None

		grids = projectdata.getGrids()
		gridsindex = grids.Index(['gridId'])
		grid = gridsindex[gridid].fetchone()
		if grid is None:
			self.logger.error('Failed to find grid information: %s' % e)
			return None
		gridlabel = grid['label']
		if grid['boxId'] != self.gridtrayid:
			boxlabel = self.gridtraylabels[grid['boxId']]
			self.logger.error('Grid "%s" is not in selected grid tray, but in "%s"' % (gridlabel,boxlabel))
			return None
		gridlocations = projectdata.getGridLocations()
		gridlocationsindex = gridlocations.Index(['gridId'])
		gridlocation = gridlocationsindex[gridid].fetchone()
		if gridlocation is None:
			self.logger.error('Failed to find grid number for grid "%s"' % (gridlabel))
			return None
		if gridlocation['gridboxId'] != self.gridtrayid:
			boxlabel = self.gridtraylabels[gridlocation['gridboxId']]
			self.logger.error('Last location for grid "%s" does not match selected tray, but "%s"' % (gridlabel,boxlabel))
			return None
		return int(gridlocation['location'])

	def getGridID(self, gridboxid, gridnumber):
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.error('Failed to find grid information: %s' % e)
			return None

		gridlocations = projectdata.getGridLocations()
		gridboxidindex = gridlocations.Index(['gridboxId'])
		gridlocations = gridboxidindex[gridboxid].fetchall()
		for gridlocation in gridlocations:
			if gridlocation['location'] == gridnumber:
				return gridlocation['gridId']
		return self.newGrid(gridboxid, gridnumber)

	def makeGridData(self, gridnumber):
		gridid = self.getGridID(self.gridtrayid, gridnumber)
		if gridid is None:
			return None
		initializer = {'grid ID': gridid}
		querydata = data.GridData(initializer=initializer)
		griddatalist = self.research(querydata)
		insertion = 0
		for griddata in griddatalist:
			if griddata['insertion'] > insertion:
				insertion = griddata['insertion']
		initializer = {'grid ID': gridid, 'insertion': insertion + 1}
		griddata = data.GridData(initializer=initializer)
		self.publish(griddata, database=True)
		return griddata

	def selectGrid(self, gridnumber):
		self.logger.info('Current grid: %d' % gridnumber)
		self.communication.gridNumber = gridnumber

	def robotReadyForInsertion(self):
		self.logger.info('Verifying robot is ready for insertion')
		while not self.communication.Signal0:
			if self.communication.Signal8:
				self.logger.warning('Robot failed to extract grid from tray')
				self.communication.Signal8 = 0
				raise GridLoadFromTrayError
			time.sleep(0.5)
		self.communication.Signal0 = 0
		self.logger.info('Robot is ready for insertion')

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

	def insert(self):
		self.lockScope()
		self.logger.info('insert '+str(self.simulate)+' setting'+str(self.settings['simulate']))

		if self.simulate or self.settings['simulate']:
			self.estimateTimeLeft()
			self.logger.info('Insertion of holder successfully completed')
			try:
				griddata = self.gridInserted(self.gridnumber)
			except Exception, e:
				self.logger.error('Failed to get scope ready for imaging: %s' % e)
				self.unlockScope()
			self.unlockScope()
			return griddata

		self.estimateTimeLeft()

		self.logger.info('Inserting holder into microscope')


		self.turboPumpOn()

		self.robotReadyForInsertion()

		try:
			self.scopeReadyForInsertion1()
		except Exception, e:
			self.unlockScope()
			self.logger.error('Failed to get scope ready for insertion 1: %s' % e)
			raise
		self.signalRobotToInsert1()
		self.waitForRobotToInsert1()

		try:
			self.scopeReadyForInsertion2()
		except Exception, e:
			self.unlockScope()
			self.logger.error('Failed to get scope ready for insertion 2: %s' % e)
			raise
		self.signalRobotToInsert2()
		self.waitForRobotToInsert2()

		self.logger.info('Insertion of holder successfully completed')
		try:
			griddata = self.gridInserted(self.gridnumber)
		except Exception, e:
			self.logger.error('Failed to get scope ready for imaging: %s' % e)
			self.unlockScope()
			return

		self.unlockScope()
		return griddata

	def extract(self):
		if self.simulate or self.settings['simulate']:
			self.logger.info('Extraction of holder successfully completed')
			return

		self.logger.info('Extracting holder from microscope')

		self.lockScope()

		self.turboPumpOn()

		self.robotReadyForExtraction()
		try:
			self.scopeReadyForExtraction()
		except Exception, e:
			self.unlockScope()
			self.logger.error('Failed to get scope ready for extraction: %s' % e)
			raise
		self.signalRobotToExtract()
		self.waitForRobotToExtract()
		self.unlockScope()

		self.logger.info('Extraction of holder successfully completed')

	def handleGridDataCollectionDone(self, ievent):
		# ...
		if self.settings['pause']:
			# pause for user check
			self.setStatus('user input')
			self.logger.info('waiting for user to continue...')
			self.usercontinue.clear()
			self.usercontinue.wait()
			self.usercontinue.clear()
			self.setStatus('processing')
			self.logger.info('continuing')

		self.panel.extractingGrid()
		self.extractcondition.acquire()
		self.extractinfo = (None, None)
		self.extractcondition.notify()
		self.extractcondition.release()

	def getTrayLabels(self):
		self.traysFromDB()
		return self.gridtrayids.keys()

	def setTray(self, traylabel):
		try:
			self.gridtrayid = self.gridtrayids[traylabel]
		except KeyError:
			raise ValueError('unknown tray label')
	
	def getGridLabels(self, gridlist):
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.error('Failed to get grid labels: %s' % e)
			return None
		gridlabels = []
		for gridid in gridlist:
			gridlabels.append(str(projectdata.getGridLabel(gridid)))
		return gridlabels

	def getGridLocations(self, traylabel):
		try:
			gridboxid = self.gridtrayids[traylabel]
		except KeyError:
			raise ValueError('unknown tray label')
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.error('Failed to get grid locations: %s' % e)
			return None
		gridlocations = projectdata.getGridLocations()
		gridboxidindex = gridlocations.Index(['gridboxId'])
		gridlocations = gridboxidindex[gridboxid].fetchall()
		gridlabels = [i['gridId'] for i in gridlocations]
		return [int(i['location']) for i in gridlocations],gridlabels

	def gridInserted(self, gridnumber):
		if self.simulate or self.settings['simulate']:
			evt = event.MakeTargetListEvent()
			evt['grid'] = self.makeGridData(gridnumber)
			if evt['grid'] is None:
				self.logger.error('Data collection event not sent')
			else:
				self.outputEvent(evt)
				self.logger.info('Data collection event outputted')
			return evt['grid']

		self.logger.info('Grid inserted.')

		self.scopeReadyForImaging()

		self.logger.info('Outputting data collection event')
		evt = event.MakeTargetListEvent()
		evt['grid'] = self.makeGridData(gridnumber)
		if evt['grid'] is None:
			self.logger.error('Data collection event not sent')
		else:
			self.outputEvent(evt)
			self.logger.info('Data collection event outputted')
		return evt['grid']

	def waitScope(self, parameter, value, interval=None, timeout=0.0):
		if self.instrument.tem.hasAttribute(parameter):
			o = self.instrument.tem
		elif self.instrument.ccdcamera.hasAttribute(parameter):
			o = self.instrument.ccdcamera
		else:
			raise ValueError('invalid parameter')
		parametervalue = getattr(o, parameter)
		elapsed = 0.0
		if interval is not None and interval > 0:
			while parametervalue != value:
				time.sleep(interval)
				if timeout > 0.0:
					elapsed += interval
					if elapsed > timeout:
						raise ValueError('parameter is not set to value')
				parametervalue = getattr(o, parameter)
		else:
			if parametervalue != value:
				raise ValueError('parameter is not set to value')

