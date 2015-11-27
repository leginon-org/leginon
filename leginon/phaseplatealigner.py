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
		'charge time': 0.0,
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
		self.player.wait()
		self.logger.info('done')
		self.setStatus('idle')
		return True

	def nextPhasePlate(self):
		self.setStatus('user input')
		self.logger.info('Waiting for user to advance PP and align.')
		self.player.pause()
		print 'should not be here before dialog close'
