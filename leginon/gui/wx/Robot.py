# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Robot.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-12-11 01:23:24 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import gui.wx.Events
import gui.wx.Icons
import gui.wx.Node
import gui.wx.ToolBar
import Queue
import threading
import wx
import unique

class NotificationPanel(gui.wx.Node.Panel):
	#icon = 'robot'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_INSERT,
													'node', shortHelpString='Insert')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_EXTRACT,
													'node', shortHelpString='Extract')
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_INSERT, False)
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_EXTRACT, False)
		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onInsertTool,
											id=gui.wx.ToolBar.ID_INSERT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onExtractTool,
											id=gui.wx.ToolBar.ID_EXTRACT)

	def onInsertTool(self, evt):
		threading.Thread(target=self.node.insert).start()

	def onExtractTool(self, evt):
		threading.Thread(target=self.node.extract).start()

class ControlPanel(gui.wx.Node.Panel):
	#icon = 'robot'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GRID,
													'grid', shortHelpString='Grid Cleared')
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, False)
		self.toolbar.Realize()

		self.ctray = wx.Choice(self, -1)
		self.ctray.Enable(False)
		sztray = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Grid tray')
		sztray.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztray.Add(self.ctray, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.tray = Tray(self, -1)

		self.bselectall = wx.Button(self, -1, 'Select All')
		self.bselectnone = wx.Button(self, -1, 'Select None')
		szselect = wx.GridBagSizer(5, 5)
		szselect.Add(self.bselectall, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szselect.Add(self.bselectnone, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(sztray, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(self.tray, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.szmain.Add(szselect, (2, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onTrayChoice(self, evt=None):
		if evt is None:
			traylabel = self.ctray.GetStringSelection()
		else:
			traylabel = evt.GetString()
		self.tray.setGrids(self.node.getGridLocations(traylabel))
		self.node.setTray(traylabel)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onGridTool, id=gui.wx.ToolBar.ID_GRID)

		self.Bind(wx.EVT_CHOICE, self.onTrayChoice, self.ctray)
		choices = self.node.getTrayLabels()
		if choices:
			self.ctray.AppendItems(choices)
			self.ctray.SetSelection(0)
			self.ctray.Enable(True)
			self.onTrayChoice()

		self.Bind(wx.EVT_BUTTON, self.onSelectAllButton, self.bselectall)
		self.Bind(wx.EVT_BUTTON, self.onSelectNoneButton, self.bselectnone)

	def onPlayTool(self, evt):
		threading.Thread(target=self.node.insert).start()

	def onGridTool(self, evt):
		threading.Thread(target=self.node.gridCleared).start()

	def onSelectAllButton(self, evt):
		self.tray.selectAll()

	def onSelectNoneButton(self, evt):
		self.tray.selectNone()

	def getNextGrid(self):
		return self.tray.getNextGrid()

	def getGridQueueSize(self):
		return self.tray.getGridQueueSize()

class Tray(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.traybitmap = gui.wx.Icons.icon('robotgridtray')
		self.gridbitmap = gui.wx.Icons.icon('realgrid')
		self.SetSize((self.traybitmap.GetWidth(), self.traybitmap.GetHeight()))
		self._buffer = wx.EmptyBitmap(*self.GetSize())
		self.brush = wx.Brush(wx.Panel.GetBackgroundColour(self)) 

		self.gridlist = []
		self.gridqueue = []

		self.updateDrawing()

		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(gui.wx.Events.EVT_UPDATE_DRAWING, self.onUpdateDrawing)

	def selectAll(self):
		grids = list(self.gridlist)
		grids.sort()
		self.gridqueue = grids
		self.updateDrawing()

	def selectNone(self):
		self.gridqueue = []
		self.updateDrawing()

	def getNextGrid(self):
		try:
			grid = self.gridqueue.pop(0)
			self.AddPendingEvent(gui.wx.Events.UpdateDrawingEvent())
		except IndexError:
			return None
		return grid

	def getGridQueueSize(self):
		return len(self.gridqueue)
		
	def onUpdateDrawing(self, evt):
		self.updateDrawing()

	def setGrids(self, grids):
		self.gridlist = grids
		self.gridqueue = []
		self.updateDrawing()

	def draw(self, dc):
		dc.SetBackground(self.brush)
		dc.Clear()
		offset = (42, 34)
		cellsize = (11, 11)
		cellspacing = (20, 20)
		n = (12, 8)
		dc.DrawBitmap(self.traybitmap, 0, 0, True)
		for grid in self.gridlist:
			i, j = divmod(grid - 1, n[1])
			i = n[0] - i - 1
			x = offset[0] + i*(cellsize[0] + cellspacing[0])
			y = offset[1] + j*(cellsize[1] + cellspacing[1])
			dc.DrawBitmap(self.gridbitmap, x, y, True)
		dc.SetFont(wx.SWISS_FONT)
		for index, grid in enumerate(self.gridqueue):
			i, j = divmod(grid - 1, n[1])
			i = n[0] - i - 1
			x = offset[0] + i*(cellsize[0] + cellspacing[0])
			y = offset[1] + j*(cellsize[1] + cellspacing[1])
			text = str(index + 1)
			xextent, yextent = dc.GetTextExtent(text)
			dc.DrawText(text, x + (cellsize[0] - xextent)/2, y + cellsize[1])

	def updateDrawing(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
		self.draw(dc)

	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self._buffer)

	def _clientToPosition(self, x, y):
		position = [x, y]
		offset = (33, 34)
		cellsize = (25, 11)
		cellspacing = (6, 20)
		n = (12, 8)
		for i in range(2):
			position[i] -= offset[i]
			if position[i] % (cellsize[i] + cellspacing[i]) > cellsize[i]:
				return None
			position[i] /= cellsize[i] + cellspacing[i]
			if position[i] < 0 or position[i] >= n[i]:
				return None
		return (n[0] - position[0] - 1)*n[1] + position[1] + 1

	def _addGrid(self, position):
		if position in self.gridlist and position not in self.gridqueue:
			self.gridqueue.append(position)
			self.updateDrawing()

	def onLeftUp(self, evt):
		position = self._clientToPosition(evt.m_x, evt.m_y)
		if position is not None:
			self._addGrid(position)

	def onRightUp(self, evt):
		position = self._clientToPosition(evt.m_x, evt.m_y)
		try:
			self.gridqueue.remove(position)
			self.updateDrawing()
		except ValueError:
			pass

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Robot Test')
			#panel = Panel(frame, 'Test')
			panel = Tray(frame, -1)
			sizer = wx.GridBagSizer(0, 0)
			sizer.Add(panel, (0, 0), (1, 1), wx.FIXED_MINSIZE)
			frame.SetSizerAndFit(sizer)
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

