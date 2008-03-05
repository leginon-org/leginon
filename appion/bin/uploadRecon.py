#!/usr/bin/python -O
# Upload pik or box files to the database

import sys
import os
import time
import apParam
import apDisplay
import apStack
import apRecon
import appionScript
import apEulerJump

#=====================
#=====================
class UploadReconScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --runid=<name> --stackid=<int> --modelid=<int>\n\t "
			+"--description='<quoted text>'\n\t [ --package=EMAN --jobid=<int> --oneiter=<iter> --zoom=<float> "
			+"--contour=<contour> --outdir=/path/ --commit ]")
		self.parser.add_option("-r", "--runid", dest="runid", 
			help="Name assigned to this reconstruction", metavar="TEXT")
		self.parser.add_option("-i", "--oneiter", dest="oneiter", type="int",
			help="Only upload one iteration", metavar="INT")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack id in the database", metavar="INT")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="Initial model id in the database", metavar="INT")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="Jobfile id in the database", metavar="INT")
		self.parser.add_option("-p", "--package", dest="package", default="EMAN",
			help="Reconstruction package used (EMAN by default)", metavar="TEXT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location of reconstruction files", metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit reconstruction to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit reconstruction to database")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the reconstruction (must be in quotes)", metavar="TEXT")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.75,
			help="Zoom factor for snapshot rendering (1.75 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("--chimera-only", dest="chimeraonly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run chimera")
		self.parser.add_option("--euler-only", dest="euleronly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run euler jump calculation")

	#=====================
	def checkConflicts(self):
		# msgPassing requires a jobId in order to get the jobfile & the paramters
		if ((self.params['package'] == 'EMAN/MsgP' or self.params['package'] == 'EMAN/SpiCoran') 
		 and self.params['jobid'] is None):
			apDisplay.printError(self.params['package']+" refinement requires a jobid. Please enter a jobId,"
				+" e.g. --jobid=734")
		if self.params['stackid'] is None:
			apDisplay.printError("please enter a stack id, e.g. --stackid=734")
		if self.params['modelid'] is None:
			apDisplay.printError("please enter a starting model id, e.g. --modelid=34")
		if self.params['description'] is None:
			apDisplay.printError("please enter a recon description, e.g. --description='my fav recon'")
		if self.params['runid'] is None:
			apDisplay.printError("please enter a recon runid, e.g. --runid=recon11")
		if self.params['jobid']:
			# if jobid is supplied, get the job info from the database
			self.params['jobinfo'] = apRecon.getClusterJobDataFromID(self.params['jobid'])
			if self.params['jobinfo'] is None:
				apDisplay.printError("jobid supplied does not exist: "+str(self.params['jobid']))
		else:
			self.params['jobinfo'] = None
		if self.params['chimeraonly'] is True:
			self.params['commit'] = False

	#=====================
	def setOutDir(self):
		if self.params['jobinfo']:
			self.params['outdir'] = self.params['jobinfo']['path']['path']
		else:
			apDisplay.printError("please specify an output directory")
		if not os.path.exists(self.params['outdir']):
			apDisplay.printError("upload directory does not exist: "+self.params['outdir'])

	#=====================
	def start(self):
		### create temp directory for extracting data
		self.params['tmpdir'] = os.path.join(self.params['outdir'], "temp")
		apParam.createDirectory(self.params['tmpdir'], warning=True)

		### make sure that the stack & model IDs exist in database
		emanJobFile = apRecon.findEmanJobFile(self.params)
		self.params['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		self.params['model'] = apRecon.getModelData(self.params['modelid'])

		### parse out the refinement parameters from the log file
		apRecon.parseLogFile(self.params)

		### parse out the massage passing subclassification parameters from the job/log file
		if self.params['package'] == 'EMAN/MsgP':
			apRecon.parseMsgPassingParams(self.params)

		### convert class average files from old to new format
		apRecon.convertClassAvgFiles(self.params)

		### get a list of the files in the directory
		apRecon.listFiles(self.params)
		
		### create a refinementRun entry in the database
		apRecon.insertRefinementRun(self.params)

		if self.params['euleronly'] is False:	
			### insert the Iteration info
			for iteration in self.params['iterations']:
				### if only uploading one iteration, skip to that one
				if self.params['oneiter'] and int(iteration['num']) != self.params['oneiter']:
					continue

				apDisplay.printColor("\nUploading iteration "+str(iteration['num'])+" of "
					+str(len(self.params['iterations']))+"\n", "green")
				for i in range(75): 
					sys.stderr.write("#")
				sys.stderr.write("\n")
				apRecon.insertIteration(iteration, self.params)

		### calculate euler jumps
		if self.params['commit'] is True:
			reconrunid = self.params['refinementRun'].dbid	
			stackid = self.params['stack'].dbid
			apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
			eulerjump = apEulerJump.ApEulerJump()
			eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, stackid)


#=====================
#=====================
if __name__ == '__main__':
	uploadRecon = UploadReconScript()
	uploadRecon.start()
	uploadRecon.close()

