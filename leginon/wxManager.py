import manager
import uiclient
import wx

class ManagerApp(wx.App):
	def __init__(self, session, tcpport=None, xmlrpcport=None, **kwargs):
		self.session = session
		self.tcpport = tcpport
		self.xmlrpcport = xmlrpcport
		self.kwargs = kwargs
		wx.App.__init__(self, 0)

	def OnInit(self):
		self.manager = manager.Manager(self.session, self.tcpport, self.xmlrpcport,
																		**self.kwargs)
		self.SetTopWindow(self.manager.frame)
		self.manager.frame.Show(True)
		return True

	def OnExit(self):
		self.manager.exit()

class ManagerStatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent, -1)

class ManagerFrame(wx.Frame):
	def __init__(self, manager):
		self.manager = manager

		wx.Frame.__init__(self, None, -1, 'Manager', size=(750, 750))

		self.menubar = wx.MenuBar()
		filemenu = wx.Menu()
		filemenu.Append(101, 'E&xit')
		self.menubar.Append(filemenu, '&File')

		self.Bind(wx.EVT_MENU, self.onExit, id=101)

		self.SetMenuBar(self.menubar)

		self.statusbar = ManagerStatusBar(self)
		self.SetStatusBar(self.statusbar)

		self.panel = ManagerPanel(self, self.manager.uicontainer.location())

	def onExit(self, evt):
		self.manager.exit()
		self.Close()

class ManagerPanel(wx.ScrolledWindow):
	def __init__(self, parent, location):
		self._enabled = True
		self._shown = True
		wx.ScrolledWindow.__init__(self, parent, -1)
		self.SetScrollRate(5, 5)
		containerclass = uiclient.SimpleContainerWidget
		containerclass = uiclient.ClientContainerFactory(containerclass)
		self.container = containerclass('UI Client', self, self, location, {})
		self.SetSizer(self.container)
		self.Fit()

	def layout(self):
		pass

