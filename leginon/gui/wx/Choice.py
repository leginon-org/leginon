import wx

class Choice(wx.Choice):
	def SetStringSelection(self, string):
		if string is None or self.FindString(string) == wx.NOT_FOUND:
			return False
		wx.Choice.SetStringSelection(self, string)
		return True
