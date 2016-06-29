#!/usr/bin/env python

import os
import sys
import glob
import shutil
from appionlib import apDisplay
from appionlib import appionLoop2
from appionlib import apDatabase

#=====================
class DeleteHidden(appionLoop2.AppionLoop):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--dryrun", dest="dryrun", default=False,
			action="store_true", help="Just show files that will be deleted, but do not delete them.")
		self.parser.add_option("--leginondata", dest="leginondata", default=False, action="store_true", help="Delete hidden image data")
		self.parser.add_option("--framesdata", dest="framesdata", default=False, action="store_true", help="Delete frames data from hidden images.")

	#=====================
	def checkConflicts(self):
		pass
	
	def preLoopFunctions(self):
		self.params['continue']=False
		self.params['commit']=False
		self.params['wait']=False
		
	def processImage(self, imgdata):
		framepath=imgdata['session']['frame path']
		imagepath=imgdata['session']['image path']
		status=apDatabase.getImgCompleteStatus(imgdata)
		if status is False:
			if self.params['leginondata'] is True:
				imgfullpath=os.path.join(imagepath,imgdata['filename']+'.mrc')
				apDisplay.printMsg('%s is hidden or rejected and will be deleted' % (imgdata['filename']))
				if os.path.exists(imgfullpath) and self.params['dryrun'] is False:
					os.remove(imgfullpath)
				
			if self.params['framesdata'] is True:			
				apDisplay.printMsg('%s is hidden or rejected and frames will be deleted' % (imgdata['filename']))
				frames=glob.glob(os.path.join(framepath,imgdata['filename']+'*'))
				if self.params['dryrun'] is False:
					for filename in frames:
						if os.path.isdir(filename):
							shutil.rmtree(filename)
						else:
							os.remove(filename)
		else:
			apDisplay.printMsg('%s will be kept' % (imgdata['filename']))

	#=====================
	def commitToDatabase(self, imgdata):
		"""
		put in any additional commit parameters
		"""
		pass
	

#=====================
#=====================
if __name__ == '__main__':
	deleteHidden= DeleteHidden()
	deleteHidden.run()

