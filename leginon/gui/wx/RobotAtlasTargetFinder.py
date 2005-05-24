# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/RobotAtlasTargetFinder.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2005-05-24 17:19:39 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import wx
import gui.wx.Events
import gui.wx.Node
import gui.wx.ToolBar

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Atlases')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.toolbar.Realize()

		self.atlaslistboxmap = {}
		self.listbox = wx.ListBox(self, -1)
		self.listbox.Enable(False)

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTargetTool('New', wx.GREEN, target=True)
		self.imagepanel.selectiontool.setDisplayed('New', True)
		self.imagepanel.addTargetTool('Submitted', wx.Color(255, 128, 0))
		self.imagepanel.selectiontool.setDisplayed('Submitted', True)
		self.imagepanel.addTargetTool('Processed', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('Processed', True)

		self.szmain.Add(self.listbox, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.Add(self.imagepanel, (0, 1), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(gui.wx.Events.EVT_GET_ATLASES_DONE, self.onGetAtlasesDone)
		self.Bind(gui.wx.Events.EVT_SET_ATLAS_DONE, self.onSetAtlasDone)
		self.Bind(gui.wx.Events.EVT_TARGETS_SUBMITTED, self.onTargetsSubmitted)

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def getAtlasesDone(self):
		self.GetEventHandler().AddPendingEvent(gui.wx.Events.GetAtlasesDoneEvent())

	def setAtlasDone(self):
		self.GetEventHandler().AddPendingEvent(gui.wx.Events.SetAtlasDoneEvent())

	def targetsSubmitted(self):
		evt = gui.wx.Events.TargetsSubmittedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onGetAtlasesDone(self, evt):
		self.listbox.Clear()
		labels = []
		self.atlaslistboxmap = {}
		for gridinsertion in self.node.grids.getGridInsertions():
			print gridinsertion
			print [type(i) for i in gridinsertion]
			gridname, gridid, number, insertion = gridinsertion
			if number is None:
				label = '%s <x%d>' % (gridname, insertion)
			else:
				label = '%s <P%d x%d>' % (gridname, number, insertion)
			labels.append(label)
			self.atlaslistboxmap[label] = (gridname, gridid, insertion)
		self.listbox.AppendItems(labels)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.listbox.Enable(True)

	def onSetAtlasDone(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.listbox.Enable(True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onGetAtlases,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTargets,
											id=gui.wx.ToolBar.ID_SUBMIT)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)
		self.listbox.Enable(True)
		self.Bind(wx.EVT_LISTBOX, self.onAtlasListBox)
		self.onGetAtlases()

	def onGetAtlases(self, evt=None):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.listbox.Enable(False)
		threading.Thread(target=self.node.getAtlases).start()

	def onAtlasListBox(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.listbox.Enable(False)
		s = evt.GetString()
		try:
			gridname, gridid, insertion = self.atlaslistboxmap[s]
			args = (gridid, insertion)
			threading.Thread(target=self.node.setAtlas, args=args).start()
		except KeyError:
			pass

	def onSubmitTargets(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		threading.Thread(target=self.node.submitTargets).start()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Atlas Viewer Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

