#!/usr/bin/env python

import leginonobject
import localtransport
import sys
#if sys.platform != 'win32':
#	import unixtransport
import tcptransport
import datahandler
import sys

class Base(leginonobject.LeginonObject):
	def __init__(self, id):
		leginonobject.LeginonObject.__init__(self, id)
		# order matters
#		if sys.platform != 'win32':
#			self.transportmodules = [localtransport, unixtransport, tcptransport]
#		else:
#			self.transportmodules = [localtransport, tcptransport]
		self.transportmodules = [localtransport, tcptransport]

class Client(Base):
	# hostname/port -> location or whatever
	# needs to be transport generalized like server
	def __init__(self, id, serverlocation):
		Base.__init__(self, id)
		self.clients = []

		for t in self.transportmodules:
			try:
				self.clients.append(apply(t.Client, (self.ID(), serverlocation,)))
			except ValueError:
				pass

		self.serverlocation = serverlocation
		if len(self.clients) == 0:
			raise IOError

	# these aren't ordering right, dictionary iteration
	def pull(self, idata):
		for c in self.clients:
			try:
				newdata = c.pull(idata)
				return newdata
			except IOError:
				pass
		self.printerror("IOError, unable to pull data " + str(idata))
		raise IOError

	def push(self, odata):
		for c in self.clients:
			try:
				ret = c.push(odata)
				return ret
			except IOError:
				pass
		self.printerror("IOError, unable to push data " + str(odata))
		raise IOError

class Server(Base):
	def __init__(self, id, dhclass = datahandler.SimpleDataKeeper, dhargs = (), tcpport=None):
		Base.__init__(self, id)
		ndhargs = [self.ID()]
		ndhargs += list(dhargs)
		self.datahandler = apply(dhclass, ndhargs)
		self.servers = {}
		for t in self.transportmodules:
			if tcpport is not None and t is tcptransport:
				args = (self.ID(), self.datahandler, tcpport)
			else:
				args = (self.ID(), self.datahandler)
			self.servers[t] = apply(t.Server, args)
			self.servers[t].start()

	def exit(self):
		for t in self.transportmodules:
			self.servers[t].exit()
		self.datahandler.exit()

	def location(self):
		loc = {}
		loc.update(leginonobject.LeginonObject.location(self))
		for t in self.transportmodules:
			loc.update(self.servers[t].location())
		return loc

if __name__ == '__main__':
	pass

