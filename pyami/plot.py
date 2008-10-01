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

if __name__ == '__main__':
	import mrc
	import sys
	import numextension
	import imagefun
	import numpil
	import wx
	a = mrc.read(sys.argv[1])
	low = float(sys.argv[2])
	high = float(sys.argv[3])

	print 'SHAPE', a.shape
	#pow = imagefun.power(a)
	#numpil.write(pow, 'pow.png')
	b = numextension.radialPower(a, low, high)

	app = wx.PySimpleApp()
	frame = wx.Frame(None, -1, title='My Plot')
	plotpanel = PlotPanel(frame, -1)
	plotpanel.plot(b)
	frame.Show()
	app.MainLoop()
