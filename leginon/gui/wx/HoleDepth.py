# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/HoleDepth.py,v $
# $Revision: 1.4 $
# $Name: not supported by cvs2svn $
# $Date: 2005-10-25 19:12:50 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Rings
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar

class Panel(gui.wx.TargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog

		self.cparameter = wx.Choice(self.toolbar, -1,
										choices=['Hole Untilt', 'Hole Tilt','I','I0'])
		self.cparameter.SetSelection(0)
		self.toolbar.InsertControl(1, self.cparameter)


		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)

		parameter = self.cparameter.GetStringSelection()		
 		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTypeTool('Edge', display=True, settings=True)
		self.imagepanel.addTypeTool('Template', display=True, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Color(0, 255, 255), target=True,
																settings=True)

		self.imagepanel.selectiontool.setDisplayed('Blobs', True)
		self.imagepanel.setTargets('Blobs', [])
		self.imagepanel.addTargetTool('PickHoles', wx.Color(255, 0, 255), target=True,
																	settings=True)
		self.imagepanel.selectiontool.setDisplayed('PickHoles', True)

		self.imagepanel.setTargets('PickHoles', [])

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onNodeInitialized(self):
		gui.wx.Node.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitQueueTool,
											id=gui.wx.ToolBar.ID_SUBMIT_QUEUE)
#		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)
		self.Bind(gui.wx.ImageViewer.EVT_SETTINGS, self.onImageSettings)
		queue = self.node.settings['queue']
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE, queue)

	def onSubmitTool(self, evt):
#		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.storeK()

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			parameter = self.cparameter.GetStringSelection()
			imagetype = str(parameter)+' filename'
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings[imagetype]
				if filename:
					self.node.readImage(filename,imagetype)
			dialog.Destroy()
			return

		if evt.name == 'Edge':
			dialog = EdgeSettingsDialog(self)
		elif evt.name == 'Template':
			dialog = TemplateSettingsDialog(self)
		elif evt.name == 'Threshold':
			dialog = ThresholdSettingsDialog(self)
		elif evt.name == 'Blobs':
			dialog = BlobsSettingsDialog(self)
		elif evt.name == 'PickHoles':
			dialog = PickHoleSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()

class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)
		parent = self.GetParent()
		parameter = parent.cparameter.GetStringSelection()
		imagetype=str(parameter)+' filename'
		self.widgets[imagetype] = filebrowse.FileBrowseButton(self, -1)
		self.bok.SetLabel('Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets[imagetype], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, imagetype)
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class TemplateSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['template lpf'] = {}
		self.widgets['template lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['template lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter (Phase Correlation)')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		self.widgets['tilt axis'] = FloatEntry(self, -1, chars=9)

		szta = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Tilt Axis:')
		szta.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szta.Add(self.widgets['tilt axis'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szta.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Tilt Axis')
		sbszta = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszta.Add(szta, 1, wx.EXPAND|wx.ALL, 5)

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
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sb = wx.StaticBox(self, -1, 'Template Correlation')
		sbsztemplate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsztemplate.Add(sztemplate, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbsztemplate, sbszlpf, sbszta, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.correlateTemplate()

class EdgeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['edge lpf'] = {}
		self.widgets['edge lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

#		self.widgets['edge'] = wx.CheckBox(self, -1, 'Use edge finding')
#		self.widgets['edge type'] = Choice(self, -1, choices=self.node.filtertypes)
#		self.widgets['edge log size'] = IntEntry(self, -1, min=1, chars=4)
#		self.widgets['edge log sigma'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['edge absolute'] = wx.CheckBox(self, -1,
#																					'Take absolute value of edge values')
		self.widgets['edge threshold'] = FloatEntry(self, -1, chars=9)

		szedge = wx.GridBagSizer(5, 5)
#		szedge.Add(self.widgets['edge'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
#		label = wx.StaticText(self, -1, 'Type:')
#		szedge.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge type'], (1, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
#		label = wx.StaticText(self, -1, 'LoG Size:')
#		szedge.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge log size'], (2, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
#		label = wx.StaticText(self, -1, 'LoG Sigma:')
#		szedge.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge log sigma'], (3, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
#		szedge.Add(self.widgets['edge absolute'], (4, 0), (1, 2),
#								wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Threshold:')
		szedge.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge threshold'], (0, 1), (1, 1),
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
		self.setNodeSettings()
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
		self.setNodeSettings()
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

		self.bpick = wx.Button(self, -1, 'Calc w/ selection')
		szbuttonpick = wx.GridBagSizer(5, 5)
		szbuttonpick.Add(self.bpick, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbuttonpick.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onPickedBlobButton, self.bpick)

		self.btest = wx.Button(self, -1, 'Find blobs / Calc depth')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszblobs,szbuttonpick,szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.findBlobs()
		self.node.getHoleDepth()

	def onPickedBlobButton(self, evt):
		self.setNodeSettings()
		parent = self.GetParent()
                pixels=parent.imagepanel.getTargetPositions('Blobs')
		if (len(pixels)==2):
			self.node.makeBlobs(pixels)
			self.node.getHoleDepth()

class PickHoleSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['pickhole radius'] = FloatEntry(self, -1, chars=6)
		self.widgets['pickhole zero thickness'] = FloatEntry(self, -1, chars=6)

		szstats = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Radius:')
		szstats.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['pickhole radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Zero thickness:')
		szstats.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['pickhole zero thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szstats.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Hole Statistics')
		sbszstats = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszstats.Add(szstats, 1, wx.EXPAND|wx.ALL, 5)

		self.bshift = wx.Button(self, -1, 'Shiftpicks')
		szbuttonshift = wx.GridBagSizer(5, 5)
		szbuttonshift.Add(self.bshift, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbuttonshift.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onShiftButton, self.bshift)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		return [sbszstats, szbuttonshift,szbutton]

	def onShiftButton(self, evt):
		self.setNodeSettings()
		parent = self.GetParent()
                pixels=parent.imagepanel.getTargetPositions('PickHoles')
		shift=self.node.correlate_I_I0()
		newtargets=self.node.applyPickTargetShift(pixels,shift)
		parent.imagepanel.setTargets('PickHoles', newtargets['PickHoles'])

	def onTestButton(self, evt):
		self.setNodeSettings()
		parent = self.GetParent()
                pixels=parent.imagepanel.getTargetPositions('PickHoles')
		self.node.getPickHoleStats(pixels)

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsd = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['skip'] = wx.CheckBox(self, -1,
																	'Skip automated hole finder')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['skip'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Hole Depth Finder Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return tfsd + [sbsz]


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Hole Depth Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

