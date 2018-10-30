import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		sb = wx.StaticBox(self, -1, 'Reference Target')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.sz = wx.GridBagSizer(5, 5)

		self.insertSizersToSZ()
		sbsz.Add(self.sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

	def insertSizersToSZ(self):
		position = self.createBypassCheckBox((0, 0))
		position = self.createSubTitleSizer((position[0],0),'Moving to Target')
		position = self.createMoveTypeChoice((position[0],0))
		position = self.createMoverChoiceSizer((position[0],0))
		position = self.createMovePrecisionSizer((position[0],0))
		position = self.createSubTitleSizer((position[0],0),'Timing')
		# seperater
		position = self.createPauseTimeEntry((position[0],0))
		position = self.createIntervalEntry((position[0],0))
		position = self.createReturnSettleTimeEntry((position[0],0))

	def createIntervalEntry(self, position):
		'''
		Defined in subclasses
		'''
		return position

	def createMoveTypeChoice(self, start_position):
		move_types = self.node.calibration_clients.keys()
		move_types.sort()
		self.widgets['move type'] = Choice(self, -1, choices=move_types)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to the reference target'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szmovetype, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createMoverChoiceSizer(self, start_position):
		szmover = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mover:')
		self.widgets['mover'] = Choice(self, -1, choices=['presets manager','navigator'])
		szmover.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmover.Add(self.widgets['mover'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		totalsize = (2,1)
		self.sz.Add(szmover, start_position, totalsize, wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+totalsize[0],start_position[1]+totalsize[1]

	def createMovePrecisionSizer(self, start_position):
		szmoveprec = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Navigator Target Tolerance (m):')
		self.widgets['move precision'] = FloatEntry(self, -1, min=0.0, chars=6)
		szmoveprec.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmoveprec.Add(self.widgets['move precision'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Navigator Acceptable Tolerance (m):')
		self.widgets['accept precision'] = FloatEntry(self, -1, min=0.0, chars=6)
		szmoveprec.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmoveprec.Add(self.widgets['accept precision'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		totalsize = (2,1)
		self.sz.Add(szmoveprec, start_position, totalsize, wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+totalsize[0],start_position[1]+totalsize[1]

	def createSubTitleSizer(self, start_position,title):
		szblank = wx.GridBagSizer(5, 5)
		szblank.Add(wx.StaticText(self, -1, '________%s__________' % (title)), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		totalsize = (1,1)
		self.sz.Add(szblank, start_position, totalsize, wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+totalsize[0],start_position[1]+totalsize[1]

	def createPauseTimeEntry(self, start_position):
		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before performing request at the reference target'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createReturnSettleTimeEntry(self, start_position):
		self.widgets['return settle time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['return settle time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds to settle the stage after returning to the starting position'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createBypassCheckBox(self,start_position):
		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Conditioner')
		self.sz.Add(self.widgets['bypass'], start_position, (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		return start_position[0]+1,start_position[1]+1

class ReferencePanel(leginon.gui.wx.Node.Panel):
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Test')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire and save current position as reference')
		self.addImagePanel()

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTest,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=leginon.gui.wx.ToolBar.ID_ACQUIRE)

	def onSettingsTool(self, evt):
		dialog = self._SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)
	
	def onTest(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		threading.Thread(target=self.node.onTest).start()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.stop()

	def onAcquireTool(self, evt):
		threading.Thread(target=self.node.onMakeReference).start()
	
