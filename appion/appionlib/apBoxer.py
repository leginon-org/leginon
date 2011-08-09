#!/usr/bin/env python
"""
This is a collection of function that
replace the EMAN1 batchboxer program with
added features like helical boxing at an
angle
"""

import sys
import math
from pyami import mrc
from scipy import ndimage	#rotation function
from appionlib import apImagicFile	#write imagic stacks
from appionlib import apDisplay
from appionlib.apImage import imagefilter	#image clipping

##=================
def processParticleData(imgdata, boxsize, partdatas, shiftdata, boxfile, rotate=False):
	"""
	for a list of partdicts from database, apply shift
	to get a new list with x, y, angle information
	
	replaces writeParticlesToBoxfile()
	"""
	imgdims = imgdata['camera']['dimension']
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
		xcoord= int(round( shiftdata['scale']*(partdata['xcoord'] - shiftdata['shiftx']) - halfbox ))
		ycoord= int(round( shiftdata['scale']*(partdata['ycoord'] - shiftdata['shifty']) - halfbox ))	
		if ( (xcoord > 0 and xcoord+boxsize <= imgdims['x'])
		and  (ycoord > 0 and ycoord+boxsize <= imgdims['y']) ):
			partdict = {
				'x_coord': xcoord,
				'y_coord': ycoord,
				'angle': partdata['angle'],
			}
			parttree.append(partdict)
			boxedpartdatas.append(partdata)
			f.write("%d\t%d\t%d\t%d\t-3\n"%(xcoord,ycoord,boxsize,boxsize))
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
def boxer(imgfile, parttree, outstack, boxsize):
	"""
	boxes the particles and saves them to a imagic file
	"""
	imgarray = mrc.read(imgfile)
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
		x1 = partdict['x_coord']
		x2 = x1+boxsize
		y1 = partdict['y_coord']
		y2 = y1+boxsize
		#numpy arrays are rows,cols --> y,x not x,y
		#print x1,x2,y1,y2, imgarray.shape
		boxpart = imgarray[y1:y2,x1:x2]
		boxedparticles.append(boxpart)
	return boxedparticles

##=================
def boxerRotate(imgfile, parttree, outstack, boxsize):
	"""
	boxes the particles with expanded size,
	applies a rotation to particle,
	reduces boxsize to requested size,
	and saves them to a imagic file
	"""
	# size needed is sqrt(2)*boxsize, using 1.5 to be extra safe
	bigboxsize = int(math.ceil(1.5*boxsize))
	imgarray = mrc.read(imgfile)
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
		#boxpart = imagefilter.frame_cut(rotatepart, boxshape)
		boxpart = rotatepart
		boxedparticles.append(boxpart)
	sys.stderr.write("done\n")
	apImagicFile.writeImagic(boxedparticles, outstack)
	return True
