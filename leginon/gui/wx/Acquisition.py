import wx
import wx.lib.masked
import wx.lib.scrolledpanel
import gui.wx.Data
import wxImageViewer
import gui.wx.Node
import gui.wx.Presets

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pAcquisition' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.stcount = wx.StaticText(self, -1, '')
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.stcount, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings
		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.ALL)

		label = wx.StaticText(self, -1, 'Wait')
		self.szsettings.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.ncwait = wx.lib.masked.NumCtrl(self, -1, 2.5,
																				integerWidth=2,
																				fractionWidth=1,
																				allowNone=False,
																				allowNegative=False,
																				name='ncWait')
		gui.wx.Data.bindWindowToDB(self.ncwait)
		self.szsettings.Add(self.ncwait, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'seconds and use')
		self.szsettings.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.cmovetype = wx.Choice(self, -1, name='cMoveType')
		gui.wx.Data.bindWindowToDB(self.cmovetype)
		self.szsettings.Add(self.cmovetype, (0, 3), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'to move to target')
		self.szsettings.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.presetorder = gui.wx.Presets.PresetOrder(self, -1, name='poPresetOrder')
		gui.wx.Data.bindWindowToDB(self.presetorder)
		self.szsettings.Add(self.presetorder, (1, 0), (1, 5),
													wx.ALIGN_CENTER|wx.EXPAND|wx.ALL)

		self.cbcorrectimage = wx.CheckBox(self, -1, 'Correct image',
																			name='cbCorrectImage')
		self.cbdisplayimage = wx.CheckBox(self, -1, 'Display image',
																			name='cbDisplayImage')
		self.cbsaveimage = wx.CheckBox(self, -1, 'Save image to database',
																		name='cbSaveImage')
		self.cbwaitimageprocess = wx.CheckBox(self, -1,
																				'Wait for a node to process the image',
																				name='cbWaitImageProcess')
		self.cbwaitrejects = wx.CheckBox(self, -1,
																			'Publish and wait for rejected targets',
																			name='cbWaitRejects')
		gui.wx.Data.bindWindowToDB(self.cbcorrectimage)
		gui.wx.Data.bindWindowToDB(self.cbdisplayimage)
		gui.wx.Data.bindWindowToDB(self.cbsaveimage)
		gui.wx.Data.bindWindowToDB(self.cbwaitimageprocess)
		gui.wx.Data.bindWindowToDB(self.cbwaitrejects)
		self.szsettings.Add(self.cbcorrectimage, (2, 0), (1, 5),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbdisplayimage, (3, 0), (1, 5),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbsaveimage, (4, 0), (1, 5),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbwaitimageprocess, (5, 0), (1, 5),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbwaitrejects, (6, 0), (1, 5),
												wx.ALIGN_CENTER_VERTICAL)

		szduplicate = wx.GridBagSizer(0, 0)
		self.cbduplicate = wx.CheckBox(self, -1, 'Duplicate targets with type:',
																		name='cbDuplicate')
		gui.wx.Data.bindWindowToDB(self.cbduplicate)
		self.cduplicatetype = wx.Choice(self, -1, name='cDuplicateType')
		gui.wx.Data.bindWindowToDB(self.cduplicatetype)
		szduplicate.Add(self.cbduplicate, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szduplicate.Add(self.cduplicatetype, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(szduplicate, (7, 0), (1, 5))

		# controls
		self.szcontrols = self._getStaticBoxSizer('Controls', (2, 0), (1, 1),
																wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)
		self.tbpause = wx.ToggleButton(self, -1, 'Pause')
		self.tbstop = wx.ToggleButton(self, -1, 'Stop')
		self.szcontrols.Add(self.tbpause, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szcontrols.Add(self.tbstop, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = wxImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.szmain.AddGrowableRow(2)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

		self.Bind(gui.wx.Presets.EVT_NEW_PRESET, self.onNewPreset)

		self.Bind(wx.lib.masked.EVT_NUM, self.onWaitNum, self.ncwait)
		self.Bind(wx.EVT_CHOICE, self.onMoveTypeChoice, self.cmovetype)
		self.Bind(gui.wx.Presets.EVT_PRESET_ORDER_CHANGED, self.onPresetOrderChanged,
							self.presetorder)
		self.Bind(wx.EVT_CHECKBOX, self.onCorrectCheckBox, self.cbcorrectimage)
		self.Bind(wx.EVT_CHECKBOX, self.onDisplayCheckBox, self.cbdisplayimage)
		self.Bind(wx.EVT_CHECKBOX, self.onSaveCheckBox, self.cbsaveimage)
		self.Bind(wx.EVT_CHECKBOX, self.onWaitCheckBox, self.cbwaitimageprocess)
		self.Bind(wx.EVT_CHECKBOX, self.onWaitRejectsCheckBox, self.cbwaitrejects)
		self.Bind(wx.EVT_CHECKBOX, self.onDuplicateCheckBox, self.cbduplicate)
		self.Bind(wx.EVT_CHOICE, self.onDuplicateTypeChoice, self.cduplicatetype)

		self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePause, self.tbpause)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleStop, self.tbstop)

		self.Bind(gui.wx.Node.EVT_SET_STATUS, self.onSetStatus)
		self.Bind(gui.wx.Node.EVT_SET_IMAGE, self.onSetImage)

	def initializeValues(self):
		movetypes = self.node.calclients.keys()
		if movetypes:
			self.cmovetype.AppendItems(movetypes)
			self.cmovetype.SetSelection(0)

		self.onNewPreset()
		# TODO: handle preset validation
		gui.wx.Data.setWindowFromDB(self.presetorder)
		gui.wx.Data.bindWindowToDB(self.presetorder)

		duplicatetypes = ['focus', 'acquisition']
		self.cduplicatetype.AppendItems(duplicatetypes)
		self.cduplicatetype.SetSelection(0)

		gui.wx.Data.setWindowFromDB(self.ncwait)
		gui.wx.Data.setWindowFromDB(self.cmovetype)
		gui.wx.Data.setWindowFromDB(self.presetorder)
		gui.wx.Data.setWindowFromDB(self.cbcorrectimage)
		gui.wx.Data.setWindowFromDB(self.cbdisplayimage)
		gui.wx.Data.setWindowFromDB(self.cbsaveimage)
		gui.wx.Data.setWindowFromDB(self.cbwaitimageprocess)
		gui.wx.Data.setWindowFromDB(self.cbwaitrejects)
		gui.wx.Data.setWindowFromDB(self.cbduplicate)
		gui.wx.Data.setWindowFromDB(self.cduplicatetype)

		self.node.wait = self.ncwait.GetValue()
		self.node.movetype = self.cmovetype.GetStringSelection()
		self.node.presetnames = self.presetorder.getValues()
		self.node.correct = self.cbcorrectimage.GetValue()
		self.node.display = self.cbdisplayimage.GetValue()
		self.node.save = self.cbsaveimage.GetValue()
		self.node.wait = self.cbwaitimageprocess.GetValue()
		self.node.waitrejects = self.cbwaitrejects.GetValue()
		self.node.duplicate = self.cbduplicate.GetValue()
		self.node.duplicatetype = self.cduplicatetype.GetStringSelection()

		self.szmain.Layout()

	def onNewPreset(self, evt=None):
		presets = self.node.presetsclient.getPresetNames()
		if presets:
			evt = gui.wx.Presets.PresetsChangedEvent(presets)
			self.presetorder.GetEventHandler().AddPendingEvent(evt)

	def onWaitNum(self, evt):
		if self.node is not None:
			self.node.wait = evt.GetValue()

	def onMoveTypeChoice(self, evt):
		self.node.movetype = evt.GetString()

	def onPresetOrderChanged(self, evt):
		if self.node is not None:
			self.node.presetnames = evt.presets

	def onCorrectCheckBox(self, evt):
		self.node.correct = evt.IsChecked()

	def onDisplayCheckBox(self, evt):
		self.node.display = evt.IsChecked()

	def onSaveCheckBox(self, evt):
		self.node.save = evt.IsChecked()

	def onWaitCheckBox(self, evt):
		self.node.wait = evt.IsChecked()

	def onWaitRejectsCheckBox(self, evt):
		self.node.waitrejects = evt.IsChecked()

	def onDuplicateCheckBox(self, evt):
		self.node.duplicate = evt.IsChecked()

	def onDuplicateTypeChoice(self, evt):
		self.node.duplicatetype = evt.GetString()

	def onTogglePause(self, evt):
		if evt.IsChecked():
			self.node.pause.clear()
		else:
			self.node.pause.set()

	def onToggleStop(self, evt):
		if evt.IsChecked():
			self.node.abort = True
		else:
			self.node.abort = False

	def onSetStatus(self, evt):
		self.ststatus.SetLabel(evt.status)

	def onSetImage(self, evt):
		self.imagepanel.setNumericImage(evt.image)

