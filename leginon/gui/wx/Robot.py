# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Robot.py,v $
# $Revision: 1.16 $
# $Name: not supported by cvs2svn $
# $Date: 2007-06-15 02:30:31 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

from gui.wx.Entry import FloatEntry
import gui.wx.Events
import gui.wx.Icons
import gui.wx.Node
import gui.wx.ToolBar
import gui.wx.Settings
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
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PAUSE,
													'pause', shortHelpString='Continue')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Trays')
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
			settings = self.node.getSettings()
			settings['grid tray'] = traylabel
			self.node.setSettings(settings)
		
		self.node.setTray(traylabel)
		gridlocations, gridids = self.node.getGridLocations(traylabel)
		gridlabels = self.node.getGridLabels(gridids)
		self.tray.setGrids(gridlocations,gridlabels)
		
	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onGridTool, id=gui.wx.ToolBar.ID_GRID)
		self.toolbar.Bind(wx.EVT_TOOL, self.onExtractTool,
											id=gui.wx.ToolBar.ID_EXTRACT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPauseTool, id=gui.wx.ToolBar.ID_PAUSE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTraysButton,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.Bind(gui.wx.Events.EVT_GRID_QUEUE_EMPTY, self.onGridQueueEmpty)
		self.Bind(gui.wx.Events.EVT_CLEAR_GRID, self.onClearGrid)
		self.Bind(gui.wx.Events.EVT_GRID_INSERTED, self.onGridInserted)
		self.Bind(gui.wx.Events.EVT_EXTRACTING_GRID, self.onExtractingGrid)

		self.Bind(wx.EVT_CHOICE, self.onTrayChoice, self.ctray)
		choices = self.node.getTrayLabels()
		self.setTraySelection(choices)

		self.Bind(wx.EVT_BUTTON, self.onSelectAllButton, self.bselectall)
		self.Bind(wx.EVT_BUTTON, self.onSelectNoneButton, self.bselectnone)
	
	def setTraySelection(self,choices):
		if choices:
			self.ctray.Clear()
			self.ctray.AppendItems(choices)
			if self.node.settings['grid tray']:
				n = self.ctray.FindString(self.node.settings['grid tray'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.ctray.SetSelection(0)
			else:
				self.ctray.SetSelection(n)
			self.ctray.Enable(True)
			self.onTrayChoice()
	

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.node.startevent.set()

	def onWaitForTrayChanged(self):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)

	def onPauseTool(self, evt):
		self.node.userContinue()

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
		
	def onRefreshTraysButton(self, evt):
		choices = self.node.getTrayLabels()
		self.setTraySelection(choices)		

	def getNextGrid(self):
		return self.tray.getNextGrid()

	def getGridQueueSize(self):
		return self.tray.getGridQueueSize()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Robot')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['column pressure threshold'] = FloatEntry(self, -1, min=0.0,
																														chars=6)
		self.widgets['default Z position'] = FloatEntry(self, -1, min=-2.0,
																														chars=8)
		self.widgets['simulate'] = wx.CheckBox(self, -1,
																	'Simulate Robot Insert/Extraction')
		self.widgets['turbo on'] = wx.CheckBox(self, -1,
																	'Turbo Pump Always On')
		self.widgets['grid clear wait'] = wx.CheckBox(self, -1,
																	'Wait for User Confirmation of Grid Clearing')
		self.widgets['pause'] = wx.CheckBox(self, -1,
																	'Pause before Extraction')

		szcolumnpressure = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Column pressure threshold:')
		szcolumnpressure.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcolumnpressure.Add(self.widgets['column pressure threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		szdefzposition = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Default Z Position:')
		szdefzposition.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdefzposition.Add(self.widgets['default Z position'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		szsimu = wx.GridBagSizer(5, 5)
		szsimu.Add(self.widgets['simulate'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		szpump = wx.GridBagSizer(5, 5)
		szpump.Add(self.widgets['turbo on'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		szgridclear = wx.GridBagSizer(5, 5)
		szgridclear.Add(self.widgets['grid clear wait'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		szpause = wx.GridBagSizer(5, 5)
		szpause.Add(self.widgets['pause'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz.Add(szcolumnpressure, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szdefzposition, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szsimu, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpump, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szgridclear, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpause, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

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
		self.showlabel = None

		self.updateDrawing()

		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
		self.Bind(wx.EVT_MIDDLE_DOWN, self.onMiddleDown)
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

	def setGrids(self, grids,gridlabels):
		self.gridlist = grids
		self.gridlabels = gridlabels
		self.gridqueue = []
		self.showlabel = None
		self.updateDrawing()

	def draw(self, dc):
		dc.SetBackground(self.brush)
		dc.Clear()
		font = wx.SWISS_FONT
		defaultpointsize = font.GetPointSize()
		offset = (42, 34)
		cellsize = (11, 11)
		cellspacing = (20, 20)
		n = (12, 8)
		dc.DrawBitmap(self.traybitmap, 0, 0, True)
		dc.SetTextForeground(wx.RED)
		dc.SetFont(font)
		for m, grid in enumerate(self.gridlist):
			i, j = divmod(grid - 1, n[1])
			i = n[0] - i - 1
			x = offset[0] + i*(cellsize[0] + cellspacing[0])
			y = offset[1] + j*(cellsize[1] + cellspacing[1])
			dc.DrawBitmap(self.gridbitmap, x, y, True)
			if grid == self.showlabel:
				#Display mid-mouse button selected grid label in red and smaller font
				label = self.gridlabels[m]
				xextent, yextent = dc.GetTextExtent(label)
				font.SetPointSize(defaultpointsize - 2)
				dc.SetFont(font)
				dc.DrawText(label, x + cellsize[0]-(xextent)/2,  y - cellsize[1])
		font.SetPointSize(defaultpointsize)
		dc.SetFont(font)
		dc.SetTextForeground(wx.BLACK)
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

	def onMiddleDown(self, evt):
		position = self._clientToPosition(evt.m_x, evt.m_y)
		try:
			self.showlabel = position
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

