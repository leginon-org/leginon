#!/usr/bin/env python

import os
import sys
import math
import glob
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apProTomo2Prep
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apParam
from appionlib import apTomoMakerBase

#=====================
class ProTomo2Reconstruct(apTomoMakerBase.TomoMaker):
	#=====================
	def setupParserOptions(self):
		super(ProTomo2Reconstruct,self).setupParserOptions()
		self.parser.set_usage( "Usage: %prog "
			+"[options]")
	
	#=====================
	def checkConflicts(self):
		if self.params['goodrange'] is not None:
				words=self.params['goodrange'].split('-')
				if len(words)!=2:
					apDisplay.printError("goodrange must have two numbers separated by a dash. e.g. '2-60'")
				else:
					self.params['goodstart']=int(words[0])
					self.params['goodend']=int(words[1])

	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def start(self):
	
	
		###do queries
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.sessiondata = sessiondata
		tiltseriesdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseries'],sessiondata)
		tiltseriessettings= apTomo.getTomographySettings(sessiondata,tiltseriesdata)
		tiltdata=apTomo.getImageList([tiltseriesdata])
		description = self.params['description']
		apDisplay.printMsg("getting imagelist")
		print "ordering list"
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(tiltdata)
		#tilts are tilt angles, ordered_imagelist are imagedata, ordered_mrc_files are paths to files, refimg is an int

		###set up files
		seriesname='series'+str(self.params['tiltseries'])
		tiltfilename=seriesname+'.tlt'
		param_out=seriesname+'.param'
		maxtilt=max([abs(tilts[0]),abs(tilts[-1])])
		apDisplay.printMsg("highest tilt angle is %f" % maxtilt)
		self.params['cos_alpha']=math.cos(maxtilt*math.pi/180)
		self.params['raw_path']=os.path.join(self.params['rundir'],'raw')

		rawexists=apParam.createDirectory(self.params['raw_path'])

		apDisplay.printMsg("copying raw images")
		newfilenames=apProTomo.getImageFiles(ordered_imagelist,self.params['raw_path'], link=False)
		
		#get alignment data
		alignerdata = apTomo.getAlignerdata(self.params['alignerid'])
		imgshape = apTomo.getTomoImageShape(ordered_imagelist[0])
		imgcenter = {'x':self.imgshape[1]/2,'y':self.imgshape[0]/2}
		specimen_euler, azimuth, origins, rotations = apTomo.getAlignmentFromDB(alignerdata,imgcenter)

		#write protomo2 tilt file
		outtltfile='series.tlt'
		seriesname='series'
		
		apProTomo.writeTiltFile2(outfilename, seriesname, specimen_eulers, azimuth, referenceimage )
		
		#reconstruct volume
		

#=====================
if __name__ == '__main__':
	protomo2reconstruct = ProTomo2Reconstruct()
	protomo2reconstruct.start()
	protomo2reconstruct.close()

