#!/usr/bin/env python


import os
import re
import sys
import time
import json
### appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apProject
from appionlib import apFile
from appionlib import apDatabase

#=====================
#=====================
class appionLauncherScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --name=<name> --stacks=<int>,<int>,<int>  "
			+"--description='<text>' --commit [options]")
		self.parser.add_option("--preset", dest="preset",
			help="image preset for unaligned frames", metavar="preset")
		self.parser.add_option("--gpuids", dest="gpuids", default='0',
			help="gpuids to be used for motion correction, separated by commas (1 job per gpuid)")
		self.parser.add_option("--alignlabel", dest="alignlabel", default='a')
		self.parser.add_option("--totaldose", dest="totaldose", metavar="FLOAT",
			help="total exposure (in e-/A^2)")

	#=====================
	def checkConflicts(self):
		# set runname to get through initialization
		self.params['runname'] = "foo"

	#=====================
	def setRunDir(self):
		pass
	#=====================
	def setupRunInfo(self,command):
		f = open(os.path.join(self.appiondir,'appionlib/apJobtypeDict.json'))
		jobdict=json.load(f)
		self.params['jobtype'] = jobdict[command]['jobtype']
		self.params['runname'] = jobdict[command]['runname']+str(self.getMaxRunNumber()+1)
		self.params['rundir'] = os.path.join(self.params['rundir'],self.params['runname'])
		f.close()

	#=====================
	def toBinOrNotToBin(self):
		if not self.params['totaldose']:
			self.params['totaldose'] = apDatabase.getDoseFromSessionPresetNames(self.params['session'],self.params['preset'])

		camdims = apDatabase.getCameraDimsFromSessionPresetName(self.params['session'],self.params['preset'])

		if camdims[0] > 4000 and camdims[1] > 4000:
			return 2
		return 1

	#=====================
	def createMotionCorCommand(self,gpuid):
		# make motioncor2 command
		cmd = "makeDDAlignMotionCor2_UCSF.py"

		self.setupRunInfo(cmd)

		pars = {}
		pars['runname'] = self.params['runname']
		pars['rundir'] = self.params['rundir']
		pars['session'] = self.params['session']
		pars['expid'] = self.params['expid']
		pars['projectid'] = self.params['projectid']
		pars['jobtype'] = self.params['jobtype']
		pars['bin'] = self.toBinOrNotToBin()
		pars['align'] = True
		pars['gpuids'] = gpuid
		pars['ddstartframe'] = 0
		pars['MaskCentrow'] = 0
		pars['MaskCentcol'] = 0
		pars['MaskSizerows'] = 1
		pars['MaskSizecols'] = 1
		pars['Patchrows'] = 5
		pars['Patchcols'] = 5
		pars['Iter'] = 7
		pars['FmRef'] = 0
		pars['doseweight'] = True
		pars['totaldose'] = self.params['totaldose']
		pars['Bft'] = 100
		pars['alignlabel'] = self.params['alignlabel']
		pars['nrw'] = 1
		pars['preset'] = self.params['preset']
		pars['commit'] = True
		pars['no-rejects'] = True
		pars['continue'] = True
		pars['parallel'] = True

		return self.convertParToString(cmd,pars)
	
	#=====================
	def createCtfFind4Command(self,preset):
		# make ctffind4 command
		cmd = "ctffind4.py"

		self.setupRunInfo(cmd)

		pars = {}
		pars['runname'] = self.params['runname']
		pars['rundir'] = self.params['rundir']
		pars['session'] = self.params['session']
		pars['expid'] = self.params['expid']
		pars['projectid'] = self.params['projectid']
		pars['jobtype'] = self.params['jobtype']
		pars['preset'] = preset
		pars['ampcontrast'] = 0.1
		pars['fieldsize'] = 1024
		pars['resmin'] = 30
		pars['resmax'] = 4
		pars['defstep'] = 0.1
		pars['numstep'] = 25
		pars['dast'] = 0.05
		pars['min_phase_shift'] = 10
		pars['max_phase_shift'] = 170
		pars['phase_search_step'] = 10
		pars['commit'] = True
		pars['no-rejects'] = True
		pars['continue'] = True
		pars['bestdb'] = True
		pars['parallel'] = True

		return self.convertParToString(cmd,pars)

	#=====================
	def convertParToString(self,cmd,pars):
		for p in pars:
			if (pars[p]) is True:
				cmd += " --%s"%(p)
			else: cmd += " --%s=%s"%(p,pars[p])
		return cmd

	#=====================
	def launchjob(self,cmd):
		apDisplay.printMsg("launching command:")
		apDisplay.printMsg("%s\n"%cmd)

	#=====================
	def start(self):
		# get session-related info
		self.sessiondata = self.getSessionData()
		self.params['session'] = self.sessiondata['name']

		# start with motion correction
		# launch one job for each gpuid specified
		for gpuid in self.params['gpuids'].split(','):
			cmd = self.createMotionCorCommand(gpuid)
			self.launchjob(cmd)

		alignedpreset = "%s-%s"%(self.params['preset'],self.params['alignlabel'])

		# wait until an aligned preset shows up
		sys.stderr.write("\nWaiting for aligned images...")
		twait0 = time.time()
		timelimit = 1800
		for i in range(timelimit/10):
			if len(apDatabase.getImagesFromDB(self.params['session'],alignedpreset,msg=False)) > 0:
				break
			time.sleep(20)
			# print a dot every 20 seconds
			sys.stderr.write(".")

			if time.time()-twait0 > timelimit:
				sys.stderr.write("\n")
				apDisplay.printWarning("No aligned images created after 30 minutes, so I am quitting")
				return False
		sys.stderr.write("\n\n")

		# launch CtfFind4
		cmd = self.createCtfFind4Command(alignedpreset)
		self.launchjob(cmd)

#=====================
if __name__ == "__main__":
	appionLauncher = appionLauncherScript()
	appionLauncher.start()
	appionLauncher.close()

