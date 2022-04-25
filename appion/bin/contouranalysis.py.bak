#!/usr/bin/env python

#pythonlib
import os
import re
import sys
import time
import shutil
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apSizing

class ContourAnalysis(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		### strings
		self.parser.add_option("--session", "--sessionname", dest="sessionname",
			help="Session name", metavar="NAME")
		### integer
		self.parser.add_option("--contourid", dest="contourid", type="int",
			help="Object contour selection run id, e.g. --contourid=5", metavar="#")

	#=====================
	def checkConflicts(self):
		"""
		standard appionScript
		"""
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		### check for contourpickerData file
		if self.params['contourid'] is None:
			apDisplay.printError("Please provide a contour selection run id number, e.g., --contourid=5")
		self.datafilepath = apSizing.getContourPickerDataFileName(self.params['sessionname'],self.params['contourid'])
		if not self.datafilepath:
			apDisplay.printError("Could not find contourpickerData file for the run")

		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")
		#if self.params['description'] is None:
		#	apDisplay.printError("Please provide a Description, e.g., --description='awesome data'")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "sizing"

	#=====================
	def start(self):
		rundir = self.params['rundir']
		sessionname = self.params['sessionname']
		imgdir = apDatabase.getImgDir(sessionname)
		contourid = self.params['contourid']
		apix = apSizing.getImagePixelSizeFromContourId(contourid)
		areas = apSizing.analyzeArea(contourid)

		if self.params['commit']:
			sizingrundata = apSizing.commitSizingRun(self.params)
			apSizing.commitSizingResults(sizingrundata,areas)

#=====================
#=====================
#=====================
if __name__ == '__main__':
	analysis = ContourAnalysis()
	analysis.start()
	analysis.close()





