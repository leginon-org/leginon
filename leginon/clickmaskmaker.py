#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import scipy.ndimage as nd
import sinedon.data
import imageassessor
import event
import node
import gui.wx.ClickMaskMaker
import os
import Image
import numpy
from pyami import imagefun, mrc
import leginondata
import polygon

try:
	import apMask
	import apCrud
	import apImage
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
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		self.maskdir = None
		self.maskrundata = None
		self.oldpreset = None
		self.oldrunname = None
		self.oldrundir = None
		imageassessor.ImageAssessor.__init__(self, id, session, managerlocation, **kwargs)
		

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
		if self.oldpreset != self.settings['preset'] or self.oldrunname != self.settings['run'] or self.oldrundir != self.settings['path']:
			self.oldpreset = self.settings['preset']
			self.oldrunname = self.settings['run']
			self.oldrundir = self.settings['path']
			return True
		else:
			return False			
	
	
	def getImageList(self):

		preset = self.settings['preset']
		self.parentdir = self.session['image path']
		maskname = self.settings['run']
		maskdir = self.settings['path']
		
		self.bin = self.settings['bin']

		presetq = leginondata.PresetData(session=self.session,name=preset)
#		q = leginondata.AcquisitionImageData(session=self.session,preset=presetq)
		#testing
		q = leginondata.AcquisitionImageData(session=self.session,filename='07jan05b_00018gr_00022sq_v01_00002sq_00_00002en_00')
		self.images = self.research(datainstance=q, readimages=False)
		
		self.files = map((lambda x: x['filename']),self.images)

		self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(maskname,self.session)
		
		try:
			self.makeRecursivePath(maskdir)
		except:
			self.logger.warning('can not create run directory')
		
		if not self.maskrundata:
			apMask.insertManualMaskRun(self.session,maskdir,maskname,self.bin)
			self.maskrundata,self.maskparamsdata = apMask.getMaskParamsByRunName(maskname,self.session)
				
		else:
			self.logger.warning('Mask Run exists, will overwrite')
			savedbin = self.maskparamsdata['bin']
			if self.bin !=savedbin:
				self.logger.warning('Change binning to that of the saved %s',(savedbin,))
				self.bin = savedbin

		self.maskdir=os.path.join(self.maskrundata['path'],"masks")	
		try:
			self.makeRecursivePath(self.maskdir)
		except:
			self.logger.warning('can not create mask directory')

		if self.images:
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
		
		self.onNext()

	def onReject(self):
		
		self.maskimg = numpy.zeros(self.maskshape)
		self.setImage(self.binnedparentimg, 'Mask')
		self.onNext()
			
			
	def displayCurrent(self):
		self.clearTargets('Regions')
		imgdata = self.images[self.currentindex]
		self.currentname = imgdata['filename']
		currentname = self.currentname
		self.logger.info('Displaying %s' % (currentname))

		dir = self.parentdir
		fullname = os.path.join(dir, currentname)

		parentimg = imgdata['image']
		maskfilename = currentname+'_mask.png'

		fullname = os.path.join(self.maskdir,maskfilename)
		maskshape = (parentimg.shape[0]/self.bin,parentimg.shape[1]/self.bin)
		if os.path.exists(fullname):
			imarray = self.readPNG(fullname)
			self.logger.warning('mask exists, cannot override')
			self.maskexist = True
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
		self.imgdata = imgdata
		return imgdata
		
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
		
				
	
	def readParent(self):
		parent=self.currentname.replace('_mask.png','')
		imageq=leginondata.AcquisitionImageData(filename=parent)
		imagedata=self.research(imageq, results=1, readimages=False)
		imarray=imagedata[0]['image']
		return imarray,imagedata[0]
