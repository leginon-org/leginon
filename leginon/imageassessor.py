#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import targetfinder
import event
import node
import gui.wx.ImageAssessor
import os
import Image
import numpy
from pyami import imagefun, mrc
try:
	import apMask
except:
	pass

class ImageAssessor(targetfinder.ClickTargetFinder):
	panelclass = gui.wx.ImageAssessor.Panel
	settingsclass = data.ImageAssessorSettingsData
	defaultsettings = {
		'image directory': '',
		'outputfile': '',
		'format': 'jpg',
		'type': 'mask',
		'run': 'test',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.results = {}
		self.currentname = None
		self.currentindex = None
		self.files = []
		self.oldformat = None
		self.oldimagedir = None

		self.start()

	def getImageList(self):
		dir = self.settings['image directory']
		files = os.listdir(dir)
		format = self.settings['format']
		type = self.settings['type']
		assessrunname = self.settings['run']
		
		if type =='mask':
			format = 'png'
		self.files = []
		for file in files:
			ext = file.split('.')[-1]
			if format == 'jpg' and ext in ('jpg','JPG','jpeg','JPEG'):
				self.files.append(file)
			if format == 'mrc' and ext in ('mrc','MRC'):
				self.files.append(file)
			if format == 'png' and ext in ('png','PNG'):
				self.files.append(file)
		if type =='mask':
			self.maskrundata,self.maskparamsdata = apMask.getMaskRunInfo(dir,files[0])
			self.assessrundata,exist = apMask.insertMaskAssessmentRun(self.session,self.maskrundata,assessrunname)
			if exist:
				self.logger.warning('Run exists, will overwrite')
		if self.files:
			self.readResults()
			self.currentindex = 0
			self.displayCurrent()
		else:
			self.logger.error('No %s files in directory' % (format,))
			

	def onKeep(self):
		type = self.settings['type']
		if type =='mask':
			keeplist = []
			keeptargets = self.panel.getTargets('Regions')
			for target in keeptargets:
				keeplist.append(target.stats['Label'])
			apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,self.imgdata,keeplist)
		else:
			self.readResults()
			self.results[self.currentname] = 'keep'
			self.writeResults()

		self.onNext()

	def onReject(self):
		type = self.settings['type']
		if type =='mask':
			keeplist = []
			apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,self.imgdata,keeplist)
		else:
			self.readResults()
			self.results[self.currentname] = 'reject'
			self.writeResults()
			self.onNext()

	def onNext(self):
		format = self.settings['format']
		imagedir = self.settings['image directory']
		if not self.files or format != self.oldformat or imagedir != self.oldimagedir:
			self.getImageList()
			self.oldformat = format
			self.oldimagedir = imagedir
			return
		if self.currentindex < len(self.files)-1:
			self.currentindex += 1
			self.displayCurrent()
		else:
			self.logger.info('End reached.')

	def onPrevious(self):
		if self.currentindex > 0:
			self.currentindex -= 1
			self.displayCurrent()
		else:
			self.logger.info('Beginning reached.')

	def displayCurrent(self):
		self.currentname = self.files[self.currentindex]
		if self.currentname in self.results:
			result = self.results[self.currentname]
		else:
			result = 'None'
		self.logger.info('Displaying %s, %s' % (self.currentname,result))
		format = self.settings['format']
		dir = self.settings['image directory']
		fullname = os.path.join(dir, self.currentname)
		if format == 'mrc':
			imarray = self.readMRC(fullname)
		if format == 'jpg':
			imarray = self.readJPG(fullname)
		if format == 'png':
			imarray = self.readPNG(fullname)
			if self.currentname.find('_mask') > -1:
				alpha = 0.5
				parentimg,imgdata = self.readMaskParent()
				maskshape = imarray.shape

				targets = apMask.getRegionsAsTargets(self.maskrundata,maskshape,imgdata)
				self.alltargets = targets[:]
				self.setTargets(targets, 'Regions')
				
				binning = parentimg.shape[0]/imarray.shape[0]
				parentimg=imagefun.bin(parentimg,binning)
				overlay=parentimg+imarray*alpha*(parentimg.max()-parentimg.min())/imarray.max()
				self.setImage(overlay, 'Mask')
				imarray=parentimg
		self.setImage(imarray, 'Image')
		self.imgdata = imgdata
		return imgdata

	def readMaskParent(self):
		parent=self.currentname.replace('_mask.png','')
#		parent=parent.replace('.jpg','.mrc')
#		parent=parent.replace('.png','.mrc')
		imageq=data.AcquisitionImageData(filename=parent)
		imagedata=self.research(imageq, results=1, readimages=False)
		imarray=imagedata[0]['image']
		return imarray,imagedata[0]
		
	def readResults(self):
		dir = self.settings['image directory']
		outputfile = self.settings['outputfile']
		outputfile = os.path.join(dir,outputfile)
		try:
			f = open(outputfile)
		except IOError:
			self.results = {}
			return
		lines = f.readlines()
		f.close()
		self.results = {}
		for line in lines:
			key,value = line.split()
			self.results[key] = value

	def writeResults(self):
		dir = self.settings['image directory']
		outputfile = self.settings['outputfile']
		outputfile = os.path.join(dir,outputfile)
		f = open(outputfile, 'w')
		for key,value in self.results.items():
			line = '%s\t%s\n' % (key,value)
			f.write(line)
		f.close()

	def readMRC(self, filename):
		return mrc.read(filename)

	def readJPG(self, filename):
		i = Image.open(filename)
		i.load()
		i = self.imageToArray(i)
		return i

	def readPNG(self, filename):
		i = Image.open(filename)
		i.load()
		i = self.imageToArray(i)
		return i

	def imageToArray(self, im, convertType='UInt8'):
		"""
		Convert PIL image to Numarray array
		copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
		"""
		if im.mode == "L":
			a = numpy.fromstring(im.tostring(), numpy.uint8)
			a = numpy.reshape(a, (im.size[1], im.size[0]))
			#a.shape = (im.size[1], im.size[0], 1)  # alternate way
		elif (im.mode=='RGB'):
			a = numpy.fromstring(im.tostring(), numpy.uint8)
			a.shape = (im.size[1], im.size[0], 3)
		elif (im.mode=='RGBA'):
			atmp = numpy.fromstring(im.tostring(), numpy.uint8)
			atmp.shape = (im.size[1], im.size[0], 4)
			a = atmp[:,:,3]
		else:
			raise ValueError, im.mode+" mode not considered"

		if convertType == 'Float32':
			a = a.astype(numpy.float32)
		return a

