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
import player

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
		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
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
			self.player.pause()
			self.repeatTargetList(targetlistdata)
			status = 'ok'

		self.markAllTargetsDone(targetlistdata)

		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dmid, status=status)
		self.outputEvent(e)
		self.logger.info('All targets and states done')

	def makeStates(self):
		pass

	def onContinue(self):
		self.player.play()
		self.userpause.set()

	def repeatTargetList(self, targetlistdata):
		states = self.makeStates()
		print 'repeating target at %d states' % (len(states),)
		for scopedata in states:
			self.setStatus('idle')
			self.setStatus('user input')
			self.logger.info('Continue to next state? waiting for user...')
			self.userpause.clear()
			self.player.pause()
			self.userpause.wait()
			self.player.play()
			self.setStatus('processing')

			self.instrument.setData(scopedata)

			newtargetlistdata = self.copyTargetList(targetlistdata)
			if newtargetlistdata is None:
				break

			# declare transform:
			self.declareTransform(self.transformtype)

			tid = self.makeTargetListEvent(newtargetlistdata)
			self.publish(newtargetlistdata, pubevent=True)
			status = self.waitForTargetListDone(tid)
			state = self.player.wait()
			if state in ('stop'):
				self.logger.info('Aborting')
				break
		self.setStatus('idle')

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

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += ''
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)
