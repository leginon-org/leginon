#!/usr/bin/env python
import sys
if len(sys.argv) < 3:
	print 'usage:    %s inst x|y label1 label2 label3....' % (sys.argv[0],)
	sys.exit(0)

import wx
import wx.lib.plot
import leginondata
import math
import gonmodel
import numpy

def querymodel(axis, hostname, label=None):
	tem = leginondata.InstrumentData(hostname=hostname)
	sm = leginondata.StageModelCalibrationData(axis=axis, tem=tem, label=label)
	model = sm.query(results=1)
	if not model:
		return None
	model = model[0]
	print 'MODEL', model.timestamp
	print model
	model['a'].shape = (-1,)
	model['b'].shape = (-1,)
	mod = gonmodel.GonModel()
	mod.fromDict(model)
	return mod

def querymodelmag(axis, label, hostname):
	tem = leginondata.InstrumentData(hostname=hostname)
	sm = leginondata.StageModelMagCalibrationData(axis=axis, label=label, tem=tem)
	magcal = sm.query(results=1)
	magcal = magcal[0]
	print 'MAGCAL', magcal.timestamp
	print magcal
	mean = magcal['mean']
	return 1.0 / mean

def normalizepoints(points, a0):
	return map(lambda x: (x[0],x[1]/a0/0.95), points)

def normalizemodel(points, a0):
	return map(lambda x: (x[0],x[1]*a0*0.95), points)

def querypoints(axis, label, hostname):
	tem = leginondata.InstrumentData(hostname=hostname)
	sm = leginondata.StageMeasurementData(label=label, axis=axis, tem=tem)
	points = sm.query()
	xy = []
	for point in points:
		x = point[axis]
		y = math.hypot(point['imagex'],point['imagey']) / abs(point['delta'])
		xy.append((x,y))
	return xy

def findrange(xy):
	minx = maxx = xy[0][0]
	miny = maxy = xy[0][1]
	for x,y in xy:
		if x > maxx: maxx = x
		if x < minx: minx = x
		if y > maxy: maxy = y
		if y < miny: miny = y
	return ((minx,maxx), (miny,maxy))

def modelpoints(model, xrange, step):
	x = numpy.arange(xrange[0], xrange[1], step)
	#x = tuple(x)
	y = map(model.eval, x)
	#y = map(lambda x: model.a0 * x, y)
	points = zip(x,y)
	return points

class MyFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, -1, "Plot")
		self.plotcan = wx.lib.plot.PlotCanvas(self)
		self.plotcan.SetFocus()

	def draw(self, *args):
		colors = 'red', 'green', 'blue', 'yellow'
		modelstep = 1e-7
		allpoints = []
		per =  0.0
		for points,mod in args:
			allpoints.extend(points)
			if mod.period > per:
				per = mod.period
		xaxis,yaxis = findrange(allpoints)
		xaxis = xaxis[0]-per, xaxis[1]+per
		for points,mod in args:
			modpoints = modelpoints(mod, xaxis, modelstep)
			allpoints.extend(modpoints)
		xaxis,yaxis = findrange(allpoints)

		objects = []
		for i, arg in enumerate(args):
			color = colors[i]
			poly = wx.lib.plot.PolyMarker(arg[0], colour=color, marker='triangle', width=1, size=0.5)
			objects.append(poly)
			xy = modelpoints(arg[1], xaxis, modelstep)
			poly = wx.lib.plot.PolyLine(xy, colour=color, width=2)
			objects.append(poly)

		graphics = wx.lib.plot.PlotGraphics(objects, 'My Plot', 'x', 'y')
		self.plotcan.Draw(graphics, xaxis, yaxis)

class MyApp(wx.PySimpleApp):
	def OnInit(self):
		self.frame = MyFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True


## args:  axis label label label
insthost = sys.argv[1]
axis = sys.argv[2]
labels = sys.argv[3:]

drawargs = []
for label in labels:
	points = querypoints(axis, label, insthost)
	modelmag = querymodelmag(axis, label, insthost)
	points = normalizepoints(points, modelmag)
	model = querymodel(axis, insthost, label=label)
	model.a0 = modelmag
	drawargs.append((points,model))

app = MyApp(0)
app.frame.draw(*drawargs)
app.MainLoop()
