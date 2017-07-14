# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

# leginon
import node
import event
from leginon import leginondata
import gui.wx.TEMController
import instrument
import presets
import cameraclient

# myami

# python standard
import threading
import time
import types
import os.path
import itertools
import math
import logging

class TEMController(node.Node):
	panelclass = gui.wx.TEMController.Panel
	settingsclass = leginondata.TEMControllerSettingsData
	defaultsettings = {
	}
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.presetsclient = presets.PresetsClient(self)

		self.start()

	def _toScope(self,name, stagedict):
		try:
			self.instrument.tem.StagePosition = stagedict
		except KeyError:
			self.logger.exception('instrument key %s not available' % (stagedict.keys(),))
		except:
			self.logger.exception('unable to set instrument')
		else:
			self.logger.info('Moved to location %s' % (name,))

	def uiSendPreset(self,presetname):
		self.logger.info('Send %s preset to scope' % (presetname,))
		self.setStatus('processing')
		self.presetsclient.toScope(presetname)
		self.setStatus('idle')
		self.panel.onSendPresetDone()

	def onResetXY(self):
		loc = {'x':0.0,'y':0.0}
		self._toScope('reset xy',loc)

	def onResetZ(self):
		loc = {'z':0.0}
		self._toScope('reset z',loc)

	def onResetAlpha(self):
		loc = {'a':0.0}
		self._toScope('reset alpha',loc)

	def onCloseColumnValve(self):
		self.setStatus('processing')
		self.safeCloseColumnValve()
		self.panel.onSetTEMParamDone()
		self.setStatus('idle')

	def safeCloseColumnValve(self):
		# no preset probably means no instrument set.
		# the scope can be in any state. Better not allowed
		if not self.hasCurrentPreset():
			self.panel.enableAll(False)
			return
		# check current preset matches microscope
		if self.isCurrentPresetSet():
			if self.isColumnValveInState('close', False):
				self.logger.info('Column valve already closed')
				self.panel.onIsLightOn(False)
				return
			try:
				self.logger.info('Closing column valve....')
				self.instrument.tem.setColumnValvePosition('closed')
			except:
				self.logger.error('Failed to close column valve')
				raise
			time.sleep(0.5)
			self.panel.onIsLightOn(not self.isColumnValveInState('closed'))

	def isColumnValveInState(self,desired_state='open', display_log=True):
		current_state = self.instrument.tem.getColumnValvePosition()
		if self.instrument.tem.getColumnValvePosition() == desired_state:
			if display_log:
				self.logger.info('Column valve is %s' % desired_state)
			return True
		else:
			if display_log:
				self.logger.error('Column valve is %s' % current_state)
			return False

	def onOpenColumnValve(self):
		self.setStatus('processing')
		self.safeOpenColumnValve()
		self.panel.onSetTEMParamDone()
		self.setStatus('idle')

	def safeOpenColumnValve(self):
		# no preset probably means no instrument set.
		# the scope can be in any state. Better not allowed
		if not self.hasCurrentPreset():
			self.panel.enableAll(False)
			return
		# check basic instrument mode
		if self.isTEMinImagingMode():
			if self.isColumnValveInState('open', False):
				self.logger.info('Column valve already opened')
				self.panel.onIsLightOn(True)
				return
			# check current preset matches microscope
			if self.isCurrentPresetSet():
				# check column vacuum
				if self.isVacuumReady():
					# open column valve
					try:
						self.logger.info('Opening column valve....')
						self.instrument.tem.setColumnValvePosition('open')
					except:
						self.logger.error('Failed to open column valve')
						raise
				time.sleep(0.5)
				self.panel.onIsLightOn(self.isColumnValveInState('open'))

	def isTEMinImagingMode(self):
		self.logger.info('Checking image mode....')
		# presets are mapped to imaging mode only
		if not self.instrument.tem:
			self.logger.error('No instrument set. Send a preset first')
			return False
		if self.instrument.tem.DiffractionMode != 'imaging':
			self.logger.error('Presets are mapped to imaging mode only. Set on scope gui to imaging mode first')
			return False
		return True

	def hasCurrentPreset(self):
		self.logger.info('Checking preset....')
		preset = self.presetsclient.getCurrentPreset()
		if preset:
			preset_name = preset['name']
			self.logger.info('Current preset on record is %s' % (preset_name,))
			return True
		else:
			self.logger.error('No current preset. Please send a preset first')
			return False

	def isCurrentPresetSet(self):
		preset = self.presetsclient.getCurrentPreset()
		preset_temid = preset['tem'].dbid
		scope_tem = self.instrument.getTEMData()
		if not scope_tem:
			self.logger.error('TEM not set.  Please send a preset to scope')
			return False
		if scope_tem.dbid != preset_temid:
			self.logger.error('Preset tem does not match current tem state, Send a preset first.')
			return False
		# preset parameter checking in case it is manually changed on TEM
		for param in ('probe mode','magnification','spot size','intensity'):
			preset_value = preset[param]
			scope_value = self.instrument.getTEMParameter(scope_tem['name'],param)
			if scope_value != preset_value:
				self.logger.error('Preset %s does not match what is on scope. Please send the preset first' % param)
				return False
		return True

	def isVacuumReady(self):
		self.logger.info('Checking scope vacuum....')
		status = self.instrument.tem.VacuumStatus
		self.logger.info('Scope Vacuum status is %s' % (status))
		if status != 'ready':
			self.logger.error('Scope Vacuum not ready for imaging')
			return False
		return True

	def getPressuresToDisplay(self, unit='Pascal'):
		# Unit is Pascal for now.  Need Log unit conversion
		pressures = {}
		pressures['column'] = self.instrument.tem.ColumnPressure
		pressures['projection'] = self.instrument.tem.ProjectionChamberPressure
		pressures['buffer tank'] = self.instrument.tem.BufferTankPressure
		return pressures

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
