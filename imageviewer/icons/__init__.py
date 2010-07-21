import os.path
import wx
import inspect

wx.InitAllImageHandlers()

bitmaps = {}

def icon(name):
	if name not in bitmaps:
		bitmaps[name] = _icon(name)
	return bitmaps[name]

def _icon(name):
	this_file = inspect.currentframe().f_code.co_filename
	path = os.path.join(os.path.dirname(this_file), '%s.png' % name)
	return wx.Bitmap(path)


