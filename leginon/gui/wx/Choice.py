# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Choice.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx

class Choice(wx.Choice):
	def SetStringSelection(self, string):
		if string is None or self.FindString(string) == wx.NOT_FOUND:
			return False
		wx.Choice.SetStringSelection(self, string)
		return True
