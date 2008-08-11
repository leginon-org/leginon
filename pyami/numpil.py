import Image
import numpy
import imagefun
import arraystats

def read(imfile):
	'''
	Read imagefile using PIL and convert to a 8 bit gray image in numpy array.
	'''
	im = Image.open(imfile)
	im = im.convert('L')
	width,height = im.size
	s = im.tostring()
	im = numpy.fromstring(s, numpy.uint8)
	im.shape = height,width
	return im

def write(a, imfile):
	'''
	Convert array to 8 bit gray scale and save to filename.
	Format is determined from filename extension by PIL.
	'''
	mean = arraystats.mean(a)
	std = arraystats.std(a)
	limit = (mean-3*std, mean+3*std)
	a = imagefun.linearscale(a, limit, (0,255))
	a = numpy.asarray(a, numpy.uint8)
	size = a.shape[1], a.shape[0]
	im = Image.frombuffer('L', size, a)
	im.save(imfile)
