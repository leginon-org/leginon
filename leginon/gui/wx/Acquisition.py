# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import threading

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY, IntEntry
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import leginon.gui.wx.Events
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.ToolBar
from leginon.gui.wx.ImageBrowser import ImageBrowserPanel
import leginon.gui.wx.Icons 
import leginon.gui.wx.Dialog

import leginon.targethandler

hide_incomplete = False

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Image Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		if self.show_basic:
			sz = self.addBasicSettings()
		else:
			sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addBasicSettings(self):
		# movetype
		szmovetype = self.createMoveTypeSizer()
		# pause time
		szpausetime = self.createPauseTimeSizer()
		# extra pause for first image
		szfirstpause = self.createFirstPauseTimeSizer()
		# process
		self.widgets['wait for process'] = wx.CheckBox(self, -1,
																				'Wait for a node to process the image')
		# transform
		sz_transform = self.createTransformSizer()
		# preset order
		self.setPresetOrderWidget()

		szleft = wx.GridBagSizer(3, 10)
		szleft.Add(szmovetype, (0, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		szleft.Add(szpausetime, (1, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		szleft.Add(szfirstpause, (2, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		szleft.Add(self.widgets['wait for process'], (3, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		szleft.Add(sz_transform, (4, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)

		sz = wx.GridBagSizer(3, 3)
		sz.Add(szleft, (0, 0), (5, 2), wx.ALIGN_CENTER)
		sz.Add(self.widgets['preset order'], (0, 2), (5, 2), wx.ALIGN_CENTER)
		return sz

	def setPresetOrderWidget(self):
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset order'] = EditPresetOrder(self, -1)
		self.widgets['preset order'].setChoices(presets)

	def createMoveTypeSizer(self):
		# move type
		movetypes = self.node.getMoveTypes()
		self.widgets['move type'] = Choice(self, -1, choices=movetypes)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to target'),
										(0, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		return szmovetype

	def createPauseTimeSizer(self):
		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		return szpausetime

	def createFirstPauseTimeSizer(self):
		# pause time
		self.widgets['first pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait extra'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['first pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before the first image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		return szpausetime

	def createPauseBetweenTimeSizer(self):
		# extra pause between presets
		self.widgets['pause between time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausebtime = wx.GridBagSizer(5, 5)
		szpausebtime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausebtime.Add(self.widgets['pause between time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausebtime.Add(wx.StaticText(self, -1, 'extra seconds between presets'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		return szpausebtime

	def createBadResponseSizer(self):
		self.widgets['bad stats response'] = Choice(self, -1, choices=['Continue', 'Pause', 'Recheck', 'Abort one','Abort all'])
		sz_response = wx.BoxSizer(wx.HORIZONTAL)
		sz_response.Add(self.widgets['bad stats response'])
		sz_response.Add(wx.StaticText(self, -1, ' target list(s)'))
		return sz_response
	
	def createBadEvaluateSizer(self):
		self.widgets['low mean'] = FloatEntry(self, -1, chars=4)
		self.widgets['high mean'] = FloatEntry(self, -1, chars=4)
		sz_evaluate = wx.BoxSizer(wx.HORIZONTAL)
		sz_evaluate.Add(wx.StaticText(self, -1, 'between'))
		sz_evaluate.Add(self.widgets['low mean'])
		sz_evaluate.Add(wx.StaticText(self, -1, 'and'))
		sz_evaluate.Add(self.widgets['high mean'])
		return sz_evaluate

	def createBadRangeSizer(self):
		self.widgets['bad stats type'] = Choice(self, -1, choices=['Mean', 'Slope'])
		# range sizer
		sz_range= wx.GridBagSizer(0, 0)
		sz_range.Add(wx.StaticText(self, -1, 'when image'), (0,0),(1,1), wx.ALIGN_RIGHT)
		sz_range.Add(self.widgets['bad stats type'],(0,1),(1,1))
		sz_range.Add(wx.StaticText(self, -1, 'is NOT'), (0,2),(1,1), wx.ALIGN_LEFT)
		return sz_range

	def createReacquireSizer(self):
		sbsim = wx.StaticBox(self, -1, 'Reacquire rule for failed images')
		sbszsim = wx.StaticBoxSizer(sbsim, wx.VERTICAL)
		szsim = wx.GridBagSizer(5, 5)
		self.widgets['reacquire when failed'] = wx.CheckBox(self, -1, 'Reacquire 3 times before pause')
		szsim.Add(self.widgets['reacquire when failed'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsim.Add(self.createBadRecheckSizer(), (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszsim.Add(szsim, 0, wx.ALIGN_CENTER)
		return sbszsim

	def createBadRecheckSizer(self):
		# recheck
		self.widgets['recheck pause time'] = IntEntry(self, -1, chars=8)
		sz_recheck = wx.GridBagSizer(0, 0)
		label = wx.StaticText(self, -1, 'Wait for')
		sz_recheck.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_recheck.Add(self.widgets['recheck pause time'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'secs before reacquiring')
		sz_recheck.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz_recheck

	def createBadStatsEvaluateResponseBoxSizer(self):
		sbeval = wx.StaticBox(self, -1, 'Evaluate Image Stats')
		sbsz_evaluate = wx.StaticBoxSizer(sbeval, wx.VERTICAL)

		sz_response = self.createBadResponseSizer()
		sz_range = self.createBadRangeSizer()
		sz_evaluate = self.createBadEvaluateSizer()
		# bad stats email
		passwordbut = wx.Button(self, -1, 'Enter Email Password')
		self.Bind(wx.EVT_BUTTON, self.onEnterPassword, passwordbut)
		# evaluate box sizer
		sbsz_evaluate.Add(sz_response, 0, wx.ALIGN_CENTER|wx.ALL, 0)
		sbsz_evaluate.Add(sz_range, 0, wx.ALIGN_CENTER|wx.ALL,0)
		sbsz_evaluate.Add(sz_evaluate, 0, wx.ALIGN_CENTER|wx.ALL,0)
		sbsz_evaluate.Add(passwordbut, 0, wx.ALIGN_CENTER|wx.ALL, 3)
		return sbsz_evaluate

	def createTransformSizer(self):
		self.widgets['adjust for transform'] = Choice(self, -1, choices=['no', 'one', 'all'])
	
		sz_transform = wx.GridBagSizer(0, 0)
		label = wx.StaticText(self, -1, 'Adjust target using')
		sz_transform.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_transform.Add(self.widgets['adjust for transform'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'ancestor(s)')
		sz_transform.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz_transform

	def createUseParentMoverSizer(self):
		self.widgets['use parent mover'] = wx.CheckBox(self, -1, 'Use ancestor image mover in adjustment')
	
		sz_transform = wx.GridBagSizer(0, 0)
		label = wx.StaticText(self, -1, 'Adjust target using')
		sz_transform.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_transform.Add(self.widgets['use parent mover'],(1,0),(1,3))
		return sz_transform

	def createOffsetSizer(self):
		# set widgets
		self.widgets['target offset row'] = IntEntry(self, -1, chars=6)
		self.widgets['target offset col'] = IntEntry(self, -1, chars=6)
		# make sizer
		sz_offset = wx.BoxSizer(wx.HORIZONTAL)
		sz_offset.Add(wx.StaticText(self, -1, 'offset target x:'))
		sz_offset.Add(self.widgets['target offset col'])
		sz_offset.Add(wx.StaticText(self, -1, 'y:'))
		sz_offset.Add(self.widgets['target offset row'])
		return sz_offset

	def createMiscSizer(self):
		# set widgets
		self.widgets['wait for process'] = wx.CheckBox(self, -1,
																				'Wait for a node to process the image')
		self.widgets['wait for rejects'] = wx.CheckBox(self, -1,
																				'Publish and wait for rejected targets')
		self.widgets['wait for reference'] = wx.CheckBox(self, -1,
																				'Publish and wait for the reference target')
		self.widgets['drift between'] = wx.CheckBox(self, -1, 'Declare drift between targets')
		self.widgets['background'] = wx.CheckBox(self, -1, 'Acquire in the background')
		self.widgets['park after target'] = wx.CheckBox(self, -1, 'Park after every target acquired')
		self.widgets['park after list'] = wx.CheckBox(self, -1, 'Park after every target list')
		# set sizers
		sz_misc = wx.BoxSizer(wx.VERTICAL)
		sz_misc.Add(self.widgets['wait for process'])
		sz_misc.Add(self.widgets['wait for rejects'])
		sz_misc.Add(self.widgets['wait for reference'])
		sz_misc.Add(self.createTransformSizer())
		sz_misc.Add(self.createUseParentMoverSizer())
		sz_misc.Add(self.createOffsetSizer())
		sz_misc.Add(self.widgets['drift between'])
		sz_misc.Add(self.widgets['background'])
		sz_misc.Add(self.widgets['park after target'])
		sz_misc.Add(self.widgets['park after list'])
		sz_misc.Add(self.createBadStatsEvaluateResponseBoxSizer())
		sz_misc.Add(self.createReacquireSizer())
		return sz_misc

	def createSimulatedTargetLoopBoxSizer(self):
		sbsim = wx.StaticBox(self, -1, 'Simulated Target Loop')
		sbszsim = wx.StaticBoxSizer(sbsim, wx.VERTICAL)

		# simulate loop settings
		self.widgets['loop delay time'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['wait time'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['iterations'] = IntEntry(self, -1, min=0.0, chars=6)

		szdelaytime = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Delay Time before first loop:')
		szdelaytime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdelaytime.Add(self.widgets['loop delay time'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		szdelaytime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szwaittime = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait Time:')
		szwaittime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szwaittime.Add(self.widgets['wait time'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		szwaittime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sziterations = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Iterations:')
		sziterations.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sziterations.Add(self.widgets['iterations'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		# simluate target loop
		szsim = wx.GridBagSizer(5, 5)
		szsim.Add(szdelaytime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsim.Add(szwaittime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsim.Add(sziterations, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszsim.Add(szsim, 0, wx.ALIGN_CENTER)
		return sbszsim

	def createMoverChoiceSizer(self):
		szmover = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mover:')
		self.widgets['mover'] = Choice(self, -1, choices=['presets manager','navigator'])
		szmover.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmover.Add(self.widgets['mover'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		return szmover

	def createMovePrecisionSizer(self):
		szmoveprec = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Navigator Target Tolerance (m):')
		self.widgets['move precision'] = FloatEntry(self, -1, min=0.0, chars=6)
		szmoveprec.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmoveprec.Add(self.widgets['move precision'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Navigator Acceptable Tolerance (m):')
		self.widgets['accept precision'] = FloatEntry(self, -1, min=0.0, chars=6)
		szmoveprec.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmoveprec.Add(self.widgets['accept precision'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.widgets['final image shift'] = wx.CheckBox(self, -1, 'Final Image Shift')
		szmoveprec.Add(self.widgets['final image shift'], (2,0), (1,2))
		return szmoveprec

	def createProcessTargetTypeSizer(self):
		sz_target_type = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Process')
		sz_target_type.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['process target type'] = Choice(self, -1, choices=leginon.targethandler.target_types)
		sz_target_type.Add(self.widgets['process target type'], (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'targets')
		sz_target_type.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz_target_type

	def createImageOptionsSizer(self):
		# set widgets
		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
		self.widgets['save integer'] = wx.CheckBox(self, -1, 'Float->Integer')
		self.widgets['display image'] = wx.CheckBox(self, -1, 'Display image')
		self.widgets['save image'] = wx.CheckBox(self, -1, 'Save image to database')
		# settings sizer
		sz_save = wx.GridBagSizer(0, 0)
		sz_save.Add(self.widgets['save image'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_save.Add(self.widgets['save integer'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz_save.Add(self.widgets['correct image'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz_save.Add(self.widgets['display image'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz_save
 
	def createTiltSizer(self):
		# set widgets
		self.widgets['use parent tilt'] = wx.CheckBox(self, -1, 'Tilt the stage like its parent image')
		self.widgets['adjust time by tilt'] = wx.CheckBox(self, -1, 'Adjust exposure time by tilt')
		self.widgets['reset tilt'] = wx.CheckBox(self, -1, 'Reset stage when done')
		if not hide_incomplete:
			self.widgets['correct image shift coma'] = wx.CheckBox(self, -1, 'Correct image shift coma effect')
		# set sizers
		sz_tilt = wx.GridBagSizer(0, 0)
		sz_tilt.Add(self.widgets['adjust time by tilt'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz_tilt.Add(self.widgets['use parent tilt'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz_tilt.Add(self.widgets['reset tilt'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		if not hide_incomplete:
			sz_tilt.Add(self.widgets['correct image shift coma'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz_tilt

	def createClearBeamPathSizer(self):
		#set widget
		self.widgets['clear beam path'] = wx.CheckBox(self, -1, 'Verify opened gun valve before acquiring')
		# mskr sizer
		sz_beampath = wx.GridBagSizer(0, 0)
		sz_beampath.Add(self.widgets['clear beam path'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz_beampath

	def createSetApertureSizer(self):
		self.widgets['set aperture'] = wx.CheckBox(self, -1, 'set these apertures while imaging')
		self.widgets['objective aperture'] = Entry(self, -1)
		self.widgets['c2 aperture'] = Entry(self, -1)
		# mskr sizer
		sz_aps = wx.GridBagSizer(0, 0)
		sz_aps.Add(self.widgets['set aperture'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label1 = wx.StaticText(self, -1, 'condenser:')
		sz_aps.Add(label1, (1, 0), (1, 1),wx.ALIGN_RIGHT)
		sz_aps.Add(self.widgets['c2 aperture'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label2 = wx.StaticText(self, -1, 'objective:')
		sz_aps.Add(label2, (2, 0), (1, 1),wx.ALIGN_RIGHT)
		sz_aps.Add(self.widgets['objective aperture'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz_aps

	def addSettings(self):
		# move type
		szmovetype = self.createMoveTypeSizer()
		# pasue time
		szpausetime = self.createPauseTimeSizer()
		# extra pause for first image
		szfirstpause = self.createFirstPauseTimeSizer()

		sz_save = self.createImageOptionsSizer()
		sz_tilt = self.createTiltSizer()
		sz_beampath = self.createClearBeamPathSizer()
		sz_obj_ap = self.createSetApertureSizer()
		sbszsim = self.createSimulatedTargetLoopBoxSizer()

		# misc
		sz_misc = self.createMiscSizer()

		# preset order
		self.setPresetOrderWidget()
		# extra pause between presets
		szpausebtime = self.createPauseBetweenTimeSizer()
		# mover
		szmover = self.createMoverChoiceSizer()
		szmoveprec = self.createMovePrecisionSizer()
		sz_target_type = self.createProcessTargetTypeSizer()

		# 3rd column
		szright = wx.GridBagSizer(3, 3)
		szright.Add(self.widgets['preset order'], (0, 0), (4, 1), wx.ALIGN_CENTER)
		szright.Add(szpausebtime, (4,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szright.Add(szmover, (5,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szright.Add(szmoveprec, (6,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szright.Add(sz_target_type, (7,0), (1,1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		# left with 2 columns
		sz.Add(szmovetype, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szfirstpause, (2, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		# left with 1 column
		sz.Add(sz_save, (3,0), (2,1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_tilt, (5,0), (2,1), wx.ALIGN_TOP)
		sz.Add(sz_beampath, (7,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_obj_ap, (8,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sbszsim, (9,0), (2,1), wx.ALIGN_BOTTOM)
		# middle with 1 column
		sz.Add(sz_misc, (3,1), (8,1), wx.ALIGN_TOP)
		# right
		sz.Add(szright, (0,2),(11,1), wx.ALIGN_TOP)
		return sz

	def onEnterPassword(self, evt):
		dialog = wx.PasswordEntryDialog(self, 'Enter Password:')
		dialog.ShowModal()
		self.node.setEmailPassword(dialog.GetValue())
		dialog.Destroy()

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'acquisition'
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	settingsdialogclass = SettingsDialog
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Process')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PAUSE, 'pause', shortHelpString='Pause')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, 'stop_queue', shortHelpString='Abort Queue')
		# hide toggle queue timeout since it is old and confuses new user
		#self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EXTRACT, 'clock', shortHelpString='Toggle queue timeout')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET, 'simulatetarget', shortHelpString='Simulate Target')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP, 'simulatetargetloop', shortHelpString='Simulate Target Loop')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP_STOP, 'simulatetargetloopstop', shortHelpString='Stop Simulate Target Loop')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_BROWSE_IMAGES, 'imagebrowser', shortHelpString='Browse Images')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)

		self.addImagePanel()

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPauseTool,
											id=leginon.gui.wx.ToolBar.ID_PAUSE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopQueueTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT_QUEUE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetTool,
											id=leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetLoopTool,
											id=leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetLoopStopTool,
											id=leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onBrowseImagesTool, id=leginon.gui.wx.ToolBar.ID_BROWSE_IMAGES)
		#self.toolbar.Bind(wx.EVT_TOOL, self.onToggleQueueTimeout, id=leginon.gui.wx.ToolBar.ID_EXTRACT)

	def onToggleQueueTimeout(self, evt):
		self.node.toggleQueueTimeout()

	def onSimulateTargetTool(self, evt):
		threading.Thread(target=self.node.simulateTarget).start()

	def onSimulateTargetLoopTool(self, evt):
		threading.Thread(target=self.node.simulateTargetLoop).start()

	def onSimulateTargetLoopStopTool(self, evt):
		threading.Thread(target=self.node.simulateTargetLoopStop).start()

	def onSettingsTool(self, evt):
		dialog = self.settingsdialogclass(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
		self.node.paused_by_gui = False
		self.node.player.play()

	def onPauseTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
		self.node.paused_by_gui = True
		self.node.player.pause()

	def onStopTargetTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
		self.node.paused_by_gui = False
		self.node.player.stoptarget()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
		self.node.paused_by_gui = False
		self.node.player.stop()

	def onStopQueueTool(self, evt):
		number_of_targets = self.node.getQueueTargetListToDo()
		if number_of_targets:
			title = 'Abort all targets in Queue'
		else:
			title = 'Abort future targets in Queue'
		dialog = AbortQueueConfirmationDialog(self, title)
		result = dialog.ShowModal()
		dialog.Destroy()
		if result == wx.ID_OK:
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
			self.node.paused_by_gui = False
			self.node.player.stopqueue()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False) 
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, True)
		elif evt.state == 'stoptarget':
			# case for stop one target
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True) 
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)
		elif evt.state == 'stop':
			# case for stop one target list
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True) 
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, True)
		elif evt.state == 'stopqueue':
			# case for stop all target lists in queue
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True) 
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT_QUEUE, False)

	def onBrowseImagesTool(self, evt):
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(leginon.gui.wx.Icons.icon("imagebrowser"))
		frame = wx.Frame(None, -1, 'Image Browser')
		frame.node = self.node
		frame.SetIcon(icon)
		panel = ImageBrowserPanel(frame)
		frame.Fit()
		frame.Show()

class AbortQueueConfirmationDialog(leginon.gui.wx.Dialog.ConfirmationDialog):
	def addDescriptionSizers(self):
		number_of_targets = self.parent.node.getQueueTargetListToDo()
		if number_of_targets:
			msg = 'Are you sure you want to abort targets in %d parent images ?' % (number_of_targets)
		else:
			msg = 'No targetlist in queue now.\n Are you sure you want to abort future target list ?'
		sz_msg = wx.GridBagSizer(0, 0)
		label1 = wx.StaticText(self, -1, msg)
		sz_msg.Add(label1, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		self.mainsz.Add(sz_msg, (0,0),(1,1))


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			panel = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

