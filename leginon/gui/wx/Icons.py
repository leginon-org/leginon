import icons
import wx

def icon(name):
	filename = '%s.png' % name
	image = wx.Image(icons.getPath(filename))
	image.ConvertAlphaToMask(64)
	bitmap = wx.BitmapFromImage(image)
	return bitmap

