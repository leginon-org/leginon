# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Icons.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-28 00:35:27 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import icons
import wx

def icon(name):
	filename = '%s.png' % name
	path = icons.getPath(filename)
	image = wx.Image(path)
	if not image.Ok():
		return None
	image.ConvertAlphaToMask(64)
	bitmap = wx.BitmapFromImage(image)
	return bitmap

