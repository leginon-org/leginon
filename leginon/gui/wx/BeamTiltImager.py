# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Focuser.py,v $
# $Revision: 1.60 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-31 02:37:06 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import threading
import sys
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.ImagePanel
import gui.wx.TargetPanel
import gui.wx.ToolBar

AlignRotationCenterEventType = wx.NewEventType()

EVT_ALIGN = wx.PyEventBinder(AlignRotationCenterEventType)

class Panel(gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = gui.wx.TargetPanel.ClickAndTargetImagePanel
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ALIGN, 'rotcenter',
							 shortHelpString='Align rotation center')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTypeTool('Tableau', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.align_dialog = AlignRotationCenterDialog(self)
		self.Bind(EVT_ALIGN, self.onAlignRotationCenter, self)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter,
						  id=gui.wx.ToolBar.ID_ALIGN)
		self.Bind(gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.scrsettings.onTableauTypeChoice()
		dialog.ShowModal()
		dialog.Destroy()

	def onAlignRotationCenter(self, evt):
		self.align_dialog.Show()

	def onImageClicked(self, evt):
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,True)

class ScrolledSettings(gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Tilt Imaging and Correlation')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['tableau type'] = Choice(self, -1, choices=self.node.tableau_types)
		label = wx.StaticText(self, -1, 'Tableau Type (method-display):')
		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['tableau type'], (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['beam tilt'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.01')
		bt_sizer = wx.GridBagSizer(5, 5)
		bt_sizer.Add(self.widgets['beam tilt'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		bt_sizer.Add(wx.StaticText(self, -1, 'radian'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Beam Tilt:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(bt_sizer, (1, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['sites'] = IntEntry(self, -1, min=0, allownone=False, chars=4, value='0')
		label = wx.StaticText(self, -1, 'Number of tilt directions:')
		sizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['sites'], (2, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['startangle'] = FloatEntry(self, -1, min=0, allownone=False, chars=4, value='0')
		label = wx.StaticText(self, -1, 'Start Angle:')
		sizer.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['startangle'], (3, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'degrees')
		sizer.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['correlation type'] = Choice(self, -1, choices=self.node.correlation_types)
		label = wx.StaticText(self, -1, 'Correlation Type:')
		sizer.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['correlation type'], (4, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['tableau binning'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='2')
		label = wx.StaticText(self, -1, 'Tableau Binning:')
		sizer.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['tableau binning'], (5, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['beam tilt count'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='1')
		label = wx.StaticText(self, -1, 'Beam Tilt Count:')
		sizer.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['beam tilt count'], (6, 1), (1, 1), wx.ALIGN_CENTER)

		self.widgets['tableau split'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='8')
		label = wx.StaticText(self, -1, 'Tableau Split:')
		sizer.Add(label, (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['tableau split'], (7, 1), (1, 1), wx.ALIGN_CENTER)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		self.widgets['tableau type'].Bind(wx.EVT_CHOICE, self.onTableauTypeChoice)

		return sizers + [sbsz]

	def onTableauTypeChoice(self, evt=None):
		tabtype = self.widgets['tableau type'].GetStringSelection()
		if tabtype == 'split image-power':
			self.enableTableauSplit(True)
		else:
			self.enableTableauSplit(False)

	def enableTableauSplit(self,isenable):
		self.widgets['tableau split'].Enable(isenable)
		self.widgets['tableau binning'].Enable(not isenable)
		self.widgets['beam tilt'].Enable(not isenable)
		self.widgets['sites'].Enable(not isenable)
		self.widgets['startangle'].Enable(not isenable)
		self.widgets['beam tilt count'].Enable(not isenable)
		
class AlignRotationCenterDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Align Rotation Center')

		self.measure = wx.Button(self, -1, 'Align')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Defocus 1:')
		self.d1value = FloatEntry(self, -1, allownone=False, chars=5, value='-2e-6')
		sbsz.Add(label, (0,0), (1,1))
		sbsz.Add(self.d1value, (0,1), (1,1))
		label = wx.StaticText(self, -1, 'Defocus 2:')
		self.d2value = FloatEntry(self, -1, allownone=False, chars=5, value='-4e-6')
		sbsz.Add(label, (1,0), (1,1))
		sbsz.Add(self.d2value, (1,1), (1,1))

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		self.Close()
		d1 = self.d1value.GetValue()
		d2 = self.d2value.GetValue()
		threading.Thread(target=self.node.alignRotationCenter, args=(d1,d2,)).start()

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		self.settingsdialog.increment.SetValue(self.node.increment)
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
		#self.MakeModal(True)

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

