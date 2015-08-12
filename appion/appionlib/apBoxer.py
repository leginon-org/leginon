#!/usr/bin/env python
"""
This is a collection of function that
replace the EMAN1 batchboxer program with
added features like helical boxing at an
angle
"""

import sys
import math
import numpy
from pyami import mrc
from scipy import ndimage	#rotation function
from appionlib import apImagicFile	#write imagic stacks
from appionlib import apDisplay
from appionlib.apImage import imagefilter	#image clipping

##=================
def getBoxStartPosition(imgdata,halfbox,partdata, shiftdata):
	### xcoord is the upper left area corner of the particle box
	start_x = int(round( shiftdata['scale']*(partdata['xcoord'] - shiftdata['shiftx']) - halfbox ))
	start_y = int(round( shiftdata['scale']*(partdata['ycoord'] - shiftdata['shifty']) - halfbox ))	
	return start_x,start_y

##=================
def checkBoxInImage(imgdims,start_x,start_y,boxsize):
	return ( (start_x > 0 and start_x+boxsize <= imgdims['x'])
		and  (start_y > 0 and start_y+boxsize <= imgdims['y']) )

##=================
def processParticleData(imgdata, boxsize, partdatas, shiftdata, boxfile, rotate=False):
	"""
	for a list of partdicts from database, apply shift
	to get a new list with x, y, angle information
	
	replaces writeParticlesToBoxfile()
	"""
	imgdims={}
	imgdims['x'] = imgdata['image'].shape[1]
	imgdims['y'] = imgdata['image'].shape[0]
	#imgdims = imgdata['camera']['dimension']
	if rotate is True:
		### with rotate we use a bigger boxsize
		halfbox = int(1.5*boxsize/2)
	else:
		halfbox = boxsize/2
	
	parttree = []
	boxedpartdatas = []
	eliminated = 0
	user = 0
	noangle = 0

	### normal single particle
	f = open(boxfile, 'w')
	for i in range(len(partdatas)):
		partdata = partdatas[i]
		### require particle with rotation
		if rotate is True and partdata['angle'] is None:
			noangle += 1
			continue

		### xcoord is the upper left area corner of the particle box
		start_x,start_y = getBoxStartPosition(imgdata,halfbox,partdata, shiftdata)
		if checkBoxInImage(imgdims,start_x,start_y,boxsize):
			partdict = {
				'x_coord': start_x,
				'y_coord': start_y,
				'angle': partdata['angle'],
			}
			parttree.append(partdict)
			boxedpartdatas.append(partdata)
			f.write("%d\t%d\t%d\t%d\t-3\n"%(start_x,start_y,boxsize,boxsize))
		else:
			eliminated += 1
	f.close()
	
	if eliminated > 0:
		apDisplay.printMsg(str(eliminated)+" particle(s) eliminated because they were out of bounds")
	if user > 0:
		apDisplay.printMsg(str(user)+" particle(s) eliminated because they were 'user' labeled targets")
	if noangle > 0:
		apDisplay.printMsg(str(noangle)+" particle(s) eliminated because they had no rotation angle")

	return parttree, boxedpartdatas

##=================
def getBoxBoundary(partdict, boxsize):
	x1 = partdict['x_coord']
	x2 = x1+boxsize
	y1 = partdict['y_coord']
	y2 = y1+boxsize
	return x1,x2,y1,y2

##=================
def boxer(imgfile, parttree, outstack, boxsize, pixlimit=None):
	"""
	boxes the particles and saves them to a imagic file
	"""
	imgarray = mrc.read(imgfile)
	imgarray = imagefilter.pixelLimitFilter(imgarray, pixlimit)
	boxedparticles = boxerMemory(imgarray, parttree, boxsize)
	apImagicFile.writeImagic(boxedparticles, outstack)
	return True

##=================
def boxerMemory(imgarray, parttree, boxsize):
	"""
	boxes the particles and returns them as a list of numpy arrays
	"""
	boxedparticles = []
	for partdict in parttree:
		x1,x2,y1,y2 = getBoxBoundary(partdict, boxsize)
		#numpy arrays are rows,cols --> y,x not x,y
		#print x1,x2,y1,y2, imgarray.shape
		boxpart = imgarray[y1:y2,x1:x2]
		boxedparticles.append(boxpart)
	return boxedparticles

##=================
def boxerRotate(imgfile, parttree, outstack, boxsize, pixlimit=None):
	"""
	boxes the particles with expanded size,
	applies a rotation to particle,
	reduces boxsize to requested size,
	and saves them to a imagic file
	"""
	# size needed is sqrt(2)*boxsize, using 1.5 to be extra safe
	bigboxsize = int(math.ceil(1.5*boxsize))
	imgarray = mrc.read(imgfile)
	imgarray = imagefilter.pixelLimitFilter(imgarray, pixlimit)
	bigboxedparticles = boxerMemory(imgarray, parttree, bigboxsize)
	
	boxedparticles = []
	boxshape = (boxsize,boxsize)
	apDisplay.printMsg("Rotating particles...")
	for i in range(len(bigboxedparticles)):
		if i % 10 == 0:
			sys.stderr.write(".")
		bigboxpart = bigboxedparticles[i]
		partdict = parttree[i]
		### add 90 degrees because database angle is from x-axis not y-axis
		angle = partdict['angle']+90.0
		rotatepart = ndimage.rotate(bigboxpart, angle=angle, reshape=False, order=1)
		boxpart = imagefilter.frame_cut(rotatepart, boxshape)
		boxedparticles.append(boxpart)
	sys.stderr.write("done\n")
	apImagicFile.writeImagic(boxedparticles, outstack)
	return True

##=================
def boxMaskStack(bmstackf, partdatas, box, xmask, ymask, falloff, imask=None, norotate=False):
	from appionlib.apSpider import operations
	from appionlib import apEMAN
	import os

	# create blank image for mask using SPIDER
	maskfile = "boxmask.spi"
	operations.createBoxMask(maskfile,box,xmask,ymask,falloff,imask)

	# convert mask to MRC
	apEMAN.executeEmanCmd("proc2d boxmask.spi boxmask.mrc",verbose=False,showcmd=False)
	os.remove("boxmask.spi")

	maskarray = mrc.read("boxmask.mrc")

	# box particles
	maskedparts = []
	for i in range(len(partdatas)):
		if norotate is True:
			rotatemask = maskarray
		else:
			angle = (-partdatas[i]['angle'])-90
			rotatemask = ndimage.rotate(maskarray, angle=angle, reshape=False, order=1)
		maskedparts.append(rotatemask)

	# write to stack
	apImagicFile.writeImagic(maskedparts, bmstackf)
	os.remove("boxmask.mrc")
	return bmstackf

##=================
def boxerFrameStack(framestackpath, parttree, outstack, boxsize,framelist):
	"""
	boxes the particles and returns them as a list of numpy arrays
	"""
	start_frame = framelist[0]
	nframe = len(framelist)
	apDisplay.printMsg("boxing %d particles from sum of total %d frames starting from frame %d using mmap" % (len(parttree),nframe,start_frame))
	boxedparticles = []
	stack = mrc.mmap(framestackpath)
	for partdict in parttree:
		x1,x2,y1,y2 = getBoxBoundary(partdict, boxsize)
		apDisplay.printDebug(' crop range of (x,y)=(%d,%d) to (%d,%d)' % (x1,y1,x2-1,y2-1))
		#numpy arrays are rows,cols --> y,x not x,y
		boxpart = numpy.sum(stack[tuple(framelist),y1:y2,x1:x2],axis=0)
		boxedparticles.append(boxpart)
	apImagicFile.writeImagic(boxedparticles, outstack)
	return True
