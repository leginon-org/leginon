import inspect
import SimpleXMLRPCServer
import socket
import threading
import uidata
import xmlrpclib
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
			self.server = SimpleXMLRPCServer.SimpleXMLRPCServer((self.hostname, 
																								 self.port), logRequests=False)
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
	def __init__(self, name='UI', port=None):
		self.uiclients = []
		XMLRPCServer.__init__(self, port=port)
		uidata.Container.__init__(self, name)
		self.server.register_function(self.setFromClient, 'SET')
		self.server.register_function(self.commandFromClient, 'COMMAND')
		self.server.register_function(self.addServer, 'ADDSERVER')

	def getObjectFromList(self, namelist):
		namelist[0] = self.name
		return uidata.Container.getObjectFromList(self, namelist)

	def setFromClient(self, namelist, value):
		#print 'setFromClient', namelist
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
		### calls base class addObject, but then updates
		### the objects with stored preferences
		uidata.Container.addObject(self, uiobject)
		self.usePreferences()

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
		### maybe want a lock on this
		fname = '%s.pref' % (self.name,)
		fname = os.path.join(leginonconfig.PREFS_PATH, fname)
		try:
			f = open(fname, 'r')
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
		### maybe want a lock on this
		fname = '%s.pref' % (self.name,)
		fname = os.path.join(leginonconfig.PREFS_PATH, fname)

		## read current value
		try:
			f = open(fname, 'r')
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
		f = open(fname, 'w')
		cPickle.dump(d, f, 1)
		f.close()

	def commandFromClient(self, namelist, args):
		#print 'commandFromClient', namelist, args
		uimethodobject = self.getObjectFromList(namelist)
		if not isinstance(uimethodobject, uidata.Method):
			raise TypeError('name list does not resolve to Method instance')
		# need to catch arg error
		#threading.Thread(name=uimethodobject.name + ' thread',
		#									target=uimethodobject.method, args=args).start()
		apply(uimethodobject.method, args)
		return ''

	def set(self, namelist, value):
		for client in self.uiclients:
			# delete if fail?
			client.execute('SET', (namelist, value))

	def addServer(self, hostname, port):
		# mapping to trackable value?
		import uiclient
		addclient = uiclient.XMLRPCClient(hostname, port)
		self.uiclients.append(addclient)
		self.addObjectsCallback(addclient)
		return ''

	def addObjectCallback(self, dependencies, namelist, typelist, value, settings, client=None):
		if client is not None:
			try:
				client.execute('ADD', (dependencies, namelist, typelist, value, settings))
			except xmlrpclib.ProtocolError, e:
				print 'Error adding to client ' + str(client) + ': ' + str(e)
		else:
			for client in self.uiclients:
				# delete if fail?
				try:
					client.execute('ADD',
													(dependencies, namelist, typelist, value, settings))
				except (xmlrpclib.ProtocolError, socket.error), e:
					print 'Error adding to client ' + str(client) + ': ' + str(e)

	def setObjectCallback(self, namelist, value):
		for client in self.uiclients:
			# delete if fail?
			try:
				client.execute('SET', (namelist, value))
			except (xmlrpclib.ProtocolError, socket.error), e:
				print 'Error setting client ' + str(client) + ': ' + str(e)

	def deleteObjectCallback(self, namelist):
		for client in self.uiclients:
			# delete if fail?
			try:
				client.execute('DEL', (namelist,))
			except (xmlrpclib.ProtocolError, socket.error), e:
				print 'Error deleting from client ' + str(client) + ': ' + str(e)

	def settingsObjectCallback(self, namelist, settings):
		for client in self.uiclients:
			# delete if fail?
			try:
				client.execute('SETTINGS', (namelist, settings))
			except xmlrpclib.ProtocolError, e:
				print 'Error setting settings client ' + str(client) + ': ' + str(e)

