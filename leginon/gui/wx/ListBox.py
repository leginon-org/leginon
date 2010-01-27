import wx
import wx.lib.buttons

import leginon.gui.wx.Icons

class OrderListBox(wx.Panel):
    def __init__(self, parent, id, label, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        self._widgets(label)
        self._sizer()
        self._bind()

    def Enable(self, enable):
        wx.Panel.Enable(self, enable)
        self.Refresh()

    def _widgets(self, label):
        if label:
            self.storder = wx.StaticText(self, -1, label)
        self.listbox = wx.ListBox(self, -1,size=(124,-1), style=wx.LB_HSCROLL)
        self.upbutton = self._bitmapButton('up', 'Move item up in order')
        self.downbutton = self._bitmapButton('down', 'Move down in order')

    def _sizer(self):
        sizer = wx.GridBagSizer(3, 3)
        sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        sizer.Add(self.listbox, (1, 0), (2, 1), wx.EXPAND|wx.ALL)
        sizer.Add(self.upbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
        sizer.Add(self.downbutton, (2, 1), (1, 1),
                            wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
        sizer.AddGrowableRow(2)
        sizer.AddGrowableCol(0)
        self.SetSizerAndFit(sizer)

    def _bind(self):
        self.Bind(wx.EVT_BUTTON, self.onUp, self.upbutton)
        self.Bind(wx.EVT_BUTTON, self.onDown, self.downbutton)
        self.Bind(wx.EVT_LISTBOX, self.onSelect, self.listbox)

    def _bitmapButton(self, name, tooltip=None):
        bitmap = leginon.gui.wx.Icons.icon(name)
        button = wx.lib.buttons.GenBitmapButton(self, -1, bitmap, size=(20, 20))
        button.SetBezelWidth(1)
        button.Enable(False)
        if tooltip is not None:
            button.SetToolTip(wx.ToolTip(tooltip))
        return button

    def onUp(self, evt):
        n = self.listbox.GetSelection()
        if n > 0:
            string = self.listbox.GetString(n)
            self.listbox.Delete(n)
            self.listbox.InsertItems([string], n - 1)
            self.listbox.SetSelection(n - 1)
        self.updateButtons(n - 1)

    def onDown(self, evt):
        n = self.listbox.GetSelection()
        if n >= 0 and n < self.listbox.GetCount() - 1:
            string = self.listbox.GetString(n)
            self.listbox.Delete(n)
            self.listbox.InsertItems([string], n + 1)
            self.listbox.SetSelection(n + 1)
        self.updateButtons(n + 1)

    def getSelected(self):
        name = self.listbox.GetStringSelection()
        if not name:
            return None
        return name

    def setSelected(self, string):
        n = self.listbox.FindString(string)
        if n == wx.NOT_FOUND:
            return False
        self.listbox.SetSelection(n)
        return True

    def getValues(self):
        values = []
        for i in range(self.listbox.GetCount()):
            try:
                values.append(self.listbox.GetString(i))
            except ValueError:
                raise
        return values

    def setValues(self, values):
        self.Enable(False)

        filtered = []
        for v in values:
            if v:
                filtered.append(v)
        values = filtered

        string = self.listbox.GetStringSelection()

        count = self.listbox.GetCount()
        if values is None:
            values = []
        n = len(values)
        if count < n:
            nsame = count
        else:
            nsame = n
        for i in range(nsame):
            try:
                if self.listbox.GetString(i) != values[i]:
                    self.listbox.SetString(i, values[i])
            except ValueError:
                raise
        if count < n:
            self.listbox.InsertItems(values[nsame:], nsame)
        elif count > n:
            for i in range(count - 1, n - 1, -1):
                self.listbox.Delete(i)

        n = self.listbox.FindString(string)
        if n != wx.NOT_FOUND:
            self.listbox.SetSelection(n)
            self.updateButtons(n)

        self.Enable(True)

    def onSelect(self, evt):
        self.updateButtons(evt.GetInt())

    def updateButtons(self, n):
        if n > 0:
            self.upbutton.Enable(True)
        else:
            self.upbutton.Enable(False)
        if n < self.listbox.GetCount() - 1:
            self.downbutton.Enable(True)
        else:
            self.downbutton.Enable(False)

class EditListBox(OrderListBox):
    def __init__(self, parent, id, label, choices, **kwargs):
        self.choices = choices
        OrderListBox.__init__(self, parent, id, label, **kwargs)

    def _widgets(self, label):
        OrderListBox._widgets(self, label)
        if self.choices is None:
            self.textentry = wx.TextCtrl(self, -1, '')
        else:
            self.textentry = wx.ComboBox(self, -1, '', choices=self.choices)
        self.insertbutton = self._bitmapButton('plus', 'Insert item into list')
        self.deletebutton = self._bitmapButton('minus', 'Remove item from list')

    def _sizer(self):
        sizer = wx.GridBagSizer(3, 3)
        sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        sizer.Add(self.textentry, (1, 0), (1, 1),
                            wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
        sizer.Add(self.insertbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
        sizer.Add(self.listbox, (2, 0), (3, 1), wx.EXPAND|wx.ALL)
        sizer.Add(self.deletebutton, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
        sizer.Add(self.upbutton, (3, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
        sizer.Add(self.downbutton, (4, 1), (1, 1),
                            wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
        sizer.AddGrowableRow(4)
        sizer.AddGrowableCol(0)
        self.SetSizerAndFit(sizer)

    def _bind(self):
        OrderListBox._bind(self)
        self.Bind(wx.EVT_BUTTON, self.onInsert, self.insertbutton)
        self.Bind(wx.EVT_BUTTON, self.onDelete, self.deletebutton)
        self.Bind(wx.EVT_TEXT, self.onText, self.textentry)
    
    def setSelected(self, string):
        result = OrderListBox.setSelected(self, string)
        self.deletebutton.Enable(result)
        return result

    def onText(self, evt):
        if evt.GetString():
            if not self.insertbutton.IsEnabled():
                self.insertbutton.Enable(True)
        else:
            if self.insertbutton.IsEnabled():
                self.insertbutton.Enable(False)
        evt.Skip()

    def onInsert(self, evt):
        try:
            string = self.textentry.GetValue()
        except ValueError:
            return
        n = self.listbox.GetSelection()
        if n < 0:
            self.listbox.Append(string)
        else:
            self.listbox.InsertItems([string], n)
            self.updateButtons(n + 1)

    def onDelete(self, evt):
        n = self.listbox.GetSelection()
        if n >= 0:
            self.listbox.Delete(n)
        count = self.listbox.GetCount()
        if n < count:
            self.listbox.SetSelection(n)
            self.updateButtons(n)
        elif count > 0:
            self.listbox.SetSelection(n - 1)
            self.updateButtons(n - 1)
        else:
            self.deletebutton.Enable(False)

    def onSelect(self, evt):
        OrderListBox.onSelect(self, evt)
        self.deletebutton.Enable(True)

if __name__ == '__main__':
    class App(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'List Box Test')
            panel = EditListBox(frame, -1, 'Test', [])
            frame.Fit()
            self.SetTopWindow(frame)
            frame.Show()
            return True

    app = App(0)
    app.MainLoop()

