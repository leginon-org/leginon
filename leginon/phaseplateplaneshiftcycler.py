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
		'shift sequence': '(0.0,)',
		'shift scale': 0.00001,
		'x projection': 1.0,
		'y projection': 0.0,
		'two d scan': False,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.shifts_on_plane = eval(self.settings['shift sequence']) #in micron defocus
		self.resetCycles()
		self.xy = self.calculateUnitVector()
		self.scale = self.settings['shift scale']
		self.shift_name = 'phase plate plane shift'
		self.scope_attr = ''.join(map((lambda x:x.capitalize()),self.shift_name.split(' ')))

	def resetCycles(self):
		self.col_shifts_cycle = itertools.cycle(eval(self.settings['shift sequence']))
		if self.settings['two d scan']:
			self.row_shifts_cycle = itertools.cycle(eval(self.settings['shift sequence']))
		else:
			self.row_shifts_cycle = itertools.cycle((0.0,))

	def calculateUnitVector(self):
		u_norm = math.hypot(self.settings['x projection'],self.settings['y projection'])
		if u_norm < 1e-12:
			raise ValueError('Shift unit vector can not have 0 length')
		return {'x': self.settings['x projection']/u_norm,'y':self.settings['y projection']/u_norm}

	def getParentShift(self,targetdata):
		if 'image' in targetdata.keys() and targetdata['image']:
			parent_shifts_on_plane = targetdata['image']['scope'][self.shift_name]
		else:
			# targetdata from simulated target operation has no image. Use current value
			#parent_shifts_on_plane = getattr(self.instrument.tem,'get%s' % self.scope_attr)()
			parent_shifts_on_plane = self.instrument.tem.getPhasePlatePlaneShift()
		self.parent_shift = parent_shifts_on_plane
		self.logger.info('Set default shifts to %s' % self.parent_shift)
		return parent_shifts_on_plane

	def processTargetList(self, newdata):
		self.shifts_on_plane = eval(self.settings['shift sequence'])
		super(PhasePlatePlaneShiftCycler, self).processTargetList(newdata)
		self.getParentShift(newdata)
		# at the end restored to parent shifts_on_plane
		if self.settings['use cycler'] and len(self.shifts_on_plane) > 0:
			if not hasattr(self, 'parent_shift'):
				self.logger.error('Open and close settings to initialize to current shift sequence.')
			else:
				getattr(self.instrument.tem,'set%s' % self.scope_attr)(self.parent_shift)

	def processTargetData(self, targetdata, attempt=None):
		if self.settings['use cycler'] and len(self.shifts_on_plane) > 0:
			if not hasattr(self, 'parent_shift'):
				self.resetCycle()
			self.c_shift = next(self.col_shifts_cycle)
			if self.iter % len(eval(self.settings['shift sequence'])) == 0:
				self.r_shift = next(self.row_shifts_cycle)
			x_unit_shift = self.xy['x']*self.settings['shift scale']
			y_unit_shift = self.xy['y']*self.settings['shift scale']
			x_value = self.parent_shift['x'] + self.c_shift*x_unit_shift + self.r_shift*y_unit_shift
			y_value = self.parent_shift['y'] + self.c_shift*y_unit_shift - self.r_shift*x_unit_shift
			getattr(self.instrument.tem,'set%s' % self.scope_attr)({'x':x_value,'y':y_value})
			self.logger.info('%s sent: %s' % (self.shift_name.capitalize(),{'x':x_value,'y':y_value}))
			self.iter += 1
			super(PhasePlatePlaneShiftCycler, self).processTargetData(targetdata, attempt)
		else:
			# process as normal
			super(PhasePlatePlaneShiftCycler, self).processTargetData(targetdata, attempt)

	def onLoopStop(self):
		self.logger.info('%s reset to %s' % (self.shift_name.capitalize(),self.parent_shift))
		getattr(self.instrument.tem,'set%s' % self.scope_attr)(self.parent_shift)
		self.logger.info('Shift sequence cycler reset to beginning')
		self.resetCycles()

	def resetCycle(self):
		# reset iteration cycle, unit vector and default value
		self.xy = self.calculateUnitVector()
		self.getParentShift({})
		self.resetCycles()
		self.iter = 0
