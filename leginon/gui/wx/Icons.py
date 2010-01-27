# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import leginon.icons
import wx

wx.InitAllImageHandlers()

bitmaps = {}

def empty():
	bitmap = wx.EmptyBitmap(16, 16)
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
	filename = '%s.png' % name
	path = leginon.icons.getPath(filename)
	image = wx.Image(path)
	if not image.Ok():
		return None
	#image.ConvertAlphaToMask(64)
	bitmap = wx.BitmapFromImage(image)
	return bitmap

