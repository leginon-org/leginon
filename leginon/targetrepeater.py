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
import targethandler
import gui.wx.TargetRepeater
import instrument

class TargetRepeater(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetRepeater.Panel
	settingsclass = leginondata.TargetRepeaterSettingsData
	defaultsettings = {
		'bypass':True,
	}
	eventinputs = node.Node.eventinputs + targethandler.TargetWaitHandler.eventinputs + [event.ImageTargetListPublishEvent]
	eventoutputs = node.Node.eventoutputs + targethandler.TargetWaitHandler.eventoutputs + [event.TargetListDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.userpause = threading.Event()
		targethandler.TargetWaitHandler.__init__(self)
		self.instrument = instrument.Proxy(self.objectservice, self.session)

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
			tid = self.makeTargetListEvent(targetlistdata)
			self.publish(targetlistdata, pubevent=True)
			self.setStatus('idle')
			status = self.waitForTargetListDone(tid)
		else:
			self.repeatTargetList(targetlistdata)
			status = 'ok'

		self.markAllTargetsDone(targetlistdata)

		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dmid, status=status)
		self.outputEvent(e)

	def makeStates(self):
		pass

	def repeatTargetList(self, targetlistdata):
		states = self.makeStates()
		for scopedata in states:
			self.instrument.setData(scopedata)
			# declare transform:

			newtargetlistdata = self.copyTargetList(targetlistdata)
			if newtargetlistdata is None:
				break

			tid = self.makeTargetListEvent(newtargetlistdata)
			self.publish(newtargetlistdata, pubevent=True)
			self.setStatus('idle')
			status = self.waitForTargetListDone(tid)

	def markAllTargetsDone(self, targetlistdata):
			alltargets = self.researchTargets(list=targetlistdata)
			donetargets = []
			for target in alltargets:
				if target['status'] not in ('done', 'aborted'):
					donetargets.append(target)
			self.markTargetsDone(donetargets)

	def copyTargetList(self, targetlistdata):
			alltargets = self.researchTargets(list=targetlistdata)
			print 'ORIGINAL', len(alltargets)
			for t in alltargets:
				print '  ', t['number'], t['status']

			newtargetlistdata = self.newTargetList()
			newtargetlistdata.update(targetlistdata)
			self.publish(newtargetlistdata, database=True, dbforce=True)

			newtargets = []
			for target in alltargets:
				if target['status'] not in ('done', 'aborted'):
					newtarget = leginondata.AcquisitionImageTargetData(initializer=target)	
					newtarget['fromtarget'] = target
					newtarget['list'] = newtargetlistdata
					newtarget.insert(force=True)
					newtargets.append(newtarget)
			
			if newtargets:
				return newtargetlistdata
			else:
				return None

