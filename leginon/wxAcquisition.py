import wx
import wx.lib.masked
import wx.lib.scrolledpanel
import wxData
import wxImageViewer
import wxPresets

'''
CreateNodeEventType = wx.NewEventType()
EVT_CREATE_NODE = wx.PyEventBinder(CreateNodeEventType)

class CreateNodeEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(CreateNodeEventType)
		self.node = node
'''

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent, name):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1,
																								name='%s.pAcquisition' % name)

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
		self.ncwait = wx.lib.masked.NumCtrl(self, -1, 0, integerWidth=2,
																											fractionWidth=1,
																											allowNone=False,
																											allowNegative=False,
																											name='ncWait')
		wxData.bindWindowToDB(self.ncwait)
		self.szsettings.Add(self.ncwait, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'seconds and use')
		self.szsettings.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.cmovetype = wx.Choice(self, -1, name='cMoveType')
		wxData.bindWindowToDB(self.cmovetype)
		self.szsettings.Add(self.cmovetype, (0, 3), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'to move to target')
		self.szsettings.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.presetorder = wxPresets.PresetOrder(self, -1, name='poPresetOrder')
		wxData.bindWindowToDB(self.presetorder)
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
		wxData.bindWindowToDB(self.cbcorrectimage)
		wxData.bindWindowToDB(self.cbdisplayimage)
		wxData.bindWindowToDB(self.cbsaveimage)
		wxData.bindWindowToDB(self.cbwaitimageprocess)
		wxData.bindWindowToDB(self.cbwaitrejects)
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
		wxData.bindWindowToDB(self.cbduplicate)
		self.cduplicatetype = wx.Choice(self, -1, name='cDuplicateType')
		wxData.bindWindowToDB(self.cduplicatetype)
		szduplicate.Add(self.cbduplicate, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szduplicate.Add(self.cduplicatetype, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(szduplicate, (7, 0), (1, 5))

		# controls
		self.szcontrols = self._getStaticBoxSizer('Controls', (2, 0), (1, 1),
																wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)
		self.bpauseplay = wx.Button(self, -1, 'Pause')
		self.bstop = wx.Button(self, -1, 'Stop')
		self.szcontrols.Add(self.bpauseplay, (0, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szcontrols.Add(self.bstop, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = wxImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.szmain.AddGrowableRow(2)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def _getStaticBoxSizer(self, label, *args):
		sbs = wx.StaticBoxSizer(wx.StaticBox(self, -1, label), wx.VERTICAL)
		gbsz = wx.GridBagSizer(5, 5)
		sbs.Add(gbsz, 1, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbs, *args)
		return gbsz

