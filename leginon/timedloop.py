#!/usr/bin/env python

import threading
import node
import event

class TimedLoop(node.Node):
	"""
	A node that implements a timed action loop
	The default interval is 0 seconds, meaning it will perform the 
	action as fast as possible.
	Event Inputs:
		StartEvent - starts the loop
		StopEvent - stops the loop
		NumericControlEvent - modifies the loop interval
	"""
	def __init__(self, nodeid, managerlocation):
		self.interval = 0
		self.nextevent = threading.Event()
		self.stopevent = threading.Event()
		self.mainlock = threading.RLock()

		node.Node.__init__(self, nodeid, managerlocation)

		self.addEventInput(event.StartEvent, self._handle_start)
		self.addEventInput(event.StopEvent, self._handle_stop)
		self.addEventInput(event.NumericControlEvent, self._handle_intervalchange)

		self.interact()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

	def main(self):
		"""
		this is the main loop, of which there can only
		be one in this node
		"""
		### main can only be run once
		if not self.mainlock.acquire(blocking=0):
			return

		self.stopevent.clear()
		while 1:
			## check for a stop event
			if self.stopevent.isSet():
				break

			## set a timer for the next action
			self.nextevent.clear()
			threading.Timer(self.interval,self._nexttimer).start()

			## this acuqire
			self.action()

			## wait for the duration of the interval timer
			## or maybe if action() took too long, the
			## timer already expired and this returns instantly
			self.nextevent.wait()

		self.mainlock.release()

	def _nexttimer(self):
		"called by a threading.Timer to initiate the next action"
		self.nextevent.set()

	def _handle_start(self, startevent):
		"""
		start a new main thread after receiving StartEvent
		"""
		print 'got start event %s' % startevent
		t = threading.Thread(name='self.main thread', target=self.main)
		t.setDaemon(1)
		t.start()

	def _handle_stop(self, stopevent):
		"""
		stop the main thread after receiving StopEvent
		"""
		print 'got stop event %s' % stopevent
		self.stopevent.set()

	def _handle_intervalchange(self, numcontrolevent):
		"""
		modify the loop interval after receiving NumericControlEvent
		"""
		print 'got control event %s' % numcontrolevent
		new_interval = numcontrolevent.content
		self._change_interval(new_interval)

	def _change_interval(self, new_interval):
		self.interval = new_interval

	def action(self):
		"""
		this is the real guts of this node and must be 
		defined in subclass
		"""
		raise NotImplementedError()


### an example of subclassing TimedLoop
import Numeric
import data

class TestLoop(timedloop.TimedLoop):
	"""
	Event Inputs:
		StartEvent - starts the acquisition loop
		StopEvent - stops the acquisition loop
		NumericControlEvent - modifies the loop interval
	"""
	def __init__(self, id, managerlocation=None):
		timedloop.TimedLoop.__init__(self, id, managerlocation)
		print 'TestLoop %s started' % (self.id,)

	def action(self):
		"""
		this is the real guts of this node
		"""
		size = 5
		a = Numeric.arrayrange(size * size)
		a = Numeric.reshape(a, (size,size)) 
		adata = data.NumericData(self.ID(), a)
		print 'publishing', adata
		self.publish(adata, event.PublishEvent)

	def defineUserInterface(self):
		timedloop.TimedLoop.defineUserInterface(self)

		self.registerUIFunction(self.myStart, (), alias='Start')
		self.registerUIFunction(self.myStop, (), alias='Stop')
		argspec = (
			{'name':'new_interval','alias':'Interval','type':'integer'},
			)
		self.registerUIFunction(self.myChange, argspec, alias='Change')

	def myStart(self):
		'start with a dummy start event'
		self._handle_start(None)
		return ''

	def myStop(self):
		'stop with a dummy stop event'
		self._handle_stop(None)
		return ''

	def myChange(self, new_interval):
		self._change_interval(new_interval)
		return ''
		


if __name__ == '__main__':
	from Tkinter import *
	import nodegui

	id = ('testloop',)
	t = TestLoop(id)

	tk = Tk()
	gui = nodegui.NodeGUI(tk, node=t)
	gui.pack()
	tk.mainloop()
