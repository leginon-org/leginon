import icons
import wx

ID_SETTINGS = 1001
ID_ACQUIRE = 1002
ID_PLAY = 1003
ID_PAUSE = 1004
ID_STOP = 1005
ID_CALIBRATE = 1006
ID_MEASURE = 1007
ID_ABORT = 1008
ID_SUBMIT = 1009
ID_ACQUISITION_TYPE = 1010
ID_MEASURE_DRIFT = 1011
ID_DECLARE_DRIFT = 1012
ID_CHECK_DRIFT = 1013
ID_REFRESH = 1014
ID_PAUSES = 1015
ID_AUTOFOCUS = 1016
ID_MANUAL_FOCUS = 1017
ID_MODEL = 1018
ID_GRID = 1019
ID_TILES = 1020
ID_MOSAIC = 1021
ID_CURRENT_POSITION = 1022
ID_FIND_SQUARES = 1023
ID_ATLAS = 1024
ID_STAGE_LOCATIONS = 1025
ID_PARAMETER_SETTINGS = 1026
ID_GET_INSTRUMENT = 1027
ID_SET_INSTRUMENT = 1028

class ToolBar(wx.ToolBar):
	def __init__(self, parent):
		pre = wx.PreToolBar()
		pre.Show(False)
		pre.Create(parent, -1, style=wx.TB_HORIZONTAL|wx.NO_BORDER)
		self.this = pre.this
		self._setOORInfo(self)
		self.spacer = wx.StaticText(self, -1, '')
		self.AddControl(self.spacer)

	def AddTool(self, id, bitmap, **kwargs):
		bitmap = '%s.png' % bitmap
		image = wx.Image(icons.getPath(bitmap))
		image.ConvertAlphaToMask(64)
		bitmap = wx.BitmapFromImage(image)
		wx.ToolBar.AddTool(self, id, bitmap, **kwargs)

	def InsertTool(self, pos, id, bitmap, **kwargs):
		bitmap = '%s.png' % bitmap
		bitmap = wx.BitmapFromImage(wx.Image(icons.getPath(bitmap)))
		wx.ToolBar.InsertTool(self, pos, id, bitmap, **kwargs)
