# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Icons.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import icons
import wx

def icon(name):
	filename = '%s.png' % name
	image = wx.Image(icons.getPath(filename))
	image.ConvertAlphaToMask(64)
	bitmap = wx.BitmapFromImage(image)
	return bitmap

