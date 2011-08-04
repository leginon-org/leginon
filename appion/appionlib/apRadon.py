#!/usr/bin/env python

import sys
import time
import math
import numpy
from scipy import ndimage
from pyami import imagefun
from appionlib import apDisplay
from appionlib.apImage import imagefile

#=========================

def classicradon(image, stepsize=2):
	"""
	computes Radon transform of image
	"""
	radonlist = []
	nsteps = int(math.ceil(180/stepsize))
	blackcircle = imagefun.filled_circle(image.shape, image.shape[0]/2*0.75)
	mask = 1 - blackcircle
	maskline = mask.sum(axis=0) + 1
	for i in range(nsteps):
		rotated = ndimage.rotate(image, -i*stepsize, reshape=False, order=1)
		rotated = mask*rotated
		line = rotated.sum(axis=0)
		radonlist.append(line/maskline)
	radon = numpy.array(radonlist)
	radon = radon/radon.std()
	#radonlr = numpy.fliplr(radon)
	#radon = numpy.vstack((radon, radonlr))
	return radon

#=========================
def classicradonlist(imagelist, stepsize=2, maskrad=None, msg=None):
	"""
	computes Radon transform of image list
	"""
	t0 = time.time()
	if msg is None and len(imagelist) > 50:
		msg = True
	elif msg is None:
		msg = False

	radonimagelist = []
	if msg is True:
		apDisplay.printMsg("Performing Radon transforms with one processor")
	for imageid in range(len(imagelist)):
		if msg is True and imageid % 50 == 0:
			### FUTURE: add time estimate
			sys.stderr.write(".")
		image = imagelist[imageid]
		radonimage = classicradon(image, stepsize)
		radonimagelist.append(radonimage)
	if msg is True:
		sys.stderr.write("\n")
		print "Classic Radon images complete in %s"%(apDisplay.timeString(time.time()-t0))

	return radonimagelist

#=========================
def project(image, row, angle, mask, queue):
	#print "%d, angle=%.3f"%(row, angle)
	### prepare mask
	if mask is None:
		maskrad = image.shape[0]/2	
		blackcircle = imagefun.filled_circle(image.shape, maskrad)
		mask = 1 - blackcircle
	maskline = mask.sum(axis=0) + 1

	### rotate and project image
	rotated = ndimage.rotate(image, angle, reshape=False, order=1)
	rotated = mask*rotated
	#imagefile.arrayToJpeg(rotated, "rotated%02d.jpg"%(row))
	line = rotated.sum(axis=0)

	### insert into radon array
	#print "insert %d, %.3f"%(row, line.mean())
	line = line/maskline
	queue.put([row, line])
	return

#=========================
def radon(image, stepsize=2, maskrad=None):
	from multiprocessing import Queue, Process
	t0 = time.time()
	### prepare mask
	if maskrad is None:
		maskrad = image.shape[0]/2
	blackcircle = imagefun.filled_circle(image.shape, maskrad)
	mask = 1 - blackcircle

	nsteps = int(math.ceil(180/stepsize))
	queuelist = []
	for row in range(nsteps):
		angle = -row*stepsize
		queue = Queue()
		queuelist.append(queue)
		#below is equivalent to "project(image, row, angle, mask, queue)"
		proc = Process(target=project, args=(image, row, angle, mask, queue))
		proc.start()
	proc.join()

	### assemble radon image
	radonimage = numpy.zeros( (nsteps, image.shape[0]) )
	for queue in queuelist:
		row, line = queue.get()
		radonimage[row, :] = line
		
	#radonlr = numpy.fliplr(radonimage)
	#radonimage = numpy.vstack((radonimage, radonlr))
	imagefile.arrayToJpeg(radonimage, "radonimage.jpg", msg=False)
	print "Multi radon completed in %s"%(apDisplay.timeString(time.time() - t0))
	return radonimage

#=========================
def radonImage(image, imageid, stepsize, mask, queue):
	"""
	computes Radon transform of single image,
	requires multiprocessing queue
	"""
	radonlist = []
	nsteps = int(math.ceil(180/float(stepsize)))
	maskline = mask.sum(axis=0) + 1

	### rotate image and assemble radon image
	for i in range(nsteps):
		angle = -i*stepsize
		rotated = ndimage.rotate(image, angle, reshape=False, order=1)
		rotated = mask*rotated
		line = rotated.sum(axis=0)
		radonlist.append(line/maskline)

	radon = numpy.array(radonlist)
	### normalize standard deviation
	radon = radon/radon.std()
	### this does not work with shifting
	#radonlr = numpy.fliplr(radon)
	#radon = numpy.vstack((radon, radonlr))

	queue.put([imageid, radon])
	return

#=========================
def radonlist(imagelist, stepsize=2, maskrad=None, msg=None):
	"""
	computes Radon transform of image list
	"""
	if msg is None and len(imagelist) > 50:
		msg = True
	elif msg is None:
		msg = False

	### Note: multiprocessing version not compatible with python 2.4
	from multiprocessing import Queue, Process
	t0 = time.time()

	### prepare mask
	shape = imagelist[0].shape
	if maskrad is None:
		maskrad = shape[0]/2
	blackcircle = imagefun.filled_circle(shape, maskrad)
	mask = 1 - blackcircle

	### preform radon transform for each image
	queuelist = []
	if msg is True:
		apDisplay.printMsg("Performing Radon transforms with multiprocessor")
	for imageid in range(len(imagelist)):
		if msg is True and imageid % 50 == 0:
			### FUTURE: add time estimate
			sys.stderr.write(".")
		image = imagelist[imageid]
		queue = Queue()
		queuelist.append(queue)
		#below is equivalent to "radonImage(image, imageid, stepsize, mask, queue)"
		proc = Process(target=radonImage, args=(image, imageid, stepsize, mask, queue))
		proc.start()
	proc.join()

	### assemble radon image list
	radonimagelist = range(len(imagelist))
	for queue in queuelist:
		imageid, radonimage = queue.get()
		radonimagelist[imageid] = radonimage
	if msg is True:
		sys.stderr.write("\n")
		print "Multi Radon images complete in %s"%(apDisplay.timeString(time.time()-t0))

	return radonimagelist

#=========================
#=========================
if __name__ == "__main__":
	t0 = time.time()
	a = numpy.zeros((512,512))
	a[128:256,256:384] = 1
	a += numpy.random.random((512,512))
	radon(a, 0.5)
	radon2(a, 0.5)
	print "Completed in %s"%(apDisplay.timeString(time.time() - t0))
