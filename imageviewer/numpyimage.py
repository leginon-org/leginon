from PIL import Image
import math
import numpy
import wx

typemap = {
    numpy.uint8: ('L', 'L'),
    numpy.uint16: ('I', 'I;16N'),
    numpy.uint32: ('I', 'I;32N'),
    numpy.uint64: ('I', 'I;32N'),
    numpy.int16: ('I', 'I;16NS'),
    numpy.int32: ('I', 'I;32NS'),
    numpy.int64: ('I', 'I;32NS'),
    numpy.float32: ('F', 'F;32NF'),
    numpy.float64: ('F', 'F;64NF')
}

def numpy2Image(array):
    arraytype = array.dtype.type
    try:
        mode, rawmode = typemap[arraytype]
    except KeyError:
        print 'TYPE', arraytype
        raise TypeError
    height, width = array.shape
    size = width, height
    if 0 in size:
        raise ValueError
    stride = 0
    orientation = 1
    args = (mode, size, array.tostring(), 'raw', rawmode, stride, orientation)
    return Image.frombuffer(*args)

def scaleImage(image, fromrange, torange):
    try:
        scale = float(torange[1] - torange[0])/float(fromrange[1] - fromrange[0])
    except ZeroDivisionError:
        scale = 0.0
    offset = scale*(torange[0] - fromrange[0])
    return image.point(lambda i: i * scale + offset)

def numpy2RGBImage(array, x=0, y=0, width=None, height=None,
                       imagewidth=None, imageheight=None,
                       fromrange=None, filter=Image.BICUBIC):
    if imagewidth is None:
        imagewidth = array.shape[1]
    if imageheight is None:
        imageheight = array.shape[0]

    if width is None:
        width = imagewidth - x
    if height is None:
        height = imageheight - y

    if imagewidth == array.shape[1] and imageheight == array.shape[0]:
        image = numpy2Image(array[y:y + height, x:x + width])
        if fromrange is None:
            fromrange = image.getextrema()
        image = scaleImage(image, fromrange, (0, 255))
        return image.convert('RGB')

    if filter == Image.NEAREST:
        pad = 1
    elif filter == Image.BILINEAR:
        pad = 1
    elif filter == Image.BICUBIC:
        pad = 2
    else:
        pad = 0

    scalex = (float(imagewidth)/array.shape[1])
    scaley = (float(imageheight)/array.shape[0])

    scaledx = x/scalex
    scaledy = y/scaley
    scaledwidth = width/scalex
    scaledheight = height/scaley

    sourcex0 = max(0, int(math.floor(scaledx - pad)))
    sourcey0 = max(0, int(math.floor(scaledy - pad)))
    sourcex1 = min(array.shape[1], int(math.ceil(scaledx + scaledwidth + pad)))
    sourcey1 = min(array.shape[0], int(math.ceil(scaledy + scaledheight + pad)))

    image = numpy2Image(array[sourcey0:sourcey1, sourcex0:sourcex1])

    left = scaledx - sourcex0
    upper = scaledy - sourcey0
    right = left + scaledwidth
    bottom = upper + scaledheight
    image = image.transform((width, height), Image.EXTENT,
                            (left, upper, right, bottom), filter)

    if fromrange is None:
        fromrange = image.getextrema()

    # ?
    image = scaleImage(image, fromrange, (0, 255))

    return image.convert('RGB')

def numpy2wxImage(*args, **kwargs):
    rgbimage = numpy2RGBImage(*args, **kwargs)
    wximage = wx.EmptyImage(*rgbimage.size)
    wximage.SetData(rgbimage.tostring())
    return wximage

def numpy2wxBitmap(*args, **kwargs):
    return wx.BitmapFromImage(numpy2wxImage(*args, **kwargs))

if __name__ == '__main__':
    import Mrc
    import sys

    array = Mrc.mrc_to_numeric(sys.argv[1])

    #app = wx.App(0)
    #print numpy2wxBitmap(array)

    numpy2RGBImage(array).show()
