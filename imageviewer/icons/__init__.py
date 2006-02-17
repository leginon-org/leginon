import os.path
import wx

wx.InitAllImageHandlers()

bitmaps = {}

def icon(name):
	if name not in bitmaps:
		bitmaps[name] = _icon(name)
	return bitmaps[name]

def _icon(name):
	path = os.path.join(os.path.dirname(__file__), '%s.png' % name)
	return wx.Bitmap(path)


