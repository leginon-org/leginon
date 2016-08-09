#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
import event
import mosaictargetfinder
import gui.wx.MosaicClickTargetFinder

class MosaicQuiltFinder(mosaictargetfinder.MosaicClickTargetFinder):
	'''
	Target selection specific for atlas made from square stitchingor atlas made from.  It retains z height in further imaging. 
	'''

	panelclass = gui.wx.MosaicClickTargetFinder.Panel
	settingsclass = leginondata.MosaicClickTargetFinderSettingsData
	defaultsettings = dict(mosaictargetfinder.MosaicClickTargetFinder.defaultsettings)
	defaultsettings.update({
		'autofinder': False,
	})

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		mosaictargetfinder.MosaicClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		if self.__class__ == MosaicQuiltFinder:
			self.start()

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

