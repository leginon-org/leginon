#!/usr/bin/env python

import xmlrpclib
import threading
import code

class ManagerCLI(object):
	def __init__(self, managerobject=None, host=None, port=None):
		if managerobject:
			self.manager = managerobject
		elif host and port:
			uri = 'http://%s:%s' % (host, port)
			self.manager = xmlrpclib.ServerProxy(uri)
		else:
			raise RuntimeError('specify either managerobject or host and port')

		self.__interact()


	def launchers(self):
		'list the available launcher nodes'
		launcherlist = self.manager.uiGetInfo('launchers')
		for launcher in launcherlist:
			print '\t%s' % launcher

	def nodes(self):
		'list all available nodes'
		nodelist = self.manager.uiGetInfo('nodes')
		for node in nodelist:
			print '\t%s' % node

	def eventclasses(self):
		'list available event classes'
		eventclasslist = self.manager.uiGetInfo('eventclasses')
		for eventclass in eventclasslist:
			print '\t%s' % eventclass

	def nodeclasses(self):
		'list available node classes'
		nodeclasslist = self.manager.uiGetInfo('nodeclasses')
		for nodeclass in nodeclasslist:
			print '\t%s' % nodeclass

	def launch(self, name, launcher, nodeclass, args=(), newproc=0):
		'''
		launches a new node
		usage:  launch(name, launcher, nodeclass, args=(), newproc=0)
		'''
		self.manager.uiLaunch(name, launcher, nodeclass, args, newproc)

	def bind(self):
		'''
		bind an event class from one node to another node
		usage:  launch(eventclass, fromnode, tonode)
		'''
		eventclass_str = self.gui_eventclasslist.get()
		self.manager.uiAddDistmap(eventclass_str, fromnode_str, tonode_str)

	def __raw_input(self, prompt):
		newprompt = '%s %s' % (self.prompt, prompt)
		return raw_input(newprompt)

	def __interact(self):
		banner = """
	Manager Command Line Interface
	Available commands:
	    nodes
	    launchers
	    eventclasses
	    nodeclasses
	    launch
	    bind
		"""
		nodeid  = self.manager.uiGetID()
		self.prompt = nodeid[-1]
		readfunc = self.__raw_input
		local = locals()
		code.interact(banner, readfunc, local)

if __name__ == '__main__':
	import sys, signal, string
	args = (sys.argv[0], 'hostname', 'port')
	if len(sys.argv) != len(args):
		print 'usage:   %s' % string.join(args, ' ')
		sys.exit()

	c = ManagerCLI(host = sys.argv[1], port = sys.argv[2])
