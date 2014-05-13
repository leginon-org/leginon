#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import pyami.quietscipy
import scipy.ndimage as nd
import sinedon.data
import imageassessor
import event
import node
import gui.wx.ClickMaskMaker
import os
from PIL import Image
import numpy
from pyami import imagefun, mrc
from leginon import leginondata
import polygon

try:
	import apMask
	import apCrud
	import apImage
	import apDatabase
except:
	pass

class ClickMaskMaker(imageassessor.ImageAssessor):
	panelclass = gui.wx.ClickMaskMaker.Panel
	settingsclass = leginondata.ClickMaskMakerSettingsData
	defaultsettings = {
		'run': 'test',
		'preset': 'en',
		'bin': 2,
		'path': None,
		'jump filename': '',
		'continueon': True,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imageassessor.ImageAssessor.__init__(self, id, session, managerlocation, **kwargs)

		self.maskdir = None
		self.maskrundata = None
		self.oldpreset = None
		self.oldrundir = None
		self.oldcontinueon = None
		self.fileext = '.mrc'
		self.noreject = True

		if self.__class__ == ClickMaskMaker:
			self.start()
		

	def makeRecursivePath(self,path):
		pathlist = path.split('/')
		childdirs = []
		currentpath = path
		while not (os.path.exists(currentpath) and os.path.isdir(currentpath)) and pathlist!=[]:
			if pathlist[-1]!='':
				childdirs.append(pathlist.pop(-1))
			else:
				pathlist.pop(-1)
			currentpath ='/'.join(pathlist)
		childdirs.reverse()
		for childdir in childdirs:
			pathlist.append(childdir)
			newpath = '/'.join(pathlist)
			os.mkdir(newpath)

	def checkSettingsChange(self):
		if self.oldpreset != self.settings['preset'] or self.oldrunname != self.settings['run'] or self.oldrundir != self.settings['path'] or self.oldcontinueon != self.settings['continueon']:
			self.oldpreset = self.settings['preset']
			self.oldrunname = self.settings['run']
			self.oldrundir = self.settings['path']
			self.oldcontinueon = self.settings['continueon']
			self.files = []
			return True
		else:
			return False			
	
	def handleDefaultPath(self,maskname):
		imagepathlist = self.parentdir.split('/')
		try:
			leginonpathindex = imagepathlist.index('leginon')
			rawpathindex = imagepathlist.index('rawdata')
			imagepathlist[leginonpathindex]='appion'
			imagepathlist[rawpathindex]='mask'
			imagepathlist.append(maskname)
			rundir = '/'.join(imagepathlist)
			rundir = '/'.join(imagepathlist)
		except:
			self.logger.warning('not a default leginon path, must specify')
			rundir = os.path.join('./',maskname)
		return rundir
	
	def getImageList(self):

		preset = self.settings['preset']
		self.parentdir = self.session['image path']
		maskname = self.settings['run']
		if self.settings['path'] is None or self.settings['path'] == '':
			rundir = self.handleDefaultPath(maskname)			
		else:
			rundir = os.path.join(self.settings['path'],maskname)
		
		self.logger.info('mask run dir %s' % rundir)
		self.bin = self.settings['bin']

		presetq = leginondata.PresetData(session=self.session,name=preset)
		q = leginondata.AcquisitionImageData(session=self.session,preset=presetq)
		allimages = self.research(datainstance=q, readimages=False)
		
		self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(maskname,self.session)
		

		if not self.maskrundata:
			apMask.insertManualMaskRun(self.session,rundir,maskname,self.bin)
			self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(maskname,self.session)
			images = allimages	
			try:
				maskdir=os.path.join(rundir,"masks")	
				self.makeRecursivePath(maskdir)
			except:
				self.logger.warning('can not create mask directory')
		
		else:
			if self.settings['continueon']:
				mode = 'continue'
			else:
				mode = 'overwrite empty masks'
			self.logger.warning('Mask Run exists, will %s' % (mode,))
			savedbin = self.maskparamsdata['bin']
			if self.bin !=savedbin:
				self.logger.warning('Change binning to that of the saved %s',(savedbin,))
				self.bin = savedbin
			savedrundir = self.maskrundata['path']['path']
			if rundir !=savedrundir:
				self.logger.warning('Change mask run path to that of the saved %s',(savedrundir,))
				rundir = savedrundir

			images = []
			for imgdata in allimages:
				regions = apMask.getMaskRegions(self.maskrundata,imgdata)
				maskfile = os.path.join(rundir,"masks",imgdata['filename']+'_mask.png')
				if mode == 'continue':
					if not os.path.exists(maskfile):
						images.append(imgdata)
				else:
					if mode == 'overwrite empty masks':
						if len(regions)==0:
							images.append(imgdata)
			
		self.maskdir=os.path.join(self.maskrundata['path']['path'],"masks")	
		
		if images:
			goodfiles = map((lambda x: x['filename']),images)
			goodfiles.sort()
			self.images = []
			self.files = []
			for i,filename in enumerate(goodfiles):
				q = leginondata.AcquisitionImageData(session=self.session,filename=filename)
				imgdatalist = self.research(datainstance=q, readimages=False)
				if imgdatalist:
					imgdata = imgdatalist[0]
					self.images.append(imgdata)
					self.files.append(filename)
				
				if self.noreject and  apDatabase.getImgAssessmentStatus(imgdata)==False:
						self.files.pop()
						self.images.pop()
		else:
			self.logger.error('No %s files in session' % (preset,))
			return
		
		if len(self.files) >0:
			self.currentindex = 0
			self.displayCurrent()
		else:
			self.logger.error('No %s files in session' % (preset,))
			
	
	def insertResults(self,rundata,imgdata,infos):
		offset=1
		for l1 in range(0,len(infos)):
		
			l=l1+offset
			info=infos[l]
			info.append(l)
			q = apMask.insertMaskRegion(rundata,imgdata,info)

	def onKeep(self):

		if self.maskexist:
			self.logger.warning('mask exists, cannot override')
			return
		image = self.binnedparentimg
		mask = self.maskimg
		imgdata = self.images[self.currentindex]
		labeled_regions,clabels=nd.label(mask)
		testlog = [False,0,""]
		infos={}

		infos,testlog=apCrud.getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),False,infos,testlog)
		maskfilename = imgdata['filename']+'_mask.png'

		self.insertResults(self.maskrundata,imgdata,infos)		
		apImage.arrayMaskToPngAlpha(mask, os.path.join(self.maskdir,maskfilename))		
		
		self.continueOn()

	def onReject(self):
		# Clear all regions
		self.maskimg = numpy.zeros(self.maskshape)
		self.setImage(self.binnedparentimg, 'Mask')
			
			
	def displayCurrent(self):
		self.clearTargets('Regions')
		currentname = self.files[self.currentindex]
		
		imgdata = self.images[self.currentindex]
		currentname = imgdata['filename']
		self.logger.info('Displaying %s' % (currentname))

		dir = self.parentdir
		fullname = os.path.join(dir, currentname)

		parentimg = imgdata['image']
		maskfilename = currentname+'_mask.png'

		fullname = os.path.join(self.maskdir,maskfilename)
		maskshape = (parentimg.shape[0]/self.bin,parentimg.shape[1]/self.bin)
		if os.path.exists(fullname):
			imarray = self.readPNG(fullname)
			if imarray.max() > 0:
				self.logger.warning('mask exists, cannot override')
				self.maskexist = True
			else:
				self.maskexist = False
		else:
			imarray = numpy.zeros(maskshape)
			self.maskexist = False
		
		maskshape = imarray.shape
				
		overlay,binnedparent = self.overlayshadow(imarray,parentimg,0.5)
		self.setImage(overlay, 'Mask')
		self.setImage(binnedparent, 'Image')
		self.maskshape = maskshape
		self.maskimg = imarray
		self.binnedparentimg = binnedparent
		
	def onAdd(self):
		if self.maskexist:
			return
		vertices = []
		vertices = self.panel.getTargetPositions('Regions')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)
		polygonimg = polygon.filledPolygon(self.maskshape,vertices)
		type(polygonimg)
		self.maskimg = self.maskimg + polygonimg
		self.maskimg = numpy.where(self.maskimg==0,0,1)
		overlay,binnedparent = self.overlayshadow(self.maskimg,self.binnedparentimg,0.5)
		self.setImage(overlay, 'Mask')
		self.clearTargets('Regions')
		
