import wx
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Camera
import gui.wx.Data
import gui.wx.Node
import wxImageViewer

class Panel(gui.wx.Node.Panel):
	icon = 'navigator'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pNavigator' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings
		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.ALL)

		sz = wx.GridBagSizer(5, 5)
		label0 = wx.StaticText(self, -1, 'Wait')
		self.fewait = FloatEntry(self, -1, min=0.0, allownone=False, chars=4,
															value='2.5', name='feWait')
		label1 = wx.StaticText(self, -1, 'seconds and use')
		self.cmovetype = wx.Choice(self, -1, name='cMoveType')
		label2 = wx.StaticText(self, -1, 'to move to target')

		sz.Add(label0, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.fewait, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		sz.Add(label1, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.cmovetype, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(label2, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		self.cbcheckerror = wx.CheckBox(self, -1, 'Check calibration error',
																			name='cbCheckError')
		self.cbcompletestate = wx.CheckBox(self, -1, 'Set complete state',
																			name='cbCompleteState')
		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		self.szsettings.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		self.szsettings.Add(self.cbcheckerror, (1, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbcompletestate, (2, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cpcamconfig, (3, 0), (1, 1),
												wx.ALIGN_CENTER)

		# controls
		self.szlocations = self._getStaticBoxSizer('Stage Locations',
																								(2, 0), (1, 1),
																			wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		stposition = {}
		self.stposition = {}
		axes = ['x', 'y', 'z', 'a', 'b']
		for i, a in enumerate(axes):
			stposition[a] = wx.StaticText(self, -1, a)
			self.stposition[a] = wx.StaticText(self, -1, '-')
			self.szlocations.Add(stposition[a], (0, i + 1), (1, 1), wx.ALIGN_CENTER)
			self.szlocations.Add(self.stposition[a], (1, i + 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label0 = wx.StaticText(self, -1, 'Position:')
		label1 = wx.StaticText(self, -1, 'Comment:')
		self.stcomment = wx.StaticText(self, -1, '(No location selected)')
		label2 = wx.StaticText(self, -1, 'Locations')
		self.lblocations = wx.ListBox(self, -1, style=wx.LB_SINGLE)
		self.bnew = wx.Button(self, -1, 'New...')
		self.btoscope = wx.Button(self, -1, 'To scope')
		self.bfromscope = wx.Button(self, -1, 'From scope')
		self.bremove = wx.Button(self, -1, 'Remove')
		self.btoscope.Enable(False)
		self.bfromscope.Enable(False)
		self.bremove.Enable(False)

		self.szlocations.Add(label0, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(label1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(self.stcomment, (2, 1), (1, 5),
													wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(label2, (3, 1), (1, 5), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(self.lblocations, (4, 1), (4, 5), wx.EXPAND)
		self.szlocations.Add(self.bnew, (4, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.btoscope, (5, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.bfromscope, (6, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.bremove, (7, 0), (1, 1), wx.ALIGN_CENTER)

		# image
		self.szimage = self._getStaticBoxSizer('Navigation', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.bacquire = wx.Button(self, -1, 'Acquire')
		self.imagepanel = wxImageViewer.ClickImagePanel(self, -1)
		self.szimage.Add(self.bacquire, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szimage.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szimage.AddGrowableCol(0)

		self.szmain.AddGrowableCol(1)
		self.szmain.AddGrowableRow(2)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def onNodeInitialized(self):
		movetypes = self.node.calclients.keys()
		if movetypes:
			self.cmovetype.AppendItems(movetypes)
			self.cmovetype.SetSelection(0)

		self.lblocations.AppendItems(self.node.getLocationNames())

		self.cpcamconfig.setSize(self.node.session)

		gui.wx.Data.setWindowFromDB(self.fewait)
		gui.wx.Data.setWindowFromDB(self.cmovetype)
		gui.wx.Data.setWindowFromDB(self.cbcheckerror)
		gui.wx.Data.setWindowFromDB(self.cbcompletestate)
		gui.wx.Data.setWindowFromDB(self.cpcamconfig)

		self.node.wait = self.fewait.GetValue()
		self.node.movetype = self.cmovetype.GetStringSelection()
		self.node.checkerror = self.cbcheckerror.GetValue()
		self.node.completestate = self.cbcompletestate.GetValue()
		self.node.camconfig = self.cpcamconfig.getConfiguration()

		gui.wx.Data.bindWindowToDB(self.fewait)
		gui.wx.Data.bindWindowToDB(self.cmovetype)
		gui.wx.Data.bindWindowToDB(self.cbcheckerror)
		gui.wx.Data.bindWindowToDB(self.cbcompletestate)
		gui.wx.Data.bindWindowToDB(self.cpcamconfig)

		self.Bind(EVT_ENTRY, self.onWaitEntry, self.fewait)
		self.Bind(wx.EVT_CHOICE, self.onMoveTypeChoice, self.cmovetype)
		self.Bind(wx.EVT_CHECKBOX, self.onErrorCheckCheck, self.cbcheckerror)
		self.Bind(wx.EVT_CHECKBOX, self.onCompleteStateCheck, self.cbcompletestate)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, self.onCamConfigChanged,
							self.cpcamconfig)
		self.Bind(wx.EVT_BUTTON, self.onAcquire, self.bacquire)
		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)
		self.Bind(wx.EVT_LISTBOX, self.onLocationSelected, self.lblocations)
		self.Bind(wxImageViewer.EVT_IMAGE_DOUBLE_CLICKED, self.onImageDoubleClicked,
							self.imagepanel)

	def onWaitEntry(self, evt):
		self.node.wait = evt.GetValue()

	def onMoveTypeChoice(self, evt):
		self.node.movetype = evt.GetString()

	def onErrorCheckCheck(self, evt):
		self.node.checkerror = evt.IsChecked()

	def onCompleteStateCheck(self, evt):
		self.node.completestate = evt.IsChecked()

	def onCamConfigChanged(self, evt):
		self.node.camconfig = evt.configuration

	def onAcquire(self, evt):
		self.node.acquireImage()

	def onNew(self, evt):
		dialog = NewLocationDialog(self)
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
		n = self.lblocation.GetSelection()
		name = self.lblocation.GetString(n)
		self.lblocations.Delete(n)
		# deselect?
		self.node.removeLocation(name)

	def onLocationSelected(self, evt):
		l = self.node.getLocation(evt.GetString())
		for a in ['x', 'y', 'z', 'a', 'b']:
			try:
				if l[a] is None:
					self.stposition[a].SetLabel('-')
				else:
					self.stposition[a].SetLabel(str(l[a]))
			except KeyError:
				self.stposition[a].SetLabel('-')
		if comment is None:
			comment = ''
		else:
			comment = l['comment']
		self.stcomment.SetLabel(comment)
		
		self.btoscope.Enable(True)
		self.bfromscope.Enable(True)
		self.bremove.Enable(True)

		self.szlocations.Layout()

	def onImageDoubleClicked(self, evt):
		# ...
		if self.node.shape is not None:
			self.node.navigate(evt.xy)

class NewLocationDialog(wx.Dialog):
	def __init__(self, parent):
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
		if not name or name in self.GetParent().node.getLocationNames():
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

