#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import event
import Mrc
import node
import gui.wx.ImageAssessor
import os
import Image
import numarray

class ImageAssessor(node.Node):
	panelclass = gui.wx.ImageAssessor.Panel
	settingsclass = data.ImageAssessorSettingsData
	defaultsettings = {
		'image directory': '',
		'outputfile': '',
		'format': 'jpg',
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
		self.files = []
		for file in files:
			ext = file.split('.')[-1]
			if format == 'jpg' and ext in ('jpg','JPG','jpeg','JPEG'):
				self.files.append(file)
			if format == 'mrc' and ext in ('mrc','MRC'):
				self.files.append(file)
		if self.files:
			self.readResults()
			self.currentindex = 0
			self.displayCurrent()
		else:
			self.logger.error('No %s files in directory' % (format,))

	def onKeep(self):
		self.readResults()
		self.results[self.currentname] = 'keep'
		self.writeResults()
		self.onNext()

	def onReject(self):
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
		self.setImage(imarray, 'Image')

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
		return Mrc.mrc_to_numeric(filename)

	def readJPG(self, filename):
		i = Image.open(filename)
		i.load()
		return i
