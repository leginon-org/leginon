from leginon import event
import threading
import leginon.node as node
import leginon.gui.wx.Conditioner
from leginon import leginondata
from leginon import instrument
import time

class Conditioner(node.Node):
	'''
	This fixes scope conditions such as vacuum and autofiller status
	by triggering the respective pump after a timeout before target list processing
	of a TargetWatcher that requests the fix.
	'''
	panelclass = leginon.gui.wx.Conditioner.Panel
	settingsclass = leginondata.ConditionerSettingsData
	defaultsettings = {}
	defaultsettings.update({
		'bypass':True,
		'repeat time': 0,
	})
	eventinputs = node.Node.eventinputs + [event.FixConditionEvent]

	def __init__(self, *args, **kwargs):
		node.Node.__init__(self, *args, **kwargs)
		self.addEventInput(event.FixConditionEvent, self.handleFixConditionEvent)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.conditionlist = []
		self.valid_ctypes = ['buffer cycle']
		# TO DO: choose ctypes used in the node. Set to all for now
		self.ctypes = self.valid_ctypes
		self.makeConditioningRequests()
		self.start()

	def makeConditioningRequests(self):
		if not self.settings['bypass']:
			for ctype in self.ctypes:
				self.saveConditioningRequest(ctype)

	def saveConditioningRequest(self, ctype):
			crequestdata = leginondata.ConditioningRequestData(session=self.session, type=ctype)
			crequestdata.insert()

	def queryConditionRequests(self):
		self.requests = {}
		for ctype in self.ctypes:
			crequestquery = leginondata.ConditioningRequestData(session=self.session, type=ctype)
			crequests = crequestquery.query(results=1)
			if crequests:
				self.requests[ctype] = crequests[0]

	def queryConditioningDone(self, crequest):
		cdonequery = leginondata.ConditioningDoneData(session=self.session, request=crequest)
		done_conditions = cdonequery.query(results=1)
		if done_conditions:
			return done_conditions[0]
		else:
			return None

	def saveConditioningDone(self, crequestdata):
		conditiondonedata = leginondata.ConditioningDoneData(session=self.session, request=crequestdata)
		conditiondonedata.insert(force=True)

	def handleFixConditionEvent(self, evt):
		self.setStatus('processing')
		if self.settings['bypass']:
			self.logger.info('bypass condition fixing')
			self.confirmEvent(evt, status='bypass')
			self.setStatus('idle')
			return
		try:
			self._handleFixConditionEvent(evt)
		except Exception, e:
			self.logger.error('handling exception %s' %(e,))
			self.confirmEvent(evt, status='exception')
		else:
			self.confirmEvent(evt, status='ok')
		self.setStatus('idle')

	def _handleFixConditionEvent(self, evt):
		self.queryConditionRequests()
		for ctype in self.requests:
			crequest = self.requests[ctype]
			conditiondone = self.queryConditioningDone(crequest)
			if conditiondone is not None:
				donetime = conditiondone.timestamp
				diff = donetime.now() - donetime
				if diff.seconds < self.settings['repeat time']:
					self.logger.info('bypass %s: only %d seconds since last' % (ctype,diff.seconds))
					continue

			self.fixCondition(ctype)
			self.saveConditioningDone(crequest)

	def fixCondition(self, condition_type):
		self.logger.info('handle fix condition request')
		self.runBufferCycle()
		self.logger.info('done %s' % (condition_type))

	def runBufferCycle(self):
		try:
			self.logger.info('Running buffer cycle...')
			self.instrument.tem.runBufferCycle()
		except AttributeError:
			self.logger.warning('No buffer cycle for this instrument')
		except Exception, e:
			self.logger.error('Run buffer cycle failed: %s' % e)

	def onTest(self):
		for ctype in self.ctypes:
			self.fixCondition(ctype)
