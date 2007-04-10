#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import targetfinder
import presets
import event
import Mrc
import node
import gui.wx.ClickTargetTransformer
import os
import Image
import numarray
import imagefun
import dbdatakeeper

class ClickTargetTransformer(targetfinder.ClickTargetFinder):
	panelclass = gui.wx.ClickTargetTransformer.Panel
	settingsclass = data.ClickTargetTransformerSettingsData
	defaultsettings = {
		'child preset': 'sq',
		'ancestor preset': 'gr',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.results = {}
		self.currentname = None
		self.currentindex = None
		self.images = []
		self.oldformat = None
		self.oldimagedir = None

		self.presetsclient = presets.PresetsClient(self)
		self.childpreset = self.settings['child preset']
		self.ancestorpreset = self.settings['ancestor preset']

		
		self.start()

	def getImageList(self):
		self.childpreset = self.settings['child preset']
		childpresetq = data.PresetData(session=self.session,name=self.childpreset)
		q = data.AcquisitionImageData(session=self.session,preset=childpresetq)
		self.images = self.research(datainstance=q, readimages=False)

		if self.images:
			self.currentindex = 0
			self.displayCurrent()
		else:
			self.logger.error('No %s images in session' % (self.childpreset,))

	def getAncestor(self):
		childimagedata=self.images[self.currentindex]
		presetq = data.PresetData(session=self.session,name=self.ancestorpreset)
		
		childimagetargetdata = self.researchDBID(data.AcquisitionImageTargetData,childimagedata['target'].dbid,readimages=False)
		parentimagedata = childimagetargetdata['image']
		while parentimagedata is not None:
			if parentimagedata['preset']['name'] != self.settings['ancestor preset']:
				childimagedata = parentimagedata.copy()
				childimagetargetdata = self.researchDBID(data.AcquisitionImageTargetData,childimagedata['target'].dbid,readimages=False)
				parentimagedata = childimagetargetdata['image']
			else:
				return parentimagedata
		return parentimagedata

	def onTransform(self):
		self.displayAncestor()
		self.onNext()

	def onClear(self):
		self.readResults()
		self.results[self.currentname] = 'reject'
		self.writeResults()
		self.onNext()

	def onNext(self):
		if not self.images:
			self.getImageList()
			return
		if self.currentindex < len(self.images)-1:
			if self.childpreset != self.settings['child preset'] or self.ancestorpreset != self.settings['ancestor preset']:
				self.childpreset = self.settings['child preset']
				self.ancestorpreset = self.settings['ancestor preset']
				self.getImageList()
				return
			else:
				self.currentindex += 1
				self.displayCurrent()
		else:
			self.logger.info('End reached.')

	def onPrevious(self):
		if self.currentindex > 0:
			if self.childpreset != self.settings['child preset'] or self.ancestorpreset != self.settings['ancestor preset']:
				self.childpreset = self.settings['child preset']
				self.ancestorpreset = self.settings['ancestor preset']
				self.getImageList()
				return
			else:
				self.currentindex -= 1
				self.displayCurrent()
		else:
			self.logger.info('Beginning reached.')

	def displayChild(self):
		self.currentname = self.images[self.currentindex]['filename']
		currentdbid = self.images[self.currentindex].dbid
		if self.currentname in self.results:
			result = self.results[self.currentname]
		else:
			result = 'None'
		self.logger.info('Displaying %s, %s' % (self.currentname,result))
		imarray = self.researchDBID(data.AcquisitionImageData,currentdbid,readimages=True)['image']
		self.setImage(imarray, 'Image')
		return imarray
		
	def displayAncestor(self):
		ancestorimagedata = self.getAncestor()
		if ancestorimagedata is None:
			self.logger.warning('No Ancestor found')
			imarray = None
		else:
			self.logger.info('Displaying %s' % (ancestorimagedata['filename']))
			imarray = self.researchDBID(data.AcquisitionImageData,ancestorimagedata.dbid,readimages=True)['image']
			self.setImage(imarray, 'Ancestor')
		return imarray
		
	def displayCurrent(self):
		self.displayChild()
		self.displayAncestor()

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
			a = numarray.fromstring(im.tostring(), numarray.UInt8)
			a = numarray.reshape(a, (im.size[1], im.size[0]))
			#a.shape = (im.size[1], im.size[0], 1)  # alternate way
		elif (im.mode=='RGB'):
			a = numarray.fromstring(im.tostring(), numarray.UInt8)
			a.shape = (im.size[1], im.size[0], 3)
		elif (im.mode=='RGBA'):
			atmp = numarray.fromstring(im.tostring(), numarray.UInt8)
			atmp.shape = (im.size[1], im.size[0], 4)
			a = atmp[:,:,3]
		else:
			raise ValueError, im.mode+" mode not considered"

		if convertType == 'Float32':
			a = a.astype(numarray.Float32)
		return a

