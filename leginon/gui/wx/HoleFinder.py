import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Rings
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate

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
	def __init__(self, parent, name):
		gui.wx.TargetFinder.Panel.__init__(self, parent, name) 

	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.targetcolors = {
			'acquisition': wx.GREEN,
			'focus': wx.BLUE,
			'All Blobs': wx.Color(0, 255, 255),
			'Lattice Blobs': wx.Color(255, 0, 255),
		}

		self.szdisplay = self._getStaticBoxSizer('Display', (2, 0), (1, 1),
																							wx.ALIGN_CENTER)
		order = [
			'Original',
			'Edge',
			'Template',
			'Threshold',
			'Blobs',
			'Lattice',
			'Final'
		]
		self.imagecheckboxes = [
			'Original',
			'Edge',
			'Template',
			'Threshold',
		]
		self.targetcheckboxes = [
			'Blobs',
			'Lattice',
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

		self.bsubmit = wx.Button(self, -1, 'Submit Targets')
		self.szbuttons.Add(self.bsubmit, (1, 0), (1, 1), wx.EXPAND)

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
		self.Bind(wx.EVT_BUTTON, self.onSubmitButton, self.bsubmit)

		for k in self.imagecheckboxes:
			self.Bind(wx.EVT_CHECKBOX, self.onDisplayImageCheckBox, self.rbdisplay[k])
		for k in self.targetcheckboxes:
			self.Bind(wx.EVT_CHECKBOX, self.onDisplayTargetsCheckBox,
								self.rbdisplay[k])

		self.Bind(wx.EVT_BUTTON, self.onOriginalSettingsButton,
							self.bhf['Original'])
		self.Bind(wx.EVT_BUTTON, self.onEdgeSettingsButton,
							self.bhf['Edge'])
		self.Bind(wx.EVT_BUTTON, self.onTemplateSettingsButton,
							self.bhf['Template'])
		self.Bind(wx.EVT_BUTTON, self.onThresholdSettingsButton,
							self.bhf['Threshold'])
		self.Bind(wx.EVT_BUTTON, self.onBlobsSettingsButton,
							self.bhf['Blobs'])
		self.Bind(wx.EVT_BUTTON, self.onLatticeSettingsButton,
							self.bhf['Lattice'])
		self.Bind(wx.EVT_BUTTON, self.onFinalSettingsButton,
							self.bhf['Final'])

	def onSubmitButton(self, evt):
		self.node.submit()

	def onSettingsButton(self, evt):
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

	def onEdgeSettingsButton(self, evt):
		dialog = EdgeSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onTemplateSettingsButton(self, evt):
		dialog = TemplateSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onThresholdSettingsButton(self, evt):
		dialog = ThresholdSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onBlobsSettingsButton(self, evt):
		dialog = BlobsSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onLatticeSettingsButton(self, evt):
		dialog = LatticeSettingsDialog(self)
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

class TemplateSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['template lpf'] = wx.CheckBox(self, -1, 'Use low pass filter')
		self.widgets['template lpf size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['template lpf sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		szlpf.Add(self.widgets['template lpf'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Size:')
		szlpf.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['template lpf size'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['template lpf sigma'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		self.widgets['template rings'] = gui.wx.Rings.Panel(self)
		self.widgets['template type'] = Choice(self, -1, choices=self.node.cortypes)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['template type'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sztemplate = wx.GridBagSizer(5, 5)
		sztemplate.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztemplate.Add(self.widgets['template rings'], (1, 0), (1, 1),
										wx.EXPAND)

		sb = wx.StaticBox(self, -1, 'Template Correlation')
		sbsztemplate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsztemplate.Add(sztemplate, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbsztemplate, sbszlpf, szbutton]

	def onTestButton(self, evt):
		self.node.correlateTemplate()

class EdgeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['edge lpf'] = wx.CheckBox(self, -1, 'Use low pass filter')
		self.widgets['edge lpf size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['edge lpf sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		szlpf.Add(self.widgets['edge lpf'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Size:')
		szlpf.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf size'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf sigma'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		self.widgets['edge'] = wx.CheckBox(self, -1, 'Use edge finding')
		self.widgets['edge type'] = Choice(self, -1, choices=self.node.filtertypes)
		self.widgets['edge log size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['edge log sigma'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['edge absolute'] = wx.CheckBox(self, -1,
																					'Take absolute value of edge values')
		self.widgets['edge threshold'] = FloatEntry(self, -1, chars=9)

		szedge = wx.GridBagSizer(5, 5)
		szedge.Add(self.widgets['edge'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Type:')
		szedge.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge type'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'LoG Size:')
		szedge.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge log size'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'LoG Sigma:')
		szedge.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge log sigma'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szedge.Add(self.widgets['edge absolute'], (4, 0), (1, 2),
								wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Threshold:')
		szedge.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge threshold'], (5, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szedge.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Edge Finding')
		sbszedge = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszedge.Add(szedge, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlpf, sbszedge, szbutton]

	def onTestButton(self, evt):
		self.node.findEdges()

class ThresholdSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['threshold'] = FloatEntry(self, -1, chars=9)

		szthreshold = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Threshold:')
		szthreshold.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szthreshold.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Threshold')
		sbszthreshold = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszthreshold.Add(szthreshold, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszthreshold, szbutton]

	def onTestButton(self, evt):
		self.node.threshold()

class BlobsSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['blobs border'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max size'] = IntEntry(self, -1, min=0, chars=6)

		szblobs = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Border:')
		szblobs.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs border'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. blobs:')
		szblobs.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs max'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. blob size:')
		szblobs.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs max size'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szblobs.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Blob finding')
		sbszblobs = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszblobs.Add(szblobs, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszblobs, szbutton]

	def onTestButton(self, evt):
		self.node.findBlobs()

class LatticeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['lattice spacing'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice tolerance'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice hole radius'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice zero thickness'] = FloatEntry(self, -1, chars=6)

		szlattice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Spacing:')
		szlattice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice spacing'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Tolerance:')
		szlattice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice tolerance'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Hole stats. radius:')
		szlattice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice hole radius'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Zero thickness:')
		szlattice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice zero thickness'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlattice.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Lattice fitting')
		sbszlattice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlattice.Add(szlattice, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlattice, szbutton]

	def onTestButton(self, evt):
		self.node.fitLattice()

class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus hole'] = Choice(self, -1, choices=self.node.focustypes)
		self.widgets['target template'] = wx.CheckBox(self, -1,
																									'Use target template')
		self.widgets['focus template'] = gui.wx.TargetTemplate.Panel(self,
																									'Focus Target Template')
		self.widgets['acquisition template'] = gui.wx.TargetTemplate.Panel(self,
																									'Acquisition Target Template')
		self.widgets['focus template thickness'] = wx.CheckBox(self, -1,
																								'Use focus template thickness')
		self.widgets['focus stats radius'] = IntEntry(self, -1, chars=6)
		self.widgets['focus min mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max stdev thickness'] = FloatEntry(self, -1, chars=6)

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Focus hole selection:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['focus hole'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Ice Thickness Threshold')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

		szftt = wx.GridBagSizer(5, 5)
		szftt.Add(self.widgets['focus template thickness'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stats. radius:')
		szftt.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus stats radius'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. mean thickness:')
		szftt.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus min mean thickness'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean thickness:')
		szftt.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus max mean thickness'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. std. thickness:')
		szftt.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus max stdev thickness'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szftt.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Focus Template Thickness')
		sbszftt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszftt.Add(szftt, 1, wx.EXPAND|wx.ALL, 5)

		sztt = wx.GridBagSizer(5, 5)
		sztt.Add(self.widgets['target template'], (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(sbszftt, (1, 0), (1, 1), wx.EXPAND)
		sztt.Add(self.widgets['focus template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER)
		sztt.Add(self.widgets['acquisition template'], (3, 0), (1, 1),
							wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Target Template')
		sbsztt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsztt.Add(sztt, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Analyze Ice')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bice, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onAnalyzeIceButton, self.bice)

		return [sbszice, sbsztt, szbutton]

	def onAnalyzeIceButton(self, evt):
		self.node.ice()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of picked holes')
		self.widgets['skip'] = wx.CheckBox(self, -1,
																							'Skip auto picking of holes')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['skip'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Hole finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Hole Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

