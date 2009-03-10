#!/usr/bin/env python
import wx
from wx.lib.intctrl import IntCtrl
import os

class HMSControl(wx.Panel):
	def __init__(self, parent, id):
		wx.Panel.__init__(self, parent, id)
		self.sizer = wx.GridBagSizer()

		self.labelhour = wx.StaticText(self, label='Hours')
		self.controlhour = wx.SpinCtrl(self, min=0, max=1000, initial=0)
		self.labelmin = wx.StaticText(self, label='Minutes')
		self.controlmin = wx.SpinCtrl(self, min=0, max=59, initial=0)
		self.labelsec = wx.StaticText(self, label='Seconds')
		self.controlsec = wx.SpinCtrl(self, min=0, max=59, initial=0)

		self.sizer.Add(self.labelhour, (0,0))
		self.sizer.Add(self.labelmin, (0,1))
		self.sizer.Add(self.labelsec, (0,2))
		self.sizer.Add(self.controlhour, (1,0))
		self.sizer.Add(self.controlmin, (1,1))
		self.sizer.Add(self.controlsec, (1,2))

		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)

	def getValues(self):
		h = self.controlhour.GetValue()
		m = self.controlmin.GetValue()
		s = self.controlsec.GetValue()
		return h,m,s

class TimerWidget(wx.Panel):
	def __init__(self, parent, id, title, callable, *args, **kwargs):
		wx.Panel.__init__(self, parent, id)

		self.callable = callable
		self.callargs = args
		self.callkwargs = kwargs
		self.later = None

		box = wx.StaticBox(self, -1, label=title)
		self.sizer = wx.StaticBoxSizer(box)

		self.timervalues = HMSControl(self, -1)

		self.startbutton = wx.Button(self, -1, label='Start')
		self.Bind(wx.EVT_BUTTON, self.onStart, self.startbutton)
		self.cancelbutton = wx.Button(self, -1, label='Cancel')
		self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelbutton)
		self.cancelbutton.Enable(False)

		self.sizer.Add(self.timervalues)
		self.sizer.Add(self.startbutton)
		self.sizer.Add(self.cancelbutton)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)

	def onStart(self, evt):
		self.startbutton.Enable(False)
		self.cancelbutton.Enable(True)
		self.timervalues.Enable(False)
		values = self.timervalues.getValues()
		ms = 1000.0 * (values[2]+60*values[1]+3600*values[0])
		print 'MS', ms
		self.later = wx.FutureCall(ms, self.call)

	def onCancel(self, evt):
		self.later.Stop()
		self.startbutton.Enable(True)
		self.cancelbutton.Enable(False)
		self.timervalues.Enable(True)
		values = self.timervalues.getValues()

	def call(self):
		self.callable(*self.callargs, **self.callkwargs)
		self.onCancel(None)

def kill_linux(pid):
	os.kill(pid, 9)

def kill_windows(pid):
	import win32api
	PROCESS_TERMINATE = 1
	handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
	win32api.TerminateProcess(handle, -1)
	win32api.CloseHandle(handle)

if __name__ == '__main__':
	from pyScope import tecnai

	class MainWindow(wx.Frame):
		def __init__(self, parent, id, title):
			wx.Frame.__init__(self, parent, id)
			self.sizer = wx.BoxSizer()

			self.timer = TimerWidget(self, -1, title, self.myCallable)
			self.sizer.Add(self.timer)
			pidlabel = wx.StaticText(self, label='Process ID')
			self.pidvalue = IntCtrl(self, size=(60,25), allow_none=True, value=None)
			self.sizer.Add(pidlabel)
			self.sizer.Add(self.pidvalue)

			self.testbutton = wx.Button(self, label='Test')
			self.Bind(wx.EVT_BUTTON, self.onTest, self.testbutton)
			self.sizer.Add(self.testbutton)

			self.SetSizer(self.sizer)
			self.SetAutoLayout(1)
			self.sizer.Fit(self)
			self.Show(True)

		def onTest(self, evt):
			self.myCallable()

		def myCallable(self):
			pid = self.getPID()
			print 'Killing process %s...' % (pid,)
			try:
				kill_windows(pid)
			except:
				kill_linux(pid)
			print 'Killed.'
			print 'Setting Screen position down...'
			t.setMainScreenPosition('down')
			print 'Screen down...'
			print 'Closing column valves...'
			t = tecnai.Tecnai()
			t.setColumnValvePosition('closed')
			t.setColumnValvePosition('closed')
			print 'Closed.'
			print 'Setting High Tension Off...'
			import win32com.client
			t.tecnai.Gun.HTState = win32com.client.constants.htOff 
			print 'High Tension Off.'

		def getPID(self):
			pid = self.pidvalue.GetValue()
			print 'PID', type(pid)
			return pid

		

	app = wx.PySimpleApp()
	frame=MainWindow(None, wx.ID_ANY, 'Tecnai Kill Timer')
	app.MainLoop()




