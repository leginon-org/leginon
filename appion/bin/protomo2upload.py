#!/usr/bin/env python

import os
import sys
import math
import glob
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apProTomo2Prep
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apParam

#=====================
class ProTomo2Prep(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --session=<session> "
			+"[options]")

		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")

		self.parser.add_option("--tiltseries", dest="tiltseries", type="int",
			help="tilt series number in the session", metavar="int")

		self.parser.add_option("--seriesname", dest="seriesname", 
			help="Base name for tilt series refinement from which param and i3t files are named, e.g. --seriesname=series1")
		
		self.parser.add_option("--cycle", dest="cycle", type="int", 
			help="iteration to upload, e.g. --cycle=3",metavar="int")	

		self.parser.add_option("--tltfile", dest="tltfile", 
			help="tlt file to upload, e.g. --tltfile=series103.tlt")	

		self.parser.add_option('--goodrange', dest='goodrange', help="Range of well aligned tilts, e.g. --goodrange=2-60")

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
	
		### some of this should go in preloop functions
	
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
		seriesname=self.params['seriesname']
		print type(seriesname)
#		param_out=seriesname+'.param'

		###insert protomo run params
		print "first insert"
		protomodata = apProTomo.insertProtomoParams(seriesname)

		print "second insert"
		alignrun = apTomo.insertTomoAlignmentRun(sessiondata,tiltseriessettings,None,protomodata,None,1,self.params['runname'],self.params['rundir'],self.params['description'])

		###insert protomo alignment

		###hack to get around need to parse protomo param file
		#should read imgref from tlt file
		refineparamdict={'alismp':None,'alibox_x':None,'alibox_y':None,'cormod':None,'imgref':None}
		###
		self.params['goodcycle']=None
		if self.params['goodrange'] is None:
			self.params['goodstart']=1
			self.params['goodend']=len(tilts)
		alignerdata = apProTomo.insertAlignIteration(alignrun, protomodata, self.params, refineparamdict,ordered_imagelist[refimg])

		# read tlt file
		print "third insert"
		alignmentdict, geometrydict, seriesname = apProTomo.parseTilt(self.params['tltfile'])

		# insert geometry model
		modeldata = apProTomo.insertModel2(alignerdata, geometrydict)

		#insert image alignments
		for i,imagedata in enumerate(ordered_imagelist):
			#Caution...assumes ordered_imagelist is in same order as tlt file
			apProTomo.insertTiltAlignment(alignerdata,imagedata,i,alignmentdict[i+1],center=None)

		print "fourth insert"
		apTomo.insertTiltsInAlignRun(alignrun, tiltseriesdata,tiltseriessettings,True)


#=====================
if __name__ == '__main__':
	protomo2prep = ProTomo2Prep()
	protomo2prep.start()
	protomo2prep.close()

