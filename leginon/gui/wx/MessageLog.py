import icons
import time
import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin

AddMessageEventType = wx.NewEventType()
EVT_ADD_MESSAGE = wx.PyEventBinder(AddMessageEventType)
class AddMessageEvent(wx.PyCommandEvent):
	def __init__(self, source, level, message, secs=None):
		wx.PyCommandEvent.__init__(self, AddMessageEventType, source.GetId())
		self.SetEventObject(source)
		self.level = level
		self.message = message
		self.secs = secs

class MessageLog(wx.ListCtrl, ColumnSorterMixin):
	def __init__(self, parent):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
		self.InsertColumn(0, 'Level')
		self.InsertColumn(1, 'Time', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(2, 'Message')

		self.levels = ['ERROR', 'WARNING', 'INFO']

		self.imagelist = wx.ImageList(16, 16)
		self.icons = {}
		for i in self.levels:
			image = wx.Image(icons.getPath('%s.png' % i.lower()))
			bitmap = wx.BitmapFromImage(image)
			self.icons[i] = self.imagelist.Add(bitmap)
		self.SetImageList(self.imagelist, wx.IMAGE_LIST_SMALL)

		self.data = 0
		self.itemDataMap = {}
		ColumnSorterMixin.__init__(self, 3)

		self.Bind(wx.EVT_CHAR, self.onChar)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onListItemActivated)
		self.Bind(EVT_ADD_MESSAGE, self.onAddMessage)

	def onAddMessage(self, evt):
		self.addMessage(evt.level, evt.message, evt.secs)

	def GetListCtrl(self):
		return self

	def GetItems(self):
		items = []
		for i in range(self.GetItemCount()):
			items.append(self.GetItem(i))
		return items

	def GetItemIds(self):
		return map(lambda item: item.GetId(), self.GetItems())

	def GetSelectedIds(self):
		ids = []
		for i in self.GetItemIds():
			if self.GetItemState(i, wx.LIST_STATE_SELECTED):
				ids.append(i)
		return ids

	def onChar(self, evt):
		keycode = evt.GetKeyCode()
		if keycode == wx.WXK_DELETE:
			ids = self.GetSelectedIds()
			ids.sort()
			ids.reverse()
			for i in ids:
				self.DeleteItem(i)
		elif keycode == 1:
			for i in self.GetItemIds():
				self.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		evt.Skip()

	def onListItemActivated(self, evt):
		pass

	def addMessage(self, level, message, secs=None):
		if level not in self.levels:
			self.levels.append(level)
		if secs is None:
			secs = time.time()
		localtime = time.localtime(secs)
		strtime = time.strftime('%I:%M:%S %p', localtime)
		strtime = strtime.lstrip('0')
		if level in self.icons:
			index = self.InsertImageStringItem(0, '', self.icons[level])
		else:
			index = self.InsertStringItem(0, level)
		self.SetStringItem(index, 1, strtime)
		self.SetStringItem(index, 2, message)
		self.SetItemData(index, self.data)
		self.itemDataMap[self.data] = (self.levels.index(level), secs, message)
		self.data += 1
		self.arrange()

	def arrange(self):
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		width, height = self.GetClientSize()
		width -= self.GetColumnWidth(0) + self.GetColumnWidth(1)
		self.SetColumnWidth(2, width)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Message Log Test')

			panel = wx.Panel(frame, -1)

			ml = MessageLog(panel)
			ml.addMessage('info', 'Message 0')
			ml.addMessage('warning', 'Message 1')
			ml.addMessage('error', 'Message 2')

			sizer = wx.GridBagSizer(5, 5)
			sizer.Add(ml, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 5)
			sizer.AddGrowableRow(0)
			sizer.AddGrowableCol(0)

			panel.SetSizerAndFit(sizer)

			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

