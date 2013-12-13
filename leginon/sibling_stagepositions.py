#!/usr/bin/env python
import sys
import os

from leginon import leginondata
from leginon import targethandler

class Siblings(object):
	'''
	This class finds all acquisition images from the same target list
	'''
	def __init__(self):
		self.imagedata = None

	def setFilename(self,inputname):
		self.filename = inputname.split('.mrc')[0]
		r = leginondata.AcquisitionImageData(filename=self.filename).query(results=1)
		if not r:
			print 'File %s does not exist in Leginon database' % inputname
			sys.exit(1)
		self.imagedata = r[0]

	def getSiblings(self):
		siblings = []
		if self.imagedata:
			targetlistdata = self.imagedata['target']['list']
			targetq = leginondata.AcquisitionImageTargetData(list=targetlistdata,type='acquisition')
			siblings = leginondata.AcquisitionImageData(target=targetq).query()
		return siblings

class ImageSorter(object):
	'''
	Sort image data
	'''
	def __init__(self,images):
		self.images = images

	def _sortByKey(self,keyfunc):
		sortdict = {}
		for image in self.images:
			sortdict[apply(keyfunc,(image,))]=image
		keys = sortdict.keys()
		keys.sort()
		sorted_images = map((lambda x:sortdict[x]),keys)
		return sorted_images

	def positionIndex(self,positiondict):
		return int((positiondict['y']*1000+positiondict['x'])*1e6)

	def sortByStagePosition(self):
		return self._sortByKey(lambda x: self.positionIndex(x['scope']['stage position']))

	def sortByTargetNumber(self):
		return self._sortByKey(lambda x: x['target']['number'])

class ResultWriter(object):
	def __init__(self,images,filename):
		self.images = images
		if not filename:
			self.printResults()
		else:
			self.writeResults(filename)

	def infoline(self, imagedata):
		filepath = os.path.join(imagedata['session']['image path'],imagedata['filename']+'.mrc')
		xposition = int(imagedata['scope']['stage position']['x']*1e6) # in microns
		yposition = int(imagedata['scope']['stage position']['y']*1e6) # in microns
		line = '%s\t%d\t%d\n' % (filepath,xposition,yposition)
		return line

	def writeResults(self,filename):
		out = open(filename,'w')
		for image in self.images:
			out.write(self.infoline(image))
		out.close()

	def printResults(self):
		for image in self.images:
			print self.infoline(image)


if __name__=='__main__':
	if len(sys.argv) < 3 or len(sys.argv) > 5:
		print 'Usage: sibling_stageposition.py <sort-type> <one-filename> <optional:outputfile>'
		print '       sort-type: position or number'
		print 'Notes: one-filename in the raster does not need to include .mrc extension'
		print 'Example: python sibling_stageposition.py position 13dec01_00001gr out.txt'
		sys.exit(1)

	# Check sort type
	sorttype = sys.argv[1]
	validtypes = ('position','number')
	if sorttype not in validtypes:
		print 'Error: sort type not valid'
		sys.exit(1)

	# Find image data objects of the siblings include itself
	a = Siblings()
	a.setFilename(sys.argv[2])
	siblings = a.getSiblings()

	# Sort image data objects
	b = ImageSorter(siblings)
	if sorttype == 'position':
		sorted_images = b.sortByStagePosition()
	else:
		sorted_images = b.sortByTargetNumber()

	# Write the results
	outputfilename = None
	if len(sys.argv) == 4:
		outputfilename = sys.argv[3]
	c = ResultWriter(sorted_images,outputfilename)
