# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Robot.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-11 02:30:09 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

from gui.wx.Entry import FloatEntry
import gui.wx.Events
import gui.wx.Icons
import gui.wx.Node
import gui.wx.ToolBar
import Queue
import threading
import wx
import unique

class Panel(gui.wx.Node.Panel):
	#icon = 'robot'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play', shortHelpString='Start')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_EXTRACT,
													'extractgrid', shortHelpString='Extract')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GRID,
													'cleargrid', shortHelpString='Grid Cleared')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_EXTRACT, False)
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
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onGridTool, id=gui.wx.ToolBar.ID_GRID)
		self.toolbar.Bind(wx.EVT_TOOL, self.onExtractTool,
											id=gui.wx.ToolBar.ID_EXTRACT)
		self.Bind(gui.wx.Events.EVT_GRID_QUEUE_EMPTY, self.onGridQueueEmpty)
		self.Bind(gui.wx.Events.EVT_CLEAR_GRID, self.onClearGrid)
		self.Bind(gui.wx.Events.EVT_GRID_INSERTED, self.onGridInserted)
		self.Bind(gui.wx.Events.EVT_EXTRACTING_GRID, self.onExtractingGrid)

		self.Bind(wx.EVT_CHOICE, self.onTrayChoice, self.ctray)
		choices = self.node.getTrayLabels()
		if choices:
			self.ctray.AppendItems(choices)
			self.ctray.SetSelection(0)
			self.ctray.Enable(True)
			self.onTrayChoice()

		self.Bind(wx.EVT_BUTTON, self.onSelectAllButton, self.bselectall)
		self.Bind(wx.EVT_BUTTON, self.onSelectNoneButton, self.bselectnone)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.node.startevent.set()

	def onGridTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, False)
		self.node.gridcleared.set()

	def onExtractTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_EXTRACT, False)
		self.node.handleGridDataCollectionDone(None)

	def onGridQueueEmpty(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)

	def gridQueueEmpty(self):
		evt = gui.wx.Events.GridQueueEmptyEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onClearGrid(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, True)

	def clearGrid(self):
		evt = gui.wx.Events.ClearGridEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onGridInserted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_EXTRACT, True)

	def extractingGrid(self):
		evt = gui.wx.Events.ExtractingGridEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onExtractingGrid(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_EXTRACT, False)

	def gridInserted(self):
		evt = gui.wx.Events.GridInsertedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onSelectAllButton(self, evt):
		self.tray.selectAll()

	def onSelectNoneButton(self, evt):
		self.tray.selectNone()

	def getNextGrid(self):
		return self.tray.getNextGrid()

	def getGridQueueSize(self):
		return self.tray.getGridQueueSize()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['column pressure threshold'] = FloatEntry(self, -1, min=0.0,
																														chars=6)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Column pressure threshold:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['column pressure threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		sb = wx.StaticBox(self, -1, 'Robot')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

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

