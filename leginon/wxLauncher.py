import logging
import launcher
import wx
import wx.lib.scrolledpanel
import wxLogging

class LauncherApp(wx.App):
	def __init__(self, name, **kwargs):
		self.name = name
		self.kwargs = kwargs
		wx.App.__init__(self, 0)

	def OnInit(self):
		# seperate thread
		self.launcher = launcher.Launcher(self.name, **self.kwargs)
		self.launcher.start()
		self.SetTopWindow(self.launcher.frame)
		self.launcher.frame.Show(True)
		return True

	def OnExit(self):
		self.launcher.exit()

class LauncherStatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent, -1)

class LauncherFrame(wx.Frame):
	def __init__(self, launcher):
		self.launcher = launcher
		wx.Frame.__init__(self, None, -1, 'Leginon', size=(750, 750),
											name='fLeginon')

		# menu
		self.menubar = wx.MenuBar()

		# file menu
		filemenu = wx.Menu()
		exit = wx.MenuItem(filemenu, -1, 'E&xit')
		self.Bind(wx.EVT_MENU, self.onExit, exit)
		filemenu.AppendItem(exit)
		self.menubar.Append(filemenu, '&File')

		# settings menu
		self.settingsmenu = wx.Menu()
		self.loggingmenuitem = wx.MenuItem(self.settingsmenu, -1, '&Logging')
		self.Bind(wx.EVT_MENU, self.onMenuLogging, self.loggingmenuitem)
		self.settingsmenu.AppendItem(self.loggingmenuitem)
		self.menubar.Append(self.settingsmenu, '&Settings')

		self.SetMenuBar(self.menubar)

		# status bar
		self.statusbar = LauncherStatusBar(self)
		self.SetStatusBar(self.statusbar)

		self.panel = LauncherPanel(self, self.launcher.uicontainer.location())

	def onExit(self, evt):
		self.launcher.exit()
		self.Close()

	def onMenuLogging(self, evt):
		dialog = wxLogging.LoggingConfigurationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class LauncherPanel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent, location):
		self._enabled = True
		self._shown = True
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1)

	def layout(self):
		pass

