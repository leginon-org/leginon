# -*- coding: iso-8859-1 -*-
import wx
from wx.lib.intctrl import IntCtrl

class Panel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, name='pCamera')
		self.geometry = None
		self.size = {'x': 4096, 'y': 4096}
		self.binnings = {'x': [1,2,4,8,16], 'y': [1,2,4,8,16]}

		# geometry
		std = wx.StaticText(self, -1, 'Dimension:')
		self.stdimension = wx.StaticText(self, -1, '')

		sto = wx.StaticText(self, -1, 'Offset:')
		self.stoffset = wx.StaticText(self, -1, '')

		stb = wx.StaticText(self, -1, 'Binning:')
		self.stbinning = wx.StaticText(self, -1, '')

		bcustom = wx.Button(self, -1, 'Custom...')

		choices, self.common = self.getCenteredGeometries()
		self.ccommon = wx.Choice(self, -1, choices=choices)

		self.szmain = wx.GridBagSizer(3, 3)

		self.szmain.Add(std, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stdimension, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(sto, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stoffset, (1, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(stb, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stbinning, (2, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(self.ccommon, (3, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szmain.Add(bcustom, (3, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		# exposure time
		stet = wx.StaticText(self, -1, 'Exposure time:')
		self.tcexposuretime = IntCtrl(self, -1, min=0, limited=True, size=(40, -1),
																	style=wx.TE_RIGHT)
		stms = wx.StaticText(self, -1, 'ms')

		self.szmain.Add(stet, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz = wx.GridBagSizer(0, 3)
		sz.Add(self.tcexposuretime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(stms, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(sz, (4, 1), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER, 3)

		self.SetSizerAndFit(self.sbsz)

		self.Bind(wx.EVT_CHOICE, self.onCommonChoice, self.ccommon)
		self.Bind(wx.EVT_BUTTON, self.onCustomButton, bcustom)

	def onCommonChoice(self, evt):
		self.setGeometry(self.common[evt.GetString()])

	def onCustomButton(self, evt):
		dialog = CustomDialog(self, self.getGeometry())
		if dialog.ShowModal() == wx.ID_OK:
			self.setGeometry(dialog.getGeometry())
		dialog.Destroy()

	def getCenteredGeometry(self, dimension, binning):
		offset = (self.size['x']/binning - dimension)/2
		geometry = {'dimension': {'x': dimension, 'y': dimension},
								'offset': {'x': offset, 'y': offset},
								'binning': {'x': binning, 'y': binning}}
		return geometry

	def getCenteredGeometries(self):
		geometries = {}
		if self.size['x'] != self.size['y']:
			return geometries
		if self.binnings['x'] != self.binnings['y']:
			return geometries
		dimensions = map(lambda b: self.size['x']/b, self.binnings['x'])
		dimensions.reverse()
		keys = []
		for d in dimensions:
			for b in self.binnings['x']:
				if d*b <= self.size['x']:
					key = '%d² × %d' % (d, b)
					geometries[key] = self.getCenteredGeometry(d, b)
					keys.append(key)
				else:
					break
		return keys, geometries

	def validateGeometry(self, geometry):
		for a in ['x', 'y']:
			if geometry['dimension'][a] < 1 or geometry['offset'][a] < 0:
				return False
			if geometry['binning'][a] not in self.binnings[a]:
				return False
			size = geometry['dimension'][a] + geometry['offset'][a]
			size *= geometry['binning'][a]
			if size > self.size[a]:
				return False
		return True

	def setGeometry(self, geometry):
		if not self.validateGeometry(geometry):
			raise ValueError
		dimension = '%d × %d' % (geometry['dimension']['x'],
														geometry['dimension']['y'])
		self.stdimension.SetLabel(dimension)
		offset = '(%d, %d)' % (geometry['offset']['x'],
															geometry['offset']['y'])
		self.stoffset.SetLabel(offset)
		binning = '%d × %d' % (geometry['binning']['x'],
														geometry['binning']['y'])
		self.stbinning.SetLabel(binning)
		self.geometry = geometry
		self.Freeze()
		self.szmain.Layout()
		self.Thaw()

	def getGeometry(self):
		return self.geometry

class CustomDialog(wx.Dialog):
	def __init__(self, parent, geometry):
		wx.Dialog.__init__(self, parent, -1, 'Custom')
		binnings = parent.binnings

		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stdimension = wx.StaticText(self, -1, 'Dimension:')
		self.tcxdimension = IntCtrl(self, -1, min=0, limited=True, size=(32, -1),
																style=wx.TE_RIGHT)
		self.tcydimension = IntCtrl(self, -1, min=0, limited=True, size=(32, -1),
																style=wx.TE_RIGHT)
		stbinning = wx.StaticText(self, -1, 'Binning:')
		self.cxbinning = wx.Choice(self, -1, choices=parent.binnings['x'])
		self.cybinning = wx.Choice(self, -1, choices=parent.binnings['y'])
		stoffset = wx.StaticText(self, -1, 'Offset:')
		self.tcxoffset = IntCtrl(self, -1, min=0, limited=True, size=(32, -1),
															style=wx.TE_RIGHT)
		self.tcyoffset = IntCtrl(self, -1, min=0, limited=True, size=(32, -1),
															style=wx.TE_RIGHT)
		self.szxy = wx.GridBagSizer(5, 5)
		self.szxy.Add(stx, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(sty, (0, 2), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(stdimension, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.tcxdimension, (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		self.szxy.Add(self.tcydimension, (1, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		self.szxy.Add(stbinning, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.cxbinning, (2, 1), (1, 1),
									wx.ALIGN_CENTER|wx.EXPAND|wx.ALL)
		self.szxy.Add(self.cybinning, (2, 2), (1, 1),
									wx.ALIGN_CENTER|wx.EXPAND|wx.ALL)
		self.szxy.Add(stoffset, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.tcxoffset, (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		self.szxy.Add(self.tcyoffset, (3, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)

		bok = wx.Button(self, wx.ID_OK, 'OK')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbsz.Add(self.szxy, 0, wx.ALIGN_CENTER)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.sbsz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		sz.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		if geometry is not None:
			self.tcxdimension.SetValue(geometry['dimension']['x'])
			self.tcydimension.SetValue(geometry['dimension']['y'])
			self.cxbinning.SetStringSelection(str(geometry['binning']['x']))
			self.cybinning.SetStringSelection(str(geometry['binning']['y']))
			self.tcxoffset.SetValue(geometry['offset']['x'])
			self.tcyoffset.SetValue(geometry['offset']['y'])

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onOK, bok)

	def getGeometry(self):
		geometry = {'dimension': {}, 'binning': {}, 'offset': {}}
		geometry['dimension']['x'] = self.tcxdimension.GetValue()
		geometry['dimension']['y'] = self.tcydimension.GetValue()
		geometry['binning']['x'] = int(self.cxbinning.GetStringSelection())
		geometry['binning']['y'] = int(self.cybinning.GetStringSelection())
		geometry['offset']['x'] = self.tcxoffset.GetValue()
		geometry['offset']['y'] = self.tcyoffset.GetValue()
		return geometry

	def onOK(self, evt):
		geometry = self.getGeometry()
		if geometry is not None and self.GetParent().validateGeometry(geometry):
			evt.Skip()
		else:
			dialog = wx.MessageDialog(self, 'Invalid camera geometry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Camera Test')
			panel = Panel(frame)
			panel.setGeometry({'dimension': {'x': 128, 'y': 128},
													'offset': {'x': 256, 'y': 256},
													'binning': {'x': 2, 'y': 2}})
			panel.getCenteredGeometries()
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

