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
import xmlrpclib

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
	def __init__(self, object_instance=None, port=None):
		self.object_instance = object_instance 
		self.port = port
		self.hostname = socket.gethostname()
		if self.port is not None:
			# this exception will fall through if __init__ fails
			self.server = SimpleXMLRPCServer.SimpleXMLRPCServer(
																	(self.hostname, self.port), logRequests=False)
			self._startServing()
			return

		# find a port in range defined by IANA as dynamic/private
		for self.port in portrange:
			try:
				self.server = SimpleXMLRPCServer.SimpleXMLRPCServer(
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
													target=self.server.serve_forever)
		t.setDaemon(1)
		t.start()
		self.serverthread = t


class Server(XMLRPCServer, uidata.Container):
	def __init__(self, name='UI', port=None, tries=5):
		self.xmlrpcclients = []
		self.localclients = []
		self.tries = tries
		self.failures = []

		self.pref_lock = threading.Lock()

		XMLRPCServer.__init__(self, port=port)
		uidata.Container.__init__(self, name)

		self.server.register_function(self.setFromClient, 'set')
		self.server.register_function(self.commandFromClient, 'command')
		self.server.register_function(self.addXMLRPCClientServer, 'add client')

	def getNameList(self):
		return ()

	def getObjectFromList(self, namelist):
		namelist[0] = self.name
		return uidata.Container.getObjectFromList(self, namelist)

	def setFromClient(self, namelist, value):
		'''this is how a UI client sets a data value'''
		uidataobject = self.getObjectFromList(namelist)
		if not isinstance(uidataobject, uidata.Data):
			raise TypeError('name list does not resolve to Data instance')
		# except from this client?
		uidataobject._set(value)

		# record new value in a pickle
		if uidataobject.persist:
			self.updatePickle(namelist, value)

		return ''

	def addObject(self, uiobject):
		uidata.Container.addObject(self, uiobject)

		# updates the objects with stored preferences
		self.usePreferences()

	def commandFromClient(self, namelist, args):
		uimethodobject = self.getObjectFromList(namelist)
		if not isinstance(uimethodobject, uidata.Method):
			raise TypeError('name list does not resolve to Method instance')
		apply(uimethodobject.method, args)
		return ''

#	def set(self, namelist, value):
#		for client in self.xmlrpcclients:
#			# delete if fail?
#			client.execute('set', (namelist, value))

	def addXMLRPCClientServer(self, hostname, port):
		# &@**!&!!!
		from uiclient import XMLRPCClient
		addclient = XMLRPCClient(hostname, port)
		self.xmlrpcclients.append(addclient)
		self.failures.append(0)
		self.addObjectsCallback(addclient)
		return ''

	def addLocalClient(self, client):
		self.localclients.append(client)
		self.addObjectsCallback(client)

	def localExecute(self, commandstring, properties, client=None):
		if client in self.localclients:
			localclients = [client]
		elif client is None:
			localclients = self.localclients
		else:
			return
		for localclient in localclients:
			target = getattr(localclient, commandstring)
			args = (properties,)
			threading.Thread(target=target, args=args).start()
#			apply(target, args)

	def XMLRPCExecute(self, commandstring, properties, client=None):
		if client in self.xmlrpcclients:
			xmlrpcclients = [client]
		elif client is None:
			xmlrpcclients = self.xmlrpcclients
		else:
			return
		failures = []
		for i, client in enumerate(xmlrpcclients):
			try:
				client.execute(commandstring, (properties,))
				self.failures[i] = 0
			except (xmlrpclib.ProtocolError, socket.error), e:
				self.failures[i] += 1
				if self.failures[i] >= self.tries:
					failures.append(i)
		for i in failures:
			del self.xmlrpcclients[i]
			del self.failures[i]

	def addObjectCallback(self, uiobject, client=None):
		properties = {}
		properties['dependencies'] = []
		properties['namelist'] = uiobject.getNameList()
		properties['typelist'] = uiobject.typelist
		try:
			properties['value'] = uiobject.value
		except AttributeError:
			pass
		properties['configuration'] = uiobject.getConfiguration()

		if 'client' in properties['typelist']:
			if properties['value'] is None:
				properties['value'] = uiobject.toXMLRPC(properties['value'])
		self.localExecute('addFromServer', properties, client)

		if hasattr(uiobject, 'toXMLRPC') and 'value' in properties:
			properties['value'] = uiobject.toXMLRPC(properties['value'])
		self.XMLRPCExecute('add', properties, client)

	def setObjectCallback(self, uiobject, client=None):
		properties = {}
		properties['namelist'] = uiobject.getNameList()
		properties['value'] = uiobject.value

		self.localExecute('setFromServer', properties, client)

		if hasattr(uiobject, 'toXMLRPC') and 'value' in properties:
			properties['value'] = uiobject.toXMLRPC(properties['value'])
		self.XMLRPCExecute('set', properties, client)

	def deleteObjectCallback(self, uiobject, client=None):
		properties = {}
		properties['namelist'] = uiobject.getNameList()
		self.localExecute('removeFromServer', properties, client)
		self.XMLRPCExecute('remove', properties, client)

	def configureObjectCallback(self, uiobject, client=None):
		properties = {}
		properties['namelist'] = uiobject.getNameList()
		properties['configuration'] = uiobject.getConfiguration()
		self.localExecute('configureFromServer', properties, client)
		self.XMLRPCExecute('configure', properties, client)

	# file based preference methods

	def setFromPickle(self, namelist, value):
		'''
		same as setFromClient, except this does not updatePickle
		'''
		uidataobject = self.getObjectFromList(namelist)
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

