#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
# from leginon import robot2nysbc ; j = robot2nysbc.Robot2nysbc(); j.moveStagePositionZ()

import Image
import sys
import threading
import time
import leginondata
import emailnotification
import event
import instrument
import node
import project
import gui.wx.Robot
import Queue
import sinedon

import robot2

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

class TestCommunication(robot2.TestCommunication):
	pass

robotattrtypemap = [(robotattr, int) for robotattr in robotattrs]

def validateGridNumber(gridnumber):
	if not isinstance(gridnumber, int):
		return False
	if gridnumber >= 1 and gridnumber <= 96:
		return True
	else:
		return False


class RobotAttributes(robot2.RobotAttributes):
	pass

class DatabaseCommunication(robot2.DatabaseCommunication):
	pass

class RobotException(robot2.RobotException):
	pass

class GridException(robot2.GridException):
	pass

class GridQueueEmpty(robot2.GridQueueEmpty):
	pass

class GridLoadError(robot2.GridLoadError):
	pass

class GridLoadFromTrayError(robot2.GridLoadFromTrayError):
	pass

class GridUnloadError(robot2.GridUnloadError):
	pass

class Request(robot2.Request):
	pass

class ExitRequest(robot2.ExitRequest):
	pass

class GridRequest(robot2.GridRequest):
	pass

class Robot2nysbc(robot2.Robot2):
	def __init__(self, id, session, managerlocation, **kwargs):
		robot2.Robot2.__init__(self, id, session, managerlocation, **kwargs)
		self.startTime = 0
		self.endTime = 0
		self.wait_time = 3
		self.tried_times = 5
		self.beamFile = "C:\\Python25\Lib\\site-packages\\pyscope\\beamStatus.cfg"
		self.beamStatus = {'start_time': None, 'end_time': None}

	#imgZposition = -119e-6								# for robot tip
	#imgXposition = 416e-6
	#imgYposition = 97e-6

	#imgZposition = -119e-6								# for robot tip
	#imgXposition = 200e-6
	#imgYposition = -100e-6

	#defZposition = 0.00		                			# changed by Minghui
	#defXposition = 11.6e-6
	#defYposition = -787.5e-6


	#imgZposition = -92.0e-6								# for Gatan tip
	imgZposition = 0
	imgXposition = 0
	imgYposition = 0

	defZposition = -45.3e-6		                			# changed by Minghui
	defXposition = 14.6e-6
	defYposition = -688.7e-6

	panelclass = gui.wx.Robot.Panel
	eventinputs = node.Node.eventinputs + [event.TargetListDoneEvent,
																					event.UnloadGridEvent,
																					event.QueueGridEvent,
																					event.QueueGridsEvent,
																					event.MosaicDoneEvent]
	eventoutputs = node.Node.eventoutputs + [event.MakeTargetListEvent,
																						event.GridLoadedEvent,
																						event.EmailEvent]
	settingsclass = leginondata.RobotSettingsData
	defaultsettings = {
		'column pressure threshold': 3.5e-5,
		'default Z position': 0,
		'simulate': False,
		'turbo on': False,
		'pause': False,
		'grid tray': None,
		'grid clear wait': False,
	}
	defaultcolumnpressurethreshold = 3.5e-5


	def readBeamStatus(self):
		beamStatus = {'start_time': None,'end_time': None}
		infile = open(self.beamFile,"r")
		lines = infile.readlines()
		line = lines[0]
		beamStatus['start_time'] = line[:-1]
		line = lines[1]
		beamStatus['end_time'] = line[:-1]
		infile.close()
		return beamStatus


	def saveBeamStatus(self, timeType, value):
		beamStatus = {'start_time': None,'end_time': None}
		beamStatus = self.readBeamStatus()
		if timeType == 'start_time':
			beamStatus['start_time'] = value
		else:
			beamStatus['end_time'] = value
		outfile = open(self.beamFile,"w")
		outfile.write(str(beamStatus['start_time']) + '\n')
		outfile.write(str(beamStatus['end_time']) + '\n')
		outfile.close()
		return True


	def _queueHandler(self):
		self.logger.info('_queueHandler '+str(self.simulate)+' setting'+str(self.settings['simulate']))
		self.communication = self.getCommunication()
		request = None
		self.communication.Signal11 = int(self.settings['grid clear wait'])
		while True:
			# need to wait if something goes wrong
			if not self.startnowait:
				self.usercontinue.clear()
				self.usercontinue.wait()
				self.stageIsReadyforInsertionExtraction()
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
				evt['grid'] = leginondata.GridData(initializer={'grid ID': gridid})
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


	def gridInserted(self, gridnumber):
		if self.simulate or self.settings['simulate']:
			evt = event.MakeTargetListEvent()
			evt['grid'] = self.makeGridData(gridnumber)
			if evt['grid'] is None:
				self.logger.error('Data collection event not sent')
			else:
				self.outputEvent(evt)
				self.logger.info('Data collection event outputted')
			self.scopeReadyForImaging()
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


	def scopeReadyForInsertion(self):
		self.startTime = time.time()						# added by Minghui
		self.logger.info('Readying microscope for insertion ...')
		self.checkHighTensionOn()
		self.setBeamOff()
		self.stageIsReadyforInsertionExtraction()
		self.logger.info('Microscope ready for insertion.')


	def robotReadyForInsertion(self):
		self.logger.info('Verifying robot is ready for insertion')
		while not self.communication.Signal0:
			if self.communication.Signal8:
				self.logger.warning('Robot failed to extract grid from tray')
				self.communication.Signal8 = 0
				raise GridLoadFromTrayError
			time.sleep(self.wait_time)
		self.logger.info('Robot is ready for insertion')


	def signalRobotToInsert(self):
		self.logger.info('Signaling robot to begin insertion')
		while self.communication.Signal0 == 1 and self.communication.Signal1 == 0 and self.communication.Signal5 == 0:
			self.communication.Signal1 = 1
			time.sleep(self.wait_time)
		self.logger.info('Signaled robot to begin insertion')


	def waitForRobotToInsert(self):
		self.logger.info('Waiting for robot to complete insertion ...')
		while not self.communication.Signal5:
			time.sleep(self.wait_time)
		self.logger.info('Robot has completed insertion')


	def scopeReadyForImaging(self):
		self.logger.info('Readying microscope for imaging...')
		self.stageIsReadyforImaging()
		self.checkHighTensionOn()
		self.setBeamOn()
		self.saveBeamStatus("start_time", time.localtime())
		self.logger.info('Microscope ready for imaging.')


	def scopeReadyForExtraction(self):
		self.logger.info('Readying microscope for extraction...')
		self.checkHighTensionOn()
		self.setBeamOff()
		self.saveBeamStatus("end_time", time.localtime())
		self.stageIsReadyforInsertionExtraction()
		self.logger.info('Microscope ready for extraction.')


	def robotReadyForExtraction(self):
		self.logger.info('Verifying robot is ready for extraction')
		while not self.communication.Signal5:
			time.sleep(self.wait_time)
		self.logger.info('Robot is ready for extraction')


	def signalRobotToExtract(self):
		self.logger.info('Signaling robot to begin extraction')
		while self.communication.Signal5 == 1 and self.communication.Signal6 == 0 and self.communication.Signal7 == 0:
			self.communication.Signal6 = 1
			time.sleep(self.wait_time)
		self.logger.info('Signaled robot to begin extraction')


	def waitForRobotToExtract(self):
		self.logger.info('Waiting for robot to complete extraction')
		while not self.communication.Signal7:
			self.communication.Signal11 = int(self.settings['grid clear wait'])  # what is this???
			if self.communication.Signal9:
				self.logger.warning('Robot failed to remove grid from specimen holder')
				if self.communication.Signal11 == 0:
					self.autoGridClear()
				else:
					self.waitForGridClear()
				self.communication.Signal9 = 0
				self.setStatus('processing')
				self.logger.info('Resuming operation')
			time.sleep(self.wait_time)
		self.logger.info('Robot has completed extraction')
		self.endTime = time.time()
		gridTime = (float(self.endTime) - float(self.startTime))/60.0
		print 'This sample takes %f minutes' % gridTime


	def insert(self):
		self.logger.info('Inserting holder into microscope')
		self.lockScope()
		try:
			self.scopeReadyForInsertion()
		except Exception, e:
			self.unlockScope()
			self.logger.error('Failed to get scope ready for insertion: %s' % e)
			raise

		self.logger.info('insert '+str(self.simulate)+' setting'+str(self.settings['simulate']))

		self.estimateTimeLeft()
		if self.simulate or self.settings['simulate']:
			self.logger.info('Simulated Insertion of holder successfully completed')
		else:
			self.robotReadyForInsertion()
			self.signalRobotToInsert()
			self.waitForRobotToInsert()
			self.logger.info('Insertion of holder successfully completed')

		try:
			griddata = self.gridInserted(self.gridnumber)
		except Exception, e:
			self.logger.error('Failed to get griddata: %s' % e)
			self.unlockScope()
			return

		self.unlockScope()
		return griddata


	def extract(self):
		self.logger.info('Extracting holder from microscope')
		self.lockScope()
		try:
			self.scopeReadyForExtraction()
		except Exception, e:
			self.unlockScope()
			self.logger.error('Failed to get scope ready for extraction: %s' % e)
			raise

		if self.simulate or self.settings['simulate']:
			self.logger.info('Simulated extraction of holder successfully completed')
		else:
			self.robotReadyForExtraction()
			self.signalRobotToExtract()
			self.waitForRobotToExtract()
			self.logger.info('Extraction of holder successfully completed')
		self.unlockScope()
		return


	def checkHighTensionOn(self):
		self.logger.info('Checking high tension state...')
		self.waitScope('HighTensionState', 'on', 0.25)
		self.logger.info('High tension is on.')


	def setBeamOn(self):						# Added by Minghui
		time.sleep(self.wait_time)
		self.logger.info('Turning on the beam...')
		self.instrument.tem.TurboPump = 'on'
		self.logger.info('Beam is turned on.')


	def setBeamOff(self):		# Added by Minghui
		self.logger.info('Turning off the beam ...')
		self.instrument.tem.TurboPump = 'off'
		self.logger.info('Beam is turned off.')
		time.sleep(self.wait_time)


	def stageIsReadyforInsertionExtraction(self):
		print "Moving stage to make it ready for insertion and extraction"
		while (not (self.moveStagePositionXYZ('z',self.defZposition) and self.moveStagePositionXYZ('x',self.defXposition) and self.moveStagePositionXYZ('y',self.defYposition))):
			self.logger.info('Stage is not ready for insertion/extraction, Trying again...')
		self.logger.info('stage is ready for insertion/extraction ...')
		return True


	def stageIsReadyforImaging(self):
		while (not (self.moveStagePositionXYZ('z',self.imgZposition) and self.moveStagePositionXYZ('x',self.imgXposition) and self.moveStagePositionXYZ('y',self.imgYposition))):
			self.logger.info('Stage is not ready for imaging, Trying again...')
		self.logger.info('stage is ready for imaging ...')
		return True


	def moveStagePositionXYZ(self,axis,val,limit=5e-6):
		if axis != 'x' and axis != 'y' and axis !='z':
			self.logger.info("You must input x, y, or z")
			return False
		else:
			triedTimes = 0
			while True:
				stage = self.instrument.tem.StagePosition
				if abs(stage[axis] - val) < limit:
					self.logger.info("%s stage position is reached" % axis)
					return True
				else:
					triedTimes = triedTimes + 1
					self.logger.info("Moving stage position %s to: %f" % (axis,val))
					self.instrument.tem.StagePosition = {axis: val}
					if triedTimes > self.tried_times:
						self.logger.info('%s stage position is not reached after 3 tries, aborting...' % axis)
						break
					else:
						self.logger.info('%s Stage position is not reached, trying again...' % axis)
			if triedTimes > self.tried_times:
				return False
			else:
				return True
