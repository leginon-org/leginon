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
import remoteserver

class TEMController(node.Node):
	panelclass = gui.wx.TEMController.Panel
	settingsclass = leginondata.TEMControllerSettingsData
	defaultsettings = {
		'retract obj ap on grid changing':False,
	}
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs
	eventinputs.append(event.LoadAutoLoaderGridEvent)
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs \
									+ [event.ManagerPauseEvent, event.ManagerContinueEvent,
										]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.addEventInput(event.LoadAutoLoaderGridEvent, self.handleLoadAutoLoaderGrid)
		self.presetsclient = presets.PresetsClient(self)
		self.loaded_grid_slot = None
		self.grid_slot_numbers = []
		self.grid_slot_names = []
		if not remoteserver.NO_REQUESTS and session is not None:
			self.remote_toolbar = remoteserver.RemoteToolbar(self.logger, session, self, self.remote.leginon_base)
		else:
			self.remote_toolbar = None
		self.start()

	def onInitialized(self):
		status = super(TEMController, self).onInitialized()
		if status is False:
			return
		# This may not give results since instrument may not be loaded, yet
		self.grid_slot_numbers = self.researchLoadableGridSlots()
		self.grid_slot_names = map((lambda x:'%d' % (x,)),self.grid_slot_numbers)
		if self.remote_toolbar:
			self._activateClickTools()

	def exit(self):
		if self.remote_toolbar:
			self.remote_toolbar.exit()
		super(TEMController, self).exit()

	def _activateClickTools(self):
			self.remote_toolbar.addClickTool('pause','uiPause','pause process','none')
			self.remote_toolbar.addClickTool('play','uiContinue','continue after pause','all')
			self.remote_toolbar.addClickTool('light_off','uiCloseColumnValve','close column valve','all')
			# finalize toolbar and send to leginon-remote
			self.remote_toolbar.finalizeToolbar()

	def uiClickReconnectRemote(self):
		'''
		handle gui check method choice.  Bypass using self.settings['check method']
		because that is not yet set.
		'''
		if not self.remote or not self.remote_toolbar.remote_server_active:
			return
		self._activateClickTools()

	def handleLoadAutoLoaderGrid(self,evt):
		# Hope instrument is loaded by now.
		self.grid_slot_numbers = self.researchLoadableGridSlots()
		grid_slot_name = evt['slot name']
		t0 = time.time()
		is_successful = self.loadGrid(grid_slot_name)
		if is_successful:
			self.confirmEvent(evt)
		else:
			# Will need restart to clear confirm event.
			self.logger.error('Failer auto loading.  Please restart.')

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
		self.uiContinue()
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
		if self.instrument.tem.ProjectionMode != 'imaging':
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
			slot_number_list = map((lambda x:x+1),range(total_grids))
			slot_number_list.reverse()
			return slot_number_list
		except Exception, e:
			if hasattr(e,'args') and len(e.args) > 0:
				self.logger.warning(e.args[0])
			else:
				self.logger.warning('error with no message')
			self.logger.warning('Send a preset to scope to set TEM and then refresh TEM display')
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
			self.grid_slot_numbers = self.researchLoadableGridSlots()
			self.grid_slot_names = map((lambda x:'%d' % (x,)),self.grid_slot_numbers)
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
		'''
		Unoad a grid to the first empty slot.
		'''
		if not self.instrument.tem.hasGridLoader():
			self.logger.error('TEM has no auto grid loader')
			return
		self.setStatus('processing')
		is_success = self._unloadGrid()
		self.setStatus('idle')
		return is_success

	def _unloadGrid(self):
		'''
		Internal function to load a grid to the first empty slot.
		'''
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
		return is_success

	def loadGrid(self, slot_name):
		'''
		Load a grid by slot name string.
		'''
		if slot_name not in self.grid_slot_names:
			self.logger.error('Selected slot is not valid for this project')
			return
		self.setStatus('processing')
		is_success = self._loadGrid(slot_name)
		self.setStatus('idle')
		return is_success

	def _retractObjectiveAperture(self):
		'''
		Retract objective aperture and return the old state.
		This is used before grid exchange and in-pair with
		reinsertObjectiveAperture.
		'''
		old_state = self._getApertureStateDisplayByName('objective')
		old_state='unknown'
		if old_state != 'unknown':
			self.selectAperture('objective', 'open')
		else:
			self.logger.error('Aperture not retracted during grid exchange due to unknown state')
		return old_state

	def _reinsertObjectiveAperture(self, old_state):
		'''
		Insert the old objective aperture selection.
		This is used after grid exchange and in-pair with
		retractObjectiveAperture.
		'''
		if old_state != 'unknown':
			self.selectAperture('objective', old_state)

	def _loadGrid(self, slot_name):
		'''
		Internal function to load a grid by slot name string.
		'''
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
				is_success = True
			elif self.loaded_grid_slot == slot_number:
				self.logger.info('Grid from slot %s is loaded. Nothing to do' % slot_number)
				is_success = True
			else:
				self.logger.warning('Detected empty slot. Can not load.')
				is_success = False
			self.panel.setTEMParamDone()
			return is_success
		if state != 'occupied':
			self.logger.warning('Invalid grid slot state. Can not load.')
			self.panel.setTEMParamDone()
			return False
		# Finished all validation. We are now sure that we need to load.
		if self.settings['retract obj ap on grid changing']:
			old_selection = self._retractObjectiveAperture()
		is_success = self.__loadGrid(slot_number)
		if self.settings['retract obj ap on grid changing'] and old_selection != 'unknown':
			self._reinsertObjectiveAperture(old_selection)
		return is_success

	def __loadGrid(self, slot_number):
		'''
		Load grid by slot number.  All validation must already be handled.
		'''
		# Loading occupied grid.
		self.logger.info('Loading grid from slot %d' % (slot_number,))
		is_success = False
		state = 'unknown'
		try:
			self.instrument.tem.loadGridCartridge(slot_number)
			state = self.instrument.tem.getGridLoaderSlotState(slot_number)
			if state == 'empty' or state == 'loaded':
				is_success = True
		except Exception, e:
			self.logger.error(e)
		if is_success == True:
			self.loaded_grid_slot = slot_number
			self.logger.info('Grid Loaded from slot %d' % (slot_number,))
		else:
			self.logger.warning('Loader slot state after loading is %s' % (state))
		self.panel.setTEMParamDone()
		return is_success

	def getApertureNames(self,mechanism):
		try:
			names = self.instrument.tem.getApertureSelections(mechanism)
		except:
			names = []
		return names

	def getApertureNameUnit(self,name):
		try:
			int_name=int(name)
			unit = 'um'
		except ValueError:
			unit = ''
		return unit

	def selectAperture(self,mechanism, name):
		unit = self.getApertureNameUnit(name)
		self.logger.info('Changing %s aperture to %s %s' % (mechanism,name,unit))
		is_success = False
		try:
			self.instrument.tem.setApertureSelection(mechanism,name)
			is_success = True
		except Exception, e:
			self.logger.error(e)
		if is_success == True:
			self.logger.info('%s aperture changed to %s %s' % (mechanism,name,unit))
		self.panel.setTEMParamDone()

	def getApertureMechanisms(self):
		try:
			return self.instrument.tem.getApertureMechanisms()
		except:
			return []

	def getApertureStatesToDisplay(self):
		names = self.getApertureMechanisms()
		name_states = {}
		for name in names:
			state = self._getApertureStateDisplayByName(name)
			name_states[name] = state
		return name_states

	def _getApertureStateDisplayByName(self, name):
		try:
			state = self.instrument.tem.getApertureSelection(name)
		except ValueError, e:
			self.logger.warning(e)
			state = 'unknown'
		except RuntimeError, e:
			self.logger.error(e)
			state = 'unknown'
		try:
			if state is None or state=='' or state not in self.instrument.tem.getApertureSelections(name):
				state = 'unknown'
		except:
			state = 'unknown'
		return state

	def uiPause(self):
		'''
		Pause all acquisition class nodes that are not idle.
		'''
		self.logger.info('Pausing workflow')
		self.outputEvent(event.ManagerPauseEvent())

	def uiContinue(self):
		'''
		Continue all paused acquisition class nodes.  This should
		only be used if all pauses are ok to continue.
		'''
		self.logger.info('Continuing workflow')
		# Send the event to manager to continue all paused nodes.
		self.outputEvent(event.ManagerContinueEvent(all=True))
		
if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
