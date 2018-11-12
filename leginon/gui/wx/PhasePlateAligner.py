import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.ReferenceCounter

class SettingsDialog(leginon.gui.wx.ReferenceCounter.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.ReferenceCounter.ScrolledSettings):
	def initialize(self):
		# Reference Target Box Sizer
		sb = wx.StaticBox(self, -1, 'Reference Target')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		position = self.createBypassCheckBox((0, 0))
		position = self.createSubTitleSizer((position[0],0),'Moving to Target')
		position = self.createMoveTypeChoice((position[0],0))
		position = self.createMoverChoiceSizer((position[0],0))
		position = self.createMovePrecisionSizer((position[0],0))
		# pause time after stage move to the position is not shown in gui
		# to avoid confusion.
		position = self.createSubTitleSizer((position[0],0),'Counting')
		position = self.createIntervalCountEntry((position[0],0))
		position = self.createReturnSettleTimeEntry((position[0],0))

		# Phase Plate Timing Box Sizer
		timingsb = wx.StaticBox(self, -1, 'Phase Plate Settling and Charging')
		timingsbsz = wx.StaticBoxSizer(timingsb, wx.VERTICAL)
		self.sz1 = wx.GridBagSizer(5, 5)
		position = self.createSettleTimeEntry((0,0))
		position = self.createChargeTimeEntry((position[0],0))
		position = self.createTiltChargeTimeEntry((position[0],0))

		# Phase Plate Position Box Sizer
		ppsb = wx.StaticBox(self, -1, 'Phase Plate Position')
		ppsbsz = wx.StaticBoxSizer(ppsb, wx.VERTICAL)

		ppsz = wx.GridBagSizer(5, 5)
		
		position = self.createPhasePlateNumberEntry((position[0],0), ppsz)
		position = self.createInitialPositionEntry((position[0],0), ppsz)
		position = self.createUpdatePositionEntry((position[0],0), ppsz)

		sbsz.Add(self.sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		timingsbsz.Add(self.sz1, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		ppsbsz.Add(ppsz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.onUpdatePositionButton, self.bupdate)

		return [sbsz,timingsbsz,ppsbsz]

	def createSettleTimeEntry(self, start_position):
		self.widgets['settle time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='3.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait for'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['settle time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds for phase plate patch to settle'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz1.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createChargeTimeEntry(self, start_position):
		self.widgets['charge time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='3.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Expose for'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['charge time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds to charge up carbon film phase plate'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz1.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createTiltChargeTimeEntry(self, start_position):
		self.widgets['tilt charge angle'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=5, value='0.01')
		self.widgets['tilt charge time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='3.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Beam tilt by +/-'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['tilt charge angle'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'radians and expose for'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['tilt charge time'], (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds to charge up beam tilt focusing position'), (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz1.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createPhasePlateNumberEntry(self, start_position, sz):
		self.widgets['phase plate number'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='1')
		szpp = wx.GridBagSizer(5, 5)
		szpp.Add(wx.StaticText(self, -1, 'Current Phase Plate Slot:'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpp.Add(self.widgets['phase plate number'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(szpp, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createInitialPositionEntry(self, start_position, sz):
		self.widgets['initial position'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='1')
		szpp = wx.GridBagSizer(5, 5)
		szpp.Add(wx.StaticText(self, -1, 'Current Phase Patch Position:'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpp.Add(self.widgets['initial position'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(szpp, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createUpdatePositionEntry(self, start_position, sz):
		self.bupdate = wx.Button(self, wx.ID_APPLY, '&Update')
		sz.Add(self.bupdate, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		return start_position[0]+1,start_position[1]+1

	def onUpdatePositionButton(self,evt):
		self.dialog.setNodeSettings()
		self.node.uiUpdatePosition()

class PhasePlateAlignerPanel(leginon.gui.wx.ReferenceCounter.ReferenceCounterPanel):
	def __init__(self, *args, **kwargs):
		super(PhasePlateAlignerPanel,self).__init__(*args, **kwargs)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MOSAIC, 'atlasmaker', shortHelpString='Patch State Mapping')

	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)

	def openSettingsDialog(self):
		'''
		Called from Leginon main to force this settings to open.
		'''
		self.onSettingsTool(None)

	def onNodeInitialized(self):
		super(PhasePlateAlignerPanel,self).onNodeInitialized()
		self.toolbar.Bind(wx.EVT_TOOL, self.onPatchStateSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_MOSAIC)

	def onPatchStateSettingsTool(self, evt):
		dialog = PatchStateSettingsDialog(self)
		dialog.ShowModal()
		#if dialog.ShowModal() == wx.ID_OK:
		#		self.node.uiSetSettings()
		dialog.Destroy()

class PatchStateSettingsDialog(leginon.gui.wx.Settings.Dialog):

	def onSet(self,evt):
		rasterpatchs = self.scr_dialog.getPatchGridValues()
		args = (rasterpatchs,)
		t = threading.Thread(target=self.node.guiSetPatchStates,args=args)
		t.start()
		super(PatchStateSettingsDialog,self).onSet(evt)

	def initialize(self):
		self.scr_dialog = PatchStateScrolledSettings(self,self.scrsize,False)
		return self.scr_dialog

class PatchStateScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		szpp = self.addPhasePlateNumber()
		gridformat = self.node.getGridFormat()
		szedit = self.addPatchGrid(gridformat)

		szbutton = wx.GridBagSizer(7, 7)
		self.bclear = wx.Button(self, -1, 'Clear')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.ball = wx.Button(self, -1, 'All')
		szbutton.Add(self.ball, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onAllButton, self.ball)
		# settings sizer
		sz = wx.GridBagSizer(5, 10)
		sz.Add(szpp, (0, 0), (1, 10))
		sz.Add(szedit, (1, 0), (10, 10))
		sz.Add(szbutton, (11, 0), (1, 2))
		return [sz]

	def onAllButton(self, evt):
		self.dialog.setNodeSettings()
		args = (True,)
		mythread = threading.Thread(target=self.node.setAllPatchStates,args=args)
		mythread.start()
		# wait for thread to finish before setting values
		mythread.join()
		self.setPatchGridValues()
		
	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		args = (False,)
		t = threading.Thread(target=self.node.setAllPatchStates,args=args)
		t.start()
		# wait for thread to finish before setting values
		t.join()
		self.setPatchGridValues()

	def addPhasePlateNumber(self):
		pp_number = self.node.guiGetPhasePlateNumber()
		text = ' %d' % (pp_number,)
		label = wx.StaticText(self, -1, 'Phase Plate Slot')
		self.labvalue = wx.StaticText(self, -1, text)
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label, (0,0), (1,1))
		sz.Add(self.labvalue, (0,1), (1,1))
		return sz

	def addPatchGrid(self,gridformat):
		'''
		PatchGrid is an editable wx.grid.Grid displaying the patchs
		registered at each gridformat raster cell.
		'''
		import wx.grid
		self.grid = wx.grid.Grid(self, -1)
		self.grid.SetDefaultColSize(40)
		self.grid.CreateGrid(gridformat['rows'], gridformat['cols'])

		attr = wx.grid.GridCellAttr()
		attr.SetEditor(wx.grid.GridCellBoolEditor())
		attr.SetRenderer(wx.grid.GridCellBoolRenderer())
		for c in range(gridformat['cols']):
			self.grid.SetColAttr(c, attr)

		try:
			# only available for newer wxpython
			self.grid.HideColLabels()
		except:
			pass
		self.setPatchGridValues()

		return self.grid

	def setPatchGridValues(self):
		'''
		Set values in the patchgrid based on current node values.
		'''
		# clear the grid first so that those are now blank
		# would not left with the old value
		self.grid.ClearGrid()
		patchregister = self.node.guiGetPatchStates()
		for key in patchregister:
			r = key[0]
			c = key[1]
			self.grid.SetCellValue(r,c,patchregister[key])
		self.grid.ForceRefresh()

	def getPatchGridValues(self):
		cols = self.grid.GetNumberCols()
		rows = self.grid.GetNumberRows()
		patchregister = {}
		for c in range(cols):
			for r in range(rows):
				patchregister[(r,c)] = self.grid.GetCellValue(r,c)
		return patchregister

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Section Target Finder Test')
			dialog = PhasePlateAlignerPanel(frame)
			frame.node = self
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

