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
import leginon.gui.wx.TiltListAlternater

class TiltListAlternater(acquisition.Acquisition):
	'''
	Node class that set stage tilt angle per target list it processes.
	'''
	panelclass = leginon.gui.wx.TiltListAlternater.Panel
	settingsclass = leginondata.TiltListAlternaterSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'use tilts': False,
		'tilts': '(0,)', # Issue #5687. defined as string. too late to change to tuple
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltindex = 0
		self.tilts = []

	def getTiltForList(self, targetlistdata):
		original_position = self.instrument.tem.getStagePosition()
		try:
			self.tilts = self.convertDegreeTiltsToRadianList(self.settings['tilts'])
		except:
			self.logger.error('Error parsing tilt list.')
			return original_position['a']
		# use parent tilt is in conflict with local tilt list
		if self.settings['use parent tilt']:
			if not  self.settings['use tilts']:
				return super(TiltListAlternater).getTiltForList(targetlistdata)
			else:
				self.logger.error('Can not set to user parent tilt and local tilt list at the same time.')
				self.logger.warning('Use local list only')
		tilt = original_position['a']
		if len(self.tilts) > 0:
			self.tiltindex = self.tiltindex % len(self.tilts)
			tilt = self.tilts[self.tiltindex]
			self.tiltindex += 1
			if self.tiltindex == len(self.tilts):
				self.tiltindex = 0
		parent_tilt = tilt
		# Set to the new value
		return parent_tilt

	def getIsResetTiltInList(self):
		'''
		Determine whether to reset tilt before the first target is processed.
		Subclasses like RCT and TiltListAlternator
		'''
		return self.settings['use tilts'] or self.settings['use parent tilt']

