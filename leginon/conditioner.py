from leginon import event
import sys
import threading
import leginon.node as node
import leginon.gui.wx.Conditioner
import leginon.gui.wx.AutoFiller
from leginon import leginondata
from leginon import instrument
from leginon import player
import time
import itertools

PAUSE_AND_INFORM_ERROR = True

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
	eventoutputs = [event.IdleTimerPauseEvent, event.IdleTimerRestartEvent]

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
			evt1 = event.IdleTimerPauseEvent()
			self.outputEvent(evt1, wait=False)
			self._handleFixConditionEvent(evt)
			status = 'ok'
		except RuntimeError, e:
			self.logger.error('Operation error: e')
			self.pauseAndInformUser(e.args[0])
		except Exception, e:
			self.logger.info('handling exception %s' %(e.args[0]))
			status='exception'
		try:
			evt2 = event.IdleTimerRestartEvent()
			self.outputEvent(evt2, wait=False)
		except Exception, e:
			self.logger.warning('handling exception for restarting idle timer %s' %(e.args[0]))
		self.confirmEvent(evt, status=status)
		self.setStatus('idle')
		self.player.stop()

	def pauseAndInformUser(self,msg):
		if not PAUSE_AND_INFORM_ERROR:
			return
		self.player.pause()
		self.instrument.tem.ColumnValvePosition = 'closed'
		self.logger.info('Column valve closed')
		self.setStatus('user input')
		try:
			self.slackNotification(msg)
		except:
			pass
		state = self.player.wait()

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
		if self.isAboveTripValue():
			self.setStatus('processing')
			self._fixCondition(condition_type)
			self.logger.info('done %s' % (condition_type))
		else:
			self.logger.info('no need to do anything')
		self.setStatus('idle')
		self.player.stop()

	def isAboveTripValue(self):
		'''
		only fix condition if above a defined monitored value
		'''
		return True

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
		evt = event.IdleTimerRestartEvent()
		self.outputEvent(evt, wait=False)
		self.player.stop()
		self.setStatus('idle')

class AutoNitrogenFiller(Conditioner):
	panelclass = leginon.gui.wx.AutoFiller.Panel
	settingsclass = leginondata.AutoFillerSettingsData
	defaultsettings = {}
	defaultsettings = dict(Conditioner.defaultsettings)
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
		self.refillRefrigerant()
		self.setStatus('idle')
		self.player.stop()

	def isAboveTripValue(self):
		# calling monitorRefillWithIsBusy first to make sure it is not already refilling
		if not self.hasAutoFiller():
			self.logger.warning('No autofiller on this tem')
			return False
		self.monitorRefillWithIsBusy()
		return self.isRefillNeeded()

	def isRefillNeeded(self):
		'''
		Check refrigerant levels and refill if necessary
		'''
		loader_level,column_level = self.getRefrigerantLevels()
		self.loader_level_before = loader_level
		self.column_level_before = column_level
		check_loader = self.settings['autofiller mode'] in ['both cold','column RT, loader cold']
		check_column = self.settings['autofiller mode'] in ['both cold','column cold, loader RT']
		force_fill = False
		if check_column and column_level <= self.settings['column fill start']:
			self.logger.info('Runing autofiller for column')
			force_fill = True
		elif check_loader and loader_level <= self.settings['loader fill start']:
			self.logger.info('Runing autofiller for loader')
			force_fill = True
		self.logger.debug('force_fill_state is %s' % (force_fill,))
		return force_fill

	def hasAutoFiller(self):
		try:
			has_auto_filler = self.instrument.tem.hasAutoFiller()
		except:
			has_auto_filler = False
		return has_auto_filler

	def refillRefrigerant(self):
		# Do refill and dark current reference update at the same time.
		self.logger.info('Start refilling autofiller thread')
		time.sleep(0.1)
		t1 = threading.Thread(target=self.runNitrogenFiller)
		t1.start()
		# Dark Current Reference Update if needed
		self.runCameraDarkCurrentReferenceUpdate()
		t1.join()

		filler_status = self.monitorRefillWithIsBusy()

	def slackNotification(self, msg):
		try:
			from slack import slack_interface
			# getTEMData here will just get the first tem in instrument.cfg on
			# scope. It gives EF-Krios if both EF-Krios and Krios are in
			# the config.
			temdata = self.instrument.getTEMData()
			temname = temdata['hostname']
			if 'description' in temdata.keys() and temdata['description']:
				temname = temdata['description']
			slack_inst = slack_interface.SlackInterface()
			channel = slack_inst.getDefaultChannel()
			slack_inst.sendMessage(channel,'%s:%s error:%s ' % (temname,self.name,msg))
		except:
			pass

	def runNitrogenFiller(self):
		try:
			self.instrument.tem.runAutoFiller()
		except RuntimeError as e:
			if self.isRealFillerError():
				message = e.args[0]
				self.logger.error('Operation error: %s' % (message,))
				self.logger.error('Can not recover. Check filler and tank')
				self.pauseAndInformUser(e.args[0])

	def isRealFillerError(self):
		'''
		AutoFiller denies filling if too full with error raised, too.
		It does not require pausing and notification.
		'''
		loader_level,column_level = self.getRefrigerantLevels()
		if loader_level >= self.settings['loader fill end'] and column_level >= self.settings['column fill end']:
			return False
		return True

	def runCameraDarkCurrentReferenceUpdate(self):
		camnames = self.instrument.getCCDCameraNames()
		need_update = False
		for name in camnames:
			self.logger.debug('set camera to %s to check dark current reference requirement' % name)
			self.instrument.setCCDCamera(name)
			if self.requireRecentDarkCurrentReferenceOnBright():
				need_update = True
				self.logger.info('%s requires dark current reference. Processing...' % name)
				break
		if need_update:
			self.updateCameraDarkCurrentReference()
		
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

	def getRefrigerantLevels(self):
		loader_level = self.instrument.tem.getRefrigerantLevel(0)
		column_level = self.instrument.tem.getRefrigerantLevel(1)
		return loader_level,column_level
