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
import targetfilter

class TargetRepeater(targetfilter.TargetFilter):
	settingsclass = leginondata.TargetFilterSettingsData
	defaultsettings = {
		'bypass':True,
		'target type':'acquisition',	
		'user check': False,
	}
										
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.userpause = threading.Event()
		targethandler.TargetWaitHandler.__init__(self)

		self.addEventInput(event.ImageTargetListPublishEvent, self.handleTargetListPublish)
		self.addEventInput(event.QueuePublishEvent, self.handleQueuePublish)

		self.test = False
		self.abort = False
		if self.__class__ == TargetFilter:
			self.start()

	def handleTargetListPublish(self, pubevent):
		targetlistdata = pubevent['data']

		self.repeatTargetList(targetlistdata)

		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dmid, status=status)
		self.outputEvent(e)

	def repeatTargetList(self, targetlistdata):
		for scopedata in states:
			self.instrument.setData(scopedata)
			# declare transform:


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

	def __filterTargetList(self, targetlistdata):
		if self.settings['bypass']:
			self.logger.info('Bypassing target filter')
			return
		else:
			oldtargets = self.researchTargets(list=targetlistdata,type=type)
			alltargets = self.researchTargets(list=targetlistdata)
			self.alltargets = alltargets
			goodoldtargets = []
			for oldtarget in oldtargets:
				if oldtarget['status'] not in ('done', 'aborted'):
					goodoldtargets.append(oldtarget)
			self.goodoldtargets = goodoldtargets
			self.logger.info('Filter input: %d' % (len(goodoldtargets),))

			newtargets = self.filterTargets(goodoldtargets)

			self.logger.info('Filter output: %d' % (len(newtargets),))
			newtargets = self.appendOtherTargets(alltargets,newtargets)
			self.displayTargets(newtargets,targetlistdata)

			if self.settings['user check']:
				self.setStatus('user input')
				self.logger.info('Waiting for user to check targets...')
				self.panel.enableSubmitTargets()
				self.userpause.clear()
				self.userpause.wait()
				self.setStatus('processing')
				if self.abort:
					self.markTargetsDone(alltargets)
					self.abort = False
					return targetlistdata
				newtargets = self.onTest()
				newtargets = self.appendOtherTargets(alltargets,newtargets)
			self.newtargets = newtargets
			self.targetlistdata = targetlistdata
			newtargetlistdata = self.submitTargets()
			return newtargetlistdata

	def onSubmitTargets(self):
		self.userpause.set()

	def onAbortTargets(self):
		self.abort = True
		self.userpause.set()

	def submitTargets(self):
			targetlistdata = self.targetlistdata
			alltargets = self.alltargets
			newtargets = self.newtargets
			totaloldtargetcount = self.getAllTargetCount(alltargets)
			self.markTargetsDone(alltargets)
			self.logger.info('Original targets marked done.')
			newtargetlistdata = self.newTargetList()
			newtargetlistdata.update(targetlistdata)
			self.publish(newtargetlistdata, database=True, dbforce=True)
			for i, newtarget in enumerate(newtargets):
				newtarget['list'] = newtargetlistdata
				newtarget['number'] = i+1+totaloldtargetcount
				self.publish(newtarget, database=True, dbforce=True)
			return newtargetlistdata

	def getAllTargetCount(self,alltargetdata):
		parentimgs =[]
		totalcount = 0
		for target in alltargetdata:
			parentim = target.special_getitem('image',dereference=False)
			if parentim.dbid not in parentimgs:
				parentimgs.append(parentim.dbid)
				imagetargets = self.researchTargets(image=parentim)
				if imagetargets:
					totalcount = totalcount + len(imagetargets)
		return totalcount

	def onTest(self):
		goodoldtargets = self.goodoldtargets
		self.logger.info('Filter input: %d' % (len(goodoldtargets),))
		newtargets = self.filterTargets(goodoldtargets)
		self.logger.info('Filter output: %d' % (len(newtargets),))
		self.displayTargets(newtargets,{'image':None})
		return newtargets
