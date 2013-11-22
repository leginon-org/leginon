from leginon import event
import threading
import leginon.node as node
import leginon.gui.wx.Conditioner
import leginon.gui.wx.AutoFiller
from leginon import leginondata
from leginon import instrument
from leginon import player
import time
import itertools

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
		# TO DO: choose ctypes used in the node. Set to all for now
		self.ctypes = []
		self.setCTypes()
		self.makeConditioningRequests()
		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.start()

	def setCTypes(self):
		self.addCType('buffer_cycle')

	def addCType(self,ctypename):
		self.ctypes.append(ctypename)

	def makeConditioningRequests(self):
		print self.ctypes
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
		self.logger.info('handle condition fixing')
		self.setStatus('processing')
		if self.settings['bypass']:
			self.logger.info('bypass condition fixing')
			self.confirmEvent(evt, status='bypass')
			self.setStatus('idle')
			return
		self.player.play()
		try:
			self._handleFixConditionEvent(evt)
			self.confirmEvent(evt, status='ok')
		except Exception, e:
			self.logger.error('handling exception %s' %(e,))
			self.confirmEvent(evt, status='exception')
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

class AutoNitrogenFiller(Conditioner):
	panelclass = leginon.gui.wx.AutoFiller.Panel
	settingsclass = leginondata.AutoFillerSettingsData
	defaultsettings = {}
	defaultsettings = Conditioner.defaultsettings
	defaultsettings.update({
		'autofiller mode':'both cold',
		'column fill start': 15,
		'column fill end': 85,
		'loader fill start': 15,
		'loader fill end': 85,
	})
	eventinputs = node.Node.eventinputs + [event.FixConditionEvent]

	modes = ['both cold','column cold, loader RT','column RT, loader cold','both RT']

	def setCTypes(self):
		self.addCType('autofiller')

	def fixCondition(self, condition_type):
		self.setStatus('processing')
		self.logger.info('handle fix condition request')
		refilled = self.refillRefrigerantLevel()
		if refilled:
			self.logger.info('done %s' % (condition_type))
		else:
			self.logger.info('no need to refill')
		self.setStatus('idle')

	def refillRefrigerantLevel(self):
		loader_level,column_level = self.getRefrigerantLevel()
		check_loader = self.settings['autofiller mode'] in ['both cold','column RT, loader cold']
		check_column = self.settings['autofiller mode'] in ['both cold','column cold, loader RT']
		force_fill = False
		print 'col N2 level initial',column_level
		if check_column and column_level <= self.settings['column fill start']:
			self.instrument.tem.runAutoFiller()
			force_fill = True
		elif check_loader and loader_level <= self.settings['loader fill start']:
			self.instrument.tem.runAutoFiller()
			force_fill = True
		if force_fill:
			self.monitorRefill(check_column,check_loader,loader_level,column_level)
			return True
		return False

	def monitorRefill(self,check_column,check_loader,loader_level,column_level):
		old_loader_level = -20
		old_column_level = -20
		new_loader_level = loader_level
		new_column_level = column_level
		column_filled = False
		loader_filled = False
		sleeptime = 10
		significance = 0.1
		if check_column:
			print 'col N2 refill initial',new_column_level, old_column_level
			while new_column_level - old_column_level > significance:
				old_column_level = new_column_level
				# for simulation testing
				#new_column_level += 20
				new_column_level = self.instrument.tem.getRefrigerantLevel(1)
				print 'col N2 level after update',new_column_level, old_column_level
				if new_column_level >= self.settings['column fill end']:
					column_filled = True
					break
				time.sleep(sleeptime)
		print 'column_filled',column_filled
		if check_loader:
			while new_loader_level - old_loader_level > significance:
				old_loader_level = new_loader_level
				# for simulation testing
				#new_loader_level += 20
				new_loader_level = self.instrument.tem.getRefrigerantLevel(0)
				print 'loader N2 level',new_loader_level, old_loader_level
				if new_loader_level >= self.settings['loader fill end']:
					loader_filled = True
					break
				time.sleep(sleeptime)
			print 'loader status',loader_filled
			if self.settings['autofiller mode'] == 'both cold' and column_filled and not loader_filled:
				self.logger.warning('Autoloader not filled but column o.k. to continue')
				return

		if check_loader and not loader_filled:
			self.logger.error('Autoloader not filled, paused.')
			self.player.pause()
			self.setStatus('user input')
			state = self.player.wait()

		if check_column and not column_filled:
			self.logger.error('Column not filled, paused.')
			self.player.pause()
			self.setStatus('waiting')
		else:
			return

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += 'Testing...'
		elif state == 'pause':
			infostr += 'Pausing...'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)

	def getRefrigerantLevel(self):
		loader_level = self.instrument.tem.getRefrigerantLevel(0)
		column_level = self.instrument.tem.getRefrigerantLevel(1)
		return loader_level,column_level
