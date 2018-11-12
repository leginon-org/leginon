#!/usr/bin/env python

import os
import sys
import wx
import time
from appionlib import apImage
import manualpicker
from PIL import Image
#import subprocess
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDatabase
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apMask
from appionlib import apCrud
from appionlib import apFindEM
from appionlib import filterLoop

#Leginon
import leginon.leginondata
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
import pyami
import numpy
import pyami.quietscipy
import scipy.ndimage as nd

##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class ManualPicker(filterLoop.FilterLoop):
	def preLoopFunctions(self):
		if not os.path.isdir(os.path.join(self.params['rundir'], "masks")):
			apDisplay.printError('mask folder missing')
		self.threadJpeg = True

	def postLoopFunctions(self):
		apDisplay.printMsg("Finishing up")
		time.sleep(2)
		apDisplay.printMsg("finished")

	def processImage(self, imgdata,filterarray):
		self.runManualPicker(imgdata)

	def commitToDatabase(self,imgdata):
        # if a kept mask was created in a previous mask run and the 
        # assess flag was used (basically combining the 2 runs) there is 
        # nothing new to commit.  
		if self.useAcceptedMask: return
        
		sessiondata = imgdata['session']
		rundir = self.params['rundir']
		maskname = self.params['runname']
		assessname = self.params['assessname']
		bin = self.params['bin']
		maskdir=os.path.join(rundir,"masks")
		maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
		if not maskrundata:
			apMask.insertManualMaskRun(sessiondata,rundir,maskname,bin)
			maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
		massessrundata,exist = apMask.insertMaskAssessmentRun(sessiondata,maskrundata,assessname)
		
		mask = self.maskimg
		maskfilename = imgdata['filename']+'_mask.png'
		
		image = self.image
		labeled_regions,clabels=nd.label(mask)
		testlog = [False,0,""]
		infos={}
		infos,testlog=apCrud.getLabeledInfo(image,mask,labeled_regions,range(1,clabels+1),False,infos,testlog)
		offset=1
		for l1 in range(0,len(infos)):

			l=l1+offset
			info=infos[l]
			info.append(l)
			regiondata= apMask.insertMaskRegion(maskrundata,imgdata,info)
			print "Inserting mask region in database"
		
		allregiondata = apMask.getMaskRegions(maskrundata,imgdata)
			
		for regiondata in allregiondata:
			apMask.insertMaskAssessment(massessrundata,regiondata,1)
			print "Inserting mask assessment in database."
		return

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'], "masks"),warning=False)

	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --session <session name> --runame <new or maskrunname> [--pickrunid <id>]  \n\t ")
		self.parser.add_option("--assess", dest="assessname",
			help="New mask assessment run name", metavar="NAME")
		self.parser.add_option("--pickrunid", dest="pickrunid", type="int",
			help="id of the particle pick to be displayed", metavar="#")
		self.parser.add_option("--pickrunname", dest="pickrunname",
			help="Name of the particle pick to be displayed", metavar="NAME")

	def checkConflicts(self):
		if self.params['commit'] and self.params['continue']==False:
			q = leginon.leginondata.SessionData(name=self.params['sessionname'])
			results = q.query(results=1)
			sessiondata = results[0]
			maskname = self.params['runname']
			maskrundata,maskparamsdata = apMask.getMaskParamsByRunName(maskname,sessiondata)
			if maskrundata:
				apDisplay.printWarning("Overwrite commited maskrun is not allowed")
                # This causes issues when combining runs usung assess flag
				#wx.Exit()

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################


	def getParticlePicks(self, imgdata):
		return []

	def runManualPicker(self, imgdata):
		#reset targets
		self.targets = []

		#set the assessment status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
        # useAccecepted mask is true when the assess flag is used, and an 
        # accepted mask is found in the indicated mask run that should be retained
        # This is checked in the preLoopFunctions().
		self.useAcceptedMask = False 

		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		maskname = imgdata['filename']+'_mask.png'
		imagepath = os.path.join(self.params['rundir'],imgname)
		maskpath = os.path.join(self.params['rundir'],'masks',maskname)

		self.image = pyami.mrc.read(imagepath)

		if not os.path.isfile(maskpath):
			self.maskimg =  numpy.zeros(self.image.shape)
		#run the picker
		self.maskimg = apImage.PngToBinarryArray(maskpath)
		

if __name__ == '__main__':
	imgLoop = ManualPicker()
	imgLoop.run()




