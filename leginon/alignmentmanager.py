from leginon import event
import threading
import leginon.targetrepeater as trepeater
import leginon.gui.wx.AlignmentManager
from leginon import leginondata

class AlignmentManager(trepeater.TargetRepeater):
	panelclass = leginon.gui.wx.AlignmentManager.Panel
	settingsclass = leginondata.AlignmentManagerSettingsData
	defaultsettings = trepeater.TargetRepeater.defaultsettings
	defaultsettings.update({
		'repeat time': 0,
	})
	eventinputs = trepeater.TargetRepeater.eventinputs + [event.FixAlignmentEvent]
	def __init__(self, *args, **kwargs):
		trepeater.TargetRepeater.__init__(self, *args, **kwargs)
		self.addEventInput(event.FixAlignmentEvent, self.handleFixAlignmentEvent)
		self.start()

	def handleTargetListPublish(self, pubevent):
		targetlistdata = pubevent['data']

		if self.settings['bypass']:
			tid = self.makeTargetListEvent(targetlistdata)
			self.publish(targetlistdata, pubevent=True)
			status = self.waitForTargetListDone(tid)
		else:
			status = 'ok'
			self.targetlist = targetlistdata

			## should be done by user button instead
			self.saveAlignmentTargetList('beam tilt')

		#self.markAllTargetsDone(targetlistdata)
		e = event.TargetListDoneEvent(targetlistid=targetlistdata.dbid, status=status)
		self.outputEvent(e)

	def saveAlignmentTargetList(self, label):
			aligntargetdata = leginondata.AlignmentTargetList(session=self.session, list=self.targetlist, label=label)
			aligntargetdata.insert(force=True)

	def queryAlignmentTargets(self):
		aligntargetquery = leginondata.AlignmentTargetList(session=self.session)
		alignment_targetlists = aligntargetquery.query()
		self.targetlists = {}
		for alignlist in alignment_targetlists:
			label = alignlist['label']
			## keep only most recent of that label
			if label in self.targetlists:
				continue
			targetlist = alignlist['list']
			self.targetlists[label] = {'time': alignlist.timestamp, 'list':alignlist}

	def queryAlignmentDone(self, alignlist):
		aligntargetquery = leginondata.AlignmentTargetListDone(session=self.session, alignlist=alignlist)
		done_alignments = aligntargetquery.query(results=1)
		if done_alignments:
			return done_alignments[0]
		else:
			return None

	def saveAlignmentDone(self, alignlist):
		aligndonedata = leginondata.AlignmentTargetListDone(session=self.session, alignlist=alignlist)
		aligndonedata.insert(force=True)

	def handleFixAlignmentEvent(self, evt):
		if self.settings['bypass']:
			self.logger.info('bypass alignment fixing')
			self.confirmEvent(evt, status='bypass')
			return
		try:
			self._handleFixAlignmentEvent(evt)
		except Exception, e:
			self.logger.error('handling exception %s' %(e,))
			self.confirmEvent(evt, status='exception')
		else:
			self.confirmEvent(evt, status='ok')

	def _handleFixAlignmentEvent(self, evt):
		self.queryAlignmentTargets()
		for label in self.targetlists:
			alignlist = self.targetlists[label]['list']
			aligndone = self.queryAlignmentDone(alignlist)
			if aligndone is not None:
				donetime = aligndone.timestamp
				diff = donetime.now() - donetime
				if diff.seconds < self.settings['repeat time']:
					self.logger.info('bypass alignment: only %d seconds since last' % diff.seconds)
					continue
			targetlistdata = alignlist['list']
			self.logger.info('handle fix alignment request')
			newtargetlistdata = self.copyTargetList(targetlistdata)
			if newtargetlistdata is None:
				self.logger.error('copy target list failed')
				break

			tid = self.makeTargetListEvent(newtargetlistdata)
			self.publish(newtargetlistdata, pubevent=True)
			self.declareDrift('stage')
			status = self.waitForTargetListDone(tid)
			self.declareDrift('stage')
			self.saveAlignmentDone(alignlist)

