#!/usr/bin/env python

import xmlrpcnode
import xmlrpclib
import os, threading, inspect

class Manager(xmlrpcnode.xmlrpcnode):
	def __init__(self, *args, **kwargs):
		xmlrpcnode.xmlrpcnode.__init__(self)

		self.nodes = {}
		self.bindings = {}

	def EXPORT_addNode(self, node):
		nodeid = node['id']
		self.nodes[nodeid] = node

		host = node['host']
		port = node['port']
		uri = 'http://' + host + ':' + `port`
		self.addProxy(nodeid, uri)
		print 'node %s has been added' % nodeid
		print 'nodes: %s' % self.nodes

	def EXPORT_deleteNode(self, nodeid):
		try:
			del(self.clients[nodeid])
			self.delProxy(nodeid)
			print 'node %s has been deleted' % id
		except KeyError:
			pass

	def EXPORT_notify(self, source, event):
		#sourceid = params['id']
		#event = params['event']
		#data = params['data']

		key = (source,event)
		print 'key', key
		if key in self.bindings:
			print 'bound to', self.bindings[key]
			calls = self.bindings[key]
			for target,method in calls:
				self.callProxy(target, method)

	def EXPORT_nodes(self):
		return self.nodes

	def EXPORT_bindings(self):
		bindlist = []
		for key in self.bindings:
			binditem = (key, self.bindings[key])
			bindlist.append(binditem)
		return bindlist

	def EXPORT_addBinding(self, source, event, target, method):
		key = (source,event)
		bindtup = (target, method)
		if key not in self.bindings:
			self.bindings[key] = []
		if bindtup not in self.bindings[key]:
			self.bindings[key].append(bindtup)
		print 'bindings', self.bindings

	def EXPORT_deleteBinding(self, source, event, target, method):
		key = (source, event)
		bindtup = (target, method)
		if key in self.bindings:
			self.bindings[key].remove(bindtup)
			if not self.bindings[key]:
				del(self.bindings[key])


class Node(xmlrpcnode.xmlrpcnode):
	def __init__(self, id, managerhost = None, managerport = None):
		xmlrpcnode.xmlrpcnode.__init__(self)

		self.id = id

		## events should be initialized by subclass before this
		self.events = getattr(self, 'events', [])

		if managerhost and managerport:
			manager_uri = 'http://' + managerhost + ':' + `managerport`
			self.manager_connect(manager_uri)

	def __del__(self):
		self.manager_close()

	def manager_connect(self, uri):
		self.addProxy('manager', uri)
		meths = self.EXPORT_methods()
		nodeinfo = {'id':self.id, 'host':self.host, 'port':self.port, 'methods':meths, 'events':self.events}
		args = (nodeinfo,)
		self.callProxy('manager', 'addNode', args)

	def manager_notify(self, event):
		args = (self.id, event)
		self.callProxy('manager', 'notify', args)

	def manager_close(self):
		print 'manager_close'
		try:
			args = (self.id,)
			self.callProxy('manager', 'deleteNode', args)
		except:
			pass


class Event(object):
	def __init__(self, source, data=None):
		self.source = source
		self.data = data


if __name__ == '__main__':
	import signal
	manager = Manager()
	print 'server running on port', manager.port
	signal.pause()
