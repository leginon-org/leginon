import Image
import numpy

def read(imfile):
	im = Image.open(imfile)
	im = im.convert('L')
	width,height = im.size
	s = im.tostring()
	im = numpy.fromstring(s, numpy.uint8)
	im.shape = height,width
	return im
