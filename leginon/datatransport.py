#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import localtransport
import tcptransport
import threading
import logging
import time
import sys

class Base(object):
	def __init__(self, logger):
		# order matters
		self.transportmodules = [localtransport, tcptransport]
		self.logger = logger

class Client(Base):
	# hostname/port -> location or whatever
	# needs to be transport generalized like server
	def __init__(self, serverlocation, logger):
		Base.__init__(self, logger)

		self.clients = []

		for t in self.transportmodules:
			try:
				self.clients.append(t.Client(serverlocation[t.locationkey],))
				self.logger.info('%s client added' % t.__name__)
			except (ValueError, KeyError):
				self.logger.warning('%s client add failed' % t.__name__)
				pass

		self.serverlocation = serverlocation
		self.logger.info('server location set to to %s' % str(self.serverlocation))
		if len(self.clients) == 0:
			raise IOError('no client connections possible')

	# these aren't ordering right, dictionary iteration
	def _send(self, request):
		for client in self.clients:
			try:
				return client.send(request)
			except IOError:
				self.logger.warning('%s client send request failed' % str(c))
		raise IOError('Unable to send request')

	def send(self, request):
		try:
			result = self._send(request)
		except Exception, e:
			raise IOError
		if isinstance(result, Exception):
			raise result
		return result

class Server(Base):
	def __init__(self, dh, logger, tcpport=None):
		Base.__init__(self, logger)
		self.datahandler = dh
		self.servers = {}
		for t in self.transportmodules:
			if tcpport is not None and t is tcptransport:
				args = (self.datahandler, tcpport)
			else:
				args = (self.datahandler,)
			self.servers[t] = t.Server(*args)
			self.servers[t].start()
			self.logger.info('%s server created at location %s'
												% (t.__name__, self.servers[t].location()))

	def exit(self):
		for t in self.transportmodules:
			self.servers[t].exit()
			self.logger.info('%s server exited' % t.__name__)
		self.logger.info('Exited')

	def location(self):
		location = {}
		for t in self.transportmodules:
			location[t.locationkey] = (self.servers[t].location())
		return location

if __name__ == '__main__':
	pass

