#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import SimpleXMLRPCServer
import socket
import threading
import uidata
import extendedxmlrpclib
import Queue

# preferences
import cPickle
import leginonconfig
import os

# range defined by IANA as dynamic/private
portrange = xrange(49152, 65536)

class XMLRPCServer(object):
	"""
	A SimpleXMLRPCServer that figures out its own host and port
	Sets self.host and self.port accordingly
	"""
	def __init__(self, port=None):
		self.hostname = socket.gethostname().lower()

		self.port = port
		if self.port is not None:
			# this exception will fall through if __init__ fails
			self.xmlrpcserver = SimpleXMLRPCServer.SimpleXMLRPCServer(
																	(self.hostname, self.port), logRequests=False)
			self._startServing()
			return

		# find a port in range defined by IANA as dynamic/private
		for self.port in portrange:
			try:
				self.xmlrpcserver = SimpleXMLRPCServer.SimpleXMLRPCServer(
																										(self.hostname, self.port),
																										logRequests=False)
				break
			except Exception, var:
				if (var[0] == 98 or var[0] == 10048 or var[0] == 112):
					continue
				else:
					raise
		if self.port is None:
			raise RuntimeError('no ports available')

		self._startServing()

	def _startServing(self):
		t = threading.Thread(name='UI XML-RPC server thread',
													target=self.xmlrpcserver.serve_forever)
		t.setDaemon(1)
		t.start()
		self.serverthread = t

class Server(XMLRPCServer, uidata.Container):
	typelist = uidata.Container.typelist + ('server',)
	def __init__(self, name='UI', port=None, tries=5):
		self.xmlrpcclients = []
		self.localclients = []
		self.tries = tries

		self.pref_lock = threading.Lock()

		XMLRPCServer.__init__(self, port=port)

		uidata.Container.__init__(self, name)
		self.server = self

		self.xmlrpcserver.register_function(self.setFromClient, 'set')
		self.xmlrpcserver.register_function(self.commandFromClient, 'command')
		self.xmlrpcserver.register_function(self.addXMLRPCClientServer,	
																				'add client')

	def location(self):
		location = {}
		location['hostname'] = self.hostname
		location['XML-RPC port'] = self.port
		location['instance'] = self
		return location

	def _getNameList(self):
		return []

	def _getObjectFromList(self, namelist):
		namelist[0] = self.name
		return uidata.Container._getObjectFromList(self, namelist)

	def setFromClient(self, namelist, value):
		'''this is how a UI client sets a data value'''
		uidataobject = self._getObjectFromList(namelist)
		if not isinstance(uidataobject, uidata.Data):
			raise TypeError('name list does not resolve to Data instance')
		# except from this client?
		uidataobject._set(value)

		# record new value in a pickle
		if uidataobject.persist:
			self.updatePickle(namelist, value)

		return ''

	def commandFromClient(self, namelist, args):
		uimethodobject = self._getObjectFromList(namelist)
		if not isinstance(uimethodobject, uidata.Method):
			raise TypeError('name list does not resolve to Method instance')
		apply(uimethodobject.method, args)
		return ''

	def addXMLRPCClientServer(self, hostname, port):
		for client in list(self.xmlrpcclients):
			if client.serverhostname == hostname and client.serverport == port:
				self.xmlrpcclients.remove(client)
			
		from uiclient import XMLRPCClient
		client = XMLRPCClient(hostname, port)
		self.xmlrpcclients.append(client)
		for childobject in self.uiobjectlist:
			self._addObject(childobject, client)
		return ''

	def addLocalClient(self, client):
		self.localclients.append(client)
		for childobject in self.uiobjectlist:
			self._addObject(childobject, client)

	def localExecute(self, commandstring, properties,
										client=None, block=True, thread=False):
		if client in self.localclients:
			localclients = [client]
		elif client is None:
			localclients = self.localclients
		else:
			return
		for localclient in localclients:
			target = getattr(localclient, commandstring)
			args = (properties,)
			if thread:
				localthread = threading.Thread(name='UI local execute thread',
																				target=target, args=args)
				localthread.start()
			else:
				apply(target, args)

	def XMLRPCExecute(self, commandstring, properties,
										client=None, block=True, thread=False):
		if client in self.xmlrpcclients:
			xmlrpcclients = [client]
		elif client is None:
			xmlrpcclients = self.xmlrpcclients
		else:
			return

		removeclients = []
		if thread:
			removeclientslock = threading.Lock()
		else:
			removeclientslock = None

		# marshalling XML-RPC data for each client inefficient
		for client in xmlrpcclients:
			if thread:
				xmlrpcthread = threading.Thread(name='UI XML-RPC execute thread',
																				target=self.XMLRPCClientExecute,
																				args=(commandstring, properties, client,
																							removeclients, removeclientslock))
				xmlrpcthread.start()
			else:
				self.XMLRPCClientExecute(commandstring, properties, client,
																	removeclients, removeclientslock)

		for removeclient in removeclients:
			try:
				self.xmlrpcclients.remove(removeclient)
			except ValueError:
				pass

	def XMLRPCClientExecute(self, commandstring, properties, client,
													removeclients=None, removeclientslock=None):
		failures = 0
		while failures < self.tries:
			try:
				client.execute(commandstring, (properties,))
				return
			except (extendedxmlrpclib.ProtocolError, socket.error), e:
				failures += 1
		if removeclientslock is not None:
			removeclientslock.acquire()
		removeclients.append(client)
		if removeclientslock is not None:
			removeclientslock.release()

	def addObject(self, uiobject, block=True, thread=False):
		uidata.Container.addObject(self, uiobject, block, thread)

		# updates the objects with stored preferences
		self.usePreferences()

	def propertiesFromObject(self, uiobject, block, thread):
		properties = {}
		properties['dependencies'] = []
		properties['namelist'] = uiobject._getNameList()
		properties['typelist'] = uiobject.typelist
		try:
			properties['value'] = uiobject.value
		except AttributeError:
			properties['value'] = None
		properties['configuration'] = uiobject.configuration
		if thread:
			block = False
		properties['block'] = block
		if isinstance(uiobject, uidata.Container):
			properties['children'] = []
			for childobject in uiobject.uiobjectlist:
				properties['children'].append(self.propertiesFromObject(childobject,
																																block, thread))
		return properties

	def _addObject(self, uiobject, client=None, block=True, thread=True):
		properties = self.propertiesFromObject(uiobject, block, thread)
		self.localExecute('addFromServer', properties, client, block, thread)
		self.XMLRPCExecute('add', properties, client, block, thread)

	def _setObject(self, uiobject, client=None, block=True, thread=False):
		properties = {}
		properties['namelist'] = uiobject._getNameList()
		properties['value'] = uiobject.value

		if thread:
			block = False
		properties['block'] = block

		self.localExecute('setFromServer', properties, client, block, thread)
		self.XMLRPCExecute('set', properties, client, block, thread)

	def _deleteObject(self, uiobject, client=None, block=True, thread=False):
		properties = {}
		properties['namelist'] = uiobject._getNameList()

		if thread:
			block = False
		properties['block'] = block

		self.localExecute('removeFromServer', properties, client, block, thread)
		self.XMLRPCExecute('remove', properties, client, block, thread)

	def _configureObject(self, uiobject, client=None, block=True, thread=False):
		properties = {}
		properties['namelist'] = uiobject._getNameList()
		properties['configuration'] = uiobject.configuration

		if thread:
			block = False
		properties['block'] = block

		self.localExecute('configureFromServer', properties, client, block, thread)
		self.XMLRPCExecute('configure', properties, client, block, thread)

	# file based preference methods

	def setFromPickle(self, namelist, value):
		'''
		same as setFromClient, except this does not updatePickle
		'''
		uidataobject = self._getObjectFromList(namelist)
		if not isinstance(uidataobject, uidata.Data):
			raise TypeError('name list does not resolve to Data instance')
		# except from this client?
		uidataobject._set(value)

	### Where should this be called?
	### and is this just a really bad idea for something like
	### EM that does a lot of stuff in a callback when a value is set
	### I guess things like that are not "preferences", but they are
	### all treated the same here.  Anything data value in the user
	### interface is a preference
	def usePreferences(self):
		'''
		this "replays" the recorded user preferences
		'''
		d = self.getPickle()
		if not d:
			return
		for key,value in d.items():
			namelist = list(key)
			try:
				self.setFromPickle(namelist, value)
			except ValueError:
				pass

	def getPickle(self, namelist=None):
		self.pref_lock.acquire()
		try:
			value = self._getPickle(namelist)
		finally:
			self.pref_lock.release()
		return value

	def _getPickle(self, namelist=None):
		### maybe want a lock on this
		fname = '%s.pref' % (self.name,)
		fname = os.path.join(leginonconfig.PREFS_PATH, fname)
		try:
			f = file(fname, 'rb')
		except IOError:
			d = {}
		else:
			try:
				d = cPickle.load(f)
			except:
				print 'bad pickle in %s' % (fname,)
				d = {}
			f.close()
		if namelist is None:
			value = d
		else:
			try:
				value = d[tuple(namelist)]
			except KeyError:
				value = None
		return value

	def updatePickle(self, namelist, value):
		self.pref_lock.acquire()
		try:
			self._updatePickle(namelist, value)
		finally:
			self.pref_lock.release()

	def _updatePickle(self, namelist, value):
		### maybe want a lock on this
		fname = '%s.pref' % (self.name,)
		fname = os.path.join(leginonconfig.PREFS_PATH, fname)

		## read current value
		try:
			f = file(fname, 'rb')
		except IOError:
			d = {}
		else:
			try:
				d = cPickle.load(f)
			except:
				print 'bad pickle in %s' % (fname,)
				d = {}
			f.close()
		## update and store
		d[tuple(namelist)] = value
		f = file(fname, 'wb')
		cPickle.dump(d, f, True)
		f.close()

