#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

#import copy
import data
import datahandler
import datatransport
import dbdatakeeper
import event
import leginonobject
import threading
import uiserver
import uidata

# for ID counter
import cPickle
import leginonconfig
import os

import sys
if sys.platform == 'win32':
	import winsound

def beep():
	try:
		winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
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
								dbdatakeeperclass=dbdatakeeper.DBDataKeeper):
		# giving these all the same id, don't know why
		self.datakeeper = datakeeperclass()
		self.databinder = databinderclass()
		self.dbdatakeeper = dbdatakeeperclass()
		self.node = mynode

	def insert(self, idata):
		if isinstance(idata, event.Event):
			self.databinder.insert(idata)
		else:
			#self.datakeeper.insert(copy.deepcopy(idata))
			self.datakeeper.insert(idata)

	def query(self, id):
		return self.datakeeper.query(id)

	def addBinding(self, eventclass, func):
		'''Overides datahandler.DataBinder, making sure it binds Event type only.'''
		if issubclass(eventclass, event.Event):
			self.databinder.addBinding(eventclass, func)
		else:
			raise event.InvalidEventError('eventclass must be Event subclass')

	def delBinding(self, eventclass, func):
		self.databinder.delBinding(eventclass, func)

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
									event.ConfirmationEvent,
									event.NodeAvailableEvent]

	eventoutputs = [event.PublishEvent,
									event.UnpublishEvent,
									event.NodeAvailableEvent,
									event.NodeUnavailableEvent,
									event.NodeInitializedEvent,
									event.NodeUninitializedEvent]

	def __init__(self, id, session, nodelocations={}, datahandler=DataHandler,
							tcpport=None, xmlrpcport=None, clientclass=datatransport.Client):
		leginonobject.LeginonObject.__init__(self, id)
		self.id_count_lock = threading.Lock()

		if session is None or isinstance(session, data.SessionData):
			self.session = session
		else:
			raise TypeError('session must be of proper type')

		self.nodelocations = nodelocations

		self.datahandler = datahandler(self)
		self.server = datatransport.Server(self.datahandler, tcpport)
		self.clientclass = clientclass

		self.uiserver = uiserver.Server(str(self.id[-1]), xmlrpcport)
		self.datahandler.insert(self.uiserver)

		self.confirmationevents = {}
		self.eventswaiting = {}
		self.ewlock = threading.Lock()

		#self.addEventInput(event.Event, self.logEventReceived)
		self.addEventInput(event.KillEvent, self.die)
		self.addEventInput(event.ConfirmationEvent, self.handleConfirmedEvent)
		self.addEventInput(event.NodeAvailableEvent, self.handleAddNode)

		if 'manager' in self.nodelocations:
			try:
				self.addManager(self.nodelocations['manager'])
			except:
				self.printerror('exception in addManager')
				self.printException()
				raise
			else:
#				self.printerror('connected to manager')
				pass
		self.die_event = threading.Event()

	# main, start/stop methods

	def ID(self):
		'''
		this is redefined so that idcounter is persistent
		'''
		newid = self.id + (self.IDCounter(),)
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
				print 'error while saving %s to pickle in file %s' % (new_count,
																															fullname)
				raise
		finally:
			self.id_count_lock.release()
		return new_count

	def main(self):
		'''The body of taking place when the node is started. See start.'''
		pass

	def exit(self):
		'''Cleans up the node before it dies.'''
		self.outputEvent(event.NodeUnavailableEvent(id=self.ID()))
		self.server.exit()
#		self.printerror('exited')

	def die(self, ievent=None):
		'''Tell the node to finish and call exit.'''
		self.die_event.set()
		if ievent is not None:
			self.confirmEvent(ievent)

	def start(self):
		'''Call to make the node active and react to a call to exit. Calls main.'''
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))
		self.main()
		self.die_event.wait()
		self.outputEvent(event.NodeUninitializedEvent(), wait=True)
		self.exit()

	# location method

	def location(self):
		location = leginonobject.LeginonObject.location(self)
		location['data transport'] = self.server.location()
		location['UI'] = self.uiserver.location()
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
		except:
			# make sure we don't wait for an event that failed
			if wait:
				eventwait.set()
			self.printException()
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
				print 'This could be bad to except KeyError'
			self.ewlock.release()
			if not notimeout:
				raise ConfirmationTimeout(str(ievent))

		return confirmationevent


	def outputEvent(self, ievent, wait=False, timeout=None):
		'''
		output an event to the manager
		'''
		return self.eventToClient(ievent, self.managerclient, wait, timeout)

	def handleConfirmedEvent(self, ievent):
		'''Handler for ConfirmationEvents. Unblocks the call waiting for confirmation of the event generated.'''
		eventid = ievent['eventid']
		if eventid in self.eventswaiting:
			self.confirmationevents[eventid] = ievent
			self.eventswaiting[eventid].set()
		## this should not confirm ever, right?

	def confirmEvent(self, ievent):
		'''Confirm that an event has been received and/or handled.'''
		if ievent['confirm']:
			self.outputEvent(event.ConfirmationEvent(id=self.ID(), eventid=ievent['id']))

	def logEvent(self, ievent, status):
		eventlog = event.EventLog(id=self.ID(), eventclass=ievent.__class__.__name__, status=status)
		# pubevent is False by default, but just in case that changes
		# we don't want infinite recursion here
		self.publish(eventlog, database=True, pubevent=False)

	def logEventReceived(self, ievent):
		self.logEvent(ievent, 'received by %s' % (self.id,))
		## this should not confirm, this is not the primary handler
		## any event

	def addEventInput(self, eventclass, func):
		'''Map a function (event handler) to be called when the specified event is received.'''
		self.datahandler.addBinding(eventclass, func)

	def delEventInput(self, eventclass):
		'''Unmap all functions (event handlers) to be called when the specified event is received.'''
		self.datahandler.delBinding(eventclass, None)

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
				if isinstance(e, IOError):
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

	def research(self, dataclass=None, datainstance=None, results=None, fill=True, readimages=True):
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
			#self.addEmptyInstances(datainstance)
			#raise NotImplementedError('research by data class is not implemented')

		### standard search for data by ID
		#if 'id' in kwargs and 'session' in kwargs and len(kwargs) == 2:
		#	if self.session == kwargs['session']:
		#		try:
		#			resultlist.append(self.researchByDataID(kwargs['id']))
		#		except ResearchError:
		#			pass

		### use DBDataKeeper query if not results yet
		if not resultlist and datainstance is not None:
			if fill:
				try:
					self.addEmptyInstances1(datainstance)
				except RuntimeError:
					self.printerror('RuntimeError, probably exceded recursion limit in addEmptyInsance1.  You should probably set fill=False when calling Node.research(), and instead, construct your own filled instance.')
					return []
			newresults = self.datahandler.dbQuery(datainstance, results, readimages=readimages)
			resultlist += newresults

		return resultlist

	def addEmptyInstances1(self, datainstance):
		'''
		this recursively fills in values of a Data instance with
		new empty Data instances, but only if they have not already
		been set to something.
		'''
		for key, datatype in datainstance.types().items():
			try:
				if issubclass(datatype, data.Data):
					if key in datainstance:
						if datainstance[key] is None:
							datainstance[key] = datatype()
					else:
						datainstance[key] = datatype()
					self.addEmptyInstances1(datainstance[key])
			except TypeError:
				pass

	def addEmptyInstances2(self, datainstance, memo={}):
		'''
		this is like addEmptyInstances1, but it will not result in
		infinite recursion, because it keeps a memo of classes
		that it has already done.
		'''
		memo[datainstance.__class__] = None
		for key, datatype in datainstance.types().items():
			try:
				issub = issubclass(datatype, data.Data)
			except TypeError:
				## datatype is not a class, so obviously not
				## a subclass of Data
				issub = False
			if issub:
				if datainstance[key] is None:
					datainstance[key] = datatype()
				if datatype not in memo:
					self.addEmptyInstances2(datainstance[key], memo)

	def unpublish(self, dataid, eventclass=event.UnpublishEvent):
		'''Make a piece of data unavailable to other nodes.'''
		if not issubclass(eventclass, event.UnpublishEvent):
			raise TypeError('UnpublishEvent subclass required')
		self.datahandler.remove(dataid)
		self.outputEvent(eventclass(id=self.ID(), dataid=dataid))

	def publishRemote(self, idata):
		'''Publish a piece of data with the specified data ID, setting all other data with the same data ID to the data value (including other nodes).'''
		dataid = idata['id']
		nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid)
		if nodeiddata is None:
			# try a partial ID lookup
			nodeiddata = self.researchByLocation(self.nodelocations['manager'], dataid[:1])

		if nodeiddata is None:
			raise PublishError('No such Data ID: %s' % (dataid,))

		for nodeid in nodeiddata['location']:
			nodelocation = self.researchByLocation(self.nodelocations['manager'], nodeid)
			client = self.clientclass(nodelocation['location']['data transport'])
			client.push(idata)

	def locateDataByID(self, dataid):
		'''
		Asks manager to find nodes that are keeping data
		Returns a list of locations
		'''
		pass

	def researchByLocation(self, location, dataid):
		'''Get a piece of data with the specified data ID by the location of a node.'''
		client = self.clientclass(location['data transport'])
		try:
			cdata = client.pull(dataid)
		except IOError:
			cdata = None
		return cdata


	def researchByDataID(self, dataid):
		'''Get a piece of data with the specified data ID. Currently retrieves the data from the last node to publish it.'''
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

	def addManager(self, location):
		'''Set the manager controlling the node and notify said manager this node is available.'''
		self.managerclient = self.clientclass(location['data transport'])
		available_event = event.NodeAvailableEvent(id=self.ID(),
																							location=self.location(),
																							nodeclass=self.__class__.__name__)
		self.outputEvent(ievent=available_event, wait=True, timeout=10)

	def handleAddNode(self, ievent):
		'''Event handler calling addManager with event info. See addManager.'''
		if ievent['nodeclass'] == 'Manager':
			self.addManager(ievent['location'])

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
		return ''

	def defineUserInterface(self):
		idarray = uidata.String('ID', str(self.id), 'r')
		classstring = uidata.String('Class', self.__class__.__name__, 'r')
		location = self.key2str(self.location())
		locationstruct = uidata.Struct('Location', location, 'r')
		datakeepercontainer = self.datahandler.datakeeper.UI()
		exitmethod = uidata.Method('Exit', self.uiExit)

		container = uidata.LargeContainer('Node')
		if datakeepercontainer is not None:
			container.addObject(datakeepercontainer)
#		container.addObjects((idarray, class_string, locationstruct, exitmethod))
#		self.uiserver.addObject(container)
		self.uiserver.addObjects((idarray, classstring, locationstruct, exitmethod))

	def outputMessage(self, title, message, number=0):
		# log too maybe
		if hasattr(self, 'uiserver'):
			if number > 0:
				messagedialog = uidata.MessageDialog('%s #%d (%s)' % (title, number, str(self.id[-1])), message)
			else:
				messagedialog = uidata.MessageDialog('%s (%s)' % (title, str(self.id[-1])), message)
			try:
				self.uiserver.addObject(messagedialog)
			except ValueError:
				self.outputMessage(title, message, number + 1)
		else:
			self.printerror(title + ': ' + message)

	def outputWarning(self, warning):
		self.outputMessage('Warning', warning)

	def outputError(self, error):
		self.outputMessage('Error', error)

class ResearchError(Exception):
	pass

class PublishError(Exception):
	pass

class ConfirmationTimeout(Exception):
	pass
