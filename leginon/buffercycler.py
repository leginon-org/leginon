#!/usr/bin/env python

from leginon import conditioner
from leginon import leginondata
import leginon.gui.wx.BufferCycler

class BufferCycler(conditioner.Conditioner):
	# Define the class for gui panel
	panelclass = leginon.gui.wx.BufferCycler.Panel
	# Define the class for node settings
	settingsclass = leginondata.BufferCyclerSettingsData
	# Inherit the default settings from the parent class, Conditioner
	defaultsettings = conditioner.Conditioner.defaultsettings
	# Inherit the eventinputs
	eventinputs = conditioner.Conditioner.eventinputs

	def setCTypes(self):
		'''
		Define a unique condition type (CType) for database record.
		'''
		self.addCType('buffer_cycle')

	def _fixCondition(self, condition_type):
		'''
		Define what to do
		'''
		self.runBufferCycle()

	def runBufferCycle(self):
		try:
			self.logger.info('Running buffer cycle...')
			self.instrument.tem.runBufferCycle()
		except AttributeError:
			self.logger.warning('No buffer cycle for this instrument')
		except Exception, e:
			self.logger.error('Run buffer cycle failed: %s' % e)

