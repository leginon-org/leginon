#!/usr/bin/env python
import sys
if len(sys.argv) < 3:
	print 'usage:    %s x|y label1 label2 label3....' % (sys.argv[0],)
	sys.exit(0)

import wx
import wx.lib.plot
from dbdatakeeper import DBDataKeeper
import data
import math
import gonmodel
import numarray

db = DBDataKeeper()

def querymodel(axis, hostname):
	tem = data.InstrumentData(hostname=hostname)
	sm = data.StageModelCalibrationData(axis=axis, tem=tem)
	model = db.query(sm, results=1)
	if not model:
		return None
	model = model[0]
	model['a'].shape = (-1,)
	model['b'].shape = (-1,)
	mod = gonmodel.GonModel()
	mod.fromDict(model)
	return mod

def querymodelmag(axis, label, hostname):
	tem = data.InstrumentData(hostname=hostname)
	sm = data.StageModelMagCalibrationData(axis=axis, label=label, tem=tem)
	magcal = db.query(sm, results=1)
	mean = magcal[0]['mean']
	return 1.0 / mean

def normalizepoints(points, a0):
	return map(lambda x: (x[0],x[1]/a0), points)

def querypoints(axis, label, hostname):
	tem = data.InstrumentData(hostname=hostname)
	sm = data.StageMeasurementData(label=label, axis=axis, tem=tem)
	points = db.query(sm)
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
	x = numarray.arange(xrange[0], xrange[1], step)
	#x = tuple(x)
	y = map(model.eval, x)
	#y = map(lambda x: model.a0 * x, y)
	return zip(x,y)

class MyFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, -1, "Plot")
		self.plotcan = wx.lib.plot.PlotCanvas(self, -1)
		self.plotcan.SetFocus()

	def draw(self, *args):
		colors = 'blue','red','green','yellow'
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
	model = querymodel(axis, insthost)
	drawargs.append((points,model))

app = MyApp(0)
app.frame.draw(*drawargs)
app.MainLoop()
