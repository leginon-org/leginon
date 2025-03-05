#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
import math
import itertools
from leginon import acq as acquisition
from leginon import leginondata
import leginon.gui.wx.TiltCycler

class TiltCycler(acquisition.Acquisition):
	'''
	Node class that set stage tilt_degrees angle according to a list at
	each target it received in the target list.  Optionally return
	to the tilt_degrees of the parent image at the end of processing.
	'''
	panelclass = leginon.gui.wx.TiltCycler.Panel
	settingsclass = leginondata.TiltCyclerSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'use cycler': False,
		'tilts': '(0.0,)',
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tilts = eval(self.settings['tilts']) #in degrees
		self.tilts_cycle = itertools.cycle(eval(self.settings['tilts']))
		self.scale = math.pi/180.0 # degrees to radians

	def getParentTilt(self,targetdata):
		if 'image' in targetdata.keys() and targetdata['image']:
			parent_tilt = targetdata['image']['scope']['stage']['a']
		else:
			parent_tilt = self.instrument.tem.getStagePosition()['a']
		self.parent_tilt = parent_tilt
		self.logger.info('set default tilt to %s' % self.parent_tilt)
		return parent_tilt

	def processTargetList(self, newdata):
		self.tilts = eval(self.settings['tilts'])
		super(TiltCycler, self).processTargetList(newdata)
		self.getParentTilt(newdata)
		# at the end restored to parent tilt_degrees
		if self.settings['use cycler'] and len(self.tilts) > 0:
			if not hasattr(self, 'parent_tilt'):
				self.logger.error('Open and close settings to initialize to current tilts.')
			else:
				self.instrument.tem.setTilt(self.parent_tilt)

	def processTargetData(self, targetdata, attempt=None):
		if self.settings['use cycler'] and len(self.tilts) > 0:
			if not hasattr(self, 'parent_tilt'):
				self.resetCycle()
			tilt_degrees = next(self.tilts_cycle)
			tilt_value = self.parent_tilt + tilt_degrees*self.scale
			self.instrument.tem.setStagePosition({'a':tilt_value})
			self.logger.info('Stage tilt sent in degrees: %.2f' % (tilt_value/self.scale))
			super(TiltCycler, self).processTargetData(targetdata, attempt)
		else:
			# process as normal
			super(TiltCycler, self).processTargetData(targetdata, attempt)

	def resetCycle(self):
		self.getParentTilt({})
		self.tilts_cycle = itertools.cycle(eval(self.settings['tilts']))
