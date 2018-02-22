#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
import event
import mosaictargetfinder
import targetfinder
import gui.wx.MosaicQuiltFinder
import jahcfindermodel
import jahcfinder

class MosaicQuiltFinder(mosaictargetfinder.MosaicClickTargetFinder):
	'''
	Target selection specific for atlas made from square stitchingor atlas made from.  It retains z height in further imaging. 
	'''

	panelclass = gui.wx.MosaicQuiltFinder.Panel
	settingsclass = leginondata.MosaicQuiltFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)
	defaultsettings.update(jahcfinder.JAHCFinder.defaultsettings)
	defaultsettings.update({
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'create on tile change': 'all',
		'autofinder': False,
	})

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		mosaictargetfinder.MosaicClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		if self.__class__ == MosaicQuiltFinder:
			self.setAutoTargetFinder()
			self.start()

	def setAutoTargetFinder(self):
		self.hf = jahcfindermodel.JAHCFinderModel(self.logger,self.settings,['acquisition','focus'])
		self.hf.setSession(self.session)
		self.cortypes = self.hf.cortypes
		self.focustypes = self.hf.focustypes
		self.extendtypes = self.hf.extendtypes

	def mosaicToTarget(self, typename, row, col):
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		### create a new target list if we don't have one already
		'''
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)
		'''
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist, last_focused=recent_imagedata['target']['list'])
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata

	def getMiddleTile(self):
		count = len(self.mosaic.tiles)
		index = self.mosaic.tiles[int(count/2.0)]
		return index

	def setOriginal(self):
		'''
		Set test tile
		'''
		tile =  self.getMiddleTile()
		print tile.imagedata.dbid
		self.hf.setCurrentImageData(tile.imagedata)
		self.hf.setImage(tile.imagedata['image'], 'Original')
		self.setImage(self.hf.getImage('Original'),'Original')

	def correlateTemplate(self):
		'''
		Test correlateTemplate on the test tile
		'''
		self.hf.setSettings(self.settings)
		self.setOriginal()
		self.hf.correlateTemplate()
		self.setImage(self.hf.getImage('Template'),'Template')

	def thresholdAndFindBlobs(self):
		'''
		Test Threshold and Blobs on the test tile
		'''
		self.hf.setSettings(self.settings)
		self.hf.threshold()
		self.setImage(self.hf.getImage('Threshold'),'Threshold')
		self.hf.findBlobs()
		self.setTargets(self.hf.imagetargets['Blobs'], 'Blobs')

	def fitLattice(self, auto_center=False):
		'''
		Test fitLattice on the tile
		'''
		self.hf.setSettings(self.settings)
		self.hf.fitLattice(auto_center)
		self.setTargets(self.hf.imagetargets['Lattice'], 'Lattice')

	def ice(self):
		'''
		Test ice on a tile
		'''
		self.hf.setSettings(self.settings)
		self.hf.ice()
		self.setTargets(self.hf.imagetargets['acquisition'], 'acquisition')
		self.setTargets(self.hf.imagetargets['focus'], 'focus')

	def findSquares(self):
		self.hf.setSettings(self.settings)
		all_targets = {}
		for k in self.hf.targetnames:
			all_targets[k] = []
		for tile in self.mosaic.tiles:
			imageshape = tile.imagedata['image'].shape
			self.hf.findTargets(tile.imagedata, self.targetlist)
			for k in self.hf.targetnames:
				acq_targets = self.hf.getTargets(k)
				for target in acq_targets:
					row, column = int(target[1]),int(target[0])
					drow = row - imageshape[0]/2
					dcol = column - imageshape[1]/2
					targetdict = {'delta row': drow,'delta column':dcol}
					y,x = self.targetToMosaic(tile, targetdict)
					all_targets[k].append((x, y))
		for k in self.hf.targetnames:
			self.setTargets(all_targets[k],k)
		self.panel.squaresFound()
		
