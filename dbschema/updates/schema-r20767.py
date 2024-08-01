#!/usr/bin/env python

from . import baseSchemaClass
from sinedon import directq
from appionlib import appiondata
from appionlib import apDDResult

class SchemaUpdate(baseSchemaClass.SchemaUpdate):
	'''
	This schema insert ApDDAlignFrameStats and ApFrameAlignTrajectory
	Issue #6143
	This is not executed for any version because it takes a very long time
	to do.
	'''

	#######################################################################
	#
	# Functions to include in every schema update sub-class 
	#
	#######################################################################

	def setFlags(self):
		# can this schema update be run more than once and not break anything
		self.isRepeatable = True 
		# should this schema update be run again whenever the branch is upgraded, i.e., 3.1 -> 3.2
		self.reRunOnBranchUpgrade = False
		# what is the number associated with this update, use 'git rev-list --count HEAD'
		self.schemaNumber = 20767
		# minimum update required (set to previous schema update number)
		self.minSchemaNumberRequired = 0
		# minimum myami version
		self.minimumMyamiVersion = 3.3
		#what is the git tag name
		self.schemaTagName = 'schema20767'
		#git tag <tag name> <commit id>
		#git tag schema1 9fceb02
		#flags for what databases are updated and which ones are not
		self.modifyAppionDB = True
		self.modifyLeginonDB = False
		self.modifyProjectDB = False

	def upgradeAppionDB(self):
		for pairdata in appiondata.ApDDAlignImagePairData().query():
			status = self.saveImageDDAlignStats(pairdata['result'])
			if status:
				print(('image frame align stats saved for %s' % (pairdata['result']['filename'])))
	#######################################################################
	#
	# Custom functions
	#
	#######################################################################

	def saveImageDDAlignStats(self, aligned_imgdata):
		if '-DW' in aligned_imgdata['filename']:
			return False
		try:
			ddr = apDDResult.DDResults(aligned_imgdata)
			if appiondata.ApDDAlignStatsData(image=aligned_imgdata).query():
				return False
			xydict = ddr.getFrameTrajectoryFromLog()
		except ValueError:
			return False
		if xydict and xydict['x'] and xydict['y']:
			trajdata = ddr.saveFrameTrajectory(ddr.ddstackrun, xydict)
			ddr.saveAlignStats(ddr.ddstackrun, trajdata)
			return True
		return False


if __name__ == "__main__":
	update = SchemaUpdate()
	update.run()
