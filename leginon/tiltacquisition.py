#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import math
from leginon import acq as acquisition
from leginon import leginondata
import leginon.gui.wx.TiltAcquisition

class TiltAcquisition(acquisition.Acquisition):
	panelclass = leginon.gui.wx.TiltAcquisition.Panel
	settingsclass = leginondata.TiltAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'use tilts': False,
		'reset per targetlist': False,
		'tilts': '(0,)',
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltindex = 0
		self.tilts = (0,0.5,1)
		self.logger.Error('This is a legacy class.  Will be deplicated. Use TiltAlternator instead')

	def getParentTilt(self,targetdata):
		if targetdata['image']:
			parent_tilt = targetdata['image']['scope']['stage position']['a']
		else:
			if len(self.tilts):
				parent_tilt = self.tilts[0]
			else:
				parent_tilt = 0.0
		return parent_tilt

	def processTargetList(self, newdata):
		self.tilts = self.convertDegreeTiltsToRadianList(self.settings['tilts'])
		super(TiltAcquisition, self).processTargetList(newdata)
		if self.settings['use tilts'] and len(self.tilts) > 0:
			parent_tilt = self.getParentTilt(newdata)
			self.instrument.tem.setStagePosition({'a':parent_tilt})
			if self.settings['reset per targetlist']:
				self.tiltindex = 0

	def processTargetData(self, targetdata, attempt=None):
		if self.settings['use tilts'] and len(self.tilts) > 0:
			self.tiltindex = self.tiltindex % len(self.tilts)
			tilt = self.tilts[self.tiltindex]
			self.instrument.tem.setStagePosition({'a':tilt})
			super(TiltAcquisition, self).processTargetData(targetdata, attempt)
		else:
			# process as normal
			super(TiltAcquisition, self).processTargetData(targetdata, attempt)
		self.tiltindex += 1

	def waitForRejects(self):
		if self.settings['use tilts'] and len(self.tilts) > 0:
			self.instrument.tem.setStagePosition({'a':self.tilts[0]})
		return super(TiltAcquisition, self).waitForRejects()
