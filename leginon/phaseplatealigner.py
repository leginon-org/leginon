import math
from leginon import leginondata, reference, calibrationclient, cameraclient
import event
import gui.wx.PhasePlateAligner
from pyami import arraystats

class PhasePlateAligner(reference.Reference):
	# relay measure does events
	settingsclass = leginondata.PhasePlateAlignerSettingsData
	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update({
		'charge time': 2.0,
	})
	eventinputs = reference.Reference.eventinputs + [event.PhasePlatePublishEvent]
	panelclass = gui.wx.PhasePlateAligner.PhasePlateAlignerPanel
	requestdata = leginondata.PhasePlateData
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.PhasePlatePublishEvent]
		reference.Reference.__init__(self, *args, **kwargs)

		self.start()

	def onTest(self):
		self.player.play()

	def execute(self, request_data=None):
		self.setStatus('processing')
		self.logger.info('handle request')
		self.nextPhasePlate()		
		self.logger.info('done')
		self.setStatus('idle')
		return True

	def nextPhasePlate(self):
		self.setStatus('processing')
		self.logger.info('Waiting for scope to advance PP')
		self.instrument.tem.nextPhasePlate()
		if self.settings['charge time']:
			self.presets_client.toScope(self.preset_name)
			self.logger.info('expose for %.1f second' % self.settings['charge time'])
			self.instrument.tem.exposeSpecimenNotCamera(self.settings['charge time'])
