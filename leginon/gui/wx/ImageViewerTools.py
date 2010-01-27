import numpy
import wx

import imageviewer.numarrayimage

import leginon.gui.wx.ImageViewerEvents as Events

class Display(wx.Panel):
	def __init__(self, *args, **kwargs):
		self.crosshairs = False

		wx.Panel.__init__(self, *args, **kwargs)

		self.sizer = wx.GridBagSizer(0, 0)

		self.crosshairsbutton = wx.Button(self, -1, 'Crosshairs')
		self.sizer.Add(self.crosshairsbutton, (0, 0), (1, 1), wx.ALIGN_CENTER)

		self.sizer.AddGrowableCol(0)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

		self.Bind(wx.EVT_BUTTON, self.onCrosshairsButton, self.crosshairsbutton)

	def onCrosshairsButton(self, evt):
		self.crosshairs = not self.crosshairs
		evt = Events.DisplayCrosshairsEvent(self, self.crosshairs)
		self.GetEventHandler().AddPendingEvent(evt)

class Information(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sizer = wx.GridBagSizer(0, 0)

		self.valuepanel = Value(self, -1)
		self.statspanel = Statistics(self, -1)

		self.sizer.Add(self.statspanel, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.valuepanel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

	def setValue(self, *args, **kwargs):
		self.valuepanel.setValue(*args, **kwargs)
		self.sizer.Layout()

	def setStatistics(self, *args, **kwargs):
		self.statspanel.setStatistics(*args, **kwargs)
		self.sizer.Layout()

class Value(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sizer = wx.GridBagSizer(0, 3)

		self.xlabel = wx.StaticText(self, -1)
		self.ylabel = wx.StaticText(self, -1)
		self.valuelabel = wx.StaticText(self, -1)

		label = wx.StaticText(self, -1, 'x:')
		self.sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.xlabel, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'y:')
		self.sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.ylabel, (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Value:')
		self.sizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.valuelabel, (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.sizer.AddGrowableCol(1)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

	def setValue(self, x=None, y=None, value=None):
		if x is None:
			xstr = ''
		else:
			xstr = '%g' % x

		if y is None:
			ystr = ''
		else:
			ystr = '%g' % y

		if value is None:
			valuestr = ''
		else:
			valuestr = '%g' % value

		self.xlabel.SetLabel(xstr)
		self.ylabel.SetLabel(ystr)
		self.valuelabel.SetLabel(valuestr)

		self.sizer.Layout()

class Statistics(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sizer = wx.GridBagSizer(0, 3)

		self.meanlabel = wx.StaticText(self, -1)
		self.minlabel = wx.StaticText(self, -1)
		self.maxlabel = wx.StaticText(self, -1)
		self.sdlabel = wx.StaticText(self, -1)

		label = wx.StaticText(self, -1, 'Mean:')
		self.sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.meanlabel, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min.:')
		self.sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.minlabel, (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max.:')
		self.sizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.maxlabel, (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Std. Dev.:')
		self.sizer.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.sdlabel, (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.sizer.AddGrowableCol(1)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

	def setStatistics(self, array=None, statistics={}):
		try:
			mean = statistics['mean']
		except KeyError:
			if array is None:
				mean = None
			else:
				mean = array.mean()
		try:
			min = statistics['min']
		except KeyError:
			if array is None:
				min = None
			else:
				min = array.min()
		try:
			max = statistics['max']
		except KeyError:
			if array is None:
				max = None
			else:
				max = array.max()
		try:
			sd = statistics['stdev']
		except KeyError:
			if array is None:
				sd = None
			else:
				sd = array.stddev()

		if mean is None:
			meanstr = ''
		else:
			meanstr = '%g' % mean
		if min is None:
			minstr = ''
		else:
			minstr = '%g' % min
		if max is None:
			maxstr = ''
		else:
			maxstr = '%g' % max 
		if sd is None:
			sd = ''
		else:
			sdstr = '%g' % sd

		self.meanlabel.SetLabel(meanstr)
		self.minlabel.SetLabel(minstr)
		self.maxlabel.SetLabel(maxstr)
		self.sdlabel.SetLabel(sdstr)

		self.sizer.Layout()

class SizeScaler(wx.Choice):
	def __init__(self, parent, id):
		self.percentages = [10, 25, 50, 75, 100, 125, 150, 200, 400, 800, 1600]
		choices = [('%d' % percentage) + '%' for percentage in self.percentages]
		choices.append('Fit to page')
		wx.Choice.__init__(self, parent, id, choices=choices)
		self.SetSelection(self.percentages.index(100))
		self.Bind(wx.EVT_CHOICE, self.onChoice)

	def getScale(self):
		i = self.GetSelection()
		return self.percentages[i]/100.0

	def onChoice(self, evt):
		evt.Skip()

		string = evt.GetString()
		if string == 'Fit to page':
			evt = Events.FitToPageEvent(self)
		else:
			i = evt.GetSelection()
			scale = self.percentages[i]/100.0
			evt = Events.ScaleSizeEvent(self, scale)
		self.GetEventHandler().AddPendingEvent(evt)

class ValueScaleBitmap(wx.StaticBitmap):
	def __init__(self, parent, id,
								extrema=(0, 255), fromrange=(0, 255), size=(256, 16)):
		wx.StaticBitmap.__init__(self, parent, id, size=size)
		self.updateParameters(extrema, fromrange)

	def updateParameters(self, extrema=None, fromrange=None):
		if extrema is not None:
			self.extrema = extrema
		if fromrange is not None:
			self.fromrange = fromrange
		self.updateBitmap()

	def updateBitmap(self):
		width, height = self.GetSize()
		types = [type(i) for i in self.fromrange]
		if float in types:
			arraytype = numpy.float
		elif int in types:
			arraytype = numpy.int
		else:
			raise TypeError

		array = numpy.arange(width, type=numpy.float, shape=(1, width))
		array *= float(self.extrema[1] - self.extrema[0])/(width - 1)
		array += self.extrema[0]
		array = numpy.asarray(array, arraytype)
		array = array.repeat(height)

		bitmap = imageviewer.numarrayimage.numarray2wxBitmap(array, fromrange=self.fromrange)
		self.SetBitmap(bitmap)

class ValueScaler(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.valuerange = None
		self.extrema = None
		self.type = None

		self.sizer = wx.GridBagSizer(3, 3)

		self.minlabel = wx.StaticText(self, -1)
		self.maxlabel = wx.StaticText(self, -1)

		self.minentry = wx.TextCtrl(self, -1, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
		self.maxentry = wx.TextCtrl(self, -1, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
		self.minentry.Enable(False)
		self.maxentry.Enable(False)

		self.minslider = wx.Slider(self, -1, 0, 0, 0)
		self.maxslider = wx.Slider(self, -1, 0, 0, 0)
		self.minslider.Enable(False)
		self.maxslider.Enable(False)

		self.sizer.Add(self.minlabel, (0, 1), (1, 1),
										wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.maxlabel, (0, 2), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.minentry, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.maxentry, (2, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.minslider, (1, 1), (1, 2), wx.EXPAND)
		self.sizer.Add(self.maxslider, (2, 1), (1, 2), wx.EXPAND)

		self.sizer.AddGrowableCol(1)
		self.sizer.AddGrowableCol(2)

		self.Bind(wx.EVT_SIZE, self.onSize)
		self.minentry.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
		self.maxentry.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
		self.minentry.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.maxentry.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.minslider.Bind(wx.EVT_SCROLL, self.onScroll)
		self.maxslider.Bind(wx.EVT_SCROLL, self.onScroll)

		self.SetSizer(self.sizer)
		self.sizer.Layout()

	def setValueRange(self, extrema, valuerange=None):
		if valuerange is None:
			valuerange = extrema

		self.valuerange = valuerange
		self.extrema = extrema

		if self.extrema is None:
			self.type = None
			self.minentry.Enable(False)
			self.maxentry.Enable(False)
			self.minslider.Enable(False)
			self.maxslider.Enable(False)
			self.minlabel.SetLabel('')
			self.maxlabel.SetLabel('')
			self.minentry.SetValue('')
			self.maxentry.SetValue('')
			self.minslider.SetValue(self.minslider.GetMin())
			self.maxslider.SetValue(self.maxslider.GetMax())
		else:
			types = [type(value) for value in self.valuerange + self.extrema]
			if float in types:
				self.type = float
			elif int in types:
				self.type = int
			else:
				raise TypeError
			self.minlabel.SetLabel('%g' % extrema[0])
			self.maxlabel.SetLabel('%g' % extrema[1])
			self.minentry.SetValue('%g' % valuerange[0])
			self.maxentry.SetValue('%g' % valuerange[1])
			slidermin = self.minslider.GetMin()
			slidermax = self.maxslider.GetMax()
			sliderscale = float(slidermax - slidermin)/(extrema[1] - extrema[0])
			self.minslider.SetValue(
				int(round((valuerange[0] - extrema[0])*sliderscale + slidermin)))
			self.maxslider.SetValue(
				int(round((valuerange[1] - extrema[0])*sliderscale + slidermin)))
			self.minentry.Enable(True)
			self.maxentry.Enable(True)
			self.minslider.Enable(True)
			self.maxslider.Enable(True)

	def onEntry(self, eventobject, string):
		try:
			value = self.type(string)
		except:
			if eventobject is self.minentry:
				eventobject.SetValue('%g' % self.valuerange[0])
			elif eventobject is self.maxentry:
				eventobject.SetValue('%g' % self.valuerange[1])
			return
		if value < self.extrema[0] or value > self.extrema[1]:
			if value < self.extrema[0]:
				value = self.extrema[0]
			elif value > self.extrema[1]:
				value = self.extrema[1]
			eventobject.SetValue('%g' % value)
		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		extremarange = self.extrema[1] - self.extrema[0]
		sliderscale = float(slidermax-slidermin)/extremarange
		if eventobject is self.minentry:
			self.valuerange = (value, self.valuerange[1])
			self.minslider.SetValue(
				int(round((value - self.extrema[0])*sliderscale + slidermin)))
		elif eventobject is self.maxentry:
			self.valuerange = (self.valuerange[0], value)
			self.maxslider.SetValue(
				int(round((value - self.extrema[0])*sliderscale + slidermin)))

		evt = Events.ScaleValuesEvent(self, self.valuerange)
		self.GetEventHandler().AddPendingEvent(evt)

	def onKillFocus(self, evt):
		eventobject = evt.GetEventObject()
		string = eventobject.GetValue()
		self.onEntry(eventobject, string)
		evt.Skip()

	def onTextEnter(self, evt):
		eventobject = evt.GetEventObject()
		string = evt.GetString()
		self.onEntry(eventobject, string)
		evt.Skip()

	def onSize(self, evt):
		width, height = evt.GetSize()

		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		minvalue = self.minslider.GetValue()
		maxvalue = self.maxslider.GetValue()

		self.minslider.SetRange(0, width)
		self.maxslider.SetRange(0, width)

		try:
			scale = float(width)/(slidermax - slidermin)
		except ZeroDivisionError:
			minvalue = 0
			maxvalue = width
		else:
			minvalue = int(round((minvalue - slidermin)*scale))
			maxvalue = int(round((maxvalue - slidermin)*scale))

		self.minslider.SetValue(minvalue)
		self.maxslider.SetValue(maxvalue)
		evt.Skip()

	def onScroll(self, evt):
		eventobject = evt.GetEventObject()
		slidermin = self.minslider.GetMin()
		slidermax = self.maxslider.GetMax()
		extremarange = self.extrema[1] - self.extrema[0]
		sliderscale = float(slidermax - slidermin)/extremarange
		position = evt.GetPosition()
		value = self.type((position - slidermin)/sliderscale + self.extrema[0])
		if eventobject is self.minslider:
			self.minentry.SetValue('%g' % value)
			self.valuerange = (value, self.valuerange[1])
		elif eventobject is self.maxslider:
			self.maxentry.SetValue('%g' % value)
			self.valuerange = (self.valuerange[0], value)

		evt.Skip()

		evt = Events.ScaleValuesEvent(self, self.valuerange)
		self.GetEventHandler().AddPendingEvent(evt)

if __name__ == '__main__':
	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = ValueScaler(frame, -1)
			#self.panel = SizeScaler(frame, -1)
			self.panel = Statistics(frame, -1)

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)
	app.MainLoop()

