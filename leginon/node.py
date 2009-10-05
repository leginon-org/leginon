#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
#

import sinedon
import leginondata
from databinder import DataBinder
import datatransport
import event
import logging
import threading
import gui.wx.Events
import gui.wx.Logging
import gui.wx.Node
import copy
import socket
import remotecall
import time
import numpy
import leginonconfig
import os
import correctorclient

class ResearchError(Exception):
	pass

class PublishError(Exception):
	pass

class ConfirmationTimeout(Exception):
	pass

class ConfirmationNoBinding(Exception):
	pass

import sys
if sys.platform == 'win32':
	import winsound

class Node(correctorclient.CorrectorClient):
	'''Atomic operating unit for performing tasks, creating data and events.'''
	panelclass = None
	eventinputs = [event.Event,
									event.KillEvent,
									event.ConfirmationEvent]

	eventoutputs = [event.PublishEvent,
									event.NodeAvailableEvent,
									event.NodeUnavailableEvent,
									event.NodeInitializedEvent,
									event.NodeUninitializedEvent]

	objectserviceclass = remotecall.NodeObjectService

	def __init__(self, name, session, managerlocation=None, otherdatabinder=None, otherdbdatakeeper=None, tcpport=None, launcher=None, panel=None):
		self.name = name
		self.panel = panel
		
		self.initializeLogger()

		self.managerclient = None

		if session is None or isinstance(session, leginondata.SessionData):
			self.session = session
		else:
			raise TypeError('session must be of proper type')

		self.launcher = launcher

		if otherdatabinder is None:
			name = DataBinder.__name__
			databinderlogger = gui.wx.Logging.getNodeChildLogger(name, self)
			self.databinder = DataBinder(self, databinderlogger, tcpport=tcpport)
		else:
			self.databinder = otherdatabinder
		if otherdbdatakeeper is None:
			self.dbdatakeeper = sinedon.getConnection('leginondata')
		else:
			self.dbdatakeeper = otherdbdatakeeper

		self.confirmationevents = {}
		self.eventswaiting = {}
		self.ewlock = threading.Lock()

		#self.addEventInput(event.Event, self.logEventReceived)
		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.SetManagerEvent, self.handleSetManager)

		self.managerlocation = managerlocation
		if managerlocation is not None:
			try:
				self.setManager(self.managerlocation)
			except:
				self.logger.exception('exception in setManager')
				raise

		correctorclient.CorrectorClient.__init__(self)

		self.initializeSettings()

	# settings

	def initializeSettings(self, user=None):
		if not hasattr(self, 'settingsclass'):
			return

		# load the requested user settings
		if user is None:
			user = self.session['user']
		qsession = leginondata.SessionData(initializer={'user': user})
		qdata = self.settingsclass(initializer={'session': qsession,
																						'name': self.name})
		settings = self.research(qdata, results=1)
		# if that failed, try to load default settings from DB
		if not settings:
			qdata = self.settingsclass(initializer={'isdefault': True, 'name': self.name})
			settings = self.research(qdata, results=1)

		# if that failed, use hard coded defaults
		if not settings:
			self.settings = copy.deepcopy(self.defaultsettings)
		else:
			# get query result into usable form
			settings = settings[0]
			self.settings = settings.toDict(dereference=True)
			del self.settings['session']
			del self.settings['name']

		# check if None in any fields
		for key,value in self.settings.items():
			if value is None:
				if key in self.defaultsettings:
					self.settings[key] = copy.deepcopy(self.defaultsettings[key])

	def setSettings(self, d, isdefault=False):
		self.settings = d
		sd = self.settingsclass.fromDict(d)
		sd['session'] = self.session
		sd['name'] = self.name
		if self.session['user']['name'] == 'administrator':
			sd['isdefault'] = True
		else:
			sd['isdefault'] = isdefault
		self.publish(sd, database=True, dbforce=True)
		self._checkSettings(sd)

	def _checkSettings(self, settings):
		if hasattr(self, 'checkSettings'):
			messages = self.checkSettings(settings)
		else:
			messages = []
		for message in messages:
			level = message[0]
			text = message[1]
			func = getattr(self.logger, level)
			func(text)

	def getSettings(self):
		return self.settings

	def initializeLogger(self):
		if hasattr(self, 'logger'):
			return
		self.logger = gui.wx.Logging.getNodeLogger(self)
		clientname = datatransport.Client.__name__
		self.clientlogger = gui.wx.Logging.getNodeChildLogger(clientname, self)

	def logToDB(self, record):
		'''insertes a logger record into the DB'''
		record_data = leginondata.LoggerRecordData(session=self.session)
		for atr in ('name','levelno','levelname','pathname','filename','module','lineno','created','thread','process','message','exc_info'):
			record_data[atr] = getattr(record,atr)
		self.publish(record_data, database=True, dbforce=True)

	# main, start/stop methods

	def start(self):
		self.onInitialized()
		self.outputEvent(event.NodeInitializedEvent())

	def onInitialized(self):
		if self.panel is None:
			return
		evt = gui.wx.Node.NodeInitializedEvent(self)
		self.panel.GetEventHandler().AddPendingEvent(evt)
		evt.event.wait()

	def setImage(self, image, typename=None):
		if image is not None:
			image = numpy.asarray(image, numpy.float32)
		evt = gui.wx.Events.SetImageEvent(image, typename)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def setTargets(self, targets, typename, block=False):
		evt = gui.wx.Events.SetTargetsEvent(targets, typename)
		if block:
			evt.event = threading.Event()
		self.panel.GetEventHandler().AddPendingEvent(evt)
		if block:
			evt.event.wait()

	def exit(self):
		'''Cleans up the node before it dies.'''
		try:
			self.objectservice._exit()
		except (AttributeError, TypeError):
			pass
		try:
			self.outputEvent(event.NodeUninitializedEvent(), wait=True,
																										timeout=3.0)
			self.outputEvent(event.NodeUnavailableEvent())
		except (ConfirmationTimeout, datatransport.TransportError):
			pass
		self.delEventInput()
		if self.launcher is not None:
			self.launcher.onDestroyNode(self)
			if self.databinder is self.launcher.databinder:
				return
		self.databinder.exit()

	def die(self, ievent=None):
		'''Tell the node to finish and call exit.'''
		self.exit()
		if ievent is not None:
			self.confirmEvent(ievent)

	# location method
	def location(self):
		location = {}
		location['hostname'] = socket.gethostname().lower()
		if self.launcher is not None:
			location['launcher'] = self.launcher.name
		else:
			location['launcher'] = None
		location['data binder'] = self.databinder.location()
		return location
	# event input/output/blocking methods

	def eventToClient(self, ievent, client, wait=False, timeout=None):
		'''
		base method for sending events to a client
		ievent - event instance
		client - client instance
		wait - True/False, sould confirmation be sent back
		timeout - how long (seconds) to wait for confirmation before
		   raising a ConfirmationTimeout
		'''
		if wait:
			## prepare to wait (but don't wait yet)
			wait_id = ievent.dmid
			ievent['confirm'] = wait_id
			self.ewlock.acquire()
			self.eventswaiting[wait_id] = threading.Event()
			eventwait = self.eventswaiting[wait_id]
			self.ewlock.release()

		### send event and cross your fingers
		try:
			client.send(ievent)
			#self.logEvent(ievent, status='%s eventToClient' % (self.name,))
		except datatransport.TransportError:
			# make sure we don't wait for an event that failed
			if wait:
				eventwait.set()
			raise
		except Exception, e:
			self.logger.exception('Error sending event to client: %s' % e)
			raise

		confirmationevent = None

		if wait:
			### this wait should be released 
			### by handleConfirmedEvent()
			eventwait.wait(timeout)
			notimeout = eventwait.isSet()
			self.ewlock.acquire()
			try:
				confirmationevent = self.confirmationevents[wait_id]
				del self.confirmationevents[wait_id]
				del self.eventswaiting[wait_id]
			except KeyError:
				self.logger.warning('This could be bad to except KeyError')
			self.ewlock.release()
			if not notimeout:
				raise ConfirmationTimeout(str(ievent))
			if confirmationevent['status'] == 'no binding':
				raise ConfirmationNoBinding('%s from %s not bound to any node' % (ievent.__class__.__name__, ievent['node']))

		return confirmationevent

	def outputEvent(self, ievent, wait=False, timeout=None):
		'''output an event to the manager'''
		ievent['node'] = self.name
		if self.managerclient is not None:
			return self.eventToClient(ievent, self.managerclient, wait, timeout)
		else:
			self.logger.warning('No manager, not sending event: %s' % (ievent,))

	def handleConfirmedEvent(self, ievent):
		'''Handler for ConfirmationEvents. Unblocks the call waiting for confirmation of the event generated.'''
		eventid = ievent['eventid']
		status = ievent['status']
		self.ewlock.acquire()
		if eventid in self.eventswaiting:
			self.confirmationevents[eventid] = ievent
			self.eventswaiting[eventid].set()
		self.ewlock.release()
		## this should not confirm ever, right?

	def confirmEvent(self, ievent, status='ok'):
		'''Confirm that an event has been received and/or handled.'''
		if ievent['confirm'] is not None:
			self.outputEvent(event.ConfirmationEvent(eventid=ievent['confirm'], status=status))

	def logEvent(self, ievent, status):
		if not leginonconfig.logevents:
			return
		eventlog = event.EventLog(eventclass=ievent.__class__.__name__, status=status)
		# pubevent is False by default, but just in case that changes
		# we don't want infinite recursion here
		self.publish(eventlog, database=True, pubevent=False)

	def logEventReceived(self, ievent):
		self.logEvent(ievent, 'received by %s' % (self.name,))
		## this should not confirm, this is not the primary handler
		## any event

	def addEventInput(self, eventclass, method):
		'''Map a function (event handler) to be called when the specified event is received.'''
		self.databinder.addBinding(self.name, eventclass, method)

	def delEventInput(self, eventclass=None, method=None):
		'''Unmap all functions (event handlers) to be called when the specified event is received.'''
		self.databinder.delBinding(self.name, eventclass, method)

	# data publish/research methods

	def publish(self, idata, database=False, dbforce=False, pubevent=False, pubeventclass=None, broadcast=False, wait=False):
		'''
		Make a piece of data available to other nodes.
		Arguments:
			idata - instance of data to publish
			Takes kwargs:
				pubeventclass - PublishEvent subclass to notify with when publishing		
				database - publish to database
		'''
		if database:
			try:
				self.dbdatakeeper.insert(idata, force=dbforce)
			except (IOError, OSError), e:
				raise PublishError(e)
			except KeyError:
				raise PublishError('no DBDataKeeper to publish data to.')
			except Exception:
				raise

		### publish event
		if pubevent:
			if pubeventclass is None:
				dataclass = idata.__class__
				try:
					eventclass = event.publish_events[dataclass]
				except KeyError:
					eventclass = None
			else:
				eventclass = pubeventclass
			if eventclass is None:
				raise PublishError('need to know which pubeventclass to use when publishing %s' % (dataclass,))
			e = eventclass()
			e['data'] = idata.reference()
			if broadcast:
				e['destination'] = ''
			r = self.outputEvent(e, wait=wait)
			return r

	def research(self, datainstance, results=None, readimages=True, timelimit=None):
		'''
		find instances in the database that match the 
		given datainstance
		'''
		try:
			resultlist = self.dbdatakeeper.query(datainstance, results, readimages=readimages, timelimit=timelimit)
		except (IOError, OSError), e:
			raise ResearchError(e)
		return resultlist

	def researchDBID(self, dataclass, dbid, readimages=True):
		return self.dbdatakeeper.direct_query(dataclass, dbid, readimages)

	# methods for setting up the manager

	def setManager(self, location):
		'''Set the manager controlling the node and notify said manager this node is available.'''
		self.managerclient = datatransport.Client(location['data binder'],
																							self.clientlogger)

		available_event = event.NodeAvailableEvent(location=self.location(),
																							nodeclass=self.__class__.__name__)
		self.outputEvent(ievent=available_event, wait=True, timeout=10)

		self.objectservice = self.objectserviceclass(self)

	def handleSetManager(self, ievent):
		'''Event handler calling setManager with event info. See setManager.'''
		## was only resetting self.session if it was previously none
		## now try setting it every time (maybe this would benefit
		## the launcher who could receive this event from different
		## sessions
		self.session = ievent['session']

		if ievent['session']['name'] == self.session['name']:
			self.setManager(ievent['location'])
		else:
			self.logger.warning('Attempt to set manager rejected')

	def beep(self):
		try:
			winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
		except:
			try:
				winsound.MessageBeep()
			except:
				sys.stdout.write('\a')
				sys.stdout.flush()
		self.logger.info('[beep]')

	def setStatus(self, status):
		self.panel.setStatus(status)

	def declareDrift(self, type):
		self.declareTransform(type)

	def OLDdeclareDrift(self, type):
		## declare drift manually
		declared = leginondata.DriftDeclaredData()
		declared['system time'] = self.instrument.tem.SystemTime
		declared['type'] = type
		declared['session'] = self.session
		declared['node'] = self.name
		self.publish(declared, database=True, dbforce=True)

	def declareTransform(self, type):
		declared = leginondata.TransformDeclaredData()
		declared['type'] = type
		declared['session'] = self.session
		declared['node'] = self.name
		self.publish(declared, database=True, dbforce=True)

	def timerKey(self, label):
		return self.name, label

	def storeTime(self, label, type):
		## disabled for now
		return
		key = self.timerKey(label)

		t = leginondata.TimerData()
		t['session'] = self.session
		t['node'] = self.name
		t['t'] = time.time()
		t['label'] = label

		if type == 'stop':
			### this is stop time, but may have no start time
			if key in start_times:
				t0 = start_times[key]
				t['t0'] = t0
				del start_times[key]
				t['diff'] = t['t'] - t0['t']
		else:
			### this is start time
			start_times[key] = t
		self.publish(t, database=True, dbforce=True)

	def startTimer(self, label):
		self.storeTime(label, type='start')

	def stopTimer(self, label):
		self.storeTime(label, type='stop')

## module global for storing start times
start_times = {}
