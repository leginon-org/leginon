#!/usr/bin/env python

import os
import sys
import glob
import shutil
from appionlib import appiondata
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
		self.parser.add_option("--propagate", default=False, action="store_true", help="Delete associated unaligned or aligned images/frames")

	#=====================
	def checkConflicts(self):
		pass
	
	def preLoopFunctions(self):
		self.params['continue']=False
		self.params['commit']=False
		self.params['wait']=False
		
	def processImage(self, imgdata):
		global delLeginonList
		global delFrameList

		checklistimgs = []

		if self.params['propagate'] is True:
			# if aligned frame, get original
			if imgdata['filename'].endswith('-a'):
				alignpairdata = appiondata.ApDDAlignImagePairData(result=imgdata).query()[0]
				imgdata = alignpairdata['source']

			checklistimgs.append(imgdata)

			# get any aligned frames associated with original
			alignedimages = appiondata.ApDDAlignImagePairData(source=imgdata).query()
			for alignimg in alignedimages:
				checklistimgs.append(alignimg['result'])

		else:
			checklistimgs=[imgdata]

		# if any of the images are hidden/trashed, remove them all
		for img in checklistimgs:
			status=apDatabase.getImgCompleteStatus(img)
			if status is False:
				break

		if status is False:
			removefiles = []
			if self.params['leginondata'] is True:
				imagepath=imgdata['session']['image path']
				for img in checklistimgs:
					imgfullpath=os.path.join(imagepath,img['filename']+'.mrc')
					apDisplay.printMsg('%s is hidden or rejected and will be deleted' % (img['filename']))

					removefiles.append(imgfullpath)
				delLeginonList+=1
				
			if self.params['framesdata'] is True:			
				# delete original frame files
				framepath=imgdata['session']['frame path']
				apDisplay.printMsg('%s is hidden or rejected and frames will be deleted' % (imgdata['filename']))
				framefiles = os.path.join(framepath,imgdata['filename']+'*')
				removefiles.extend(glob.glob(framefiles))

				# delete ddstack frame files
				if self.params['propagate'] is True:
					for alignimg in alignedimages:
						ddframes = os.path.join(alignimg['ddstackrun']['path']['path'],imgdata['filename']+'*')
						removefiles.extend(glob.glob(ddframes))

				for filename in removefiles:
					if self.params['dryrun'] is False:
						print "deleting: %s"%filename
						if os.path.isdir(filename):
							shutil.rmtree(filename)
						elif os.path.isfile(filename):
							os.remove(filename)
					else:
						print "dryrun - won't delete: %s"%filename			
				delFrameList+=1

		else:
			apDisplay.printMsg('%s will be kept' % (imgdata['filename']))

	#=====================
	def commitToDatabase(self, imgdata):
		"""
		put in any additional commit parameters
		"""
		pass
	
	
	#=====================
	def printSummary(self):
		global delLeginonList
		global delFrameList
		drun = ""
		if self.params['propagate'] is True: drun += " (and associated aligned images)"
		if self.params['dryrun']: drun += " will be"
		apDisplay.printMsg("%s images%s deleted"%(delLeginonList,drun))
		apDisplay.printMsg("%s frame stacks%s deleted"%(delFrameList,drun))

#=====================
#=====================
if __name__ == '__main__':
	delLeginonList = 0
	delFrameList = 0
	deleteHidden= DeleteHidden()
	deleteHidden.run()
	deleteHidden.printSummary()
