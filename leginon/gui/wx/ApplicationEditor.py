import wx
import gui.wx.Master

class ApplicationEditorFrame(wx.Frame):
	def __init__(self, parent):
		style = wx.DEFAULT_FRAME_STYLE
		style |= wx.FRAME_NO_TASKBAR
		wx.Frame.__init__(self, parent, -1, 'Application Editor', style=style)

		self.menubar = wx.MenuBar()

		menu = wx.Menu()

		load = wx.MenuItem(menu, -1, '&Load...')
		save = wx.MenuItem(menu, -1, '&Save')
		saveas = wx.MenuItem(menu, -1, 'Save &As...')
		exit = wx.MenuItem(menu, -1, 'E&xit')

		self.Bind(wx.EVT_MENU, self.onLoad, load)
		self.Bind(wx.EVT_MENU, self.onSave, save)
		self.Bind(wx.EVT_MENU, self.onSaveAs, saveas)
		self.Bind(wx.EVT_MENU, self.onExit, exit)
		menu.AppendItem(load)
		menu.AppendItem(save)
		menu.AppendItem(saveas)
		menu.AppendItem(exit)

		self.menubar.Append(menu, '&Application')

		self.SetMenuBar(self.menubar)

		self.applicationeditor = gui.wx.Master.ApplicationEditorCanvas(self, -1)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.applicationeditor, (0, 0), (1, 1), wx.EXPAND)
		sz.SetItemMinSize(self.applicationeditor, (640, 480))
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)
		self.SetSizerAndFit(sz)

	def onLoad(self, evt):
		pass

	def onSave(self, evt):
		pass

	def onSaveAs(self, evt):
		pass

	def onExit(self, evt):
		self.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Application Editor Test')
			dialog = ApplicationEditorFrame(frame)
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

