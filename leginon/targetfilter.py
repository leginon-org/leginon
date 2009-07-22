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
import leginondata
import event
import threading
import targethandler
import gui.wx.TargetFilter

class TargetFilter(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetFilter.Panel
	settingsclass = leginondata.TargetFilterSettingsData
	defaultsettings = {
		'bypass':True,
		'target type':'acquisition',	
		'user check': False,
	}
	eventinputs = node.Node.eventinputs + targethandler.TargetWaitHandler.eventinputs + [event.ImageTargetListPublishEvent]
	eventoutputs = node.Node.eventoutputs + targethandler.TargetWaitHandler.eventoutputs + [event.TargetListDoneEvent]
										
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
		newtargetlistdata = self.__filterTargetList(targetlistdata,self.settings['target type'])
		tid = self.makeTargetListEvent(newtargetlistdata)
		self.publish(newtargetlistdata, pubevent=pubevent)
		self.setStatus('idle')
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
				newtargetlist = self.__filterTargetList(oldtargetlist,self.settings['target type'])
				if newtargetlist is not oldtargetlist:
					# newtargetlist has already been put in queue, now dequeue old one
					donetargetlist = leginondata.DequeuedImageTargetListData(list=oldtargetlist,queue=queuedata)
					self.publish(donetargetlist, database=True)
		self.publish(queuedata, pubevent=True)
		self.setStatus('idle')

	def __filterTargetList(self, targetlistdata,type='acquisition'):
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
			oldtargets = self.researchTargets(list=targetlistdata,type=type)
			alltargets = self.researchTargets(list=targetlistdata)
			self.alltargets = alltargets
			goodoldtargets = []
			for oldtarget in oldtargets:
				if oldtarget['status'] not in ('done', 'aborted'):
					goodoldtargets.append(oldtarget)
			self.goodoldtargets = goodoldtargets
			self.logger.info('Filter input: %d' % (len(goodoldtargets),))
			self.test = False
			if len(goodoldtargets) > 0:
				newtargets = self.filterTargets(goodoldtargets)
			else:
				newtargets = goodoldtargets
			self.logger.info('Filter output: %d' % (len(newtargets),))
			newtargets = self.appendOtherTargets(alltargets,newtargets)
			self.displayTargets(newtargets,targetlistdata)
			if self.settings['user check'] and len(goodoldtargets) > 0:
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

	def appendOtherTargets(self,alltargets,newtargets):
		filteredtype = self.settings['target type']
		for target in alltargets:
			if target['type'] != filteredtype and target['status'] not in ('done','aborted'):
				newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
				newtarget['delta row'] = target['delta row']
				newtarget['delta column'] = target['delta column']
				newtargets.append(newtarget)
		return newtargets
		
	def displayTargets(self,targets,oldtargetlistdata):
		done = []
		acq = []
		foc = []
		preview = []
		if oldtargetlistdata['image'] is not None:
			halfrows = oldtargetlistdata['image']['camera']['dimension']['y'] / 2
			halfcols = oldtargetlistdata['image']['camera']['dimension']['x'] / 2
			image = oldtargetlistdata['image']['image']
		elif len(targets) > 0:
			halfrows = targets[0]['image']['camera']['dimension']['y'] / 2
			halfcols = targets[0]['image']['camera']['dimension']['x'] / 2
			image = targets[0]['image']['image']
		else:
			return
		self.setImage(image, 'Image')
		for target in targets:
			drow = target['delta row']
			dcol = target['delta column']
			x = dcol + halfcols
			y = drow + halfrows
			disptarget = x,y
			if target['status'] in ('done', 'aborted'):
				done.append(disptarget)
			elif target['type'] == 'acquisition':
				acq.append(disptarget)
			elif target['type'] == 'preview':
				preview.append(disptarget)
			elif target['type'] == 'focus':
				foc.append(disptarget)
		self.setTargets(acq, 'acquisition', block=True)
		self.setTargets(foc, 'focus', block=True)
		self.setTargets(preview, 'preview', block=True)

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

	def filterTargets(self, targetlist):
		raise NotImplementedError()

	def onTest(self):
		self.test = True
		goodoldtargets = self.goodoldtargets
		self.logger.info('Filter input: %d' % (len(goodoldtargets),))
		newtargets = self.filterTargets(goodoldtargets)
		self.logger.info('Filter output: %d' % (len(newtargets),))
		self.displayTargets(newtargets,{'image':None})
		return newtargets
