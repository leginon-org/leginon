#!/usr/bin/env python
import leginonobject
import copy

class Server(leginonobject.LeginonObject):
	def __init__(self, dk):
		leginonobject.LeginonObject.__init__(self)
		self.datakeeper = dk

class PullServer(Server):
	def datafromid(self, data_id):
		return self.datakeeper.query(data_id)

class PushServer(Server):
	def datatoid(self, data_id, newdata):
		return self.datakeeper.insert(newdata)

class Client(leginonobject.LeginonObject):
	def __init__(self, server):
		leginonobject.LeginonObject.__init__(self)
		self.server = server

class PullClient(Client):
	def pull(self, data_id):
		return copy.deepcopy(self.server.datafromid(data_id))

class PushClient(Client):
	def push(self, data_id, data):
		# copy the data_id?
		return self.server.datatoid(data_id, copy.deepcopy(data))

if __name__ == '__main__':
	import threading

	class dummyServer:
		def datafromid(self, data_id):
			return {data_id : 'foo bar'}
		def datatoid(self, data_id, data):
			print `{data_id : data}`

	pullserver = PullServer(dummyServer())
	pushserver = PushServer(dummyServer())

	pullclient = PullClient(pullserver)
	pushclient = PushClient(pushserver)
	print 'Test pulling:'
	print pullclient.pull('my data id')
	print 'Test pushing:'
	print pushclient.push('my data id', [1,2,3,4])

