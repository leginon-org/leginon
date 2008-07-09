#!/usr/bin/python -O

import appionScript
import sys
import os
import apParam
import apDisplay
import apUpload

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
		if self.params['description'] is None:
			apDisplay.printError("enter a file description")
		if self.params['session'] is None and self.params['recon'] is None:
			apDisplay.printError("please enter either session or reconID")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "misc"

	#=====================
	def start(self):
		self.params['name'] = os.path.basename(self.params['file'])

		# make sure that the stack & model IDs exist in database
		if self.params['reconid'] is not None and self.params['reconid'] > 0:
			apDisplay.printMsg("recon id is: "+str(self.params['reconid']))
			apUpload.checkReconId(self.params)

		if self.params['session'] is not None:
			apUpload.getProjectId(self.params)
		# insert the info
		if self.params['commit'] is True:
			apUpload.insertMisc(self.params)	
		else:
			apDisplay.printWarning("not committing to DB")


#=====================
#=====================
if __name__ == '__main__':
	uploadMisc = UploadMiscScript()
	uploadMisc.start()
	uploadMisc.close()




