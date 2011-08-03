#!/usr/bin/env python
"""
This is a collection of function that
replace the EMAN1 batchboxer program with
added features like helical boxing at an
angle
"""

from scipy import ndimage	#rotation function
from appionlib import apImagicFile	#write imagic stacks
from appionlib.apImage import imagefilter	#image clipping

#emancmd = "batchboxer input=%s dbbox=%s output=%s newsize=%i" %(imgpath, emanboxfile, tempimgstackfile, doublebox)

def processParticleData(parttree, shiftdata):
	"""
	for a list of partdicts from database, apply shift
	to get a new list with x, y, angle information
	"""


def boxer(imgarray, parttree, outstack, boxsize):
	"""
	boxes the particles and saves them to a imagic file
	"""
	boxedparticles = boxerMemory(imgdict, parttree, boxsize)
	apImagicFile.saveImagic(boxedparticles, outstack)
	return True

def boxerMemory(imgarray, parttree, boxsize):
	"""
	boxes the particles and returns them as a list of numpy arrays
	"""
	boxedparticles = []
	for partdict in parttree:
		x1 = int(partdict['x_coord']-boxsize/2.)
		x2 = x1+boxsize
		y1 = int(partdict['y_coord']-boxsize/2.)
		y2 = y1+boxsize
		#numpy arrays are rows,cols --> y,x not x,y
		boxpart = imgdict['image'][y1:y2,x1:x2]
		boxedparticles.append(boxpart)
	return boxedparticles

def boxerRotate(imgarray, parttree, outstack, boxsize):
	"""
	boxes the particles with expanded size,
	applies a rotation to particle,
	reduces boxsize to requested size,
	and saves them to a imagic file
	"""
	# size needed is sqrt(2)*boxsize, using 1.5 to be extra safe
	bigboxsize = int(math.ceil(1.5*boxsize))
	
	bigboxedparticles = boxerMemory(imgdict, parttree, bigboxsize)
	
	boxedparticles = []
	boxshape = (boxsize,boxsize)
	for i in range(len(bigboxedparticles)):
		bigboxpart = bigboxedparticles[i]
		partdict = parttree[i]
		angle = partdict['angle']
		rotatepart = ndimage.rotate(bigboxpart, angle=angle, reshape=False, order=2)
		boxpart = imagefilter.frame_cut(rotatepart, boxshape)
		boxedparticles.append(boxpart)
		
	apImagicFile.saveImagic(boxedparticles, outstack)
	return True