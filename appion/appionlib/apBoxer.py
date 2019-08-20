#!/usr/bin/env python
"""
This is a collection of function that
replace the EMAN1 batchboxer program with
added features like helical boxing at an
angle
"""

import os,sys
import math
import numpy
import random
import time
from pyami import mrc
from scipy import ndimage	#rotation function
try:
	from scipy.interpolate import griddata
except:
	pass
from appionlib import apRelion
from appionlib import apImagicFile	#write imagic stacks
from appionlib import apDisplay
from appionlib.apImage import imagefilter	#image clipping
from appionlib import apDatabase

##=================
def getBoxStartPosition(halfbox, partdata, shiftdata):
	### xcoord is the upper left area corner of the particle box
	start_x = int(round( shiftdata['scale']*(partdata['xcoord'] - shiftdata['shiftx']) - halfbox ))
	start_y = int(round( shiftdata['scale']*(partdata['ycoord'] - shiftdata['shifty']) - halfbox ))
	return start_x,start_y

##=================
def checkBoxInImage(imgdims,start_x,start_y,boxsize):
	return ( (start_x > 0 and start_x+boxsize <= imgdims['x'])
		and  (start_y > 0 and start_y+boxsize <= imgdims['y']) )

##=================
def writeParticlesToStar(imgdata, boxsize, partdatas, shiftdata, boxfile, ctfdata=None, localCTF=False):
	"""
	for a list of partdicts from database,
	generate a Star file for particle extraction
	"""
	imgdims = {}
	imgdims['x'] = imgdata['image'].shape[1]
	imgdims['y'] = imgdata['image'].shape[0]

	parttree = []
	boxedpartdatas = []
	eliminated = 0
	user = 0

	gridDu=None
	
	# for local ctf estimation:
	if ctfdata is not None:
		if ctfdata['localCTFstarfile'] is not None and localCTF is True:
			t0 = time.time()
			apDisplay.printMsg("Determining local CTF values...")

			localctf = os.path.join(ctfdata['acerun']['path']['path'],ctfdata['localCTFstarfile'])
			matDu = [[numpy.nan for y in range(imgdims['y'])] for x in range(imgdims['x'])]	
			matDv = [[numpy.nan for y in range(imgdims['y'])] for x in range(imgdims['x'])]	
			labels = apRelion.getStarFileColumnLabels(localctf)
			for line in open(localctf):
				l = line.strip().split()
				if len(l)<3: continue
				x = int(float(l[labels.index("_rlnCoordinateX")]))
				y = int(float(l[labels.index("_rlnCoordinateY")]))
				du = float(l[labels.index("_rlnDefocusU")])
				dv = float(l[labels.index("_rlnDefocusV")])
				da = float(l[labels.index("_rlnDefocusAngle")])
				matDu[x][y]=du
				matDv[x][y]=dv

			# assume only 1 angle of astigmatism
			matDu = numpy.asarray(matDu)
			matDv = numpy.asarray(matDv)
		
			x = numpy.arange(0,matDu.shape[1])
			y = numpy.arange(0,matDu.shape[0])
			xx,yy = numpy.meshgrid(x,y)

			matDu = numpy.ma.masked_invalid(matDu)
			matDv = numpy.ma.masked_invalid(matDv)

			x1 = xx[~matDu.mask]
			y1 = yy[~matDu.mask]
			newDu = matDu[~matDu.mask]
			try: 
				gridDu = griddata((x1,y1),newDu.ravel(),(xx,yy),method='cubic')
			except:
				apDisplay.printError("Cannot estimate local CTF without griddata")
			x1 = xx[~matDv.mask]
			y1 = yy[~matDv.mask]
			newDv = matDv[~matDv.mask]
			gridDv = griddata((x1,y1),newDv.ravel(),(xx,yy),method='cubic')
			apDisplay.printColor("Time to estimate local CTF:\t"+apDisplay.timeString(time.time()-t0),"green")

	labels = ['_rlnMicrographName',
		'_rlnCoordinateX',
		'_rlnCoordinateY']
	if ctfdata: labels.extend([
		'_rlnVoltage',
		'_rlnDefocusU',
		'_rlnDefocusV',
		'_rlnDefocusAngle',
		'_rlnSphericalAberration',
		'_rlnDetectorPixelSize',
		'_rlnMagnification',
		'_rlnAmplitudeContrast',
		'_rlnCtfFigureOfMerit',
#		'_rlnAutopickFigureOfMerit'
#		'_rlnPhaseShift'
	])
	apRelion.writeRelionStarHeader(labels,boxfile)
	apix = apDatabase.getPixelSize(imgdata)
	c = apRelion.formatCtfForRelion(imgdata,ctfdata,apix)
	f = open(boxfile, 'a')
	for i in range(len(partdatas)):
		partdata = partdatas[i]
		xcoord = partdata['xcoord']
		ycoord = partdata['ycoord']
		if gridDu is not None:
			du = gridDu[xcoord][ycoord]
			dv = gridDv[xcoord][ycoord]
		else:
			du = c['defU']
			dv = c['defV']
			da = c['defAngle']
		f.write("micrographs/%s "%(imgdata['filename']+".mrc"))
		f.write("%12.6f %12.6f "%(xcoord,ycoord))
		if ctfdata:
			if gridDu is not None:
				du = gridDu[xcoord][ycoord]
				dv = gridDv[xcoord][ycoord]
			else:
				du = c['defU']
				dv = c['defV']
				da = c['defAngle']
			f.write("%12.6f %12.6f %12.6f %12.6f "%(c['kev'],du,dv,da))
			f.write("%12.6f %12.6f %12.6f %12.6f %12.6f "%(c['cs'],c['dstep'],c['mag'],c['amp'],c['cc']))
		f.write("\n")

		partdict = {
			'x_coord': xcoord,
			'y_coord': ycoord,
			'angle': partdata['angle'],
		}
		parttree.append(partdict)
		boxedpartdatas.append(partdata)

	f.close()
	return parttree, boxedpartdatas

##=================
def processParticleData(imgdata, boxsize, partdatas, shiftdata, boxfile, rotate=False, checkInside=True):
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

	helixmode = False
	for i in range(3):
		partdata = random.choice(partdatas)
		if partdata.get('helixnum', 0) > 0:
			helixmode = True
			break

	### normal single particle
	f = open(boxfile, 'w')
	for i in range(len(partdatas)):
		partdata = partdatas[i]

		### require particle with rotation
		if rotate is True and partdata['angle'] is None:
			noangle += 1
			continue

		### xcoord is the upper left area corner of the particle box
		start_x, start_y = getBoxStartPosition(halfbox, partdata, shiftdata)
		if checkInside is False:
			checkStatus = True
		else:
			checkStatus = checkBoxInImage(imgdims, start_x, start_y, boxsize)

		if checkStatus is False:
			eliminated += 1
			continue

		#write box information to file
		if helixmode is True:
			if i+1 >= len(partdatas):
				continue
			endhelix = partdatas[i+1]
			if endhelix['helixnum'] != partdata['helixnum']:
				continue
			new_start_x, new_start_y = getBoxStartPosition(halfbox, endhelix, shiftdata)
			if checkInside is False:
				checkStatus = True
			else:
				checkStatus = checkBoxInImage(imgdims, new_start_x, new_start_y, boxsize)
				if checkStatus is False:
					eliminated += 1
					continue
			#write box information to file, helix mode
			f.write("%d\t%d\t%d\t%d\t-1\n"%(start_x, start_y, boxsize, boxsize))
			f.write("%d\t%d\t%d\t%d\t-2\n"%(new_start_x, new_start_y, boxsize, boxsize))
		else:
			#write box information to file, normal
			f.write("%d\t%d\t%d\t%d\t-3\n"%(start_x, start_y, boxsize, boxsize))
		partdict = {
			'x_coord': start_x,
			'y_coord': start_y,
			'angle': partdata['angle'],
		}
		parttree.append(partdict)
		boxedpartdatas.append(partdata)


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
