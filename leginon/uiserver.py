import inspect
import SimpleXMLRPCServer
import socket
import threading
import uidata

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

class UIServer(XMLRPCServer, uidata.UIContainer):
	def __init__(self, name='Server', port=None):
		self.uiclients = []
		XMLRPCServer.__init__(self, port=port)
		uidata.UIContainer.__init__(self, name)
		self.server.register_function(self.setFromClient, 'SET')
		self.server.register_function(self.addServer, 'ADDSERVER')

#	def clientDataPull(self, namelist):
#		'''UI client calls this over network to get a data value'''
#		uidataboject = self.getUIObjectFromList(namelist)
#		if not isinstance(uidataobject, uidata.UIData):
#			raise TypeError('name hierarchy list does not resolve to UIData instance')
#		value = uidataobject.get()
#		return value

	def setFromClient(self, namelist, value):
		'''this is how a UI client sets a data value'''
		print 'setFromClient', namelist, value
		uidataobject = self.getUIObjectFromList(namelist)
		print uidataobject
		if not isinstance(uidataobject, uidata.UIData):
			raise TypeError('name hierarchy list does not resolve to UIData instance')
		# except from this client?
		uidataobject.set(value)
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
		for uiobject in self.uiobjectdict.values():
			self.addUIObjects(addclient, uiobject, (self.name, uiobject.name))
		return ''

	def addUIObjects(self, client, uiobject, namelist):
		print 'updating', namelist
		client.execute('ADD', (namelist, uiobject.typename, uiobject.value))
		if isinstance(uiobject, uidata.UIContainer):
			for childuiobject in uiobject.uiobjectdict.values():
				self.addUIObjects(client, childuiobject, namelist+(childuiobject.name,))

	def addUIObjectCallback(self, namelist, typename, value):
		for client in self.uiclients:
			# delete if fail?
			client.execute('ADD', ((self.name,) + namelist, typename, value))

	def setUIObjectCallback(self, namelist, value):
		for client in self.uiclients:
			# delete if fail?
			client.execute('SET', ((self.name,) + namelist, value))

	def deleteUIObjectCallback(self, namelist):
		for client in self.uiclients:
			# delete if fail?
			client.execute('DEL', ((self.name,) + namelist,))

