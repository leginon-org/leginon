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

		self.grid_slot_numbers = self.researchLoadableGridSlots()
		self.grid_slot_names = map((lambda x:'%d' % (x,)),self.grid_slot_numbers)
		self.loaded_grid_slot = None
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
		self.panel.sendPresetDone()

	def onResetXY(self):
		loc = {'x':0.0,'y':0.0}
		self._toScope('reset xy',loc)

	def onResetZ(self):
		loc = {'z':0.0}
		self._toScope('reset z',loc)

	def onResetAlpha(self):
		loc = {'a':0.0}
		self._toScope('reset alpha',loc)

	def uiCloseColumnValve(self):
		self.setStatus('processing')
		self.safeCloseColumnValve()
		self.panel.setTEMParamDone()
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
				self.panel.setIsLightOn(False)
				return
			try:
				self.logger.info('Closing column valve....')
				self.instrument.tem.setColumnValvePosition('closed')
			except:
				self.logger.error('Failed to close column valve')
				raise
			time.sleep(0.5)
			self.panel.setIsLightOn(not self.isColumnValveInState('closed'))

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

	def uiOpenColumnValve(self):
		self.setStatus('processing')
		self.safeOpenColumnValve()
		self.panel.setTEMParamDone()
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
				self.panel.setIsLightOn(True)
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
				self.panel.setIsLightOn(self.isColumnValveInState('open'))

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

	def researchLoadableGridSlots(self):
		'''
		place holder for future cartridges by project restriction.
		Slot name refers to the position on grid loader
		Grid name refers to the identity grid preparation. 
		'''
		try:
			total_grids = self.instrument.tem.getGridLoaderNumberOfSlots()
			return map((lambda x:x+1),range(total_grids))[1:]
		except:
			return []

	def getGridSlotNames(self):
		return self.grid_slot_names

	def getCurrentGridSlot(self):
		return self.loaded_grid_slot

	def getAllSlotState(self):
		states = {}
		for slot_number in self.grid_slot_numbers:
			state = self.instrument.tem.getGridLoaderSlotState(slot_number)
			states[slot_number] = state
		return states

	def getGridSlotStatesToDisplay(self):
		try:
			number_states = self.getAllSlotState()
			name_states = {}
			for key in number_states:
				name_key = '%d' % key
				name_states[name_key] = number_states[key]
		except:
			return {}
		return name_states

	def findFirstEmptySlotName(self):
		try:
			total_slots = self.instrument.tem.getGridLoaderNumberOfSlots()
		except AttributeError:
			self.logger.error('Send a preset to set instrument state first')
			return None
		empty_slot_invalid = False
		for s in range(total_slots):
			slot_number = s + 1
			state = self.instrument.tem.getGridLoaderSlotState(slot_number)
			if state == 'empty':
				slot_name = '%d' % (slot_number,)
				# add empty slot to available list so that unloaded grid can go back in.
				if slot_name not in self.grid_slot_names:
					empty_slot_invalid = True
					continue
				else:
					return slot_name
		if empty_slot_invalid:
			self.logger.error('Empty slot exists but not valid for the project')
		return None

	def unloadGrid(self):
		if not self.instrument.tem.hasGridLoader():
			self.logger.error('TEM has no auto grid loader')
			return
		# Must have empty slot in range
		empty_slot_name = self.findFirstEmptySlotName()
		if empty_slot_name is None:
			self.logger.error('No empty slot on grid loader. Can not unload.')
			self.panel.setTEMParamDone()
			return
		empty_slot_number = int(empty_slot_name)
		is_success = False
		try:
			self.logger.info('UnLoading grid from column')
			self.instrument.tem.unloadGridCartridge()
			state = self.instrument.tem.getGridLoaderSlotState(empty_slot_number)
			if state == 'occupied':
				is_success = True
		except Exception, e:
			self.logger.error(e)
		if is_success == True:
			self.loaded_grid_slot = None
		self.logger.info('Done unLoading grid from column')
		self.panel.setTEMParamDone()

	def loadGrid(self, slot_name):
		if slot_name not in self.grid_slot_names:
			self.logger.error('Selected slot is not valid for this project')
			return
		try:
			slot_number = int(slot_name)
		except:
			self.logger.error('Slot not selected')
			return
		if not self.instrument.tem.hasGridLoader():
			self.logger.error('TEM has no auto grid loader')
			return

		state = 'unknown'
		try:
			state = self.instrument.tem.getGridLoaderSlotState(slot_number)
		except Exception, e:
			self.logger.error(e)
		# Just set this grid as loaded grid if it is an empty slot
		# Grid can not be unloaded if we don't set it here.
		if state == 'empty':
			if self.loaded_grid_slot is None:
				self.logger.info('Unknown loaded grid. Set loaded grid to empty slot %s' % slot_name)
				self.loaded_grid_slot = slot_number
			elif self.loaded_grid_slot == slot_number:
				self.logger.info('Grid from slot is loaded. Nothing to do')
			else:
				self.logger.warning('Detected empty slot. Can not load.')
			self.panel.setTEMParamDone()
			return
		if state != 'occupied':
			self.logger.warning('Invalid grid slot state. Can not load.')
			self.panel.setTEMParamDone()
			return
		return self._loadGrid(slot_number)

	def _loadGrid(self, slot_number):
		# Loading occupied grid.
		self.logger.info('Loading grid from slot %d' % (slot_number,))
		is_success = False
		try:
			self.instrument.tem.loadGridCartridge(slot_number)
			state = self.instrument.tem.getGridLoaderSlotState(slot_number)
			if state == 'empty':
				is_success = True
		except Exception, e:
			self.logger.error(e)
		if is_success == True:
			self.loaded_grid_slot = slot_number
			self.logger.info('Grid Loaded from slot %d' % (slot_number,))
		self.panel.setTEMParamDone()

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
