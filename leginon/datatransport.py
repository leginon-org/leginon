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

class Base(object):
	def __init__(self):
		# order matters
		self.transportmodules = [localtransport, tcptransport]

class Client(Base):
	# hostname/port -> location or whatever
	# needs to be transport generalized like server
	def __init__(self, serverlocation):
		Base.__init__(self)
		self.clients = []

		for t in self.transportmodules:
			try:
				self.clients.append(apply(t.Client, (serverlocation[t.locationkey],)))
			except (ValueError, KeyError):
				pass

		self.serverlocation = serverlocation
		if len(self.clients) == 0:
			raise IOError('no client connections possible')

		self.lock = threading.RLock()

	# these aren't ordering right, dictionary iteration
	def _pull(self, idata):
		for c in self.clients:
			try:
				newdata = c.pull(idata)
				return newdata
			except IOError:
				pass
		print "IOError, unable to pull data " + str(idata)
		raise IOError

	def pull(self, idata):
		self.lock.acquire()
		try:
			ret = self._pull(idata)
			self.lock.release()
			return ret
		except:
			self.lock.release()
			raise

	def _push(self, odata):
		for c in self.clients:
			try:
				ret = c.push(odata)
				return ret
			except IOError:
				pass
			except:
				raise
		print "IOError, unable to push data " + str(odata)
		raise IOError()

	def push(self, odata):
		self.lock.acquire()
		try:
			ret = self._push(odata)
			self.lock.release()
			return ret
		except:
			self.lock.release()
			raise

class Server(Base):
	def __init__(self, dh, tcpport=None):
		Base.__init__(self)
		self.datahandler = dh
		self.servers = {}
		for t in self.transportmodules:
			if tcpport is not None and t is tcptransport:
				args = (self.datahandler, tcpport)
			else:
				args = (self.datahandler,)
			self.servers[t] = apply(t.Server, args)
			self.servers[t].start()

	def exit(self):
		for t in self.transportmodules:
			self.servers[t].exit()

	def location(self):
		location = {}
		for t in self.transportmodules:
			location[t.locationkey] = (self.servers[t].location())
		return location

if __name__ == '__main__':
	pass

