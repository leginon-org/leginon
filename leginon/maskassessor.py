#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import sinedon.data
import imageassessor
import event
import node
import gui.wx.MaskAssessor
import os
import Image
import numpy
from pyami import imagefun, mrc
import leginondata
try:
	from appionlib import apMask
	from appionlib import apDatabase
except:
	pass

class MaskAssessor(imageassessor.ImageAssessor):
	panelclass = gui.wx.MaskAssessor.Panel
	settingsclass = leginondata.MaskAssessorSettingsData
	defaultsettings = {
		'mask run': 'test',
		'run': 'test',
		'jump filename': '',
		'continueon': True,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imageassessor.ImageAssessor.__init__(self, id, session, managerlocation, **kwargs)

		self.maskdir = None
		self.maskrundata = None
		self.oldrun = None
		self.oldmaskname = None
		self.oldcontinueon = None
		self.noreject = True

		if self.__class__ == MaskAssessor:
			self.start()

	def checkSettingsChange(self):
		if self.oldrun != self.settings['run'] or self.oldmaskname != self.settings['mask run'] or self.oldcontinueon != self.settings['continueon']:
			self.oldrun = self.settings['run']
			self.oldmaskname = self.settings['mask run']
			self.oldcontinueon = self.settings['continueon']
			return True
		else:
			return False			
		
	def getImageList(self):
		self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(self.settings['mask run'],self.session)
		self.maskdir=os.path.join(self.maskrundata['path']['path'],"masks")
		files = os.listdir(self.maskdir)
		format = 'png'
		assessrunname = self.settings['run']
		
		goodfiles = []
		for file in files:
			ext = file.split('.')[-1]
			if format == 'png' and ext in ('png','PNG'):
				goodfiles.append(file)

		self.assessrundata,exist = apMask.insertMaskAssessmentRun(self.session,self.maskrundata,assessrunname)
		if exist:
			if self.settings['continueon']:
				mode = 'continue'
			else:
				mode = 'overwrite'
			self.logger.warning('Assessor Run exists, will %s' % (mode,))
			if mode == 'continue':
				assessedmaskfiles = apMask.getAssessedMasks(self.assessrundata,self.maskrundata)
				for assessedmaskfile in assessedmaskfiles:
					try:
						aindex = goodfiles.index(assessedmaskfile)
						del goodfiles[aindex]
					except ValueError:
						pass
		if goodfiles:
			goodfiles.sort()
			self.images=[]
			self.files=[]
			for i,filename in enumerate(goodfiles):
				imgdata = self.readParent(filename)
				self.images.append(imgdata)
				self.files.append(filename)

				if self.noreject and apDatabase.getImgAssessmentStatus(imgdata)==False:
					self.files.pop()
					self.images.pop()
		else:
			self.logger.error('No %s files in directory' % (format,))
			

	def onKeep(self):
		keeplist = []
		keeptargets = self.panel.getTargets('Regions')
		imgdata = self.images[self.currentindex]
		for target in keeptargets:
			keeplist.append(target.stats['Label'])
		apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,imgdata,keeplist)

		self.continueOn()

	def onKeepAll(self):
		self.getImageList()
		
		# get maskshape from first mask
		currentname = self.files[0]
		dir = self.maskdir
		fullname = os.path.join(dir, currentname)
		imarray = self.readPNG(fullname)
		maskshape = imarray.shape
		if self.images:
			for i,imgdata in enumerate(self.images):
				targets = apMask.getRegionsAsTargets(self.maskrundata,maskshape,imgdata)
			
				keeplist = []
				keeptargets = targets
				for target in keeptargets:
					keeplist.append(target['stats']['Label'])
				apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,imgdata,keeplist)
			self.logger.info('Keep All Regions of mask run: %s' % (self.maskrundata['name'],))

	def onReject(self):

		keeplist = []
		imgdata = self.images[self.currentindex]
		apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,imgdata,keeplist)
		
		self.continueOn()


	def displayCurrent(self):
		imarray = numpy.zeros((2,2))
		while imarray.max() == 0:
			currentname = self.files[self.currentindex]

			self.logger.info('Displaying %s' % (currentname))
			dir = self.maskdir
			fullname = os.path.join(dir, currentname)

			imarray = self.readPNG(fullname)
			
			if imarray.max() ==0:
				if self.forward:
					if self.currentindex == len(self.files)-1:
						self.logger.info('End reached.')
						return
					else:
						self.currentindex += 1
				else:
					if self.currentindex == 0:
						self.logger.info('Beginning reached.')
						return
					else:
						self.currentindex -= 1
		if currentname.find('_mask') > -1:
			alpha = 0.5
			imgdata = self.images[self.currentindex]
			parentimg = imgdata['image']
			maskshape = imarray.shape

			targets = apMask.getRegionsAsTargets(self.maskrundata,maskshape,imgdata)
			if targets is None or len(targets)==0:
				self.logger.warning('No Mask Regions in this Image')
			keep = apDatabase.getImgAssessmentStatus(imgdata)
			if keep == False:
				self.logger.warning('Rejected Image, Mask Irelavent')
			self.alltargets = targets[:]
			self.setTargets(targets, 'Regions')
				
			binning = parentimg.shape[0]/imarray.shape[0]
			parentimg=imagefun.bin(parentimg,binning)
			overlay = apMask.overlayMask(parentimg,imarray)
			self.setImage(overlay, 'Mask')
			imarray=parentimg
		self.setImage(imarray, 'Image')
		
	def getMaskRunNames(self):
		names = apMask.getMaskMakerRunNamesFromSession(self.session)		
		return names

	def readParent(self,maskfilename):
		parent=maskfilename.replace('_mask.png','')
		imageq=leginondata.AcquisitionImageData(filename=parent)
		imagedata=self.research(imageq, results=1, readimages=False)
		return imagedata[0]
