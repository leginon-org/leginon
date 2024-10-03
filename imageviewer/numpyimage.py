from pyami import numpil
Image = numpil.Image2
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
        raise TypeError
    height, width = array.shape
    size = width, height
    if 0 in size:
        raise ValueError
    stride = 0
    orientation = 1
    args = (mode, size, array.tobytes(), 'raw', rawmode, stride, orientation)
    return Image.frombuffer(*args)

def scaleImage(image, fromrange, torange):
    try:
        if fromrange[0] == fromrange[1]:
            raise ZeroDivisionError
        scale = float(torange[1] - torange[0])/float(fromrange[1] - fromrange[0])
    except ZeroDivisionError:
        scale = 0.0
    offset = scale*(torange[0] - fromrange[0])
    return image.point(lambda i: i * scale + offset)

def numpy2RGBImage(array, x=0, y=0, width=None, height=None,
                       imagewidth=None, imageheight=None,
                       fromrange=None, filter=Image.BICUBIC):
    '''
    Convert numpy array to RGBImage scaled and croped according the canvas
    and final image size.  The transformation method here is fast since
    PIL Image bin first before croping.  However, it makes binned K2 image looks
    really bad.  Use for zoomed image only now.
    '''
    # width and height is the canvas size.
    # imagewidth and imageheight is the image size after binning or zomming.
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

    # Filtering is especially useful on zoomed correlation image
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

def numpy2wxImageZoom(*args, **kwargs):
    rgbimage = numpy2RGBImage(*args, **kwargs)
    wximage = wx.Image(*rgbimage.size)
    wximage.SetData(numpil.pil_image_tobytes(rgbimage))
    return wximage

def numpy2wxImageBin(array, x=0, y=0, width=None, height=None,
                       imagewidth=None, imageheight=None,
                       array_offset_x=0, array_offset_y=0,
                       divide_factor=1,
                       fromrange=None, filter=Image.BICUBIC):
    '''
    use wx.Image methods to bin the image after crop to dividable
    image size.  The result displays k2 images better than numpy2RGBImage
    but is slower.
    '''
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
        rgbimage = image.convert('RGB')
        wximage = wx.Image(*rgbimage.size)
        wximage.SetData(numpil.pil_image_tobytes(rgbimage))
        return wximage

    sourcex0 = array_offset_x
    sourcey0 = array_offset_y
    sourcex1 = array_offset_x + imagewidth*divide_factor
    sourcey1 = array_offset_y + imageheight*divide_factor

    image = numpy2Image(array[sourcey0:sourcey1, sourcex0:sourcex1])

    if fromrange is None:
        fromrange = image.getextrema()

    # Scale Intensity
    image = scaleImage(image, fromrange, (0, 255))

    rgbimage = image.convert('RGB')

    wximage = wx.Image(*rgbimage.size)
    wximage.SetData(numpil.pil_image_tobytes(rgbimage))
    # Scale size
    wximage.Rescale(imagewidth,imageheight)
    # Crop to final size
    wximage.Resize((width,height),(x,y))
    return wximage

def numpy2wxBitmap(array, x=0, y=0, width=None, height=None,
                       imagewidth=None, imageheight=None,
                       array_offset_x=0, array_offset_y=0,
                       divide_factor=1,
                       fromrange=None, filter=Image.BICUBIC):
    if divide_factor > 1:
        return wx.Bitmap(numpy2wxImageBin(array, x, y, width, height, imagewidth, imageheight, array_offset_x, array_offset_y, divide_factor, fromrange, filter))
    else:
        return wx.Bitmap(numpy2wxImageZoom(array, x, y, width, height, imagewidth, imageheight, fromrange, filter))

if __name__ == '__main__':
    from pyami import mrc
    import sys

    array = mrc.read(sys.argv[1])

    #app = wx.App(0)
    #print(numpy2wxBitmap(array))

    numpy2RGBImage(array).show()
