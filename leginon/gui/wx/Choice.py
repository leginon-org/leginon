# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Choice.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2005-09-21 00:28:01 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx

class Choice(wx.Choice):
	def SetStringSelection(self, string):
		if string is None or self.FindString(string) == wx.NOT_FOUND:
			if not self.IsEmpty():
				first = self.GetString(0)
				wx.Choice.SetStringSelection(self, first)
				return True
			else:
				return False
		wx.Choice.SetStringSelection(self, string)
		return True
