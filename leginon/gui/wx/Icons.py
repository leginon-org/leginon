# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Icons.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-29 22:38:52 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import icons
import wx

wx.InitAllImageHandlers()

bitmaps = {}

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
	path = icons.getPath(filename)
	image = wx.Image(path)
	if not image.Ok():
		return None
	image.ConvertAlphaToMask(64)
	bitmap = wx.BitmapFromImage(image)
	return bitmap

