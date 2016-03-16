import time
from leginon import leginondata, reference
import event
import gui.wx.ScreenCurrentLogger

class ScreenCurrentLogger(reference.Reference):
	# relay measure does events
	settingsclass = leginondata.ScreenCurrentLoggerSettingsData
	defaultsettings = reference.Reference.defaultsettings
	eventinputs = reference.Reference.eventinputs + [event.ScreenCurrentLoggerPublishEvent]
	panelclass = gui.wx.ScreenCurrentLogger.ScreenCurrentLoggerPanel
	requestdata = leginondata.ScreenCurrentLoggerData
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.ScreenCurrentLoggerPublishEvent]
		reference.Reference.__init__(self, *args, **kwargs)

		self.start()

	def onTest(self):
		self.player.play()

	def execute(self, request_data=None):
		self.setStatus('processing')
		self.logger.info('handle request')
		self.measureScreenCurrent()		
		self.logger.info('done')
		self.setStatus('idle')
		return True

	def measureScreenCurrent(self):
		self.setStatus('processing')
		self.logger.info('Send %s preset to scope' % (self.preset_name,))
		self.presets_client.toScope(self.preset_name)
		self.preset = self.presets_client.getPresetFromDB(self.preset_name)
		self.logger.info('Putting main screen down')
		self.instrument.tem.setMainScreenPosition('down')
		time.sleep(2)
		current = self.instrument.tem.ScreenCurrent
		self.logger.info('Screen current is %s' % (current,))
		self.logger.info('Putting main screen up')
		self.instrument.tem.setMainScreenPosition('up')
		self.publishCurrentValue(current)

	def publishCurrentValue(self,current): 
		resetdata = leginondata.ScreenCurrentData()
		resetdata['session'] = self.session
		resetdata['reference'] = self.reference_target
		resetdata['preset'] = self.preset
		resetdata['current'] = current
		resetdata.insert()
