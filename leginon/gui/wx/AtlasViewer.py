# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/AtlasViewer.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-01-28 01:07:42 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.Node
import gui.wx.ToolBar

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Print Tile List')
		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onPrintTileList,
											id=gui.wx.ToolBar.ID_PLAY)

	def onPrintTileList(self, evt):
		self.node.getMosaicTileData()

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

