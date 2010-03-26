#!/usr/bin/env python
# Upload pik or box files to the database

#python
import os
import sys
import time
import glob
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apRecon
from appionlib import apEulerJump
from appionlib import apCoranPlot

#=====================
#=====================
class UploadReconScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --runname=<name> --stackid=<int> --modelid=<int>\n\t "
			+"--description='<quoted text>'\n\t [ --package=EMAN --jobid=<int> --oneiter=<iter> --startiter=<iter> --zoom=<float> "
			+"--contour=<contour> --rundir=/path/ --commit ]")

		### integers
		self.parser.add_option("-i", "--oneiter", dest="oneiter", type="int",
			help="Only upload one iteration", metavar="INT")
		self.parser.add_option("--startiter", dest="startiter", type="int",
			help="Begin upload from this iteration", metavar="INT")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack id in the database", metavar="INT")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="Initial model id in the database", metavar="INT")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="Jobfile id in the database", metavar="INT")

		### floats
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.75,
			help="Zoom factor for snapshot rendering (1.75 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("--mass", dest="mass", type="int",
			help="Mass (in kDa) at which snapshot of density will be contoured", metavar="kDa")
		self.parser.add_option("--filter", dest="snapfilter", type="float",
			help="Low pass filter in angstrum for snapshot rendering (0.6*FSC_0.5 by default)", metavar="FLOAT")

		### true / false
		self.parser.add_option("--chimera-only", dest="chimeraonly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run chimera")
		self.parser.add_option("--euler-only", dest="euleronly", default=False,
			action="store_true", help="Do not do any reconstruction calculations only run euler jump calculation")

		### choices
		self.packages = ( "EMAN", "EMAN/MsgP", "EMAN/SpiCoran")
		self.parser.add_option("-k", "--package", dest="package", default="EMAN",
			help="Reconstruction package used (EMAN by default)", metavar="TEXT",
			type="choice", choices=self.packages, )

	#=====================
	def checkConflicts(self):
		if self.params['package'] not in self.packages:
			apDisplay.printError("No valid reconstruction package method specified")
		# msgPassing requires a jobId in order to get the jobfile & the paramters
		if ((self.params['package'] == 'EMAN/MsgP' or self.params['package'] == 'EMAN/SpiCoran')
		 and self.params['jobid'] is None):
			err = self.tryToGetJobID()
			if err:
				apDisplay.printError(self.params['package']
					+" refinement requires a jobid. Please enter a jobId,"
					+" e.g. --jobid=734" + '\n' + err)
		if self.params['package'] != "EMAN/SpiCoran":
			### check if we have coran files
			corans = glob.glob("classes_coran.*.hed")
			if corans and len(corans) > 0:
				apDisplay.printError("You used coran in the recon, but it was not selected\n"
					+"set package to coran, e.g. --package='EMAN/SpiCoran'")
		if self.params['stackid'] is None:
			apDisplay.printError("please enter a stack id, e.g. --stackid=734")
		if self.params['modelid'] is None:
			apDisplay.printError("please enter a starting model id, e.g. --modelid=34")
		if self.params['description'] is None:
			apDisplay.printError("please enter a recon description, e.g. --description='my fav recon'")
		if self.params['runname'] is None:
			apDisplay.printError("please enter a recon run name, e.g. --runname=recon11")
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
	def tryToGetJobID(self):
		jobname = self.params['runname'] + '.job'
		jobtype = 'recon'
		jobpath = self.params['rundir']
		qpath = appiondata.ApPathData(path=os.path.abspath(jobpath))
		q = appiondata.ApClusterJobData(name=jobname, jobtype=jobtype, path=qpath)
		results = q.query()
		if len(results) == 1:
			## success, only one job id found
			self.params['jobid'] = results[0].dbid
			return ''
		elif len(results) > 1:
			## fail because too many job ids
			jobids = [result.dbid for result in results]
			return 'Several Job IDs found for this run: %s\nYou will have to manually specify a jobid' % (jobids,)
		else:
			## no job found
			self.params['jobid'] = None
			return ''

	#=====================
	def setRunDir(self):
		jobdata = apRecon.getClusterJobDataFromID(self.params['jobid'])
		if jobdata:
			self.params['rundir'] = jobdata['path']['path']


	#=====================
	def start(self):
		if self.params['rundir'] is None or not os.path.isdir(self.params['rundir']):
			apDisplay.printError("upload directory does not exist: "+str(self.params['rundir']))


		### create temp directory for extracting data
		self.params['tmpdir'] = os.path.join(self.params['rundir'], "temp")
		apParam.createDirectory(self.params['tmpdir'], warning=True)

		### make sure that the stack & model IDs exist in database
		emanJobFile = apRecon.findEmanJobFile(self.params)
		self.params['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		self.params['stackmapping'] = apRecon.partnum2defid(self.params['stackid'])
		self.params['model'] = apRecon.getModelData(self.params['modelid'])
		self.params['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])

		### parse out the refinement parameters from the log file
		apRecon.parseLogFile(self.params)

		### parse out the message passing subclassification parameters from the job/log file
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
				### if beginning at later iteration, skip to that one
				if self.params['startiter'] and int(iteration['num']) < self.params['startiter']:
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
			if self.params['oneiter'] is None:
				apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
				eulerjump = apEulerJump.ApEulerJump()
				eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, stackid)
			### coran keep plot
			if self.params['package']=='EMAN/SpiCoran':
				apCoranPlot.makeCoranKeepPlot(reconrunid)
			apRecon.getGoodBadParticlesFromReconId(reconrunid)

#=====================
#=====================
if __name__ == '__main__':
	uploadRecon = UploadReconScript()
	uploadRecon.start()
	uploadRecon.close()


