#!/usr/bin/env python

import interface
import threading
import code

class ManagerCLI(object):
	def __init__(self, hostname, port):
		self.uiclient = interface.Client(hostname, port)
		self.refresh()
		self.__interact()

	def refresh(self):
		self.uiclient.getMethods()

	def launchers(self):
		'list the available launcher nodes'
		launcherlist = self.uiclient.execute('launchers')
		for launcher in launcherlist:
			print '\t%s' % launcher

	def nodes(self):
		'list all available nodes'
		nodelist = self.uiclient.execute('nodes')
		for node in nodelist:
			print '\t%s' % node

	def eventclasses(self):
		'list available event classes'
		eventclasslist = self.uiclient.execute('eventclasses')
		for eventclass in eventclasslist:
			print '\t%s' % eventclass

	def nodeclasses(self):
		'list available node classes'
		nodeclasslist = self.uiclient.execute('nodeclasses')
		for nodeclass in nodeclasslist:
			print '\t%s' % nodeclass

	def launch(self, name, launcher, nodeclass, args='', newproc=0):
		'''
		launches a new node
		usage:  launch(name, launcher, nodeclass, args='', newproc=0)
		'''
		self.uiclient.setarg('launch', 'name', name)
		self.uiclient.setarg('launch', 'launcher_str', launcher)
		self.uiclient.setarg('launch', 'nodeclass_str', nodeclass)
		self.uiclient.setarg('launch', 'args', args)
		self.uiclient.setarg('launch', 'newproc', newproc)
		self.uiclient.execute('launch')

	def bind(self, eventclass, fromnode, tonode):
		'''
		bind an event class from one node to another node
		usage:  launch(eventclass, fromnode, tonode)
		'''
		self.uiclient.setarg('bind', 'eventclass_str', eventclass)
		self.uiclient.setarg('bind', 'fromnode_str', fromnode)
		self.uiclient.setarg('bind', 'tonode_str', tonode)
		self.uiclient.execute('bind')

	def __raw_input(self, prompt):
		newprompt = '%s %s' % (self.prompt, prompt)
		raw = raw_input(newprompt)
		if raw != '':
			selfish = 'self.' + raw
		else:
			selfish = ''
		return selfish

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
		nodeid  = self.uiclient.execute('id')
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

	c = ManagerCLI(hostname = sys.argv[1], port = sys.argv[2])
