import threading
import wx
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Camera
from gui.wx.Choice import Choice
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar

LocationsEventType = wx.NewEventType()

EVT_LOCATIONS = wx.PyEventBinder(LocationsEventType)

class LocationsEvent(wx.PyCommandEvent):
	def __init__(self, source, locations):
		wx.PyCommandEvent.__init__(self, LocationsEventType, source.GetId())
		self.SetEventObject(source)
		self.locations = locations

class Panel(gui.wx.Node.Panel):
	icon = 'navigator'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STAGE_LOCATIONS,
													'stagelocations',
													shortHelpString='Stage Locations')
		# image
		self.imagepanel = gui.wx.ImageViewer.ClickImagePanel(self, -1)

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(EVT_LOCATIONS, self.onLocations)

	def onNodeInitialized(self):
		self.locationsdialog = StageLocationsDialog(self.GetParent(), self.node)

		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStageLocationsTool,
											id=gui.wx.ToolBar.ID_STAGE_LOCATIONS)
		self.Bind(gui.wx.ImageViewer.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)

	def onSetImage(self, evt):
		self.imagepanel.setImage(evt.image)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def _acquisitionEnable(self, enable):
		self.toolbar.Enable(enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage).start()

	def onStageLocationsTool(self, evt):
		self.locationsdialog.ShowModal()

	def onImageClicked(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

	def onLocations(self, evt):
		self.locationsdialog.setLocations(evt.locations)

	def locationsEvent(self, locations):
		evt = LocationsEvent(self, locations)
		self.GetEventHandler().AddPendingEvent(evt)

class StageLocationsDialog(wx.Dialog):
	def __init__(self, parent, node):
		self.node = node
		wx.Dialog.__init__(self, parent, -1, 'Stage Locations')

		self.sz = wx.GridBagSizer(5, 5)

		stposition = {}
		self.stposition = {}
		axes = ['x', 'y', 'z', 'a', 'b']
		for i, a in enumerate(axes):
			stposition[a] = wx.StaticText(self, -1, a)
			self.stposition[a] = wx.StaticText(self, -1, '-')
			self.sz.Add(stposition[a], (0, i + 1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.stposition[a], (1, i + 1), (1, 1), wx.ALIGN_CENTER)

		label0 = wx.StaticText(self, -1, 'Position:')
		label1 = wx.StaticText(self, -1, 'Comment:')
		self.stcomment = wx.StaticText(self, -1, '(No location selected)')
		label2 = wx.StaticText(self, -1, 'Locations')
		choices = self.node.getLocationNames()
		self.lblocations = wx.ListBox(self, -1, choices=choices, style=wx.LB_SINGLE)
		self.bnew = wx.Button(self, -1, 'New...')
		self.btoscope = wx.Button(self, -1, 'To scope')
		self.bfromscope = wx.Button(self, -1, 'From scope')
		self.bremove = wx.Button(self, -1, 'Remove')
		self.btoscope.Enable(False)
		self.bfromscope.Enable(False)
		self.bremove.Enable(False)

		self.sz.Add(label0, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(label1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.stcomment, (2, 1), (1, 5),
													wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(label2, (3, 1), (1, 5), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.lblocations, (4, 1), (1, 5), wx.EXPAND)

		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(self.bnew, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.btoscope, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bfromscope, (2, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bremove, (3, 0), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add(szbuttons, (4, 0), (1, 1),
								wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		self.sz.AddGrowableCol(1)
		self.sz.AddGrowableCol(2)
		self.sz.AddGrowableCol(3)
		self.sz.AddGrowableCol(4)
		self.sz.AddGrowableCol(5)
		self.sz.AddGrowableRow(4)

		szdialog = wx.GridBagSizer(5, 5)
		szdialog.Add(self.sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(szdialog)

		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)
		self.Bind(wx.EVT_LISTBOX, self.onLocationSelected, self.lblocations)

	def onNew(self, evt):
		dialog = NewLocationDialog(self, self.node)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.fromScope(dialog.name, dialog.comment, dialog.xyonly)
		dialog.Destroy()

	def onToScope(self, evt):
		name = self.lblocations.GetStringSelection()
		self.node.toScope(name)

	def onFromScope(self, evt):
		name = self.lblocations.GetStringSelection()
		self.node.fromScope(name)

	def onRemove(self, evt):
		n = self.lblocations.GetSelection()
		if n < 0:
			return
		name = self.lblocations.GetString(n)
		self.lblocations.Delete(n)
		self.node.removeLocation(name)

	def _setLocation(self, l):
		for a in ['x', 'y', 'z', 'a', 'b']:
			if l is None:
				self.stposition[a].SetLabel('-')
			else:
				try:
					if l[a] is None:
						self.stposition[a].SetLabel('-')
					else:
						self.stposition[a].SetLabel(str(l[a]))
				except KeyError:
					self.stposition[a].SetLabel('-')

		if l is None:
			comment = '(No location selected)'
		elif l['comment'] is None:
			comment = ''
		else:
			comment = l['comment']
		self.stcomment.SetLabel(comment)

		if l is None:
			enable = False
		else:
			enable = True
		self.btoscope.Enable(enable)
		self.bfromscope.Enable(enable)
		self.bremove.Enable(enable)

		self.sz.Layout()
		self.Fit()

	def onLocationSelected(self, evt):
		if evt.IsSelection():
			location = self.node.getLocation(evt.GetString())
		else:
			location = None
		self._setLocation(location)

	def setLocations(self, locations):
		string = self.lblocations.GetStringSelection()
		self.lblocations.Clear()
		self.lblocations.AppendItems(locations)
		if self.lblocations.FindString(string) == wx.NOT_FOUND:
			self._setLocation(None)
		else:
			location = self._setLocation(self.node.getLocation(string))
			self.lblocations.SetStringSelection(string)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		# move type
		movetypes = self.node.calclients.keys()
		self.widgets['move type'] = Choice(self, -1, choices=movetypes)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to target'),
										(0, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# misc. checkboxes
		self.widgets['check calibration'] = wx.CheckBox(self, -1,
																										'Check calibration error')
		self.widgets['complete state'] = wx.CheckBox(self, -1,
																								'Set complete instrument state')
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)

		# settings sizer
		sz = wx.GridBagSizer(5, 10)
		sz.Add(szmovetype, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['check calibration'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['complete state'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (0, 1), (5, 1),
						wx.ALIGN_CENTER)
		sz.AddGrowableRow(4)

		sb = wx.StaticBox(self, -1, 'Navigation')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class NewLocationDialog(wx.Dialog):
	def __init__(self, parent, node):
		self.node = node
		wx.Dialog.__init__(self, parent, -1, 'New Location')

		stname = wx.StaticText(self, -1, 'Name:')
		stcomment = wx.StaticText(self, -1, 'Comment:')
		self.tcname = wx.TextCtrl(self, -1, '')
		self.tccomment = wx.TextCtrl(self, -1, '')
		self.cbxyonly = wx.CheckBox(self, -1, 'Save x and y only')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stname, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.tcname, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(stcomment, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.tccomment, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(self.cbxyonly, (2, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		bsave = wx.Button(self, wx.ID_OK, 'Save')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bsave, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		szmain.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onSave, bsave)

	def onSave(self, evt):
		name = self.tcname.GetValue()
		if not name or name in self.node.getLocationNames():
			dialog = wx.MessageDialog(self, 'Invalid location name', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.name = name
			self.comment = self.tccomment.GetValue()
			self.xyonly = self.cbxyonly.GetValue()
			evt.Skip()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Navigator Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

