import wx
from gui.wx.Entry import FloatEntry
import gui.wx.Camera
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ImageViewer
import gui.wx.MessageLog

ImageUpdatedEventType = wx.NewEventType()
EVT_IMAGE_UPDATED = wx.PyEventBinder(ImageUpdatedEventType)
class ImageUpdatedEvent(wx.PyCommandEvent):
	def __init__(self, source, name, image, targets={}, stats={}):
		wx.PyCommandEvent.__init__(self, ImageUpdatedEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.image = image
		self.targets = targets
		self.stats = stats

LoopStartedEventType = wx.NewEventType()
EVT_LOOP_STARTED = wx.PyEventBinder(LoopStartedEventType)
class LoopStartedEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, LoopStartedEventType, source.GetId())
		self.SetEventObject(source)

LoopStoppedEventType = wx.NewEventType()
EVT_LOOP_STOPPED = wx.PyEventBinder(LoopStoppedEventType)
class LoopStoppedEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, LoopStoppedEventType, source.GetId())
		self.SetEventObject(source)

class Panel(gui.wx.Node.Panel):
	icon = 'manualacquisition'
	imageclass = gui.wx.ImageViewer.ImagePanel
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.initialize()

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def initialize(self):
		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.messagelog = gui.wx.MessageLog.MessageLog(self)
		self.szmain.Add(self.messagelog, (0, 0), (1, 2), wx.EXPAND|wx.ALL, 3)

		# settings

		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.bgrid = wx.Button(self, -1, 'Grid...')
		self.bgrid.Enable(False)
		self.bacquire = wx.Button(self, -1, 'Acquire')
		self.bcontinuous = wx.Button(self, -1, 'Continuous')

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.Add(self.bsettings, (0, 0), (1, 1), wx.EXPAND)
		self.szbuttons.Add(self.bgrid, (1, 0), (1, 1), wx.EXPAND)
		self.szbuttons.Add(self.bacquire, (2, 0), (1, 1), wx.EXPAND)
		self.szbuttons.Add(self.bcontinuous, (3, 0), (1, 1), wx.EXPAND)
		self.szmain.Add(self.szbuttons, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(1)

		# image
		self.imagepanel = self.imageclass(self, -1)
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (5, 1),
																						wx.EXPAND|wx.ALL)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szimage.AddGrowableRow(0)
		self.szimage.AddGrowableCol(0)
		self.szmain.AddGrowableRow(5)

		self.Bind(EVT_IMAGE_UPDATED, self.onImageUpdated)
		self.Bind(EVT_LOOP_STARTED, self.onLoopStarted)
		self.Bind(EVT_LOOP_STOPPED, self.onLoopStopped)

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_BUTTON, self.onAcquireButton, self.bacquire)
		self.Bind(wx.EVT_BUTTON, self.onContinuousButton, self.bcontinuous)
		if self.node.projectdata.isConnected():
			self.Bind(wx.EVT_BUTTON, self.onGridButton, self.bgrid)
			self.bgrid.Enable(True)

	def onImageUpdated(self, evt):
		self.imagepanel.setImage(evt.image)

	def imageUpdated(self, name, image, targets=None):
		evt = ImageUpdatedEvent(self, name, image, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onGridButton(self, evt):
		dialog = GridDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.gridbox = dialog.gridbox
			self.node.grid = dialog.grid
		dialog.Destroy()

	def onAcquireButton(self, evt):
		self.node.acquireImage()

	def onLoopStopped(self, evt):
		self.bcontinuous.SetLabel('Continuous')
		self.bcontinuous.Enable(True)
		self.bacquire.Enable(True)

	def loopStopped(self):
		evt = LoopStoppedEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onLoopStarted(self, evt):
		self.bcontinuous.SetLabel('Stop')
		self.bcontinuous.Enable(True)

	def loopStarted(self):
		evt = LoopStartedEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onContinuousButton(self, evt):
		if self.bcontinuous.GetLabel() == 'Continuous':
			self.node.acquisitionLoopStart()
		elif self.bcontinuous.GetLabel() == 'Stop':
			self.node.acqusitionLoopStop()
		else:
			raise RuntimeError
		self.bacquire.Enable(False)
		self.bcontinuous.Enable(False)

class GridDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node
		wx.Dialog.__init__(self, parent, -1, 'Grid Selection')

		choices = ['None'] + self.node.getGridBoxes()
		self.cgridbox = wx.Choice(self, -1, choices=choices)
		self.cgrid = wx.Choice(self, -1)

		if self.node.gridbox is None:
			self.cgridbox.SetStringSelection('None')
		else:
			self.cgridbox.SetStringSelection(self.node.gridbox)
		self.onGridBoxChoice()
		if self.node.grid is None:
			self.cgrid.SetStringSelection('None')
		else:
			self.cgrid.SetStringSelection(self.node.grid)
		self.onGridChoice()

		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Grid box:')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgridbox, (0, 1), (1, 1), wx.EXPAND)
		label = wx.StaticText(self, -1, 'Grid:')
		szgrid.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgrid, (1, 1), (1, 1), wx.EXPAND)
		szgrid.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Grid')
		sbszgrid = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszgrid.Add(szgrid, 1, wx.EXPAND|wx.ALL, 5)

		self.bselect = wx.Button(self, wx.ID_OK, 'Select')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bselect, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszgrid, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_CHOICE, self.onGridBoxChoice, self.cgridbox)
		self.Bind(wx.EVT_CHOICE, self.onGridChoice, self.cgrid)

	def onGridBoxChoice(self, evt=None):
		if evt is None:
			gridbox = self.cgridbox.GetStringSelection()
		else:
			gridbox = evt.GetString()
		choices = ['None']
		if gridbox == 'None':
			self.gridbox = None
		else:
			choices += self.node.getGrids(gridbox)
			self.gridbox = gridbox

		self.cgrid.Clear()
		self.cgrid.AppendItems(choices)
		self.cgrid.SetSelection(0)
		self.onGridChoice()

	def onGridChoice(self, evt=None):
		if evt is None:
			grid = self.cgrid.GetStringSelection()
		else:
			grid = evt.GetString()
		if grid == 'None':
			self.grid = None
		else:
			self.grid = grid

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)
		self.widgets['screen up'] = wx.CheckBox(self, -1, 'Up before acquire')
		self.widgets['screen down'] = wx.CheckBox(self, -1, 'Down after acquired')
		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
		self.widgets['save image'] = wx.CheckBox(self, -1,
																							'Save image to the database')
		self.widgets['loop pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['low dose'] = wx.CheckBox(self, -1, 'Use low dose')
		self.widgets['low dose pause time'] = FloatEntry(self, -1, min=0.0, chars=4)

		szscreen = wx.GridBagSizer(5, 5)
		szscreen.Add(self.widgets['screen up'], (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		szscreen.Add(self.widgets['screen down'], (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Main Screen')
		sbszscreen = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszscreen.Add(szscreen, 1, wx.EXPAND|wx.ALL, 5)

		szlowdose = wx.GridBagSizer(5, 5)
		szlowdose.Add(self.widgets['low dose'], (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Low dose pause')
		szlowdose.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlowdose.Add(self.widgets['low dose pause time'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		szlowdose.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlowdose.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Dose')
		sbszlowdose = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlowdose.Add(szlowdose, 1, wx.EXPAND|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['camera settings'], (0, 0), (1, 3), wx.EXPAND)
		sz.Add(self.widgets['correct image'], (1, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save image'], (2, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Loop pause')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['loop pause time'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		sz.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz, sbszscreen, sbszlowdose]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Manual Acquisition Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

