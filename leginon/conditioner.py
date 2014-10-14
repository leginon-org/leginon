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
	This fixes one or more instrument condition
	by triggering a condition fixing function after a timeout 
	before target list processing of a TargetWatcher that requests the fix.
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
		'''
		Define a unique condition type (CType) for database record.
		Required definition in the subclass
		'''
		#self.addCType('your_type_name')
		raise NotImplementedError()

	def addCType(self,ctypename):
		'''
		Add a ctype to the class list
		'''
		self.ctypes.append(ctypename)

	def makeConditioningRequests(self):
		'''
		Reset condition fixing request timeout
		'''
		if not self.settings['bypass']:
			for ctype in self.ctypes:
				self.saveConditioningRequest(ctype)

	def saveConditioningRequest(self, ctype):
		'''
		Save timestamped conditioning request to database
		'''
		crequestdata = leginondata.ConditioningRequestData(session=self.session, type=ctype)
		crequestdata.insert()

	def queryConditionRequests(self):
		'''
		Get the most recent conditioning request from all ctypes
		'''
		self.requests = {}
		for ctype in self.ctypes:
			crequestquery = leginondata.ConditioningRequestData(session=self.session, type=ctype)
			crequests = crequestquery.query(results=1)
			if crequests:
				self.requests[ctype] = crequests[0]

	def queryConditioningDone(self, crequest):
		'''
		Get the most recent conditioning request that fixing was completed, i.e., not bypassed.
		'''
		cdonequery = leginondata.ConditioningDoneData(session=self.session, request=crequest)
		done_conditions = cdonequery.query(results=1)
		if done_conditions:
			return done_conditions[0]
		else:
			return None

	def saveConditioningDone(self, crequestdata):
		'''
		Record that a condition is fixed.
		'''
		conditiondonedata = leginondata.ConditioningDoneData(session=self.session, request=crequestdata)
		conditiondonedata.insert(force=True)

	def handleFixConditionEvent(self, evt):
		'''
		Handle FixConditionEvent with bypass option and exceptions.
		'''
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
			self.logger.warning('handling exception %s' %(e,))
			self.confirmEvent(evt, status='exception')
		self.setStatus('idle')

	def _handleFixConditionEvent(self, evt):
		'''
		Internal function to handl FixConditionEvent. Only fix condition
		if "repeat time" settings has passed since last done.
		'''
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

	def onPlayer(self, state):
		'''
		Print in logger the current status of the player buttons
		'''
		infostr = ''
		if state == 'pause':
			infostr += 'Pausing...'
		elif state == 'stop':
			infostr += 'Continue'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)

	def fixCondition(self, condition_type):
		'''
		Handle fix condition request on a given condition type
		'''
		self.logger.info('handle fix condition request')
		self._fixCondition(condition_type)
		self.logger.info('done %s' % (condition_type))

	def _fixCondition(self, condition_type):
		'''
		Define what to do in the subclass to fix the condition of a given type
		'''
		self.logger.info('Base Class not really doing anything')
	
	def onTest(self):
		'''
		Run fixCondition once as a test
		'''
		for ctype in self.ctypes:
			self.testprint('ctype %s' % ctype)
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


	def getFillerModes(self):
		return ['both cold','column cold, loader RT','column RT, loader cold','both RT']

	def setCTypes(self):
		self.addCType('autofiller')

	def _fixCondition(self, condition_type):
		self.setStatus('processing')
		self.logger.info('handle fix condition request')
		self.monitorRefillWithIsBusy()
		refilled = self.refillRefrigerantLevel()
		if refilled:
			self.logger.info('done %s' % (condition_type))
		else:
			self.logger.info('no need to do anything')
		self.setStatus('idle')
		self.player.stop()

	def refillRefrigerantLevel(self):
		loader_level,column_level = self.getRefrigerantLevels()
		check_loader = self.settings['autofiller mode'] in ['both cold','column RT, loader cold']
		check_column = self.settings['autofiller mode'] in ['both cold','column cold, loader RT']
		force_fill = False
		if check_column and column_level <= self.settings['column fill start']:
			self.logger.info('Runing autofiller for column')
			self.instrument.tem.runAutoFiller()
			force_fill = True
		elif check_loader and loader_level <= self.settings['loader fill start']:
			self.logger.info('Runing autofiller for loader')
			self.instrument.tem.runAutoFiller()
			force_fill = True
		if force_fill:
			filler_status = self.monitorRefillWithIsBusy()
			if filler_status is None:
				self.monitorRefill(check_column,check_loader)
			return True
		return False

	def monitorRefillWithIsBusy(self):
		'''
		Wait until autofiller not busy if can be monitored by function in tem.
		If the function is not available returns None immediately.
		returned status is either False (finished refill or not busy)
		or None (not available)
		'''
		try:
			isbusy = self.instrument.tem.isAutoFillerBusy()
		except AttributeError:
			return None

		# handle script not available
		if isbusy is None:
			return isbusy

		if isbusy is True:
			self.logger.info('filling')
		else:
			self.logger.info('filler is idle')
		while isbusy is True:
			isbusy = self.instrument.tem.isAutoFillerBusy()
			time.sleep(10)
		return isbusy

	def monitorRefill(self,check_column,check_loader):
		sleeptime = 3
		significance = 0.1
		column_filled = False
		loader_filled = False
		if check_column:
			column_filled = self.monitorColumnRefill(sleeptime,significance)

		if check_loader:
			loader_filled = self.monitorGridLoaderRefill(sleeptime,significance)

			# report final values
			loader_level,column_level = self.getRefrigerantLevels()
			self.logger.info('Column N2 at %.1f %%' % (column_level,))
			self.logger.info('Grid autoloader at %.1f %%' % (loader_level,))

			# OK if autoloader not filled when 'both cold' mode is used
			if self.settings['autofiller mode'] == 'both cold' and column_filled and not loader_filled:
				self.logger.warning('Grid autoloader not full but column o.k. to continue')
				return
		self.testprint('loader_filled=%s, column_filled=%s, filler_mode=%s' % (loader_filled, column_filled, self.settings['autofiller mode']))
		# Handle autoloader malfunctioning
		if check_loader and not loader_filled:
			self.logger.error('Autoloader not filled, paused.')
			self.player.pause()
			self.setStatus('user input')
			state = self.player.wait()

		# Handle autoloader malfunctioning
		if check_column and not column_filled:
			self.logger.error('Column not filled, paused.')
			self.player.pause()
			self.setStatus('user input')
			state = self.player.wait()
		else:
			# Successful refill
			return

	def monitorColumnRefill(self,sleeptime=3,significance=0.1):
		column_filled = False
		old_column_level = -20
		new_column_level = self.instrument.tem.getRefrigerantLevel(1)
		self.logger.info('col N2 refill initial at %.1f %%' % (new_column_level))
		time.sleep(sleeptime)
		while new_column_level - old_column_level > significance:
			# Filling in progress
			old_column_level = new_column_level
			new_column_level = self.instrument.tem.getRefrigerantLevel(1)
			self.logger.debug('Refilling column N2 level at %.1f %%' % (new_column_level,))
			if new_column_level >= self.settings['column fill end']:
				self.logger.info('Stop refilling column at %.1f %%' % (new_column_level,))
				column_filled = True
				break
			time.sleep(sleeptime)
		return column_filled

	def monitorGridLoaderRefill(self,sleeptime=3,significance=0.1):
		loader_filled = False
		old_loader_level = -20
		new_loader_level = self.instrument.tem.getRefrigerantLevel(0)
		# Since this is normally reached after column filling, loader level may have changed
		if new_loader_level >= self.settings['loader fill end']:
			self.logger.debug('Grid autoloader is already full after column refill')
			loader_filled = True
		else:
			self.logger.debug('Filling grid autoloader at %.1f %%' % (new_loader_level))
			time.sleep(sleeptime)
			while new_loader_level - old_loader_level > significance:
				# Filling in progress
				old_loader_level = new_loader_level
				new_loader_level = self.instrument.tem.getRefrigerantLevel(0)
				if new_loader_level >= self.settings['loader fill end']:
					self.logger.debug('Stop refilling loader at %.1f %%' % (new_loader_level,))
					loader_filled = True
					break
				else:
					self.logger.debug('Wait for refilling loader at %.1f %%' % (new_loader_level,))
				time.sleep(sleeptime)
		return loader_filled

	def getRefrigerantLevels(self):
		loader_level = self.instrument.tem.getRefrigerantLevel(0)
		column_level = self.instrument.tem.getRefrigerantLevel(1)
		return loader_level,column_level
