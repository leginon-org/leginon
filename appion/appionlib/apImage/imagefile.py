## pythonlib
import os
import subprocess
## PIL
from PIL import Image
from PIL import ImageDraw
## numpy
import numpy
from numpy import ma
## appion
from appionlib import apDisplay
from appionlib import apFile
from appionlib.apImage import imagenorm
## pyami
from pyami import mrc, imagefun, spider

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#===============================
def convertPostscriptToPng(psfile, pngfile, size=1024):

	### better pstopnm pre-step
	pstopnmcmd = "pstopnm -xsize=2000 -ysize=2000 -xborder=0 -yborder=0 -portrait "+psfile
	proc = subprocess.Popen(pstopnmcmd, shell=True)
	proc.wait()

	### direct conversion
	ppmfile = os.path.splitext(psfile)[0]+"001.ppm"
	if os.path.isfile(ppmfile):
		imagemagickcmd = ("convert -colorspace Gray -trim -resize "
			+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
	else:
		ppmfile = psfile+"001.ppm"
		if os.path.isfile(ppmfile):
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
		else:
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+psfile+" "+pngfile)
	proc = subprocess.Popen(imagemagickcmd, shell=True)
	proc.wait()

	if os.path.isfile(ppmfile):
		apFile.removeFile(ppmfile)

	if not os.path.isfile(pngfile):
		apDisplay.printWarning("Postscript image conversion failed")

#=========================
def imageToArray(im, convertType='uint8', dtype=None, msg=True):
	"""
	Convert PIL image to numpy array
	copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
	"""
	if im.mode == "L":
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a = numpy.reshape(a, (im.size[1], im.size[0]))
		#a.shape = (im.size[1], im.size[0], 1)  # alternate way
	elif (im.mode=='RGB'):
		apDisplay.printMsg("reading RGB and converting to L")
		grey = im.convert('L')
		a = numpy.fromstring(grey.tostring(), numpy.uint8)
		a = numpy.reshape(a, (grey.size[1], grey.size[0]))
	elif (im.mode=='RGBA'):
		apDisplay.printMsg("reading RGBA and converting to L")
		grey = im.convert('L')
		a = numpy.fromstring(grey.tostring(), numpy.uint8)
		a = numpy.reshape(a, (grey.size[1], grey.size[0]))
	else:
		raise ValueError, im.mode+" mode not considered"

	if convertType == 'float32':
		a = a.astype(numpy.float32)
	if dtype is not None:
		a = a.astype(dtype)

	return a

#=========================
def _arrayToImage(a):
	"""
	Converts array object (numpy) to image object (PIL).
	"""
	h, w = a.shape[:2]
	boolean = numpy.bool_
	int32 = numpy.int32
	uint32 = numpy.uint32
	float32 = numpy.float32
	float64 = numpy.float64

	if a.dtype==boolean or a.dtype==int32 or a.dtype==uint32 or a.dtype==float32 or a.dtype==float64:
		a = a.astype(numpy.uint8) # convert to 8-bit

	if len(a.shape)==3:
		if a.shape[2]==3:  # a.shape == (y, x, 3)
			r = Image.fromstring("L", (w, h), a[:,:,0].tostring())
			g = Image.fromstring("L", (w, h), a[:,:,1].tostring())
			b = Image.fromstring("L", (w, h), a[:,:,2].tostring())
			return Image.merge("RGB", (r,g,b))
		elif a.shape[2]==1:  # a.shape == (y, x, 1)
			return Image.fromstring("L", (w, h), a.tostring())
	elif len(a.shape)==2:  # a.shape == (y, x)
		return Image.fromstring("L", (w, h), a.tostring())
	else:
		raise ValueError, "unsupported image mode"

#=========================
def arrayToImage(numer, normalize=True, stdevLimit=3.0):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = imagenorm._maxNormalizeImage(numer, stdevLimit)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	return image

#=========================
def mrcToArray(filename, msg=True):
	"""
	takes a numpy and writes a Mrc
	"""
	numer = mrc.read(filename)
	if msg is True:
		apDisplay.printMsg("reading MRC: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	return numer

#=========================
def arrayToMrc(numer, filename, msg=True):
	"""
	takes a numpy and writes a Mrc
	"""
	#numer = numpy.asarray(numer, dtype=numpy.float32)
	if msg is True:
		apDisplay.printMsg("writing MRC: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	mrc.write(numer, filename)
	return

#=========================
def spiderToArray(filename, msg=True):
	"""
	takes a numpy and writes a SPIDER image
	"""
	numer = spider.read(filename)
	if msg is True:
		apDisplay.printMsg("reading SPIDER image: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	return numer

#=========================
def arrayToSpider(numer, filename, msg=True):
	"""
	takes a numpy and writes a SPIDER imag
	"""
	#numer = numpy.asarray(numer, dtype=numpy.float32)
	if msg is True:
		apDisplay.printMsg("writing SPIDER image: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	spider.write(numer, filename)
	return

#=========================
def arrayToJpeg(numer,filename,normalize=True, msg=True):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = imagenorm._maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	if msg is True:
		apDisplay.printMsg("writing JPEG: "+apDisplay.short(filename))
	image.save(filename, "JPEG", quality=85)
	return

#=========================
def arrayToPng(numer, filename, normalize=True, msg=True):
	"""
	takes a numpy and writes a PNG
	best for masks and line art
	"""
	if normalize:
		numer = imagenorm._maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	if msg is True:
		apDisplay.printMsg("writing PNG: "+apDisplay.short(filename))
	image.save(filename, "PNG")
	return

#=========================
def arrayMaskToPng(numer, filename, msg=True):
	"""
	Until PIL can read alpha channel again, the mask is on the main channel
	as 255
	"""
	arrayToPng(numer, filename, True, True)
	return

#=========================
def arrayMaskToPngAlpha(numer,filename, msg=True):
	"""
	Create PNG file of a binary mask (array with only 0 and 1)
	that uses the values in the alpha channel for transparency
	"""
	alpha=int(0.4*255)
	numera = numer*alpha
	numerones=numpy.ones(numpy.shape(numer))*255
	imagedummy = _arrayToImage(numerones)

	alphachannel = _arrayToImage(numera)

	image = imagedummy.convert('RGBA')
	image.putalpha(alphachannel)
	if msg is True:
		apDisplay.printMsg("writing alpha channel PNG mask: "+apDisplay.short(filename))
	image.save(filename, "PNG")
	return

#=========================
def PngAlphaToBinarryArray(filename):
	RGBAarray = readPNG(filename)
	print RGBAarray.shape
	alphaarray = RGBAarray[:,:,3]
	masked_alphaarray = ma.masked_greater_equal(alphaarray,50)
	bmask = masked_alphaarray.filled(1)
	return alphaarray

#=========================
def PngToBinarryArray(filename):
	RGBAarray = readPNG(filename)
	print RGBAarray.shape
	alphaarray = RGBAarray[:,:]
	masked_alphaarray = ma.masked_greater_equal(alphaarray,50)
	bmask = masked_alphaarray.filled(1)
	return alphaarray

#=========================
def arrayToJpegPlusPeak(numer, outfile, peak=None, normalize=True):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = imagenorm._maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	image = image.convert("RGB")

	if peak != None:
		draw = ImageDraw.Draw(image)
		peak2 = numpy.asarray(peak)
		for i in range(2):
			if peak[i] < 0:
				peak2[i] = (numer.shape)[i] + peak[i]
			elif peak[i] > (numer.shape)[i]:
				peak2[i] = peak[i] - (numer.shape)[i]
		drawPeak(peak2, draw, numer.shape)

	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=85)

	return

#=========================
def drawPeak(peak, draw, imshape, rad=10.0, color0="red", numshapes=4, shape="circle"):
	"""
	Draws a shape around a peak
	"""

	mycolors = {
		"red":		"#ff4040",
		"green":	"#3df23d",
		"blue":		"#3d3df2",
		"yellow":	"#f2f23d",
		"cyan":		"#3df2f2",
		"magenta":	"#f23df2",
		"orange":	"#f2973d",
		"teal":		"#3df297",
		"purple":	"#973df2",
		"lime":		"#97f23d",
		"skyblue":	"#3d97f2",
		"pink":		"#f23d97",
	}
	row1=float(peak[1])
	col1=float(peak[0])
	#Draw (numcircs) circles of size (circmult*pixrad)
	for count in range(numshapes):
		trad = rad + count
		coord=(row1-trad, col1-trad, row1+trad, col1+trad)
		if(shape == "square"):
			draw.rectangle(coord,outline=mycolors[color0])
		else:
			draw.ellipse(coord,outline=mycolors[color0])
	updown    = (0, imshape[1]/2, imshape[0], imshape[1]/2)
	leftright = (imshape[0]/2, 0, imshape[0]/2, imshape[1])
	draw.line(updown,   fill=mycolors['blue'])
	draw.line(leftright,fill=mycolors['blue'])
	return

#=========================
def readMRC(filename):
	return mrc.read(filename)

#=========================
def readJPG(filename):
	i = Image.open(filename)
	i.load()
	i = imageToArray(i)
	return i

#=========================
def readPNG(filename):
	i = Image.open(filename)
	i.load()
	i = imageToArray(i)
	return i

#=========================
def writeMrcStack(path, stackname, mrc_files, binning=1):
	apDisplay.printMsg("Writing MRC stack file... ")
	stackname = os.path.join(path, stackname)
	im = mrc.read(mrc_files[0])
	image = imagefun.bin(im, binning)
	mrc.write(image,stackname)
	del mrc_files[0]
	for mrcfile in mrc_files:
		im = mrc.read(mrcfile)
		image = imagefun.bin(im, binning)
		mrc.append(image, stackname)

#=========================
def shiftMRCStartToZero(filename):
	h = mrc.readHeaderFromFile(filename)
	if h['nxstart'] != 0 or h['nystart'] !=0:
		apDisplay.printMsg("Shifting image header start to zero on %s" %(os.path.basename(filename)))
		a = mrc.read(filename)
		mrc.write(a, filename)

####
# This is a low-level file with NO database connections
# Please keep it this way
####

