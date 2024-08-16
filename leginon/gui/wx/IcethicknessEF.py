# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import threading

from leginon.gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetPanel
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Presets import PresetChoice


class Panel(leginon.gui.wx.Node.Panel):
	icon = 'ice_t'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelp='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelp='Process')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelp='Stop')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)

		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addImagePanel(self):
		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.FFTTargetImagePanel(self, -1,imagesize=(512,512))
		self.imagepanel.addTypeTool('Icethickness', display=True) #wjr
		self.imagepanel.selectiontool.setDisplayed('Icethickness', True) #wjr
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		#self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
		#									id=leginon.gui.wx.ToolBar.ID_PLAY)
		#self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
		#									id=leginon.gui.wx.ToolBar.ID_STOP)
		self.addImagePanel()
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SHAPE_FOUND, self.onShapeFound, self.imagepanel)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.node.onStartPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)

	def onStopTool(self, evt):
		self.node.onStopPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

	def onNewPixelSize(self, pixelsize,center,hightension,cs):
		idcevt = leginon.gui.wx.ImagePanelTools.ImageNewPixelSizeEvent(self.imagepanel, pixelsize,center,hightension,cs)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		self.center = center

	def onShapeFound(self, evt):
		centers = [(self.center['y'],self.center['x']),]
		idcevt = leginon.gui.wx.ImagePanelTools.ShapeNewCenterEvent(self.imagepanel, centers)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		threading.Thread(target=self.node.estimateAstigmation, args=(evt.params,)).start()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Ice Thickness using Energy Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Ice Thickness using Aperture Limited Scattering')
		sbszdb = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Collect ice thickness image')
		self.widgets['mean free path'] = FloatEntry(self, -1, min=0.0, chars=6)
		szmeanfreepath = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mean free path (nm):')
		szmeanfreepath.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeanfreepath.Add(self.widgets['mean free path'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.widgets['exposure time'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_exp_time = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Exposure time for thickness images (ms):')
		sz_exp_time.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_exp_time.Add(self.widgets['exposure time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.widgets['slit width'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_slit_width = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Slit width for thickness measurement (15 eV suggested):')
		sz_slit_width.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_slit_width.Add(self.widgets['slit width'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.widgets['decimate'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_decimate = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Measure every N images, where N=')
		sz_decimate.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_decimate.Add(self.widgets['decimate'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.widgets['binning'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_binning = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Binning for test images, use 4 or 8 to speed up')
		sz_binning.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_binning.Add(self.widgets['binning'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.widgets['process_obj_thickness'] = wx.CheckBox(self, -1, 'Calculate ice thickness from aperture limited scattering')
		self.widgets['obj mean free path'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_objmeanfreepath = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'ALS coefficient (nm):')
		sz_objmeanfreepath.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_objmeanfreepath.Add(self.widgets['obj mean free path'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.widgets['vacuum intensity'] = FloatEntry(self, -1, min=0.0, chars=6)
		sz_vac = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Vacuum intensity for exposure images:')
		sz_vac.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_vac.Add(self.widgets['vacuum intensity'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.widgets['use_best_quart_stats'] = wx.CheckBox(self, -1, 'Use best quadrant stats')
		self.widgets['cfeg'] = wx.CheckBox(self, -1, 'Correct for changing Cold FEG intensity')
		self.widgets['cfeg_slope'] = FloatEntry(self, -1, chars=8)
		sz_cfegslope = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Slope for CFEG correction (fractional drop per second):')
		sz_cfegslope.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_cfegslope.Add(self.widgets['cfeg_slope'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.widgets['cfeg_intercept'] = FloatEntry(self, -1, chars=6)
		sz_cfegintercept = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Intercept for CFEG correction:')
		sz_cfegintercept.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_cfegintercept.Add(self.widgets['cfeg_intercept'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)


		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['process'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_exp_time, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_slit_width, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmeanfreepath, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_decimate, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_binning, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 10)
		#label = wx.StaticText(self, -1, 'Find images in this session with label:')
		sz.Add(self.widgets['process_obj_thickness'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_objmeanfreepath, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_vac, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['use_best_quart_stats'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['cfeg'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_cfegslope, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_cfegintercept, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszdb.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz, sbszdb]

	def GetPresetNameWidget(self,preset_type): # simply creates a widget to choose a preset for the preset type
		self.widgets[preset_type] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets[preset_type].setChoices(presets)


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Ice Thickness EF Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

