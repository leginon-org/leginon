# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetTemplate.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-06 18:27:10 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
import math
from gui.wx.Entry import IntEntry

TemplateUpdatedEventType = wx.NewEventType()
EVT_TEMPLATE_UPDATED = wx.PyEventBinder(TemplateUpdatedEventType)
class TemplateUpdatedEvent(wx.PyCommandEvent):
	def __init__(self, source, template):
		wx.PyCommandEvent.__init__(self, TemplateUpdatedEventType, source.GetId())
		self.SetEventObject(source)
		self.template = template

class Dialog(wx.Dialog):
	def __init__(self, parent, title, target=None, targetname='Relative target'):
		wx.Dialog.__init__(self, parent, -1, title)

		self.targetname = targetname
		self.iex = IntEntry(self, -1, chars=4)
		self.iey = IntEntry(self, -1, chars=4)

		if target is not None:
			if not parent.validate(target):
				raise ValueError
			x, y = target
			self.iex.SetValue(x)
			self.iey.SetValue(y)

		sztarget = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'x')
		sztarget.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		sztarget.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, self.targetname)
		sztarget.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztarget.Add(self.iex, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sztarget.Add(self.iey, (1, 2), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'pixels')
		sztarget.Add(label, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsztarget = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Target'),
																		wx.VERTICAL)
		sbsztarget.Add(sztarget, 1, wx.EXPAND|wx.ALL, 5)

		self.bok = wx.Button(self, wx.ID_OK, 'OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bok, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbsztarget, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onOK, self.bok)

	def onOK(self, evt):
		target = (self.iex.GetValue(), self.iey.GetValue())
		if not self.GetParent().validate(target):
			dialog = wx.MessageDialog(self, 'Invalid target dimensions', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.target = target
			evt.Skip()

class Panel(wx.Panel):
	def __init__(self, parent, title, targetname='Relative target'):
		wx.Panel.__init__(self, parent, -1)

		self.targetname = targetname

		self.lbtemplate = wx.ListBox(self, -1, style=wx.LB_SINGLE)
		self.badd = wx.Button(self, -1, 'Add...')
		self.bedit = wx.Button(self, -1, 'Edit...')
		self.bdelete = wx.Button(self, -1, 'Delete')
		self.bautofill = wx.Button(self, -1, 'Auto Fill...')

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, title)
		sz.Add(label, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.lbtemplate, (1, 0), (2, 4), wx.EXPAND)
		sz.Add(self.badd, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.bedit, (3, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bdelete, (3, 2), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bautofill, (3, 3), (1, 1), wx.ALIGN_CENTER)
		sz.AddGrowableRow(1)
		sz.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onAddButton, self.badd)
		self.Bind(wx.EVT_BUTTON, self.onEditButton, self.bedit)
		self.Bind(wx.EVT_BUTTON, self.onDeleteButton, self.bdelete)
		self.Bind(wx.EVT_BUTTON, self.onAutoFillButton, self.bautofill)
		self.Bind(wx.EVT_LISTBOX, self.onTemplateListBox, self.lbtemplate)

		self._template = []
		self._updated(False)

		self.SetSizerAndFit(sz)
		minsize = (sz.GetSize().width, self.lbtemplate.GetSize().height)
		sz.SetItemMinSize(self.lbtemplate, minsize)
		self.Fit()

	def _updated(self, evt=False):
		enable = self.lbtemplate.GetSelection() >= 0
		self.bedit.Enable(enable)
		enable = enable and self.lbtemplate.GetCount() > 0
		self.bdelete.Enable(enable)
		if evt:
			e = TemplateUpdatedEvent(self, list(self._template))
			self.GetEventHandler().AddPendingEvent(e)

	def onTemplateListBox(self, evt):
		self._updated(False)

	def getTemplate(self):
		if len(self._template) < 0:
			raise RuntimeError
		return list(self._template)

	def setTemplate(self, template):
		if len(template) < 0:
			raise ValueError
		self.lbtemplate.Clear()
		self._template = []
		for target in template:
			self._addTarget(target)
		self._updated(False)

	def onAddButton(self, evt):
		dialog = Dialog(self, 'Add Target')
		if dialog.ShowModal() == wx.ID_OK:
			self._addTarget(dialog.target)
			self._updated(True)
		dialog.Destroy()

	def onEditButton(self, evt):
		n = self.lbtemplate.GetSelection()
		dialog = Dialog(self, 'Edit Target', self._template[n])
		if dialog.ShowModal() == wx.ID_OK:
			self._setTarget(n, dialog.target)
			self._updated(True)
		dialog.Destroy()

	def onAutoFillButton(self, evt):
		n = self.lbtemplate.GetSelection()
		dialog = AutoFillTargets(self, 'Auto Fill Targets')
		if dialog.ShowModal() == wx.ID_OK:
			for target in dialog.targets:
				self._addTarget(target)
			self._updated(True)
		dialog.Destroy()

	def validate(self, target):
		if None in target:
			return False
		return True

	def _addTarget(self, target):
		if not self.validate(target):
			raise ValueError
		string = '%s: (%s, %s)' % ((self.targetname,) + target)
		self.lbtemplate.Append(string)
		self._template.append(target)

	def _setTarget(self, n, target):
		if not self.validate(target):
			raise ValueError
		string = '%s: (%s, %s)' % ((self.targetname,) + target)
		self.lbtemplate.SetString(n, string)
		self._template[n] = target

	def onDeleteButton(self, evt):
		selection = self.lbtemplate.GetSelection()
		if selection < 0:
			return
		del self._template[selection]
		self.lbtemplate.Delete(selection)
		self._updated(True)

class AutoFillTargets(wx.Dialog):
	def __init__(self, parent, title, targetname='Relative target'):
		wx.Dialog.__init__(self, parent, -1, title)

		self.targetname = targetname
		self.numtargets = IntEntry(self, -1, chars=4, value='1')
		self.radius = IntEntry(self, -1, chars=4, value='100')
		self.angleoffset = IntEntry(self, -1, chars=4, value='0')
		self.targets = []

		valueentry = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'number of targets')
		valueentry.Add(label, (0, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL, 3)
		valueentry.Add(self.numtargets, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 3)

		label = wx.StaticText(self, -1, 'radius (pixels)')
		valueentry.Add(label, (1, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL, 3)
		valueentry.Add(self.radius, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 3)

		label = wx.StaticText(self, -1, 'angle offset (degrees)')
		valueentry.Add(label, (2, 0), (1, 1), wx.ALIGN_LEFT|wx.ALL, 3)
		valueentry.Add(self.angleoffset, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 3)

		self.bok = wx.Button(self, wx.ID_OK, 'OK')
		self.Bind(wx.EVT_BUTTON, self.onOK, self.bok)
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bok, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(valueentry, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(sz)

	def onOK(self, evt):
		numtargets = float(self.numtargets.GetValue())
		radius = float(self.radius.GetValue())
		degoffset = float(self.angleoffset.GetValue())
		deg = 0.0
		degincr = 360.0/numtargets
		while(deg < 359.9):
			rad = (deg + degoffset) * math.pi / 180.0
			x = int(math.sin(rad)*radius)
			y = int(math.cos(rad)*radius)
			target = (x, y)
			if not self.GetParent().validate(target):
				dialog = wx.MessageDialog(self, 'Invalid target dimensions (%d,%d)' % x,y, 'Error', wx.OK|wx.ICON_ERROR)
				dialog.ShowModal()
				dialog.Destroy()
			self.targets.append(target)
			deg += degincr
		evt.Skip()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Target Template Test')
			panel = Panel(frame, 'Test Template')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

