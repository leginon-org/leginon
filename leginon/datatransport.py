#!/usr/bin/env python

import leginonobject
import localtransport
import tcptransport
import datahandler

class Base(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.transportmodules = [localtransport, tcptransport]

class Client(Base):
	# hostname/port -> location or whatever
	# needs to be transport generalized like server
	def __init__(self, serverlocation):
		Base.__init__(self)
		self.clients = {}

#		for t in self.transportmodules:
#			self.clients[t] = apply(t.Client, (serverlocation,))

		# will make manager sort this out soon
		clientlocation = self.location()
		if ('hostname' in serverlocation) and ('hostname' in clientlocation) and (serverlocation['hostname'] == clientlocation['hostname']):
				self.clients[localtransport] = apply(localtransport.Client, (serverlocation,))
		self.clients[tcptransport] = apply(tcptransport.Client, (serverlocation,))

	def pull(self, id):
		try:
			return self.clients[localtransport].pull(id)
		except KeyError, IOError:
			return self.clients[tcptransport].pull(id)

	def push(self, idata):
		try:
			self.clients[localtransport].push(idata)
		except KeyError, IOError:
			self.clients[tcptransport].push(idata)

class Server(Base):
	def __init__(self, dhclass = datahandler.SimpleDataKeeper, dhargs = ()):
		Base.__init__(self)
		self.datahandler = apply(dhclass, dhargs)
		self.servers = {}
		for t in self.transportmodules:
			self.servers[t] = apply(t.Server, (self.datahandler,))
			self.servers[t].start()

	def location(self):
		loc = {}
		loc.update(leginonobject.LeginonObject.location(self))
		for t in self.transportmodules:
			loc.update(self.servers[t].location())
		return loc

if __name__ == '__main__':
	pass

