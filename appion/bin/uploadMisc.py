#!/usr/bin/python -O


import sys
import os
import appionScript
import apDatabase
import apRecon
import apParam
import apDisplay
import apUpload
import appionData

#=====================
#=====================
class UploadMiscScript(appionScript.AppionScript):
	#==================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --recon=<#> \n\t "
			+" --description='text' ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="File to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with file (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-r", "--reconid", dest="reconid", type='int', default=None,
			help="ReconID associated with file (e.g. --reconid=311)", metavar="RECONID")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the file (must be in quotes)", metavar="'TEXT'")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit file to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit file database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the file to", metavar="PATH")

	#=====================
	def checkConflicts(self):
		# make sure the necessary parameters are set
		if self.params['file'] is None:
			apDisplay.printError("no file was specified")
		if self.params['description'] is None:
			apDisplay.printError("enter a file description")
		if self.params['session'] is None and self.params['recon'] is None:
			apDisplay.printError("please enter either session or reconID")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "misc"

	#=====================
	def insertMisc(self):
		print "inserting into database"
		miscq = appionData.ApMiscData()
		if self.params['session'] is not None:
			miscq['session'] = self.sessiondata
		if self.params['reconid'] is not None:
			miscq['refinementRun'] = self.recondata
		if self.params['projectId'] is not None:
			miscq['project|projects|project'] = self.params['projectId']
		miscq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		miscq['name'] = os.path.basename(self.params['file'])
		miscq['description'] = self.params['description']
		appiondb.insert(miscq)

	#=====================
	def start(self):

		if self.params['reconid'] is not None:
			self.recondata = apRecon.getRefineRunDataFromID(self.params['reconid'])
			print "Associated with",recondata['name'],":",recondata['path']
		if self.params['session'] is not None:
			self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			self.params['projectId'] = apDatabase.getProjectIdFromSessionName(self.params['session'])

		# insert the info
		if self.params['commit'] is True:
			self.insertMisc()	
		else:
			apDisplay.printWarning("not committing to DB")


#=====================
#=====================
if __name__ == '__main__':
	uploadMisc = UploadMiscScript()
	uploadMisc.start()
	uploadMisc.close()




