# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Entry.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2006-05-10 22:55:26 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
import re

EntryEventType = wx.NewEventType()

EVT_ENTRY = wx.PyEventBinder(EntryEventType)

class EntryEvent(wx.PyCommandEvent):
	def __init__(self, source, value):
		wx.PyCommandEvent.__init__(self, EntryEventType, source.GetId())
		self.SetEventObject(source)
		self.SetValue(value)

	def GetValue(self):
		return self.value

	def SetValue(self, value):
		self.value = value

class Entry(wx.TextCtrl):
	def __init__(self, parent, id, chars=None, allowspaces=True, **kwargs):
		try:
			if not kwargs['style'] & wx.TE_MULTILINE:
				kwargs['style'] |= wx.TE_PROCESS_ENTER
		except KeyError:
			kwargs['style'] = wx.TE_PROCESS_ENTER

		wx.TextCtrl.__init__(self, parent, id, **kwargs)
		if chars is not None:
			size = self.GetClientSize()
			# ppi?
			size.width = self.GetFont().GetPointSize()*chars + 2
			self.SetClientSize(size)

		self.dirty = False
		self.cleancolor = self.GetBackgroundColour()
		self.dirtycolor = wx.Color(196, 225, 255)
		self.allowspaces = allowspaces

		stuff = wx.TextCtrl.GetValue(self)
		if not self._setStringValue(stuff):
			raise ValueError

		self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
		self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.Bind(wx.EVT_CHAR, self.onChar)

	def valueToString(self, value):
		return value

	def stringToValue(self, string):
		if self.allowspaces is False:
			string = re.sub(" ","",string)
		return string

	def _validateString(self, string):
		return True

	def _validateValue(self, string):
		return True

	def _setDirty(self, value):
		if value == self.dirty:
			return
		self.dirty = value
		if self.dirty:
			self.SetBackgroundColour(self.dirtycolor)
			self.Refresh()
		else:
			self.SetBackgroundColour(self.cleancolor)
			self.Refresh()

	def _setValue(self, value):
		if not self._validateValue(value):
			return False
		self.value = value
		self._setDirty(False)
		return True

	def _setStringValue(self, string):
		if self._validateString(string):
			self.SetValue(self.stringToValue(string))
			return True
		else:
			return False

	def SetValue(self, value):
		if not self._setValue(value):
			raise ValueError
		wx.TextCtrl.SetValue(self, self.valueToString(value))

	def GetValue(self):
		return self.value

	def setStringValue(self, string):
		if self.dirty:
			self._setStringValue(string)
			evt = EntryEvent(self, self.value)
			self.GetEventHandler().AddPendingEvent(evt)

	def onKillFocus(self, evt):
		self.setStringValue(wx.TextCtrl.GetValue(self))
		evt.Skip()

	def onTextEnter(self, evt):
		self.setStringValue(evt.GetString())
		evt.Skip()

	def onChar(self, evt):
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			wx.TextCtrl.SetValue(self, self.valueToString(self.value))
			self._setDirty(False)
		else:
			# this isn't necessarily true
			self._setDirty(True)
		evt.Skip()

class TypeEntry(Entry):
	_nonestring = ''
	def __init__(self, parent, id, allownone=True, **kwargs):
		self.allownone = allownone
		Entry.__init__(self, parent, id, **kwargs)

	def valueToString(self, value):
		if value is None:
			return self._nonestring
		return str(value)

	def stringToValue(self, string):
		if string == self._nonestring:
			return None
		return self._type(string)

	def _validateValue(self, value):
		if value == None:
			return self.allownone
		try:
			self._type(value)
		except:
			return False
		return True

	def _validateString(self, string):
		if string is None:
			string = self._nonestring
		try:
			value = self.stringToValue(string)
		except:
			return False
		return self._validateValue(value)

class TypeSequenceEntry(TypeEntry):
	def valueToString(self, value):
		if not value:
			return self._nonestring
		return ', '.join(map(str, value))

	def stringToValue(self, string):
		print 'STRING', string
		if string == '':
			return None
		strings = string.split(',')
		stuff = TypeEntry.stringToValue
		values = map(TypeEntry.stringToValue, strings)
		return tuple(values)

	def _validateString(self, string):
		try:
			value = self.stringToValue(string)
			return True
		except:
			return False

class NumberEntry(TypeEntry):
	def __init__(self, parent, id, min=None, max=None, values=None, **kwargs):
		try:
			kwargs['style'] |= wx.TE_RIGHT
		except KeyError:
			kwargs['style'] = wx.TE_RIGHT

		self.min = min
		self.max = max
		self.values = values

		TypeEntry.__init__(self, parent, id, **kwargs)

	def _validateValue(self, value):
		if value is not None:
			if self.values is not None and value not in self.values:
				return False
			if self.min is not None and value < self.min:
				return False
			if self.max is not None and value > self.max:
				return False
		return TypeEntry._validateValue(self, value)

class IntEntry(NumberEntry):
	_type = int

class FloatEntry(NumberEntry):
	_type = float

	def valueToString(self, value):
		if value is None:
			return self._nonestring
		return '%g' % value

class FloatSequenceEntry(TypeSequenceEntry):
	_type = float

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Entry Test')
			panel = wx.Panel(frame, -1)
			sizer = wx.GridBagSizer(5, 5)
			self.entry = Entry(panel, -1)
			self.intentry = IntEntry(panel, -1, values=[1, 2, 3, 5])
			self.floatentry = FloatEntry(panel, -1, min=1, max=2, chars=4)
			sizer.Add(self.entry, (0, 0), (1, 1),
								wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, border=5)
			sizer.Add(self.intentry, (1, 0), (1, 1),
								wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, border=5)
			sizer.Add(self.floatentry, (2, 0), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE, border=5)
			sizer.AddGrowableCol(0)
			panel.SetSizerAndFit(sizer)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

