# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetFinder.py,v $
# $Revision: 1.13 $
# $Name: not supported by cvs2svn $
# $Date: 2005-05-11 23:49:32 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')
		self.Bind(gui.wx.Events.EVT_SUBMIT_TARGETS, self.onSubmitTargets)
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE,
													'send_queue_out',
													shortHelpString='Submit Queued Targets')
		self.Bind(gui.wx.Events.EVT_TARGETS_SUBMITTED, self.onTargetsSubmitted)

		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE, False)

		self.initialize()
		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		gui.wx.Node.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitQueueTool,
											id=gui.wx.ToolBar.ID_SUBMIT_QUEUE)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, True)
		queue = self.node.settings['queue']
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE, queue)

	def targetsSubmitted(self):
		evt = gui.wx.Events.TargetsSubmittedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def initialize(self):
		pass

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def onSettingsTool(self, evt):
		dialog = self.SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.submitTargets()

	def onSubmitQueueTool(self, evt):
		self.node.publishQueue()

	def onSubmitTargets(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)

	def submitTargets(self):
		evt = gui.wx.Events.SubmitTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)


class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		#self.widgets['wait for done'] = wx.CheckBox(self, -1,
		#			'Wait for another node to process targets before marking them done')
		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of picked holes')
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

		sb = wx.StaticBox(self, -1, 'General Target Finder Settings ')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

	def onQueueCheckbox(self, evt):
		state = evt.IsChecked()
		parent = self.GetParent()
		parent.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE, state)
		evt.Skip()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

