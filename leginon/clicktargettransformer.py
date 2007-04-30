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
import node
import gui.wx.ClickTargetTransformer
#import dbdatakeeper
import threading
import caltransformer

import gui.wx.ClickTargetTransformer


class ClickTargetTransformer(targetfinder.ClickTargetFinder):
	panelclass = gui.wx.ClickTargetTransformer.Panel
	eventoutputs = targetfinder.TargetFinder.eventoutputs
	settingsclass = data.ClickTargetTransformerSettingsData
	defaultsettings = {
		'child preset': 'sq',
		'ancestor preset': 'gr',
		'jump filename': '',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
 		targetfinder.ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.userpause = threading.Event()

		self.currentindex = None

		self.presetsclient = presets.PresetsClient(self)
		self.childpreset = self.settings['child preset']
		self.ancestorpreset = self.settings['ancestor preset']
		self.targetnames = ['acquisition','focus']
		self.displayedtargetnames = self.targetnames+['transformed']
		self.imageids = None

		self.start()

	def getImageList(self):
		self.childpreset = self.settings['child preset']
		childpresetq = data.PresetData(session=self.session,name=self.childpreset)
		q = data.AcquisitionImageData(session=self.session,preset=childpresetq)
		images = self.research(datainstance=q, readimages=False)

		self.imageids = []
		for image in images:
			anc = self.getAncestor(image)
			if anc is not None:
				print image.dbid,anc.dbid
				self.imageids.append((image.dbid,anc.dbid))

		if not self.imageids:
			self.logger.error('No %s images in session' % (self.childpreset,))

		self.currentindex = None

	def getAncestor(self, childimagedata):
		ancpreset =  self.settings['ancestor preset']

		# get parent image
		try:
			parentimagedata = childimagedata['target']['image']
		except:
			parentimagedata = None

		# no parent image
		if parentimagedata is None:
			return None

		# if preset and grid match, this is a winner
		if parentimagedata['preset']['name'] == ancpreset:
			if parentimagedata['grid'].dbid == childimagedata['grid'].dbid:
				return parentimagedata

		# no match, but need to search deeper
		return self.getAncestor(parentimagedata)

	def transformTargets(self,im1,im2,targets):
		shape = {}

		lastnumber = self.lastTargetNumber(image=im1,
																				session=self.session)
		number = lastnumber + 1
		for type in self.targetnames:
			for targetdata in targets:
				if targetdata['type'] == type:
					drow = targetdata['delta row']
					dcol = targetdata['delta column']

					targetdata = self.newTargetForImage(im1, drow, dcol, type='transformed', list=self.childtargetlist, number=number)
					self.publish(targetdata, database=True)
					number += 1

		shape['im1'] = im1['image'].shape		
		im1scope = im1['scope']
		im1camera = im1['camera']
		im1trans = caltransformer.getTransformer(im1scope['tem'], im1camera['ccdcamera'], im1scope['high tension'], im1scope['magnification'], im1.timestamp)
		
		im2scope = im2['scope']
		im2camera = im2['camera']
		im2trans = caltransformer.getTransformer(im2scope['tem'], im2camera['ccdcamera'], im2scope['high tension'], im2scope['magnification'], im2.timestamp)

		newtargets = []
		shape['im2'] = im2['image'].shape
		lastnumber = self.lastTargetNumber(image=im2,
																				session=self.session)
		newtargets = []
		number = lastnumber + 1

		for type in self.targetnames:
			for targetdata in targets:
				if targetdata['type'] == type:
					drow = targetdata['delta row']
					dcol = targetdata['delta column']
					pixvect = {'row':drow,'col':dcol}
					
					## get stage position of target on first image
					bin = im1camera['binning']
					stage0 = im1scope['stage position']
					stage = im1trans.transform(pixvect, stage0, bin)

					## get pixel position of stage position on second image
					bin = im2camera['binning']
					stage0 = im2scope['stage position']
					pix = im2trans.itransform(stage, stage0, bin)

					drow =  pix['row']
					dcol =  pix['col']

					targetdata = self.newTargetForImage(im2, drow, dcol, type=type, list=self.targetlist, number=number)
					self.publish(targetdata, database=True)
					newtargets.append(targetdata)
					number += 1

		return newtargets

	def getTargets(self, imagedata, typename, targetlist):
		targets = []
		imagetargets = self.panel.getTargetPositions(typename)
		if not imagetargets:
			return targets
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata,
																				session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			
			targets.append(targetdata)
			number += 1
		return targets

	def childTargetsOnAncestor(self,childtargets):
		childtargetsonancestor = []
		for target in childtargets:
			drowchild = target['delta row']
			dcolchild = target['delta column']

			childshape = self.childimagedata['image'].shape
			ancestorshape = self.ancestorimagedata['image'].shape
			drowancestor = target['delta row'] + childshape[0]/2 - ancestorshape[0]/2
			dcolancestor = target['delta column'] + childshape[1]/2 - ancestorshape[1]/2
			targetdata = self.newTargetForImage(self.ancestorimagedata, drowancestor, dcolancestor, type='transformed', list=None, number=1)
			childtargetsonancestor.append(targetdata)
		return childtargetsonancestor
	
	def onTransform(self):
		childtargets = []
		for typename in self.targetnames:
			childtargets.extend(self.getTargets(self.childimagedata, typename,None))
		newtargets = self.transformTargets(self.childimagedata,self.ancestorimagedata,childtargets)

		childtargetsonancestor = self.childTargetsOnAncestor(childtargets)
					
		alltargets = newtargets	+ childtargetsonancestor
			
		self.displayTargets(self.ancestorimagedata,alltargets,self.displayedtargetnames)

	def onClear(self):
		targets2keep = self.getTargets(self.ancestorimagedata,'transformed',None)
		self.displayTargets(self.ancestorimagedata,targets2keep,self.displayedtargetnames)
		
	def onBegin(self):
		self.currentindex = -1
		self.onNext()

	def onJump(self):
		imagename = self.settings['jump filename'].split('.mrc')[0]
		q = data.AcquisitionImageData(session=self.session,filename=imagename)
		images = self.research(datainstance=q, readimages=False)
		foundid = None
		for i,ids in enumerate(self.imageids):
			if foundid is None:
				try:
					foundid = list(ids).index(images[0].dbid)
				except:
					foundid = None
			else:
				self.currentindex = i
				break
		if foundid is None:
			self.logger.warning('image %s not found in the child/ancestor pairs' % (imagename))
		else:	
			self.onPrevious()

	def checkNewSettings(self):
		if self.childpreset != self.settings['child preset'] or self.ancestorpreset != self.settings['ancestor preset']:
			self.childpreset = self.settings['child preset']
			self.ancestorpreset = self.settings['ancestor preset']
			return True
		return False

	def onNext(self):
		## first click, load image list
		if not self.imageids or self.checkNewSettings():
			self.getImageList()
			self.currentindex = -1

		if self.currentindex < len(self.imageids)-1:
			self.currentindex += 1
			self.displayCurrent()
		else:
			self.logger.info('End reached.')

	def onPrevious(self):
		## first click, load image list
		if not self.imageids or self.checkNewSettings():
			self.getImageList()
			self.currentindex = len(self.imageids)

		if self.currentindex > 0:
			self.currentindex -= 1
			self.displayCurrent()
		else:
			self.logger.info('Beginning reached.')

	def onEnd(self):
		if not self.imageids or self.checkNewSettings():
			self.getImageList()
		self.currentindex = len(self.imageids)
		self.onPrevious()

	def displayImage(self,imagedata,imagetype):
		currentname = imagedata['filename']
		currentdbid = imagedata.dbid
		self.logger.info('Displaying %s, %s' % (currentname,self.currentindex))
		self.setImage(imagedata['image'], imagetype)
		
	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		# check if there is already a target list for this image
		# exclude sublists (like rejected target lists)
		#Ancestor
		previoustargets = []
		for targettype in self.targetnames:
			previoustargets.extend(self.researchTargets(image=imagedata, type=targettype))
			
		#Child
		previoustransformedtargets = []
		previoustransformedtargets.extend(self.researchTargets(image=self.childimagedata, type='transformed'))
		previoustargets.extend(self.childTargetsOnAncestor(previoustransformedtargets))
			
		self.displayTargets(imagedata,previoustargets, self.displayedtargetnames)

		# create new target list
		self.targetlist = self.newTargetList(image=imagedata, queue=False)
		self.childtargetlist = self.newTargetList(image=self.childimagedata, queue=False)

		## if queue is turned on, do not notify other nodes of each target list publish
#		if self.settings['queue']:
#			pubevent = False
#		else:
#			pubevent = True
#		self.publish(targetlist, database=db, pubevent=pubevent)
#		self.logger.debug('Published targetlist %s' % (self.targetlist.dbid,))

#		if self.settings['wait for done'] and not self.settings['queue']:
#			self.makeTargetListEvent(targetlist)
#			self.setStatus('waiting')
#			self.waitForTargetListDone()
#			self.setStatus('processing')

	def displayTargets(self,imdata,targetdatalist,displayedtargetnames):
		if imdata is None:
			return
		self.logger.info('Displaying targets...')
		donetargets = []
		self.displayedtargetdata = {}
		targets = {}
		shape = imdata['image'].shape

		for type in displayedtargetnames:
			targets[type] = []
			for targetdata in targetdatalist:
				if targetdata['type'] == type:
					drow = targetdata['delta row']
					dcol = targetdata['delta column']
					vcoord = dcol+shape[1]/2,drow+shape[0]/2
					if vcoord not in self.displayedtargetdata:
						self.displayedtargetdata[vcoord] = []
					if targetdata['status'] in ('done', 'aborted'):
						donetargets.append(vcoord)
						self.displayedtargetdata[vcoord].append(targetdata)
					elif targetdata['status'] in ('new','processing'):
						targets[type].append(vcoord)
						self.displayedtargetdata[vcoord].append(targetdata)
					else:
						# other status ignored (mainly NULL)
						pass
			self.setTargets(targets[type], type)
		self.setTargets(donetargets,'done')

		n = 0
		for type in ('acquisition','focus'):
			n += len(targets[type])
		if 'transformed' in targets.keys():
			ntransformed = len(targets['transformed'])
		else:
			ntransformed = 0
		self.logger.info('displayed %s targets (%s transformed)' % (n, ntransformed))
		return n
	
	def findTargets(self, imdata, targetlist):
		pass
			
	def displayCurrent(self):
		child,ancestor = self.imageids[self.currentindex]
		self.childimagedata = self.researchDBID(data.AcquisitionImageData, child)
		self.ancestorimagedata = self.researchDBID(data.AcquisitionImageData, ancestor)
		self.displayImage(self.childimagedata,'Image')
		self.displayImage(self.ancestorimagedata,'Ancestor')
		self.processImageData(self.ancestorimagedata)
