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
import leginon.gui.wx.PhasePlatePlaneShiftCycler

class PhasePlatePlaneShiftCycler(acquisition.Acquisition):
	'''
	Node class that set stage shifts_on_plane angle according to a list at
	each target it received in the target list.  Optionally return
	to the shifts_on_plane of the parent image at the end of processing.
	'''
	panelclass = leginon.gui.wx.PhasePlatePlaneShiftCycler.Panel
	settingsclass = leginondata.PhasePlatePlaneShiftCyclerSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'use cycler': False,
		'shifts on plane': '(0.0,)',
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.shifts_on_plane = eval(self.settings['shifts on plane']) #in micron defocus
		self.shifts_on_plane_cycle = itertools.cycle(eval(self.settings['shifts on plane']))
		self.xy = {'y':-0.91,'x':0.4142}
		self.scale = 0.00001

	def getParentShiftOnPlane(self,targetdata):
		if 'image' in targetdata.keys() and targetdata['image']:
			parent_shifts_on_plane = targetdata['image']['scope']['phase plate plane shift']
		else:
			parent_shifts_on_plane = self.instrument.tem.getPhasePlatePlaneShift()
		self.parent_shifts_on_plane = parent_shifts_on_plane
		self.logger.info('set default shifts to %s' % self.parent_shifts_on_plane)
		return parent_shifts_on_plane

	def processTargetList(self, newdata):
		self.shifts_on_plane = eval(self.settings['shifts on plane'])
		super(PhasePlatePlaneShiftCycler, self).processTargetList(newdata)
		self.getParentShiftOnPlane(newdata)
		# at the end restored to parent shifts_on_plane
		if self.settings['use cycler'] and len(self.shifts_on_plane) > 0:
			if not hasattr(self, 'parent_shifts_on_plane'):
				self.logger.error('Open and close settings to initialize to current shifts on plane.')
			else:
				self.instrument.tem.setPhasePlatePlaneShift(self.parent_shifts_on_plane)

	def processTargetData(self, targetdata, attempt=None):
		if self.settings['use cycler'] and len(self.shifts_on_plane) > 0:
			if not hasattr(self, 'parent_shifts_on_plane'):
				self.resetCycle()
			shifts_on_plane = next(self.shifts_on_plane_cycle)
			x_value = self.parent_shifts_on_plane['x'] + shifts_on_plane*self.xy['x']*self.scale
			y_value = self.parent_shifts_on_plane['y'] + shifts_on_plane*self.xy['y']*self.scale
			self.instrument.tem.setPhasePlatePlaneShift({'x':x_value,'y':y_value})
			self.logger.info('LPP plane shift sent: %s' % {'x':x_value,'y':y_value})
			super(PhasePlatePlaneShiftCycler, self).processTargetData(targetdata, attempt)
		else:
			# process as normal
			super(PhasePlatePlaneShiftCycler, self).processTargetData(targetdata, attempt)

	def resetCycle(self):
		self.getParentShiftOnPlane({})
		self.shifts_on_plane_cycle = itertools.cycle(eval(self.settings['shifts on plane']))
