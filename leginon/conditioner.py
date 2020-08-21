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
import datetime

PAUSE_ON_ERROR = True
EARLY_WARNING_FOR_REFILL = False

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
	eventoutputs = []

	def __init__(self, *args, **kwargs):
		node.Node.__init__(self, *args, **kwargs)
		self.addEventInput(event.FixConditionEvent, self.handleFixConditionEvent)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.onInit()

	def onInit(self):
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
			status = 'ok'
		except RuntimeError, e:
			self.logger.error('Operation error: e')
			self.pauseOnError()
		except Exception, e:
			self.logger.info('handling exception %s' %(e.args[0]))
			status='exception'
		self.confirmEvent(evt, status=status)
		self.setStatus('idle')
		self.player.stop()

	def pauseOnError(self):
		if not PAUSE_ON_ERROR:
			return
		self.player.pause()
		self.instrument.tem.ColumnValvePosition = 'closed'
		self.logger.error('Paused workflow on real filler error')
		self.logger.info('Column valve closed')
		self.setStatus('user input')
		state = self.player.wait()
		self.instrument.tem.resetAutoFillerError()

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
			self._repeatCondition(condition_type)
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
	
	def _repeatCondition(self, condition_type):
		'''
		Define what to do in the subclass each time the node repeats the check
		but not needing to go through _fixCondition
		'''
		self.logger.info('no need to do anything')

	def onTest(self):
		'''
		Run fixCondition once as a test
		'''
		for ctype in self.ctypes:
			self.testprint('ctype %s' % ctype)
			self.fixCondition(ctype)
		self.player.stop()
		self.setStatus('idle')

class AutoNitrogenFiller(Conditioner):
	panelclass = leginon.gui.wx.AutoFiller.Panel
	settingsclass = leginondata.AutoFillerSettingsData
	defaultsettings = {}
	defaultsettings = dict(Conditioner.defaultsettings)
	defaultsettings.update({
		'autofiller mode':'both cold',
		'column fill start': 45,
		'column fill end': 70,
		'loader fill start': 17,
		'loader fill end': 70,
		'delay dark current ref': 120,
		'start dark current ref hr': 0,
		'end dark current ref hr': 24,
		'extra dark current ref': False,
		'dark current ref repeat time': 180, # seconds
	})
	eventinputs = node.Node.eventinputs + [event.FixConditionEvent]

	def onInit(self):
		super(AutoNitrogenFiller, self).onInit()
		# initialize these to 0 so that it does not trigger early warning.
		self.loader_level_before = 0
		self.column_level_before = 0
		self.last_dark_update = time.time()

	def getFillerModes(self):
		return ['both cold','column cold, loader RT','column RT, loader cold','both RT']

	def setCTypes(self):
		self.addCType('autofiller')

	def _fixCondition(self, condition_type):
		self.setStatus('processing')
		self.refillRefrigerant()
		self.setStatus('idle')
		self.player.stop()

	def _repeatCondition(self, condition_type):
		if not self.settings['extra dark current ref']:
			return super(AutoNitrogenFiller, self)._repeatCondition(condition_type)
		time_delta = int(time.time() - self.last_dark_update)
		if time_delta >= self.settings['dark current ref repeat time']:
			self.checkAndRunCameraDarkCurrentReferenceUpdate()
		else:
			self.logger.info('dark current ref not expired. %d seconds since last' % (time_delta))

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
		# catch only if the levels are going down
		loader_delta = max((self.loader_level_before - loader_level, 0))
		column_delta = max((self.column_level_before - column_level, 0))
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
		# Give a fake error for checking
		if not force_fill and EARLY_WARNING_FOR_REFILL:
			if (check_column and column_level <= self.settings['column fill start']+column_delta) or (check_loader and loader_level <= self.settings['loader fill start']+loader_delta):
				self.logger.error('DEBUG: Runing autofiller soon. Go and observe it')

		self.logger.info('force_fill_state is %s' % (force_fill,))
		return force_fill

	def hasAutoFiller(self):
		try:
			has_auto_filler = self.instrument.tem.hasAutoFiller()
		except:
			has_auto_filler = False
		return has_auto_filler

	def refillRefrigerant(self):
		isbusy = self.instrument.tem.isAutoFillerBusy()
		if isbusy:
			self.logger.error('Autofiller is busy despite previous check. Abort filling')
			return
		# Do refill and dark current reference update at the same time.
		self.logger.info('Start refilling autofiller thread')
		time.sleep(0.1)
		t1 = threading.Thread(target=self.runNitrogenFiller)
		t1.start()
		time_delta = int(time.time() - self.last_dark_update)
		if self.settings['extra dark current ref'] and time_delta < self.settings['dark current ref repeat time']:
			self.logger.info('dark current ref not expired. %d seconds since last' % (time_delta))
		else:
			self.checkAndRunCameraDarkCurrentReferenceUpdate()
		t1.join()

		filler_status = self.monitorRefillWithIsBusy()

	def checkAndRunCameraDarkCurrentReferenceUpdate(self):
		# Dark Current Reference Update if needed
		if self.withinGoodHours():
			self.runCameraDarkCurrentReferenceUpdate()
		else:
			self.logger.info('Outside the good hours to acquire camera dark current reference. Skipped')

	def withinGoodHours(self):
		'''
		Acquire Dark Current Reference may cause camera to misbehave such as black stripe.
		This makes it possible to limit the time it performs this to day time.
		'''
		within_good_hours = False
		if self.settings['start dark current ref hr'] == self.settings['end dark current ref hr']:
			return False
		my_hour = datetime.datetime.today().hour
		self.logger.info('Current hour of day: %d' % my_hour)
		if self.settings['start dark current ref hr'] <= my_hour and my_hour < self.settings['end dark current ref hr']:
			self.logger.info('Within the good hours to perform dark current reference acquisition')
			within_good_hours = True
		return within_good_hours

	def runNitrogenFiller(self):
		try:
			self.instrument.tem.runAutoFiller()
		except RuntimeError as e:
			if self.isRealFillerError():
				message = e.args[0]
				self.logger.error('Operation error: %s' % (message,))
				self.logger.error('Can not recover. Check filler and tank')
				self.pauseOnError()

	def isRealFillerError(self):
		'''
		AutoFiller raises com error in a few non-fatal cases.
		It does not require pausing and notification.
		'''
		loader_level,column_level = self.getRefrigerantLevels()
		# fill error above upper trip level can be ignored. It will recover itself
		if loader_level >= self.settings['loader fill end'] and column_level >= self.settings['column fill end']:
			self.logger.warning('Error received from instrument but liquid level above upper trip level. Error can be ignored.')
			return False
		# some fill did occur but is slow in filling
		if loader_level > self.settings['loader fill start'] and column_level > self.settings['column fill start']:
			if loader_level > self.loader_level_before or column_level > self.column_level_before:
				self.logger.error('Error received from instrument but level did increase above lower trip level.')
				self.logger.error('Workflow continue, but a system check is recommended.')
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
				# TODO: What if there are multiple K2/K3 ?  Need to break now because
				# Super and Counting are the same physical camera.
				break
		if need_update:
			self.logger.info('Waiting for %d seconds before running camera dark current reference update' % (self.settings['delay dark current ref']))
			time.sleep(self.settings['delay dark current ref'])
			self.updateCameraDarkCurrentReference()
		self.last_dark_update = time.time()
		
	def monitorRefillWithIsBusy(self):
		'''
		Wait until autofiller not busy if can be monitored by function in tem.
		If the function is not available returns None immediately.
		returned status is either False (finished refill or not busy)
		or None (not available)
		'''
		t0 = time.time()
		timeout = 30*60 # Fill should never take more than 30 min
		try:
			isbusy = self.instrument.tem.isAutoFillerBusy()
		except AttributeError:
			self.logger.warning('No auto filler isAutoFillerBusy')
			return None

		# handle script not available
		if isbusy is None:
			self.logger.warning('Auto filler isAutoFillerBusy call returns None')
			return isbusy

		if isbusy is True:
			self.logger.info('filling')
		else:
			self.logger.info('filler is idle')
		while isbusy is True:
			isbusy = self.instrument.tem.isAutoFillerBusy()
			if time.time() - t0 > timeout:
				self.logger.error('Auto filler remains busy for %.1f min,' % (timeout/60.0))
				self.pauseOnError()
				continue
			self.logger.info('filler is busy. check again in 1 min.')
			time.sleep(60)
		return isbusy

	def getRefrigerantLevels(self):
		loader_level = self.instrument.tem.getRefrigerantLevel(0)
		column_level = self.instrument.tem.getRefrigerantLevel(1)
		self.logger.info('Grid loader liquid N2 level is %d %%' % int(loader_level))
		self.logger.info('Column liquid N2 level is %d %%' % int(column_level))
		return loader_level,column_level
