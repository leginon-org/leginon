#!/usr/bin/env python

from Tkinter import *
import threading
import leginonobject
import datahandler
import node
import data
import common
import event
import signal
import os

class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, 'manager', None)

		self.common = common
		self.distmap = {}

		## this makes every received event get distributed
		self.addEventInput(event.Event, self.distribute)
		self.addEventInput(event.NodeReadyEvent, self.registerNode)
		#self.addDistmap(event.PublishEvent, , ):

		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.ListPublishEvent, self.registerData)

		self.main()

	def main(self):
		print self.location()

		guithread = threading.Thread(target=self.gui)
		guithread.setDaemon(1)
		guithread.start()

		self.interact()

	def registerNode(self, readyevent):
		print 'registering node', readyevent.origin
		self.addEventClient(readyevent.origin['id'], readyevent.origin['location'])
		print self.clients

	def registerData(self, publishevent):
		#print 'registering data, from', publishevent.origin
		if isinstance(publishevent, event.PublishEvent):
			id = publishevent.content
			self.publishDataLocation(id, publishevent.origin['id'])
		elif isinstance(publishevent, event.ListPublishEvent):
			for id in publishevent.content:
				self.publishDataLocation(id, publishevent.origin['id'])
		else:
			raise TypeError

	# I think the data location should be looked up dynamically based on
	# node ID, I had a ManagerDataHandler, but things didn't quite work out
	# To keep it simple for now the static location is stored
	def publishDataLocation(self, dataid, nodeid):
		locationdata = self.server.datahandler.query(dataid)
		#print "locationdata =", locationdata
		if locationdata == None:
			locationdata = data.LocationData(dataid, [self.clients[nodeid].serverlocation])
		else:
			locationdata.content.append(self.clients[nodeid].serverlocation)
		self.server.datahandler._insert(locationdata)

	def launchNode(self, launcher, newproc, target, newid, nodeargs=()):
		manloc = self.location()
		args = tuple([newid, manloc] + list(nodeargs))
		self.launch(launcher, newproc, target, args)

	def launch(self, launcher, newproc, target, args=(), kwargs={}):
		"""
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = callable object under self.common
		args, kwargs = args for callable object
		"""
		#ev = event.LaunchEvent(nodeid, nodeclass, newproc)
		ev = event.LaunchEvent(newproc, target, args, kwargs)
		self.clients[launcher].push(ev)

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, ievent):
		'''push event to eventclients based on event class and source'''
		#print 'DIST', event.origin
		eventclass = ievent.__class__
		from_node = ievent.origin['id']
		done = []
		for distclass,fromnodes in self.distmap.items():
			if issubclass(eventclass, distclass):
				for fromnode in (from_node, None):
					if fromnode in fromnodes:
						for to_node in fromnodes[from_node]:
							if to_node:
								if to_node not in done:
									self.clients[to_node].push(ievent)
									done.append(to_node)
							else:
								for to_node in self.handler.clients:
									if to_node not in done:
										self.clients[to_node].push(ievent)
										done.append(to_node)


	def gui(self):
		"""
		open a GUI for the manager	
		"""

		root = Tk()

		self.gui_launch_launcher = StringVar()
		self.gui_launch_target = StringVar()
		self.gui_launch_newproc = IntVar()
		self.gui_launch_id = StringVar()
		self.gui_launch_args = StringVar()

		#### Launch Node Frame
		launch_frame = Frame(root)

		f = Frame(launch_frame)
		lab = Label(f, text='Launcher')
		ent = Entry(f, textvariable=self.gui_launch_launcher)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Class')
		ent = Entry(f, textvariable=self.gui_launch_target)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node ID')
		ent = Entry(f, textvariable=self.gui_launch_id)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Args')
		ent = Entry(f, textvariable=self.gui_launch_args)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		newproc = Checkbutton(launch_frame, text='New Process', variable=self.gui_launch_newproc) 
		newproc.pack(side=TOP)

		launch_but = Button(launch_frame, text='LAUNCH')
		launch_but['command'] = self.gui_launch_command
		launch_but.pack(side=TOP)

		launch_frame.pack(side=TOP)

		root.mainloop()

	def gui_launch_command(self):
		launcher = self.gui_launch_launcher.get()
		newproc = self.gui_launch_newproc.get()

		target = self.gui_launch_target.get()
		target = 'self.common.%s' % target
		print 'TARGET', target
		try:
			target = eval(target)
		except:
			print 'problem evaluating target'
			return
		newid = self.gui_launch_id.get()

		args = self.gui_launch_args.get()
		args = '(%s)' % args
		print 'args', args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher, newproc, target, newid, args)


if __name__ == '__main__':
	import signal, sys
	m = Manager()




