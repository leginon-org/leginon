# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Rings.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2005-12-03 01:36:47 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import IntEntry

RingsUpdatedEventType = wx.NewEventType()
EVT_RINGS_UPDATED = wx.PyEventBinder(RingsUpdatedEventType)
class RingsUpdatedEvent(wx.PyCommandEvent):
	def __init__(self, source, rings):
		wx.PyCommandEvent.__init__(self, RingsUpdatedEventType, source.GetId())
		self.SetEventObject(source)
		self.rings = rings

class Dialog(wx.Dialog):
	def __init__(self, parent, title, ring=None):
		wx.Dialog.__init__(self, parent, -1, title)
		sbszring = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Ring'), wx.VERTICAL)

		self.ieinside = IntEntry(self, -1, min=0, chars=4)
		self.ieoutside = IntEntry(self, -1, min=0, chars=4)

		if ring is not None:
			if not parent.validate(ring):
				raise ValueError
			inside, outside = ring
			self.ieinside.SetValue(inside)
			self.ieoutside.SetValue(outside)

		szring = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Inside')
		szring.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Outside')
		szring.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Diameter')
		szring.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szring.Add(self.ieinside, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szring.Add(self.ieoutside, (1, 2), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'pixels')
		szring.Add(label, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszring.Add(szring, 1, wx.EXPAND|wx.ALL, 5)

		self.bok = wx.Button(self, wx.ID_OK, 'OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bok, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszring, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onOK, self.bok)

	def onOK(self, evt):
		ring = (self.ieinside.GetValue(), self.ieoutside.GetValue())
		if not self.GetParent().validate(ring):
			dialog = wx.MessageDialog(self, 'Invalid ring dimensions', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.ring = ring
			evt.Skip()

class Panel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)

		self.lbrings = wx.ListBox(self, -1, style=wx.LB_SINGLE)
		self.badd = wx.Button(self, -1, 'Add...')
		self.bedit = wx.Button(self, -1, 'Edit...')
		self.bdelete = wx.Button(self, -1, 'Delete')

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Rings')
		sz.Add(label, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.lbrings, (1, 0), (1, 3), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(self.badd, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.bedit, (2, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bdelete, (2, 2), (1, 1), wx.ALIGN_CENTER)

		self.Bind(wx.EVT_BUTTON, self.onAddButton, self.badd)
		self.Bind(wx.EVT_BUTTON, self.onEditButton, self.bedit)
		self.Bind(wx.EVT_BUTTON, self.onDeleteButton, self.bdelete)
		self.Bind(wx.EVT_LISTBOX, self.onRingsListBox, self.lbrings)

		self._rings = []
		self._updated(False)

		self.SetSizerAndFit(sz)
		minsize = (sz.GetSize().width, self.lbrings.GetSize().height)
		sz.SetItemMinSize(self.lbrings, minsize)
		self.Fit()

	def _updated(self, evt=False):
		enable = self.lbrings.GetSelection() >= 0
		self.bedit.Enable(enable)
		enable = self.lbrings.GetSelection() >= 0 and self.lbrings.GetCount() > 1
		self.bdelete.Enable(enable)
		if evt:
			e = RingsUpdatedEvent(self, list(self._rings))
			self.GetEventHandler().AddPendingEvent(e)

	def onRingsListBox(self, evt):
		self._updated(False)

	def getRings(self):
		return list(self._rings)

	def setRings(self, rings):
		if len(rings) < 1:
			raise ValueError
		self.lbrings.Clear()
		self._rings = []
		for ring in rings:
			self._addRing(ring)
		self._updated(False)

	def onAddButton(self, evt):
		dialog = Dialog(self, 'Add Ring')
		if dialog.ShowModal() == wx.ID_OK:
			self._addRing(dialog.ring)
			self._updated(True)
		dialog.Destroy()

	def onEditButton(self, evt):
		n = self.lbrings.GetSelection()
		dialog = Dialog(self, 'Edit Ring', self._rings[n])
		if dialog.ShowModal() == wx.ID_OK:
			self._setRing(n, dialog.ring)
			self._updated(True)
		dialog.Destroy()

	def validate(self, ring):
		if None in ring:
			return False
		inside, outside = ring
		if inside < 0:
			return False
		if inside > outside:
			return False
		return True

	def _addRing(self, ring):
		if not self.validate(ring):
			raise ValueError
		string = 'Diameters - Inside: %s, Outside: %s' % ring
		self.lbrings.Append(string)
		self._rings.append(ring)

	def _setRing(self, n, ring):
		if not self.validate(ring):
			raise ValueError
		string = 'Diameters - Inside: %s, Outside: %s' % ring
		self.lbrings.SetString(n, string)
		self._rings[n] = ring

	def onDeleteButton(self, evt):
		selection = self.lbrings.GetSelection()
		if selection < 0:
			return
		del self._rings[selection]
		self.lbrings.Delete(selection)
		self._updated(True)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Rings Test')
			panel = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

