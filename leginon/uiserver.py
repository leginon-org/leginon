import inspect
import SimpleXMLRPCServer
import socket
import threading
import uidata
import xmlrpclib

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
	def __init__(self, name='UI', port=None):
		self.uiclients = []
		XMLRPCServer.__init__(self, port=port)
		uidata.UIContainer.__init__(self, name)
		self.server.register_function(self.setFromClient, 'SET')
		self.server.register_function(self.commandFromClient, 'COMMAND')
		self.server.register_function(self.addServer, 'ADDSERVER')

	def getUIObjectFromList(self, namelist):
		namelist[0] = self.name
		return uidata.UIContainer.getUIObjectFromList(self, namelist)

	def setFromClient(self, namelist, value):
		'''this is how a UI client sets a data value'''
		uidataobject = self.getUIObjectFromList(namelist)
		if not isinstance(uidataobject, uidata.UIData):
			raise TypeError('name list does not resolve to UIData instance')
		# except from this client?
		uidataobject._set(value)
		return ''

	def commandFromClient(self, namelist, args):
		uimethodobject = self.getUIObjectFromList(namelist)
		if not isinstance(uimethodobject, uidata.UIMethod):
			raise TypeError('name list does not resolve to UIMethod instance')
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
		#for uiobject in self.uiobjectdict.values():
		for uiobject in self.uiobjectlist:
			self.addAllUIObjects(addclient, uiobject, (uiobject.name,))
		return ''

	def addAllUIObjects(self, client, uiobject, namelist):
		if hasattr(uiobject, 'value'):
			value = uiobject.value
		else:
			value = ''
		if hasattr(uiobject, 'read'):
			read = uiobject.read
		else:
			read = False
		if hasattr(uiobject, 'write'):
			write = uiobject.write
		else:
			write = False
		client.execute('ADD', (namelist, uiobject.typelist, value, read, write))
		if isinstance(uiobject, uidata.UIContainer):
			#for childuiobject in uiobject.uiobjectdict.values():
			for childuiobject in uiobject.uiobjectlist:
				self.addAllUIObjects(client, childuiobject, namelist+(childuiobject.name,))

	def addUIObjectCallback(self, namelist, typelist, value, read, write):
		for client in self.uiclients:
			# delete if fail?
			client.execute('ADD', (namelist, typelist, value, read, write))

	def setUIObjectCallback(self, namelist, value):
		for client in self.uiclients:
			# delete if fail?
			client.execute('SET', (namelist, value))

	def deleteUIObjectCallback(self, namelist):
		for client in self.uiclients:
			# delete if fail?
			client.execute('DEL', (namelist,))
			#threading.Thread(target=client.execute, args=('DEL', (namelist,))).start()

