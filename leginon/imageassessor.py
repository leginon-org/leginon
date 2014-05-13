#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
import targetfinder
import event
import node
import gui.wx.ImageAssessor
import os
from PIL import Image
import numpy
from pyami import imagefun, mrc

class ImageAssessor(targetfinder.ClickTargetFinder):
	panelclass = gui.wx.ImageAssessor.Panel
	settingsclass = leginondata.ImageAssessorSettingsData
	defaultsettings = {
		'image directory': '',
		'outputfile': '',
		'format': 'jpg',
		'run': 'test',
		'jump filename': '',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.results = {}
		self.currentname = None
		self.currentindex = None
		self.files = []
		self.oldformat = None
		self.oldrunname = None
		self.oldimagedir = None
		self.fileext = ''
		self.forward = True
		
		if self.__class__ == ImageAssessor:
			self.start()

	def checkSettingsChange(self):
		if self.oldformat != self.settings['format'] or self.oldrunname != self.settings['run'] or self.oldimagedir != self.settings['image directory']:
			self.oldformat = self.settings['format']
			self.oldrunname = self.settings['run']
			self.oldimagedir = self.settings['image directory']
			return True
		else:
			return False			
	
	def getImageList(self):
		dir = self.settings['image directory']
		files = os.listdir(dir)
		format = self.settings['format']

		self.files = []
		for file in files:
			ext = file.split('.')[-1]
			if format == 'jpg' and ext in ('jpg','JPG','jpeg','JPEG'):
				self.files.append(file)
			if format == 'mrc' and ext in ('mrc','MRC'):
				self.files.append(file)
			if format == 'png' and ext in ('png','PNG'):
				self.files.append(file)
		if self.files:
			self.readResults()
		else:
			self.logger.error('No %s files in directory' % (format,))
			

	def onKeep(self):
		self.readResults()
		self.results[self.currentname] = 'keep'
		self.writeResults()
		self.continueOn()


	def onReject(self):
		self.readResults()
		self.results[self.currentname] = 'reject'
		self.writeResults()
		self.continueOn()

	def onBegin(self):
		settingchanged = self.checkSettingsChange()
		self.currentindex = -1
		self.onNext()

	def onNext(self):
		self.forward = True
		settingchanged = self.checkSettingsChange()
		if (not self.files) or settingchanged:
			self.getImageList()
			self.currentindex = -1
		if self.currentindex < len(self.files)-1:
			self.currentindex += 1
			self.displayCurrent()
		else:
			self.logger.info('End reached.')

	def onPrevious(self):
		self.forward = False
		settingchanged = self.checkSettingsChange()
		if (not self.files) or settingchanged:
			self.getImageList()
			self.currentindex = len(self.files)
		if self.currentindex > 0:
			self.currentindex -= 1
			self.displayCurrent()
		else:
			self.logger.info('Beginning reached.')

	def onEnd(self):
		settingchanged = self.checkSettingsChange()
		if not self.files or settingchanged:
			self.getImageList()
		self.currentindex = len(self.files)
		self.onPrevious()

	def onJump(self):
		settingchanged = self.checkSettingsChange()
		if not self.files or settingchanged:
			self.getImageList()
			self.currentindex = 0
		files = self.files
		found = False
		if self.fileext != '':
			imagename = self.settings['jump filename'].split(self.fileext)[0]
		else:
			imagename = self.settings['jump filename']
		try:
			foundindex = files.index(imagename)
			self.currentindex = foundindex
		except ValueError:
			self.logger.warning('image %s not found' % (imagename))
		self.displayCurrent()
		
	def continueOn(self):
		if self.forward:
			self.onNext()
		else:
			self.onPrevious()

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
		self.setImage(imarray, 'Mask')
		self.setImage(imarray, 'Image')
		
	def overlayshadow(self,shadowimg,parentimg,alpha=0.5):
		binning = parentimg.shape[0]/shadowimg.shape[0]
		if binning != 1:
			parentimg=imagefun.bin(parentimg,binning)
		overlay=parentimg+shadowimg*alpha*(parentimg.max()-parentimg.min())/max(shadowimg.max(),1)
		return overlay,parentimg
		
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
		try:
			i.load()
		except:
			self.logger.error('PIL 1.1.5 can not load PNG on 64 bit machine')
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

