# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Selector.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-27 23:06:44 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import wx.lib.scrolledpanel
import gui.wx.Icons

bitmaps = {}

SelectEventType = wx.NewEventType()
EVT_SELECT = wx.PyEventBinder(SelectEventType)
class SelectEvent(wx.PyCommandEvent):
	def __init__(self, source, item, selected):
		wx.PyCommandEvent.__init__(self, SelectEventType, source.GetId())
		self.SetEventObject(source)
		self.item = item
		self.selected = selected

class SelectorItem(object):
	def __init__(self, parent, name, icon=None, data=None):
		self.parent = parent
		self.name = name
		self.data = data
		self.items = []

		self.items.append(None)

		if icon is not None:
			if name not in bitmaps:
				bitmaps[icon] = gui.wx.Icons.icon(icon)
			bitmap = bitmaps[icon]
			sb = wx.StaticBitmap(parent, -1, bitmap)
			self.items.append(sb)
		else:
			self.items.append(None)

		label = wx.StaticText(parent, -1, name)
		self.items.append(label)

		for item in self.items:
			if item is None:
				continue
			item.Bind(wx.EVT_LEFT_DOWN, self.parent.onLeftDown)

	def destroy(self):
		while self.items:
			item = self.items.pop()
			if item is None:	
				continue
			item.Destroy()

	def setSelected(self, selected):
		if selected:
			self.items[2].SetBackgroundColour(wx.Color(49, 106, 197))
			self.items[2].SetForegroundColour(wx.WHITE)
		else:
			self.items[2].SetBackgroundColour(wx.WHITE)
			self.items[2].SetForegroundColour(wx.BLACK)
		self.items[2].Refresh()

class Selector(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1)

		self.order = []
		self.items = {}

		self.selected = None

		self.SetBackgroundColour(wx.WHITE)

		self.sz = wx.GridBagSizer(1, 3)
		self.sz.SetEmptyCellSize((16, 16))
		self.sz.AddGrowableCol(2)

		self.SetSizer(self.sz)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)

	def onLeftDown(self, evt):
		evtobj = evt.GetEventObject()
		row = None
		if evtobj is self:
			y = 0
			for i, height in enumerate(self.sz.GetRowHeights()):
				height += self.sz.GetVGap()
				if evt.m_y >= y and evt.m_y <= y + height:
					row = i
					break
				y += height
		else:
			item = self.sz.FindItem(evtobj)
			if item is not None:
				row = item.GetPos().row
		evt.Skip()

		if row is None:
			return

		name = self.order[row]
		item = self.items[name]

		if self.selected is item:
			self.selected.setSelected(False)
			self.selected = None
			selected = False
		else:
			if self.selected is not None:
				self.selected.setSelected(False)
			self.selected = item
			selected = True
			self.selected.setSelected(True)

		evt = SelectEvent(self, item, selected)
		self.GetEventHandler().AddPendingEvent(evt)

	def addItem(self, row, item):
		for i, additem in enumerate(item.items):
			if additem is None:
				continue
			if isinstance(additem, wx.StaticText):
				flags = wx.ALIGN_CENTER_VERTICAL
			else:
				flags = wx.ALIGN_CENTER
			self.sz.Add(additem, (row, i), (1, 1), flags)

	def moveItem(self, row, item):
		for column, moveitem in enumerate(item.items):
			if moveitem is None:
				continue
			self.sz.SetItemPosition(moveitem, (row, column))

	def detachItem(self, item):
		for removeitem in item.items:
			if removeitem is None:
				continue
			self.sz.Detach(removeitem)

	def destroyItem(self, item):
		self.detachItem(item)
		item.destroy()

	def insert(self, index, item):
		rows = range(index, len(self.order))
		rows.reverse()
		for row in rows:
			self.moveItem(row + 1, self.items[self.order[row]])

		self.addItem(index, item)

		self.items[item.name] = item
		self.order.insert(index, item.name)

		self.sz.Layout()

	def append(self, item):
		index = len(self.order)
		self.insert(index, item)

	def remove(self, name):
		index = self.order.index(name)
		del self.order[index]

		item = self.items[name]
		del self.items[name]

		self.destroyItem(item)

		for row in range(index, len(self.order)):
			self.moveItem(row, self.items[self.order[row]])

		self.sz.Layout()

	def sort(self, cmpfunc=None):
		order = list(self.order)
		order.sort(cmpfunc)
		for name in order:
			i = (self.order.index(name), order.index(name))
			if i[0] == i[1]:
				continue
			item = self.items[self.order[i[1]]]
			self.moveItem(len(self.order), item)
			self.moveItem(i[1], self.items[name])
			self.moveItem(i[0], item)
			self.order[i[0]], self.order[i[1]] = self.order[i[1]], self.order[i[0]]

		self.sz.Layout()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Selector Test')
			panel = wx.Panel(frame, -1)
			sizer = wx.GridBagSizer(0, 0)

			self.selector = Selector(panel)
			sizer.Add(self.selector, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 5)
			sizer.AddGrowableRow(0)
			sizer.AddGrowableCol(0)

			panel.SetSizerAndFit(sizer)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()

			return True

	app = App(0)
	app.selector.append(SelectorItem(app.selector, '7', 'node'))
	app.selector.append(SelectorItem(app.selector, '1', 'node'))
	app.selector.append(SelectorItem(app.selector, '4', 'node'))
	app.selector.append(SelectorItem(app.selector, '3', 'node'))
	app.selector.append(SelectorItem(app.selector, '5', 'node'))
	app.selector.append(SelectorItem(app.selector, '2', 'node'))
	app.selector.append(SelectorItem(app.selector, '6', 'node'))
	app.selector.append(SelectorItem(app.selector, '0', 'node'))
	app.selector.remove('2')
	app.selector.insert(3, SelectorItem(app.selector, 'asdf', 'node'))
	app.selector.remove('3')
	app.selector.sort()
	app.MainLoop()

