# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import sys
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar
import leginon.gui.wx.ManualFocus

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()
AlignRotationCenterEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)
EVT_ALIGN = wx.PyEventBinder(AlignRotationCenterEventType)

class UpdateImagesEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckDoneEventType, source.GetId())
		self.SetEventObject(source)

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.ClickAndTargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddSeparator()
		self.imagepanel.addTypeTool('Tableau', display=True)

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.manualdialog = leginon.gui.wx.ManualFocus.ManualBeamTiltWobbleDialog(self, self.node)

		leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onImageClicked(self, evt):
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Lpp ImageShift Imaging')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['tableau type'] = Choice(self, -1, choices=self.node.tableau_types)
		label = wx.StaticText(self, -1, 'Tableau Type (method-display):')
		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['tableau type'], (0, 1), (1, 1), wx.ALIGN_LEFT)

		self.widgets['image shift'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=8, value='1e-7')
		bt_sizer = wx.GridBagSizer(5, 5)
		bt_sizer.Add(self.widgets['image shift'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		bt_sizer.Add(wx.StaticText(self, -1, 'm'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Image Shift:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(bt_sizer, (1, 1), (1, 1), wx.ALIGN_LEFT)

		self.widgets['sites'] = IntEntry(self, -1, min=0, allownone=False, chars=4, value='0')
		label = wx.StaticText(self, -1, 'Number of shift directions:')
		sizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['sites'], (2, 1), (1, 1), wx.ALIGN_LEFT|wx.FIXED_MINSIZE)

		angle_sizer = wx.GridBagSizer(5, 5)
		self.widgets['startangle'] = FloatEntry(self, -1, min=0, allownone=False, chars=4, value='0')
		label = wx.StaticText(self, -1, 'Start Angle:')
		sizer.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		angle_sizer.Add(self.widgets['startangle'], (0, 0), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degrees')
		angle_sizer.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(angle_sizer, (3, 1), (1, 1), wx.ALIGN_LEFT)

		rot_sizer = wx.GridBagSizer(5, 5)
		self.widgets['fringe rotation'] = FloatEntry(self, -1, allownone=False, chars=4, value='0.0')
		label = wx.StaticText(self, -1, 'Laser Fringe Angle:')
		sizer.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		rot_sizer.Add(self.widgets['fringe rotation'], (0, 0), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degrees')
		rot_sizer.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(rot_sizer, (4, 1), (1, 1), wx.ALIGN_LEFT)

		self.widgets['tableau binning'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='2')
		label = wx.StaticText(self, -1, 'Tableau Binning:')
		sizer.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['tableau binning'], (5, 1), (1, 1), wx.ALIGN_LEFT|wx.FIXED_MINSIZE)

		self.widgets['image shift count'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='1')
		label = wx.StaticText(self, -1, 'Image Shift Count:')
		sizer.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['image shift count'], (6, 1), (1, 1), wx.ALIGN_LEFT|wx.FIXED_MINSIZE)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		self.widgets['tableau type'].Bind(wx.EVT_CHOICE, self.onTableauTypeChoice)

		self.widgets['tableau binning'].Enable(True)
		self.widgets['image shift'].Enable(True)
		self.widgets['sites'].Enable(True)
		self.widgets['startangle'].Enable(True)
		self.widgets['image shift count'].Enable(True)
		return sizers + [sbsz]

	def onTableauTypeChoice(self, evt=None):
		tabtype = self.widgets['tableau type'].GetStringSelection()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = ManualFocusDialog(frame,None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

