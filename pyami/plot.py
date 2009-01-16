#!/usr/bin/env python

import wxmpl

class PlotPanel(wxmpl.PlotPanel):
	def plot(self, *args):
		if len(args) == 1:
			x = range(len(args[0]))
			y = args[0]
		elif len(args) == 2:
			x = args[0]
			y = args[1]
		fig = self.get_figure()
		axes = fig.gca()
		axes.plot(x,y)

	def clear(self):
		fig = self.get_figure()
		axes = fig.gca()
		axes.cla()
		

if __name__ == '__main__':
	import wx

	import numextension
	from pyami import mrc
	from pyami import imagefun
	import sys
	im = mrc.read(sys.argv[1])
	pow = imagefun.power(im)
	b = numextension.radialPower(pow, 5, 20)

	app = wx.PySimpleApp()
	frame = wx.Frame(None, -1, title='My Plot')
	plotpanel = PlotPanel(frame, -1)
	#b = [2,3,5,4,3]
	plotpanel.plot(b)
	frame.Show()
	app.MainLoop()
