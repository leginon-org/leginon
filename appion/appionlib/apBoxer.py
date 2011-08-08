#!/usr/bin/env python
"""
This is a collection of function that
replace the EMAN1 batchboxer program with
added features like helical boxing at an
angle
"""

from pyami import mrc
from scipy import ndimage	#rotation function
from appionlib import apImagicFile	#write imagic stacks
from appionlib.apImage import imagefilter	#image clipping

##=================
def processParticleData(imgdata, boxsize, partdatas, shiftdata, boxfile):
	"""
	for a list of partdicts from database, apply shift
	to get a new list with x, y, angle information
	
	replaces writeParticlesToBoxfile()
	"""
	imgdims = imgdata['camera']['dimension']
	halfbox = boxsize/2
	
	parttree = []
	eliminated = 0
	user = 0
	noangle = 0

	### normal single particle
	f = open(boxfile, 'w')
	for i in range(len(partdatas)):
		partdata = partdatas[i]
		### xcoord is the upper left area corner of the particle box
		xcoord= int(round( shiftdata['scale']*(partdata['xcoord'] - shiftdata['shiftx']) - halfbox ))
		ycoord= int(round( shiftdata['scale']*(partdata['ycoord'] - shiftdata['shifty']) - halfbox ))	

		if ( (xcoord > 0 and xcoord+boxsize <= imgdims['x'])
		and  (ycoord > 0 and ycoord+boxsize <= imgdims['y']) ):
			partdict = {
				'x_coord': xcoord,
				'y_coord': ycoord,
				'angle': self.params['angle'],
			}
			parttree.append(partdict)
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

	return parttree

##=================
def boxer(imgfile, parttree, outstack, boxsize):
	"""
	boxes the particles and saves them to a imagic file
	"""
	imgarray = mrc.read(imgfile)
	boxedparticles = boxerMemory(imgarray, parttree, boxsize)
	apImagicFile.saveImagic(boxedparticles, outstack)
	return True

##=================
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

##=================
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
		rotatepart = ndimage.rotate(bigboxpart, angle=angle, reshape=False, order=1)
		boxpart = imagefilter.frame_cut(rotatepart, boxshape)
		boxedparticles.append(boxpart)
		
	apImagicFile.saveImagic(boxedparticles, outstack)
	return True