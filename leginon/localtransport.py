#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import datatransport

locationkey = 'local transport'

class TransportError(datatransport.TransportError):
	pass

class Server(object):
	def __init__(self, dh):
		self.datahandler = dh

	def start(self):
		pass

	def exit(self):
		pass

	def handle(self, request):
		try:
			return self.datahandler.handle(request)
		except AttributeError:
			if self.datahandler is None:
				raise TransportError('error handling request, no handler')
			else:
				raise

	def location(self):
		return {'instance': self}

	def __reduce__(self):
		return (Server, (None,), {})

class Client(object):
	def __init__(self, location):
		if 'instance' not in location:
			raise ValueError('local client can only connect within a process')
		if not isinstance(location['instance'], Server):
			raise ValueError('local client can only connect to local server')
		self.serverobject = location['instance']

	def send(self, request):
		return self._send(request)

	def _send(self, request):
		return self.serverobject.handle(request)

if __name__ == '__main__':
	pass

