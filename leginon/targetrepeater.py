#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import threading
import node
import gui.wx.TargetRepeater

class TargetRepeater(node.Node):
	panelclass = gui.wx.TargetRepeater.Panel
	settingsclass = leginondata.TargetRepeaterSettingsData
	defaultsettings = {
		'bypass':True,
	}

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.userpause = threading.Event()
		targethandler.TargetWaitHandler.__init__(self)

		self.addEventInput(event.ImageTargetListPublishEvent, self.handleTargetListPublish)
		# not yet...
		#self.addEventInput(event.QueuePublishEvent, self.handleQueuePublish)

		self.test = False
		self.abort = False
		if self.__class__ == TargetRepeater:
			self.start()

	def handleTargetListPublish(self, pubevent):
		targetlistdata = pubevent['data']

		if self.settings['bypass']:
			tid = self.makeTargetListEvent(newtargetlistdata)
			self.publish(targetlistdata, pubevent=True)
			self.setStatus('idle')
			status = self.waitForTargetListDone(tid)
		else:
			self.repeatTargetList(targetlistdata)
			status = 'ok'

		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dmid, status=status)
		self.outputEvent(e)

	def makeStates(self):
		pass

	def repeatTargetList(self, targetlistdata):
		states = self.makeStates()
		for scopedata in states:
			self.instrument.setData(scopedata)
			# declare transform:


			newtargetlistdata = copyTargetList(targetlistdata)

			tid = self.makeTargetListEvent(newtargetlistdata)
			self.publish(newtargetlistdata, pubevent=pubevent)
			self.setStatus('idle')
			status = self.waitForTargetListDone(tid)

	def copyTargetList(self, targetlistdata):
			alltargets = self.researchTargets(list=targetlistdata)

			newtargetlistdata = self.newTargetList()
			newtargetlistdata.update(targetlistdata)
			self.publish(newtargetlistdata, database=True, dbforce=True)

			for target in alltargets:
				if target['status'] not in ('done', 'aborted'):
					newtarget = leginondata.AcqusitionImageTargetData(initializer=target)	
					newtarget['fromtarget'] = target
					newtarget['list'] = newtargetlist

			return newtargetlistdata

