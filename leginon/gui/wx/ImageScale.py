import wx
from PIL import Image
from PIL import ImageDraw

PreviewScaleEventType = wx.NewEventType()
SetScaleEventType = wx.NewEventType()

EVT_PREVIEW_SCALE = wx.PyEventBinder(PreviewScaleEventType)
EVT_SET_SCALE = wx.PyEventBinder(SetScaleEventType)

class PreviewScaleEvent(wx.PyCommandEvent):
	def __init__(self, source, min, max):
		wx.PyCommandEvent.__init__(self, PreviewScaleEventType, source.GetId())
		self.SetEventObject(source)
		self.min = min
		self.max = max

class SetScaleEvent(wx.PyCommandEvent):
	def __init__(self, source, min, max):
		wx.PyCommandEvent.__init__(self, SetScaleEventType, source.GetId())
		self.SetEventObject(source)
		self.min = min
		self.max = max

def getGrayscaleColorMap():
	rgb = range(256)
	return zip(rgb, rgb, rgb)

def getRGBColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	colors = zip(r, g, b)
	return colors[:-256]

colormaps = {}

def addColorMap(name, colormap):
	image = Image.new('RGB', (len(colormap), 1))
	image.putdata(colormap)
	colormaps[name] = image

addColorMap('grayscale', getGrayscaleColorMap())
addColorMap('rgb', getRGBColorMap())

def getColorMapBitmap(image, scale, size):
	width, height = size
	if scale is None:
		image = image.resize((width, height), Image.BILINEAR)
	else:
		invert = scale[0] > scale[1]
		if invert:
			scale = (1 - scale[0], 1 - scale[1])
		scaledwidth = abs(int((scale[1] - scale[0])*width))
		subimage = image.resize((scaledwidth, height), Image.BILINEAR)
		image = Image.new('RGB', (width, height))
		offset = int(scale[0]*width)
		image.paste(subimage, (offset, 0))
		color = (colormap[0], colormap[-1])
		area = (((0, 0), (offset - 1, image.size[1] - 1)),
						((offset + subimage.size[0], 0), image.size))
		draw = ImageDraw.Draw(image)
		draw.rectangle(area[0], outline=color[0], fill=color[0])
		draw.rectangle(area[1], outline=color[1], fill=color[1])
		if invert:
			image = image.transpose(Image.FLIP_LEFT_RIGHT)
	wximage = wx.EmptyImage(*image.size)
	wximage.SetData(image.tostring())
	return wx.BitmapFromImage(wximage)

class ColorMapBitmap(wx.StaticBitmap):
	def __init__(self, *args, **kwargs):
		wx.StaticBitmap.__init__(self, *args, **kwargs)
		self.setColorMap('grayscale')
		self.setScale(None)
		self.updateBitmap()

	def setColorMap(self, colormap):
		if colormap not in colormaps:
			raise ValueError
		self.colormap = colormap

	def setScale(self, scale):
		self.scale = scale

	def updateBitmap(self):
		colormapimage = colormaps[self.colormap]
		bitmap = getColorMapBitmap(colormapimage, self.scale, self.GetSize())
		self.SetBitmap(bitmap)

class ScaleMixIn(object):
	def __init__(self):
		self.range = {'min': None, 'max': None}
		self.values = {'min': None, 'max': None}
		n = 256
		self.sizer = wx.GridBagSizer(3, 3)
		self.sliders = {
			'min': wx.Slider(self, -1, 0, 0, n, size=(n, -1)),
			'max': wx.Slider(self, -1, n, 0, n, size=(n, -1)),
		}
		self.textctrls = {
			'min': wx.TextCtrl(self, -1, '', style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER),
			'max': wx.TextCtrl(self, -1, '', style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER),
		}
		self.statictexts = {
			'min': wx.StaticText(self, -1, ''),
			'max': wx.StaticText(self, -1, ''),
		}

		self.sizer.Add(self.statictexts['min'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		self.sizer.Add(self.statictexts['max'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sizer.Add(self.sliders['min'], (1, 0), (1, 2), wx.ALIGN_CENTER)
		self.sizer.Add(self.sliders['max'], (2, 0), (1, 2), wx.ALIGN_CENTER)
		self.sizer.Add(self.textctrls['min'], (1, 2), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.textctrls['max'], (2, 2), (1, 1), wx.ALIGN_CENTER)

		self.setRange(**self.range)
		self.setValues(**self.values)

		self.SetSizerAndFit(self.sizer)
		self.Layout()

		self.Bind(wx.EVT_SCROLL, self.onScrollMin, self.sliders['min'])
		self.Bind(wx.EVT_SCROLL, self.onScrollMax, self.sliders['max'])
		self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocusMin, self.textctrls['min'])
		self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocusMax, self.textctrls['max'])
		self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnterMin, self.textctrls['min'])
		self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnterMax, self.textctrls['max'])

	def slider2value(self, key, value):
		slider = self.sliders[key]
		valuemin = self.range['min']
		valuerange = self.range['max'] - valuemin
		slidermin = slider.GetMin()
		sliderrange = slider.GetMax() - slidermin
		try:
			value = (float(value) - slidermin)/sliderrange
		except ZeroDivisionError:
			value = self.range[key]
		value = value*valuerange + valuemin
		value = self.clip(value)
		return type(self.values[key])(value)

	def value2slider(self, key, value):
		slider = self.sliders[key]
		if value is None:
			if key == 'min':
				return slider.GetMin()
			elif key == 'max':
				return slider.GetMax()
			else:
				raise ValueError
		valuemin = self.range['min']
		valuerange = self.range['max'] - valuemin
		slidermin = slider.GetMin()
		sliderrange = slider.GetMax() - slidermin
		try:
			value = (float(value) - valuemin)/valuerange
		except ZeroDivisionError:
			value = 0.5
		value = value*sliderrange + slidermin
		return int(value)

	def clip(self, value):
		if value < self.range['min']:
			return self.range['min']
		elif value > self.range['max']:
			return self.range['max']
		return value

	def onScroll(self, key, evt):
		value = self.slider2value(key, evt.GetPosition())
		kwargs = {key: value}
		self._setValues(**kwargs)
		self.setTextCtrls(**kwargs)
		evt = SetScaleEvent(self, self.values['min'], self.values['max'])
		self.GetEventHandler().AddPendingEvent(evt)

	def onScrollMin(self, evt):
		self.onScroll('min', evt)

	def onScrollMax(self, evt):
		self.onScroll('max', evt)

	def string2value(self, key, string):
		try:
			return self.clip(type(self.values[key])(string))
		except:
			return None

	def value2string(self, key, value):
		if value is None:
			return ''
		else:
			return '%g' % value

	def onText(self, key, string):
		value = self.string2value(key, string)
		if value is None:
			kwargs = {key: self.values[key]}
		else:
			kwargs = {key: value}
			self._setValues(**kwargs)
			self.setSliders(**kwargs)
		self.setTextCtrls(**kwargs)

	def onKillFocusMin(self, evt):
		self.onText('min', self.textctrls['min'].GetValue())
		evt.Skip()

	def onKillFocusMax(self, evt):
		self.onText('max', self.textctrls['max'].GetValue())
		evt.Skip()

	def onTextEnterMin(self, evt):
		self.onText('min', evt.GetString())
		evt.Skip()

	def onTextEnterMax(self, evt):
		self.onText('max', evt.GetString())
		evt.Skip()

	def setRange(self, **kwargs):
		for key in ['min', 'max']:
			try:
				self.range[key] = kwargs[key]
			except KeyError:
				continue
			if self.range[key] is None:
				string = ''
			else:
				string = '%g' % self.range[key]
			self.statictexts[key].SetLabel(string)
		self.setValues(**kwargs)

	def setTextCtrls(self, **kwargs):
		for key, textctrl in self.textctrls.items():
			try:
				value = kwargs[key]
				if value is None:
					textctrl.Enable(False)
				else:
					textctrl.Enable(True)
				textctrl.SetValue(self.value2string(key, value))
			except KeyError:
				pass

	def setSliders(self, **kwargs):
		for key, slider in self.sliders.items():
			try:
				value = kwargs[key]
				if value is None:
					slider.Enable(False)
				else:
					slider.Enable(True)
				slider.SetValue(self.value2slider(key, kwargs[key]))
			except KeyError:
				pass

	def _setValues(self, **kwargs):
		for key in self.values:
			try:
				self.values[key] = kwargs[key]
			except KeyError:
				pass

	def setValues(self, **kwargs):
		self._setValues(**kwargs)
		self.setSliders(**kwargs)
		self.setTextCtrls(**kwargs)

class Control(ColorMapBitmap):
	def __init__(self, *args, **kwargs):
		ColorMapBitmap.__init__(self, *args, **kwargs)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)

	def onLeftUp(self, evt):
		popup = ScalePopupWindow(self, style=wx.SIMPLE_BORDER)
		eventobject = evt.GetEventObject()
		position = eventobject.ClientToScreen((0, 0))
		size = eventobject.GetSize()
		popup.Position(position, (0, size.height))
		popup.Popup()

class ScalePopupWindow(wx.PopupTransientWindow, ScaleMixIn):
	def __init__(self, *args, **kwargs):
		wx.PopupTransientWindow.__init__(self, *args, **kwargs)
		ScaleMixIn.__init__(self)

	def OnDismiss(self):
		print 'asdf'

if __name__ == '__main__':
	import sys

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Scale Tool')
			self.sizer = wx.BoxSizer(wx.VERTICAL)
			self.panel = Control(frame, -1, size=(128, 16))
			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((512, 512))
			frame.Show(True)
			return True

	app = MyApp(0)
	app.MainLoop()

