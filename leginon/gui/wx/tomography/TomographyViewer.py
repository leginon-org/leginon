import wx
from imageviewer import events
from imageviewer import viewer

ImageEventType = wx.NewEventType()
EVT_IMAGE = wx.PyEventBinder(ImageEventType)

class ImageEvent(wx.PyEvent):
    def __init__(self, name, args, kwargs):
        wx.PyEvent.__init__(self)
        self.SetEventType(ImageEventType)
        self.name = name
        self.args = args
        self.kwargs = kwargs

class Viewer(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.imageviewer1 = viewer.Viewer(self, -1)
        self.imageviewer2 = viewer.Viewer(self, -1)
        self.xcviewer = viewer.Viewer(self, -1)

        self.viewers = (
            self.imageviewer1,
            self.imageviewer2,
            self.xcviewer,
        )

        for v in self.viewers:
            v.tools.sizescaler.SetStringSelection('Fit to page')
            evt = events.FitToPageEvent(self)
            v.tools.sizescaler.GetEventHandler().AddPendingEvent(evt)

        self.sizer = wx.GridBagSizer(16, 16)
        self.sizer.AddGrowableRow(0)
        for i, v in enumerate(self.viewers):
            self.sizer.Add(v, (0, i), (1, 1), wx.EXPAND)
            self.sizer.AddGrowableCol(i)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

        self.Bind(EVT_IMAGE, self.onImage)

    def onImage(self, evt):
        getattr(self, evt.name)(*evt.args, **evt.kwargs)

    def clearImages(self, *args, **kwargs):
        evt = ImageEvent('_clearImages', args, kwargs)
        self.GetEventHandler().AddPendingEvent(evt)

    def _clearImages(self, index=None):
        if index is None:
            for v in self.viewers:
                v.targetsplugin.clearTargets()
                v.setNumpy(None)
        else:
            self.viewers[index].targetsplugin.clearTargets()
            self.viewers[index].setNumpy(None)

    def setImage(self, *args, **kwargs):
        evt = ImageEvent('_setImage', args, kwargs)
        self.GetEventHandler().AddPendingEvent(evt)

    def _setImage(self, index, image, shift=None,use_extrema=False):
        self.viewers[index].targetsplugin.clearTargets()
        self.viewers[index].setNumpy(image,use_extrema)
        if image is not None and shift is not None:
            x, y = shift
            x += image.shape[1]/2
            y += image.shape[0]/2
            self.viewers[index].targetsplugin.addTargets([(x, y)])

    def _setShift(self, index, shift, center=True):
        self.viewers[index].targetsplugin.clearTargets()
        image = self.viewers[index].getNumpy()
        if image is None or shift is None:
            return
        x, y = shift
        if center:
            x += image.shape[1]/2
            y += image.shape[0]/2
        self.viewers[index].targetsplugin.addTargets([(x, y)])

    def setXC(self, *args, **kwargs):
        evt = ImageEvent('_setXC', args, kwargs)
        self.GetEventHandler().AddPendingEvent(evt)

    def _setXC(self, xc, shift=None):
				# change use_extrema to True for old style graph
        self.setImage(2, xc, shift=shift, use_extrema=False)

    def setXCShift(self, *args, **kwargs):
        evt = ImageEvent('_setXCShift', args, kwargs)
        self.GetEventHandler().AddPendingEvent(evt)

    def _setXCShift(self, shift, **kwargs):
        self._setShift(2, shift, **kwargs)

    def addImage(self, *args, **kwargs):
        evt = ImageEvent('_addImage', args, kwargs)
        self.GetEventHandler().AddPendingEvent(evt)

    def _addImage(self, image, foo=None):
        image1 = self.imageviewer1.getNumpy()
        image2 = self.imageviewer2.getNumpy()
        if image1 is None:
            self.imageviewer1.setNumpy(image)
        elif image2 is None:
            self.imageviewer2.setNumpy(image)
        else:
            self.imageviewer1.setNumpy(image2)
            self.imageviewer2.setNumpy(image)

if __name__ == '__main__':
    class MyApp(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'Image Viewer')
            self.panel = Viewer(frame, -1)
            frame.SetSize((768, 256))
            self.SetTopWindow(frame)
            frame.Show(True)
            return True

    app = MyApp(0)
    app.MainLoop()

