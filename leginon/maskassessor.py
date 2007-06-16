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
	import apMask
except:
	pass

class MaskAssessor(imageassessor.ImageAssessor):
	panelclass = gui.wx.MaskAssessor.Panel
	settingsclass = leginondata.MaskAssessorSettingsData
	defaultsettings = {
		'mask run': 'test',
		'run': 'test',
		'jump filename': '',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.currentindex = None
		self.files = []
		self.maskdir = None
		self.maskrundata = None
		self.oldrun = None
		self.oldmaskname = None
		self.fileext = ''

		self.start()

	def checkSettingsChange(self):
		if self.oldrun != self.settings['run'] or self.oldmaskname != self.settings['mask run']:
			self.oldrun = self.settings['run']
			self.oldmaskname = self.settings['mask run']
			return True
		else:
			return False			
		
	def getImageList(self):
		self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(self.settings['mask run'],self.session)
		self.maskdir=os.path.join(self.maskrundata['path'],"masks")
		files = os.listdir(self.maskdir)
		format = 'png'
		assessrunname = self.settings['run']
		
		self.files = []
		for file in files:
			ext = file.split('.')[-1]
			if format == 'png' and ext in ('png','PNG'):
				self.files.append(file)

		self.assessrundata,exist = apMask.insertMaskAssessmentRun(self.session,self.maskrundata,assessrunname)
		if exist:
			self.logger.warning('Assessor Run exists, will overwrite')
		if self.files:
			pass
		else:
			self.logger.error('No %s files in directory' % (format,))
			

	def onKeep(self):

		keeplist = []
		keeptargets = self.panel.getTargets('Regions')
		for target in keeptargets:
			keeplist.append(target.stats['Label'])
		apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,self.imgdata,keeplist)

		self.onNext()

	def onReject(self):

		keeplist = []
		apMask.saveAssessmentFromTargets(self.maskrundata,self.assessrundata,self.imgdata,keeplist)
		
		self.onNext()


	def displayCurrent(self):
		currentname = self.files[self.currentindex]

		self.logger.info('Displaying %s' % (currentname))
		dir = self.maskdir
		fullname = os.path.join(dir, currentname)

		imarray = self.readPNG(fullname)
		if currentname.find('_mask') > -1:
			alpha = 0.5
			parentimg,imgdata = self.readParent(currentname)
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
		
	def getMaskRunNames(self):
		names = apMask.getMaskMakerRunNamesFromSession(self.session)		
		return names

	def readParent(self,maskfilename):
		parent=maskfilename.replace('_mask.png','')
		imageq=leginondata.AcquisitionImageData(filename=parent)
		imagedata=self.research(imageq, results=1, readimages=False)
		imarray=imagedata[0]['image']
		return imarray,imagedata[0]
