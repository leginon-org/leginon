#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#
from leginon import event
from leginon import conditioner
# load the database definition module
from leginon import leginondata
# load the gui class module
import leginon.gui.wx.ColdFegFlasher

class ColdFegFlasher(conditioner.Conditioner):
	panelclass = leginon.gui.wx.ColdFegFlasher.Panel
	settingsclass = leginondata.ColdFegFlasherSettingsData
	defaultsettings = {}
	defaultsettings = dict(conditioner.Conditioner.defaultsettings)
	defaultsettings.update({
	})
	eventinputs = conditioner.Conditioner.eventinputs

	def onInit(self):
		super(ColdFegFlasher, self).onInit()
		# initialize these to 0 so that it does not trigger early warning.

	def setCTypes(self):
		self.addCType('cfeg')

	def _fixCondition(self, condition_type):
		self.setStatus('processing')
		self.flash()
		self.setStatus('idle')
		self.player.stop()

	def isAboveTripValue(self):
		# calling monitorRefillWithIsBusy first to make sure it is not already refilling
		if not self.hasColdFeg():
			self.logger.warning('No cold feg on this tem')
			return False
		return self.isFlashingNeeded()

	def isFlashingNeeded(self):
		'''
		Check if flash necessary
		'''
		need_flashing = True
		self.logger.info('cfeg need flashing')
		return need_flashing

	def hasColdFeg(self):
		try:
			has_cold_feg = self.instrument.tem.hasColdFeg()
		except:
			has_cold_feg = False
		return has_cold_feg

	def flash(self):
		is_flashing = self.instrument.tem.ColdFegFlashing
		if is_flashing != 'off':
			self.logger.error('Cold Feg not available for flashing despite previous check. Abort ')
			return
		# Do flashing
		self.runFlashing()
		# Any delay we need to add before resuming the workflow.
		flash_status = self.monitorFlashing()

	def runFlashing(self):
		try:
			self.instrument.tem.ColdFegFlashing = 'on'
		except RuntimeError as e:
			message = e.args[0]
			self.logger.error('Operation error: %s' % (message,))
			self.pauseOnError()

	def monitorFlashing(self):
		'''
		place holder in case we need extra wait after runFlashing is returned.
		'''
		return False
