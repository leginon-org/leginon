# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/TargetFinder.py,v $
# $Revision: 1.19 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-11 23:48:05 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.ImagePanelTools

hide_incomplete = False

class Panel(leginon.gui.wx.Node.Panel):
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')
		self.Bind(leginon.gui.wx.Events.EVT_SUBMIT_TARGETS, self.onSubmitTargets)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE,
													'send_queue_out',
													shortHelpString='Submit Queued Targets')
		self.Bind(leginon.gui.wx.Events.EVT_TARGETS_SUBMITTED, self.onTargetsSubmitted)

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE, False)


		self.initialize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		leginon.gui.wx.Node.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=leginon.gui.wx.ToolBar.ID_SUBMIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitQueueTool,
											id=leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, True)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)
		queue = self.node.settings['queue']
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE, queue)
		self.imagepanel.imagevector = self.node.getTargetImageVector()
		self.imagepanel.beamradius = self.node.getTargetBeamRadius()

	def onSetImage(self, evt):
		super(Panel,self).onSetImage(evt)
		try:
			self.imagepanel.imagevector = self.node.getTargetImageVector()
			self.imagepanel.beamradius = self.node.getTargetBeamRadius()
		except AttributeError:
			# This function is called on initialization and self.node would be None
			pass

	def onImageSettings(self, evt):
		pass

	def targetsSubmitted(self):
		evt = leginon.gui.wx.Events.TargetsSubmittedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def initialize(self):
		pass

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def getTargets(self, typename):
		return self.imagepanel.getTargets(typename)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.submitTargets()

	def onSubmitQueueTool(self, evt):
		self.node.publishQueue()

	def onSubmitTargets(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)

	def submitTargets(self):
		evt = leginon.gui.wx.Events.SubmitTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)


class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'General Target Finder Settings ')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		if self.show_basic:
			sz = self.addBasicSettings()
		else:
			sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addBasicSettings(self):
		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of selected targets')
		self.widgets['queue'] = wx.CheckBox(self, -1,
																							'Queue up targets')
		self.Bind(wx.EVT_CHECKBOX, self.onQueueCheckbox, self.widgets['queue'])
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(self.widgets['wait for done'], (1, 0), (1, 1),
		#				wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['queue'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz

	def addSettings(self):
		#self.widgets['wait for done'] = wx.CheckBox(self, -1,
		#			'Wait for another node to process targets before marking them done')
		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of selected targets')
		self.widgets['queue'] = wx.CheckBox(self, -1,
																							'Queue up targets')
		self.widgets['queue drift'] = wx.CheckBox(self, -1, 'Declare drift when queue submitted')
		self.widgets['sort target'] = wx.CheckBox(self, -1, 'Sort targets by shortest path')
		self.widgets['allow append'] = wx.CheckBox(self, -1, 'Allow target finding on old images')
		self.Bind(wx.EVT_CHECKBOX, self.onQueueCheckbox, self.widgets['queue'])

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(self.widgets['wait for done'], (1, 0), (1, 1),
		#				wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['queue'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['queue drift'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['sort target'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		if not hide_incomplete:
			sz.Add(self.widgets['allow append'], (4, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)

		return sz

	def onQueueCheckbox(self, evt):
		state = evt.IsChecked()
		parent = self.panel
		parent.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE, state)
		evt.Skip()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Target Finder Test')
			panel = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

