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
import data

# preferences
import cPickle
import leginonconfig
import os

# range defined by IANA as dynamic/private
portrange = xrange(49152, 65536)

class NoValueError(Exception):
	pass

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
	def __init__(self, name='UI', port=None, tries=5,
								dbdatakeeper=None, session=None):
		self.xmlrpcclients = []
		self.localclients = []
		self.tries = tries
		self.dbdatakeeper = dbdatakeeper
		self.session = session

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
			self.setDatabaseFromObject(uidataobject)

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

#	def addObject(self, uiobject, block=True, thread=False):
#		uidata.Container.addObject(self, uiobject, block, thread)
#		self.usePreferences()

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
		if client is None:
			flag = self.setObjectFromDatabase(uiobject)
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

	def setObjectFromDatabase(self, uiobject):
		if self.dbdatakeeper is None or self.session is None:
			return False
		if isinstance(uiobject, uidata.Container):
			for childobject in uiobject.uiobjectlist:
				self.setObjectFromDatabase(childobject)
		if not isinstance(uiobject, uidata.Data) or not uiobject.persist:
			return False
		namelist = uiobject._getNameList()
		try:
			session = data.SessionData()
			session['user'] = self.session['user']
			initializer = {'session': session,
											'object': namelist}
			odata = data.UIData(initializer=initializer)
			results = self.dbdatakeeper.query(odata, results=1)
			if results:
				try:
					pickledvalue = results[0]['pickled value']
					try:
						value = cPickle.loads(pickledvalue)
					except:
						print 'Error unpickling UI value'
						return False
					uiobject.set(value, server=False)
					return True
				except KeyError:
					return False
		except:
			print 'Error setting preference'
		return False

	def setDatabaseFromObject(self, uiobject):
		if self.dbdatakeeper is None or self.session is None:
			print 'Cannot save UI values to database'
			return
		if isinstance(uiobject, uidata.Container):
			for childobject in uiobject.uiobjectlist:
				self.setDatabaseFromObject(childobject)
		if not isinstance(uiobject, uidata.Data):
			return
		namelist = uiobject._getNameList()
		value = uiobject.get()
		pickledvalue = cPickle.dumps(value, True)
		initializer = {'session': self.session,
										'object': namelist,
										'pickled value': pickledvalue}
		odata = data.UIData(initializer=initializer)
		self.dbdatakeeper.insert(odata, force=True)

	def _setObjectFromFile(self, uiobject, d):
		if isinstance(uiobject, uidata.Container):
			for childobject in uiobject.uiobjectlist:
				self._setObjectFromFile(childobject, d)
		if not isinstance(uiobject, uidata.Data) or not uiobject.persist:
			return
		namelist = uiobject._getNameList()
		if tuple(namelist) in d:
			try:
				uiobject.set(d[tuple(namelist)], server=False)
			except:
				print 'Error setting preference'

	def setObjectFromFile(self, uiobject):
		try:
			f = file(leginonconfig.PREFS_FILE, 'rb')
		except IOError, e:
			print 'Error setting preferences', e.strerror
			return
		try:
			d = cPickle.load(f)
		except Exception, e:
			print 'Invalid file for preferences'
			f.close()
			return
		self._setObjectFromFile(uiobject, d)
		f.close()
	
	def setFileFromObject(self, uiobject):
		if not isinstance(uiobject, uidata.Data):
			return
		try:
			f = file(leginonconfig.PREFS_FILE, 'wb')
		except IOError, e:
			print 'Error saving preferences', e.strerror
			return
		try:
			d = cPickle.load(f)
		except:
			d = {}
		namelist = uiobject._getNameList()
		d[tuple(namelist)]= uiobject.get()
		cPickle.dump(d, f, True)
		f.close()

	def setFromPickle(self, namelist, value):
		uidataobject = self._getObjectFromList(namelist)
		if not isinstance(uidataobject, uidata.Data):
			raise TypeError('name list does not resolve to Data instance')
		uidataobject._set(value)

	def usePreferences(self):
		d = self.getPickle()
		if not d:
			return
		for key, value in d.items():
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

