#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

#import socket
#import threading

locationkey = 'local transport'

class Server(object):
	def __init__(self, dh):
		self.datahandler = dh

	def start(self):
		pass

	def exit(self):
		pass

	def handle(self, request):
		return self.datahandler.handle(request)

	def location(self):
		return {'instance': self}

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
		try:
			return self.serverobject.handle(request)
		except Exception, e:
			raise IOError('Local transport client send request')

if __name__ == '__main__':
	pass

