# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

import leginon.icons
import wx

bitmaps = {}

def empty():
	bitmap = wx.Bitmap(16, 16)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

def null():
	return icon('null')

def icon(name):
	if name is None:
		return wx.NullBitmap
	if name not in bitmaps:
		bitmaps[name] = _icon(name)
	bitmap = bitmaps[name]
	if bitmap is None:
		return wx.NullBitmap
	return bitmap

def _icon(name):
	# workaround for wx 4.1.1 bug showing bitmap alpha as black instead of transparency.
	if name == 'null' and wx.__version__=='4.1.1':
		name = 'null_white'
	filename = '%s.png' % name
	path = leginon.icons.getPath(filename)
	image = wx.Image(path)
	if not image.IsOk():
		return None
	#image.ConvertAlphaToMask(64)
	image.Rescale(16, 16)
	bitmap = wx.Bitmap(image)
	return bitmap

