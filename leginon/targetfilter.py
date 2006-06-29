#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

'''
The TargetFilter node takes a list of targets and produces a new list of targets.
It would typically be placed between a TargetFinder and an Acquisition node.
Subclasses need to implement the filterTargets method.
'''

import node
import data
import event
import targethandler
import gui.wx.TargetFilter

class TargetFilter(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetFilter.Panel
	settingsclass = data.TargetFilterSettingsData
	defaultsettings = {'bypass':True}
	eventinputs = node.Node.eventinputs + targethandler.TargetWaitHandler.eventinputs + [event.ImageTargetListPublishEvent]
	eventoutputs = node.Node.eventoutputs + targethandler.TargetWaitHandler.eventoutputs + [event.TargetListDoneEvent]
										
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		targethandler.TargetWaitHandler.__init__(self)

		self.addEventInput(event.ImageTargetListPublishEvent, self.handleTargetListPublish)
		self.addEventInput(event.QueuePublishEvent, self.handleQueuePublish)

		self.start()

	def handleTargetListPublish(self, pubevent):
		targetlistdata = pubevent['data']
		newtargetlistdata = self.__filterTargetList(targetlistdata)
		tid = self.makeTargetListEvent(newtargetlistdata)
		self.publish(newtargetlistdata, pubevent=pubevent)
		status = self.waitForTargetListDone(tid)
		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dmid, status=status)
		self.outputEvent(e)

	def handleQueuePublish(self, pubevent):
		'''
		filter just passes input queuedata to the output, but the target lists
		in that queue are filtered.  The old target list is dequeued.
		'''
		queuedata = pubevent['data']
		## this is only active (not dequeued) target lists
		oldtargetlists = self.getListsInQueue(queuedata)

		for oldtargetlist in oldtargetlists:
				newtargetlist = self.__filterTargetList(oldtargetlist)
				if newtargetlist is not oldtargetlist:
					# newtargetlist has already been put in queue, now dequeue old one
					donetargetlist = data.DequeuedImageTargetListData(list=oldtargetlist,queue=queuedata)
					self.publish(donetargetlist, database=True)
		self.publish(queuedata, pubevent=True)

	def __filterTargetList(self, targetlistdata):
		'''
		- create a new ImageTargetListData for the new targets
		- run the custom filter method on targets in this list
		- publish each target
		- return new target list data
		'''
		if self.settings['bypass']:
			self.logger.info('Bypassing target filter')
			return targetlistdata
		else:
			oldtargets = self.researchTargets(list=targetlistdata)
			self.logger.info('Filter input: %d' % (len(oldtargets),))
			newtargets = self.filterTargets(oldtargets)
			self.logger.info('Filter output: %d' % (len(newtargets),))
			newtargetlistdata = targethandler.newTargetList()
			newtargetlistdata.update(targetlistdata)
			self.publish(newtargetlistdata, database=True, dbforce=True)
			for newtarget in newtargets:
				newtarget['list'] = newtargetlistdata
				self.publish(newtarget, database=True)
			return newtargetlistdata

	def filterTargets(self, targetlist):
		raise NotImplementedError()
