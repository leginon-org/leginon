#!/usr/bin/env python

import leginonobject
import localtransport
#import unixtransport
import tcptransport
import datahandler
import sys

class Base(leginonobject.LeginonObject):
	def __init__(self, id):
		leginonobject.LeginonObject.__init__(self, id)
#		self.transportmodules = [localtransport, unixtransport, tcptransport]
		self.transportmodules = [localtransport, tcptransport]

class Client(Base):
	# hostname/port -> location or whatever
	# needs to be transport generalized like server
	def __init__(self, id, serverlocation):
		Base.__init__(self, id)
		self.clients = {}

#		for t in self.transportmodules:
#			self.clients[t] = apply(t.Client, (self.ID(), serverlocation,))

		# will make manager sort this out soon
		clientlocation = self.location()
		if ('hostname' in serverlocation) and ('hostname' in clientlocation) \
				and (serverlocation['hostname'] == clientlocation['hostname']):
#			if ('PID' in serverlocation) and ('PID' in clientlocation) \
#					and (serverlocation['PID'] == clientlocation['PID']):
			self.clients[localtransport] = \
				apply(localtransport.Client, (self.ID(), serverlocation,))

#			try:
#				self.clients[unixtransport] = \
#					apply(unixtransport.Client, (self.ID(), serverlocation,))
#			except AttributeError:
#				del self.clients[unixtransport]

		self.clients[tcptransport] = apply(tcptransport.Client, (self.ID(), serverlocation,))

		self.serverlocation = serverlocation

	def pull(self, idata):
		try:
			return self.clients[localtransport].pull(idata)
		except KeyError, IOError:
#			try:
#				return self.clients[unixtransport].pull(idata)
#			except KeyError, IOError:
			return self.clients[tcptransport].pull(idata)

	def push(self, odata):
		try:
			self.clients[localtransport].push(odata)
		except KeyError, IOError:
#			try:
#				return self.clients[unixtransport].push(odata)
#			except KeyError, IOError:
			return self.clients[tcptransport].push(odata)

class Server(Base):
	def __init__(self, id, dhclass = datahandler.SimpleDataKeeper, dhargs = ()):
		Base.__init__(self, id)
		ndhargs = [self.ID()]
		ndhargs += list(dhargs)
		self.datahandler = apply(dhclass, ndhargs)
		self.servers = {}
		for t in self.transportmodules:
			self.servers[t] = apply(t.Server, (self.ID(), self.datahandler))
			self.servers[t].start()

	def __del__(self):
		#self.exit()
		pass

	def exit(self):
		self.datahandler.exit()
		for s in self.servers:
			self.servers[s].exit()

	def location(self):
		loc = {}
		loc.update(leginonobject.LeginonObject.location(self))
		for t in self.transportmodules:
			loc.update(self.servers[t].location())
		return loc

if __name__ == '__main__':
	pass

