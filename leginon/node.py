#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import datahandler
import datatransport
import dbdatakeeper
import event
import leginonobject
import extendedlogging
import threading
import uiserver
import uidata

# for ID counter
import cPickle
import leginonconfig
import os

class ResearchError(Exception):
	pass

class PublishError(Exception):
	pass

class ConfirmationTimeout(Exception):
	pass

import sys
if sys.platform == 'win32':
	import winsound

def beep():
	try:
		winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
		print 'BEEP!'
	except:
		print '\aBEEP!'

class DataHandler(object):
	'''
	handles data published by the node
	'''
	def __init__(self, mynode,
								datakeeperclass=datahandler.SizedDataKeeper,
								databinderclass=datahandler.DataBinder,
								dbdatakeeperclass=dbdatakeeper.DBDataKeeper,
								loggername=None):
		self.logger = extendedlogging.getLogger(self.__class__.__name__, loggername)

		self.datakeeper = datakeeperclass(loggername=self.logger.name)
		self.databinder = databinderclass(loggername=self.logger.name)
		self.dbdatakeeper = dbdatakeeperclass(loggername=self.logger.name)
		if self.datakeeper.logger.container not in self.logger.container.values():
			self.logger.container.addObject(self.datakeeper.logger.container,
																			position={'span': (1,2), 'expand': 'all'})
		if self.databinder.logger.container not in self.logger.container.values():
			self.logger.container.addObject(self.databinder.logger.container,
																			position={'span': (1,2), 'expand': 'all'})
		if self.dbdatakeeper.logger.container not in self.logger.container.values():
			self.logger.container.addObject(self.dbdatakeeper.logger.container,
																			position={'span': (1,2), 'expand': 'all'})
		self.node = mynode

	def exit(self):
		self.datakeeper.exit()
		self.databinder.exit()
		self.dbdatakeeper.exit()

	def insert(self, idata):
		if isinstance(idata, event.Event):
			self.databinder.insert(idata)
		else:
			self.datakeeper.insert(idata)

	def query(self, id):
		return self.datakeeper.query(id)

	def addBinding(self, nodeid, eventclass, method):
		'''Overides datahandler.DataBinder, making sure it binds Event type only.'''
		if issubclass(eventclass, event.Event):
			self.databinder.addBinding(nodeid, eventclass, method)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

	def delBinding(self, nodeid, eventclass=None, method=None):
		self.databinder.delBinding(nodeid, eventclass, method)

	def dbInsert(self, idata, force=False):
		self.dbdatakeeper.insert(idata, force=force)

	def dbQuery(self, idata, results=None, readimages=True):
		return self.dbdatakeeper.query(idata, results, readimages=readimages)

	def __getattr__(self, attr):
		return getattr(self.datakeeper, attr)

class Node(leginonobject.LeginonObject):
	'''Atomic operating unit for performing tasks, creating data and events.'''

	eventinputs = [event.Event,
									event.KillEvent,
									event.ConfirmationEvent]

	eventoutputs = [event.PublishEvent,
									event.UnpublishEvent,
									event.NodeAvailableEvent,
									event.NodeUnavailableEvent,
									event.NodeInitializedEvent,
									event.NodeUninitializedEvent]

	def __init__(self, id, session, nodelocations={}, datahandler=None,
								uicontainer=None, launcher=None,
								clientclass=datatransport.Client):
		leginonobject.LeginonObject.__init__(self, id)
		
		self.initializeLogger()

		self.managerclient = None

		self.id_count_lock = threading.Lock()

		if session is None or isinstance(session, data.SessionData):
			self.session = session
		else:
			raise TypeError('session must be of proper type')

		self.launcher = launcher

		self.nodelocations = nodelocations

		if datahandler is not None:
			self.datahandler = datahandler
		self.clientclass = clientclass

		if uicontainer is not None:
			self.uicontainer = uidata.LargeContainer(str(self.id[-1]))
			uicontainer.addObject(self.uicontainer)

		self.confirmationevents = {}
		self.eventswaiting = {}
		self.ewlock = threading.Lock()

		#self.addEventInput(event.Event, self.logEventReceived)
		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.SetManagerEvent, self.handleSetManager)

		if 'manager' in self.nodelocations:
			try:
				self.setManager(self.nodelocations['manager'])
			except:
				self.logger.exception('exception in setManager')
				raise
			else:
				pass

	def initializeLoggerUserInterface(self):
		if self.datahandler.logger.container not in self.logger.container.values():
			self.logger.container.addObject(self.datahandler.logger.container,
																			position={'span': (1,2), 'expand': 'all'})
		if self.server.logger.container not in self.logger.container.values():
			self.logger.container.addObject(self.server.logger.container,
																			position={'span': (1,2), 'expand': 'all'})

	def initializeLogger(self, name=None):
		if hasattr(self, 'logger'):
			return
		if name is None:
			name = self.id[-1]
		self.logger = extendedlogging.getLogger(name)

	# main, start/stop methods

	def ID(self):
		'''
		this is redefined so that idcounter is persistent
		'''
		newid = self.id + (self.IDCounter(),)
		self.logger.debug('New ID %s generated' % (newid,))
		return newid

	def IDCounter(self):
		self.id_count_lock.acquire()
		try:
			# read current ID count value
			if not hasattr(self, 'idcount'):
				self.idcount = 0
			self.idcount += 1
	
			if self.session is not None:
				session_name = self.session['name']
			else:
				session_name = ''

			my_name = self.id[-1]
			fname = my_name + '.id'
			idpath = os.path.join(leginonconfig.ID_PATH, session_name)
			leginonconfig.mkdirs(idpath)
			fullname = os.path.join(idpath, fname)
			try:
				f = open(fullname, 'r')
				last_count = cPickle.load(f)
				f.close()
			except:
				last_count = 0
	
			# create new id count
			new_count = last_count + 1
			try:
				f = open(fullname, 'w')
				cPickle.dump(new_count, f, 0)
				f.close()
			except:
				self.logger.exception('Error while saving %s to pickle in file %s'
															% (new_count, fullname))
				raise
		finally:
			self.id_count_lock.release()
		return new_count

	def start(self):
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))

	def exit(self):
		'''Cleans up the node before it dies.'''
		if self.uicontainer is not None:
			self.uicontainer.delete()
		try:
			self.outputEvent(event.NodeUninitializedEvent(id=self.ID()), wait=True,
																										timeout=3.0)
			self.outputEvent(event.NodeUnavailableEvent(id=self.ID()))
		except (ConfirmationTimeout, IOError):
			pass
		self.delEventInput()
		if self.launcher is not None:
			self.launcher.onDestroyNode(self)

	def die(self, ievent=None):
		'''Tell the node to finish and call exit.'''
		self.exit()
		if ievent is not None:
			self.confirmEvent(ievent)

	# location method

	def location(self):
		location = leginonobject.LeginonObject.location(self)
		location['launcher'] = self.launcher.id
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
		## give event an id if it doesn't have one
		if ievent['id'] is None:
			eventid = self.ID()
			ievent['id'] = eventid
		else:
			eventid = ievent['id']

		## if we are going to wait for confirmation, label
		## the event as such
		ievent['confirm'] = wait

		if wait:
			## prepare to wait (but don't wait yet)
			self.ewlock.acquire()
			self.eventswaiting[eventid] = threading.Event()
			eventwait = self.eventswaiting[eventid]
			self.ewlock.release()

		### send event and cross your fingers
		try:
			client.push(ievent)
			#self.logEvent(ievent, status='%s eventToClient' % (self.id,))
		except Exception, e:
			# make sure we don't wait for an event that failed
			if wait:
				eventwait.set()
			if not isinstance(e, IOError):
				self.logger.exception('')
			raise

		confirmationevent = None

		if wait:
			### this wait should be released 
			### by handleConfirmedEvent()
			eventwait.wait(timeout)
			notimeout = eventwait.isSet()
			self.ewlock.acquire()
			try:
				confirmationevent = self.confirmationevents[eventid]
				del self.confirmationevents[eventid]
				del self.eventswaiting[eventid]
			except KeyError:
				self.logger.warning('This could be bad to except KeyError')
			self.ewlock.release()
			if not notimeout:
				raise ConfirmationTimeout(str(ievent))

		return confirmationevent

	def outputEvent(self, ievent, wait=False, timeout=None):
		'''output an event to the manager'''
		if self.managerclient is None:
			raise IOError('Not connnected to manager, output event failed')
		return self.eventToClient(ievent, self.managerclient, wait, timeout)

	def handleConfirmedEvent(self, ievent):
		'''Handler for ConfirmationEvents. Unblocks the call waiting for confirmation of the event generated.'''
		eventid = ievent['eventid']
		self.ewlock.acquire()
		if eventid in self.eventswaiting:
			self.confirmationevents[eventid] = ievent
			self.eventswaiting[eventid].set()
		self.ewlock.release()
		## this should not confirm ever, right?

	def confirmEvent(self, ievent):
		'''Confirm that an event has been received and/or handled.'''
		if ievent['confirm']:
			self.outputEvent(event.ConfirmationEvent(id=self.ID(),
												eventid=ievent['id']))

	def logEvent(self, ievent, status):
		eventlog = event.EventLog(id=self.ID(), eventclass=ievent.__class__.__name__, status=status)
		# pubevent is False by default, but just in case that changes
		# we don't want infinite recursion here
		self.publish(eventlog, database=True, pubevent=False)

	def logEventReceived(self, ievent):
		self.logEvent(ievent, 'received by %s' % (self.id,))
		## this should not confirm, this is not the primary handler
		## any event

	def addEventInput(self, eventclass, method):
		'''Map a function (event handler) to be called when the specified event is received.'''
		self.datahandler.addBinding(self.id, eventclass, method)

	def delEventInput(self, eventclass=None, method=None):
		'''Unmap all functions (event handlers) to be called when the specified event is received.'''
		self.datahandler.delBinding(self.id, eventclass, method)

	# data publish/research methods

	def publish(self, idata, **kwargs):
		'''
		Make a piece of data available to other nodes.
		Arguments:
			idata - instance of data to publish
			Takes kwargs:
				eventclass - PublishEvent subclass to notify with when publishing		
				confirm - Wait until Event is confirmed to return
				database - publish to database
				remote - publish to another node's datahandler (may be changed)
		'''
		if 'remote' in kwargs and kwargs['remote']:
			self.publishRemote(idata)
			return

		if 'database' in kwargs and kwargs['database']:
			if 'dbforce' in kwargs:
				dbforce = kwargs['dbforce']
			else:
				dbforce = False
			if isinstance(idata, data.InSessionData):
				self.addSession(idata)
			try:
				self.datahandler.dbInsert(idata, force=dbforce)
			except Exception, e:
				if isinstance(e, OSError):
					message = str(e)
				elif isinstance(e, IOError):
					message = str(e)
				elif isinstance(e, KeyError):
					message = 'no DBDataKeeper to publish: %s' % str(idata['id'])
				else:
					raise
				raise PublishError(message)

		self.datahandler.insert(idata)

		if 'pubeventclass' in kwargs:
			pubeventclass = kwargs['pubeventclass']
		else:
			pubeventclass = None

		### publish event
		if 'publisheventinstance' in kwargs:
			return self.outputEvent(kwargs['publisheventinstance'])
		elif 'pubevent' in kwargs and kwargs['pubevent']:
			if 'confirm' in kwargs:
				confirm = kwargs['confirm']
			else:
				confirm = False
			wait = False
			if confirm and 'wait' in kwargs:
				wait = kwargs['wait']
			
			if pubeventclass is None:
				eventclass = event.publish_events[idata.__class__]
			else:
				eventclass = pubeventclass
			e = eventclass(id=self.ID(), dataid=idata['id'], confirm=confirm)
			return self.outputEvent(e, wait=wait)

	def addSession(self, datainstance):
		## setting an item of datainstance will reset the dbid
		if datainstance['session'] is not self.session:
			datainstance['session'] = self.session
		for key in datainstance:
			if isinstance(datainstance[key], data.InSessionData):
				self.addSession(datainstance[key])

	def research(self, dataclass=None, datainstance=None, results=None, readimages=True):
		'''
		How a node finds some data in the leginon system:
			1) Using a data class and keyword args:
				self.research(dataclass=myclass, stuff=4)
			2) Using a partially filled data instance:
				self.research(datainstance=mydata)

			In both cases, zero or more results (data instances)
			will be returned in a list.  The result list will
			not contain two instaces with the same ID.
		'''

		resultlist = []

		#### make some sense out of args
		### for research by dataclass, use kwargs to find instance
		if dataclass is not None:
			datainstance = dataclass()

		### use DBDataKeeper query if not results yet
		if not resultlist and datainstance is not None:
			## always fill empty session
			self.addEmptySession(datainstance)
			try:
				newresults = self.datahandler.dbQuery(datainstance, results, readimages=readimages)
			except Exception, e:
				if isinstance(e, OSError):
					message = str(e)
				elif isinstance(e, IOError):
					message = str(e)
				else:
					raise
				raise ResearchError(message)
			resultlist += newresults

		return resultlist

	def addEmptySession(self, datainstance):
		if isinstance(datainstance, data.InSessionData):
			if datainstance['session'] is None:
				datainstance['session'] = data.SessionData()
		for key in datainstance:
			if isinstance(datainstance[key], data.InSessionData):
				self.addSession(datainstance[key])

	def getClient(self, location):
		return self.clientclass(location, loggername=self.logger.name)

	def publishRemote(self, idata):
		'''Publish a piece of data with the specified data ID, setting all other data with the same data ID to the data value (including other nodes).'''
		dataid = idata['id']
		if not dataid:
			raise RuntimeError('%s data needs an ID to be published' %
													(idata.__class__.__name__,))
		nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid)
		if nodeiddata is None:
			# try a partial ID lookup
			nodeiddata = self.researchByLocation(self.nodelocations['manager'],
																						dataid[:1])

		if nodeiddata is None:
			raise PublishError('No such Data ID: %s' % (dataid,))

		for nodeid in nodeiddata['location']:
			nodelocation = self.researchByLocation(self.nodelocations['manager'],
																							nodeid)
			client = self.getClient(nodelocation['location']['data transport'])
			client.push(idata)

	def researchByLocation(self, location, dataid):
		'''Get a piece of data with the specified data ID by the location of a node.'''
		client = self.getClient(location['data transport'])
		try:
			cdata = client.pull(dataid)
		except IOError:
			cdata = None
		return cdata


	def researchByDataID(self, dataid):
		'''Get a piece of data with the specified data ID. Currently retrieves the data from the last node to publish it.'''
		if self.managerclient is None:
			raise ResearchError('Not connected to manager, research failed')

		nodeiddata = self.managerclient.pull(dataid)

		if nodeiddata is None:
			raise ResearchError('No such data ID: %s' % (dataid,))

		# should interate over nodes, be crafty, etc.
		datalocationdata = self.managerclient.pull(nodeiddata['location'][-1])
		newdata = self.researchByLocation(datalocationdata['location'], dataid)
		return newdata

	def researchPublishedDataByID(self, dataid):
		newdata = self.researchByDataID(dataid)
		if newdata is None:
			if issubclass(publishevent.dataclass, data.Data):
				initializer = {'id': dataid}
				if issubclass(publishevent.dataclass, data.InSessionData):
					initializer['session'] = self.session
				datainstance = publishevent.dataclass(initializer=initializer)
				newdatalist = self.research(datainstance=datainstance)
				if newdatalist:
					newdata = newdatalist[0]
		return newdata

	def researchPublishedData(self, publishevent):
		newdata = None
		if 'dataid' in publishevent:
			dataid = publishevent['dataid']
			if dataid is not None:
				newdata = self.researchPublishedDataByID(dataid)
		return newdata

	# methods for setting up the manager

	def setManager(self, location):
		'''Set the manager controlling the node and notify said manager this node is available.'''
		self.managerclient = self.getClient(location['data transport'])
		available_event = event.NodeAvailableEvent(id=self.ID(),
																							location=self.location(),
																							nodeclass=self.__class__.__name__)
		self.outputEvent(ievent=available_event, wait=True, timeout=10)

	def handleSetManager(self, ievent):
		'''Event handler calling setManager with event info. See setManager.'''
		if self.session is None:
			self.session = ievent['session']
		if ievent['session'] == self.session:
			self.setManager(ievent['location'])
		else:
			self.logger.warning('Attempt to set manager rejected')

	# utility methods

	def key2str(self, d):
		'''Makes keys and values into strings.'''
		if type(d) is dict:
			newdict = {}
			for k in d:
				newdict[str(k)] = self.key2str(d[k])
			return newdict
		else:
			return str(d)

	def uiExit(self):
		'''UI function calling die. See die.'''
		self.die()

	def defineUserInterface(self):
		idarray = uidata.String('ID', str(self.id), 'r')
		classstring = uidata.String('Class', self.__class__.__name__, 'r')
		location = self.key2str(self.location())
		locationstruct = uidata.Struct('Location', location, 'r')
		exitmethod = uidata.Method('Exit', self.uiExit)

		# cheat a little here
		clientlogger = extendedlogging.getLogger(self.logger.name + '.'
																							+ self.clientclass.__name__)
		if clientlogger.container not in self.logger.container.values():
			self.logger.container.addObject(clientlogger.container,
																			position={'span': (1,2), 'expand': 'all'})

		container = uidata.LargeContainer('Node')
		self.uicontainer.addObjects((idarray, classstring, locationstruct,
																	self.logger.container, exitmethod))

