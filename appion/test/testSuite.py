#!/usr/bin/python -O

#python
import os
import sys
import subprocess
#appion
import appionScript
import apDisplay

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ --commit --show-cmd --verbose ]")
		### commit
		self.parser.add_option("-C", "--commit", dest="commit", default=False,
			action="store_true", help="Commit runs to database")
		self.parser.add_option("--no-commit", dest="commit", default=False,
			action="store_false", help="Do not commit runs to database")
		### showcmd
		self.parser.add_option("-S", "--show-cmd", dest="showcmd", default=True,
			action="store_true", help="Show each command before running")
		self.parser.add_option("--no-show-cmd", dest="showcmd", default=True,
			action="store_false", help="Do not show each command before running")
		### verbose
		self.parser.add_option("-v", "--verbose", dest="verbose", default=True,
			action="store_true", help="Show command output while running")
		self.parser.add_option("-q", "--quiet", dest="verbose", default=True,
			action="store_false", help="Do not show command output while running")
		### outdir
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to store output files", metavar="PATH")
		return

	#=====================
	def checkConflicts(self):
		return

	#=====================
	def setOutDir(self):
		self.params['outdir'] = os.path.join(os.getcwd(), self.timestamp)
		return

	#=====================
	def runCommand(self, cmd):
		if self.params['showcmd'] is True:
			sys.stderr.write(
				apDisplay.colorString("COMMAND: \n","magenta")
				+apDisplay.colorString(cmd, "cyan")+"\n")
		try:
			if self.params['verbose'] is False:
				proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			else:
				proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		except:
			apDisplay.printWarning("could not run command: "+cmd)
			return False
		return True

	#=====================
	def runDogPicker(self):
		runid = "dog"
		cmd = (os.path.join(self.appiondir, "bin", "dogPicker.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" diam=140 bin=8 maxpeaks=50 overlapmult=3 nocontinue "
			+" lp=0 hp=0 pixlimit=3.0 median=3 ")
		if self.params['commit'] is True:
			cmd += " commit "
		self.runCommand(cmd)

	#=====================
	def runFindEM(self):
		runid = "findem"
		cmd = (os.path.join(self.appiondir, "bin", "templateCorrelator.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" diam=140 bin=4 maxpeaks=50 overlapmult=3 nocontinue "
			+" templateIds=53 range1=0,180,30 thresh=0.45 "
			+" lp=25 hp=600 pixlimit=3.0 median=3 ")
		if self.params['commit'] is True:
			cmd += " commit "
		self.runCommand(cmd)

	#=====================
	def runManualPicker(self):
		runid = "manpick"
		cmd = (os.path.join(self.appiondir, "bin", "manualpicker.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" diam=140 bin=4 nocontinue "
			+" pickrunid=53 "
			+" lp=25 hp=600 pixlimit=3.0 median=3 ")
		if self.params['commit'] is True:
			cmd += " commit "
		self.runCommand(cmd)

	#=====================
	def runAce(self):
		runid = "ace"
		cmd = (os.path.join(self.appiondir, "bin", "pyace.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" edgethcarbon=0.8 edgethice=0.6 pfcarbon=0.9 pfice=0.3 "
			+" overlap=2 fieldsize=512 resamplefr=1 medium=carbon cs=2.0 drange=0 "
			+" display=1 stig=0 nocontinue ")
		if self.params['commit'] is True:
			cmd += " commit "
		self.runCommand(cmd)

	#=====================
	def runMakeStack(self):
		runid = "stack"
		cmd = (os.path.join(self.appiondir, "bin", "makestack.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" single=start.hed phaseflip boxsize=128 bin=4 "
			+" pickrunid=53 mindefocus=-0.25e-6 ace=0.95 "
			+" lp=25 hp=600 partlimit=150  description='testing'")
		if self.params['commit'] is True:
			cmd += " commit "
		self.runCommand(cmd)

	#=====================
	def start(self):
		self.images = ("07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc "
			+"07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc "
			+"07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc "
			+"07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc "
			+"07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc ")

		### Dog Picker
		self.runDogPicker()
		### FindEM
		self.runFindEM()
		### Man Picker
		self.runManualPicker()
		### ACE
		self.runAce()
		### Make Stack
		self.runMakeStack()

		return

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

