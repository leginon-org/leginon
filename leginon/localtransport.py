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

	def location(self):
		return {'instance': self}
		#return {}

class Client(object):
	def __init__(self, location):
		if 'instance' not in location:
			raise ValueError('local client can only connect within a process')
		if not isinstance(location['instance'], Server):
			raise ValueError('local client can only connect to local server')
		self.serverobject = location['instance']

	def push(self, idata):
		return self._push(idata)

	def _push(self, idata):
		try:
			return self.serverobject.datahandler.insert(idata)
		except:
			raise IOError('Local transport client unable to insert data')

	def pull(self, id):
		return self._pull(id)

	def _pull(self, id):
		try:
			return self.serverobject.datahandler.query(id)
		except:
			raise IOError('Local transport client unable to query id')

if __name__ == '__main__':
	pass

