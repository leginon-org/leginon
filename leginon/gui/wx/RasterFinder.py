import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar

AddTargetTypesEventType = wx.NewEventType()
AddTargetsEventType = wx.NewEventType()
SetTargetsEventType = wx.NewEventType()

EVT_ADD_TARGET_TYPES = wx.PyEventBinder(AddTargetTypesEventType)
EVT_ADD_TARGETS = wx.PyEventBinder(AddTargetsEventType)
EVT_SET_TARGETS = wx.PyEventBinder(SetTargetsEventType)

class AddTargetTypesEvent(wx.PyCommandEvent):
	def __init__(self, source, typenames):
		wx.PyCommandEvent.__init__(self, AddTargetTypesEventType, source.GetId())
		self.SetEventObject(source)
		self.typenames = typenames

class AddTargetsEvent(wx.PyCommandEvent):
	def __init__(self, source, typename, targets):
		wx.PyCommandEvent.__init__(self, AddTargetsEventType, source.GetId())
		self.SetEventObject(source)
		self.typename = typename
		self.targets = targets

class SetTargetsEvent(wx.PyCommandEvent):
	def __init__(self, source, typename, targets):
		wx.PyCommandEvent.__init__(self, SetTargetsEventType, source.GetId())
		self.SetEventObject(source)
		self.typename = typename
		self.targets = targets

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.targetcolors = {
			'acquisition': wx.GREEN,
			'focus': wx.BLUE,
			'Raster': wx.Color(0, 255, 255),
		}

		self.szdisplay = self._getStaticBoxSizer('Display', (2, 0), (1, 1),
																							wx.ALIGN_CENTER)
		order = [
			'Original',
			'Raster',
			'Final'
		]
		self.imagecheckboxes = [
			'Original',
		]
		self.targetcheckboxes = [
			'Raster',
			'Final'
		]
		self.rbdisplay = {}
		self.bhf = {}
		for i, n in enumerate(order):
			self.rbdisplay[n] = wx.CheckBox(self, -1, n)
			self.bhf[n] = wx.Button(self, -1, 'Settings...')
			self.szdisplay.Add(self.rbdisplay[n], (i, 0), (1, 1),
													wx.ALIGN_CENTER_VERTICAL)
			self.szdisplay.Add(self.bhf[n], (i, 1), (1, 1), wx.ALIGN_CENTER)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.szimage = self._getStaticBoxSizer('Target Image', (1, 1), (3, 1),
																						wx.EXPAND|wx.ALL)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szimage.AddGrowableRow(0)
		self.szimage.AddGrowableCol(0)
		self.szmain.AddGrowableRow(3)

		self.Bind(EVT_ADD_TARGET_TYPES, self.onAddTargetTypes)
		self.Bind(EVT_ADD_TARGETS, self.onAddTargets)
		self.Bind(EVT_SET_TARGETS, self.onSetTargets)
		self.Bind(gui.wx.TargetFinder.EVT_IMAGE_UPDATED, self.onImageUpdated)

	def onImageUpdated(self, evt):
		if self.rbdisplay[evt.name].GetValue():
			if evt.name in self.imagecheckboxes:
				self.imagepanel.setImage(evt.image)
			if evt.name in self.targetcheckboxes:
				if evt.targets is not None:
					self._setTargets(evt.targets)

	def imageUpdated(self, name, image, targets=None):
		evt = gui.wx.TargetFinder.ImageUpdatedEvent(self, name, image, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def onAddTargetTypes(self, evt):
		for typename in evt.typenames:
			try:
				color = self.targetcolors[typename]
			except KeyError:
				color = None
			self.imagepanel.addTargetType(typename, color)

	def onAddTargets(self, evt):
		for target in evt.targets:
			x, y = target
			self.imagepanel.addTarget(evt.typename, x, y)

	def onSetTargets(self, evt):
		self.imagepanel.clearTargets(evt.typename)
		self.onAddTargets(evt)

	def addTargetTypes(self, typenames):
		evt = AddTargetTypesEvent(self, typenames)
		self.GetEventHandler().AddPendingEvent(evt)

	def addTargets(self, typename, targets):
		evt = AddTargetsEvent(self, typename, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def setTargets(self, typename, targets):
		evt = SetTargetsEvent(self, typename, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def getTargets(self, typename):
		return self.imagepanel.getTargetTypeValue(typename)

	def onDisplayImageCheckBox(self, evt):
		key = evt.GetEventObject().GetLabel()
		for k in self.imagecheckboxes:
			if k != key:
				self.rbdisplay[k].SetValue(False)
		if evt.IsChecked():
			try:
				image = self.node.images[key]
			except KeyError:
				image = None
		else:
			image = None
		self.imagepanel.setImage(image)

	def _setTargets(self, targets):
		for typename, targetlist in targets.items():
			self.imagepanel.clearTargets(typename)
			for target in targetlist:
				x, y = target
				self.imagepanel.addTarget(typename, x, y)

	def onDisplayTargetsCheckBox(self, evt):
		key = evt.GetEventObject().GetLabel()
		try:
			targets = self.node.imagetargets[key]
		except KeyError:
			targets = {}
		if evt.IsChecked():
			self._setTargets(targets)
		else:
			for typename in targets:
				self.imagepanel.clearTargets(typename)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)

		for k in self.imagecheckboxes:
			self.Bind(wx.EVT_CHECKBOX, self.onDisplayImageCheckBox, self.rbdisplay[k])
		for k in self.targetcheckboxes:
			self.Bind(wx.EVT_CHECKBOX, self.onDisplayTargetsCheckBox,
								self.rbdisplay[k])

		self.Bind(wx.EVT_BUTTON, self.onOriginalSettingsButton,
							self.bhf['Original'])
		self.Bind(wx.EVT_BUTTON, self.onRasterSettingsButton,
							self.bhf['Raster'])
		self.Bind(wx.EVT_BUTTON, self.onFinalSettingsButton,
							self.bhf['Final'])

	def onSubmitTool(self, evt):
		self.node.submit()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onOriginalSettingsButton(self, evt):
		dialog = OriginalSettingsDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			filename = self.node.settings['image filename']
			if filename:
				self.node.readImage(filename)
		dialog.Destroy()

	def onRasterSettingsButton(self, evt):
		dialog = RasterSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onFinalSettingsButton(self, evt):
		dialog = FinalSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.bok.SetLabel('Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class RasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['raster spacing'] = IntEntry(self, -1, chars=4)
		self.widgets['raster limit'] = IntEntry(self, -1, chars=4)

		szraster = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Spacing:')
		szraster.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster spacing'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Limit:')
		szraster.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster limit'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szraster.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Raster')
		sbszraster = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszraster.Add(szraster, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszraster, szbutton]

	def onTestButton(self, evt):
		self.node.createRaster()

class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['ice box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice thickness'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['focus convolve template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['focus constant template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Constant Template')
		self.widgets['acquisition convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['acquisition convolve template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['acquisition constant template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Constant Template')

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Box size:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice box size'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Zero thickness:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Ice Analysis')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

		szft = wx.GridBagSizer(5, 5)
		szft.Add(self.widgets['focus convolve'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus convolve template'], (1, 0), (1, 1),
							wx.ALIGN_CENTER)
		szft.Add(self.widgets['focus constant template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER)
		szft.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Focus Targets')
		sbszft = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszft.Add(szft, 1, wx.EXPAND|wx.ALL, 5)

		szat = wx.GridBagSizer(5, 5)
		szat.Add(self.widgets['acquisition convolve'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		szat.Add(self.widgets['acquisition convolve template'], (1, 0), (1, 1),
							wx.ALIGN_CENTER)
		szat.Add(self.widgets['acquisition constant template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER)
		szat.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Acquisition Targets')
		sbszat = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszat.Add(szat, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Analyze Ice')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bice, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onAnalyzeIceButton, self.bice)

		return [sbszice, sbszft, sbszat, szbutton]

	def onAnalyzeIceButton(self, evt):
		self.node.ice()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['user check'] = wx.CheckBox(self, -1,
																'Allow for user verification of raster points')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Raster Points')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raster Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

