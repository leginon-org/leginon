# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Query.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2004-12-16 18:56:59 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import leginondata
import dbdatakeeper
import unique
import wx


FieldSelectedEventType = wx.NewEventType()

EVT_FIELD_SELECTED = wx.PyEventBinder(FieldSelectedEventType)

class FieldSelectedEvent(wx.PyCommandEvent):
	def __init__(self, source, field, value):
		wx.PyCommandEvent.__init__(self, FieldSelectedEventType, source.GetId())
		self.SetEventObject(source)
		self.field = field
		self.value = value

class FieldSelector(wx.Panel):
	def __init__(self, fields, dbdatakeeper, queryinstance, *args, **kwargs):
		self.dbdatakeeper = dbdatakeeper
		self.queryinstance = queryinstance
		self.order = []
		self.map = {}
		wx.Panel.__init__(self, *args, **kwargs)
		self.sizer = wx.GridBagSizer(5, 5)

		choices = ['(Select a field)'] + fields
		self.fieldchoice = wx.Choice(self, -1, choices=choices)
		self.listbox = wx.ListBox(self, -1, choices=['All'])

		self.fieldchoice.SetSelection(0)
		self.onChoice(None)

		self.sizer.Add(self.fieldchoice, (0, 0), (1, 1), wx.EXPAND)
		self.sizer.Add(self.listbox, (1, 0), (1, 1), wx.EXPAND)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableRow(1)

		self.Bind(wx.EVT_CHOICE, self.onChoice, self.fieldchoice)
		self.Bind(wx.EVT_LISTBOX, self.onListBox, self.listbox)
		self.SetSizerAndFit(self.sizer)

	def getField(self):
		selection = self.fieldchoice.GetSelection()
		if selection is not None and selection > 0:
			field = self.fieldchoice.GetString(selection)
		else:
			field = None
		return field

	def onListBox(self, evt):
		field = self.getField()
		if evt is None:
			selection = self.listbox.GetSelection()
		else:
			selection = evt.GetSelection()
		if selection is not None and selection > 0:
			key = self.listbox.GetString(selection)
			value = self.map[key]
		else:
			value = None
		e = FieldSelectedEvent(self, field, value)
		self.GetEventHandler().AddPendingEvent(e)

	def onChoice(self, evt):
		if evt is None:
			selection = self.fieldchoice.GetSelection()
		else:
			selection = evt.GetSelection()
		self.listbox.Clear()
		if selection is not None and selection > 0:
			field = self.fieldchoice.GetString(selection)
			values = self.getValues(field)
			values = ['Any (%d possibilities)' % len(values)] + values
			self.listbox.AppendItems(values)

	def getValues(self, field):
		datalist = self.dbdatakeeper.query(self.queryinstance,
																				#results=64,
																				readimages=False)
		values = [i.special_getitem(field, False) for i in datalist]
		values = unique.unique(values)
		self.order = []
		self.map = {}
		for value in values:
			key = str(value)
			self.order.append(key)
			self.map[key] = value
		return self.order

class QueryPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		self.dbdatakeeper = dbdatakeeper.DBDataKeeper()
		wx.Panel.__init__(self, *args, **kwargs)
		self.sizer = wx.GridBagSizer(5, 5)

		choices = []
		for i in dir(leginondata):
			try:
				if issubclass(getattr(leginondata, i), leginondata.Data):
					choices.append(i)
			except TypeError:
				pass
		self.tablechoice = wx.Choice(self, -1, choices=choices)

		self.sizer.Add(self.tablechoice, (0, 0), (1, 1), wx.EXPAND)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableRow(1)

		self.fieldselectors = []

		if choices:
			self.tablechoice.SetSelection(0)
			self.onChoice(None)
		else:
			self.tablechoice.Enable(False)

		self.Bind(wx.EVT_CHOICE, self.onChoice, self.tablechoice)
		self.Bind(EVT_FIELD_SELECTED, self.onFieldSelected)
		self.SetSizerAndFit(self.sizer)

	def onFieldSelected(self, evt):
		self.queryinstance[evt.field] = evt.value

		fieldselector = evt.GetEventObject()
		index = self.fieldselectors.index(fieldselector) + 1
		indices = range(index, len(self.fieldselectors)) 
		indices.reverse()
		for i in indices:
			fs = self.fieldselectors[i]
			#fs = self.fieldselectors.pop(i)
			field = fs.getField()
			if field is not None:
				self.queryinstance[field] = None
			fs.onChoice(None)
			#self.sizer.Detach(fs)
			#fs.Destroy()

		if index == len(self.fieldselectors):
			fieldselector = FieldSelector(self.fields,
																		self.dbdatakeeper,
																		self.queryinstance,
																		self, -1)
			column = len(self.fieldselectors)
			self.sizer.Add(fieldselector, (1, column), (1, 1), wx.EXPAND)
			self.sizer.AddGrowableCol(column)
			self.sizer.Layout()
			self.fieldselectors.append(fieldselector)

	def onChoice(self, evt):
		for fs in self.fieldselectors:
			self.queryinstance = self.dataclass()
			self.sizer.Detach(fs)
			fs.Destroy()

		if evt is None:
			string = self.tablechoice.GetStringSelection()
		else:
			string = evt.GetString()
		self.dataclass = getattr(data, string)
		self.queryinstance = self.dataclass()
		self.fields = map(lambda typemap: typemap[0], self.dataclass.typemap())
		fieldselector = FieldSelector(self.fields,
																	self.dbdatakeeper,
																	self.queryinstance,
																	self, -1)
		self.sizer.Add(fieldselector, (1, 0), (1, 1), wx.EXPAND)
		self.sizer.Layout()
		self.fieldselectors = [fieldselector]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Query Test')
			panel = QueryPanel(frame, -1)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

