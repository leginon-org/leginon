#!/usr/bin/python -O

#python
import os
import sys
import time
import subprocess
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apStack
from appionlib import apParam

class testScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ --commit --show-cmd --verbose ]")
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
		return

	#=====================
	def checkConflicts(self):
		return

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.path.join(os.getcwd(), self.timestamp)
		return

	#=====================
	def runCommand(self, cmd):
		t0 = time.time()
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "magenta")
			sys.stderr.write(
				apDisplay.colorString("COMMAND: \n","magenta")
				+apDisplay.colorString(cmd, "cyan")+"\n")
			apDisplay.printColor("###################################", "cyan")
		try:
			if self.params['verbose'] is False:
				proc = subprocess.Popen(cmd, shell=True, 
					stdout=subprocess.PIPE)#, stderr=subprocess.PIPE)
			else:
				proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		except:
			apDisplay.printError("could not run command: "+cmd)
		runtime = time.time() - t0
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "cyan")
			apDisplay.printColor("command ran in "+apDisplay.timeString(runtime), "cyan")
		if runtime < 1:
			apDisplay.printError("command runtime was too short: "
				+apDisplay.timeString(runtime))
		elif runtime < 10:
			apDisplay.printWarning("command runtime was very short: "
				+apDisplay.timeString(runtime))
			return False

		#self.timestamp = apParam.makeTimestamp()
		return True

	#=====================
	def runFindEM(self):
		runid = "findem"
		cmd = (os.path.join(self.appiondir, "bin", "templateCorrelator.py ")
			+" "+self.images+" runid="+runid+" outdir="+self.params['outdir']+" "
			+" diam=140 bin=4 maxpeaks=50 overlapmult=3 nocontinue "
			+" templateIds=53 range1=0,180,30 thresh=0.50 maxthresh=0.60 "
			+" lp=25 hp=600 pixlimit=3.0 median=3 ")
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def uploadImages(self):
		imglist = [
			'06jul12a_00004gr_00054sq_00022hl_00005en.mrc',
			'06jul12a_00022gr_00013sq_00002hl_00004en.mrc',
			'06jul12a_00022gr_00037sq_00025hl_00005en.mrc',
			'06jul12a_00015gr_00028sq_00004hl_00002en.mrc',
			'06jul12a_00022gr_00013sq_00003hl_00005en.mrc',
			'06jul12a_00027gr_00065sq_00009hl_00005en.mrc',
			'06jul12a_00015gr_00028sq_00011hl_00003en.mrc',
			'06jul12a_00022gr_00037sq_00005hl_00002en.mrc',
			'06jul12a_00035gr_00063sq_00012hl_00004en.mrc',
			'06jul12a_00015gr_00028sq_00023hl_00002en.mrc',
			'06jul12a_00022gr_00037sq_00005hl_00005en.mrc',
			'06jul12a_00015gr_00028sq_00023hl_00004en.mrc',
			'06jul12a_00022gr_00037sq_00025hl_00004en.mrc',
		]

		imgtree = apDatabase.getSpecificImagesFromSession(imglist, '06jul12a')

		### create batch file
		imagedatfile = os.path.join(self.params['rundir'], "image%s.dat"%(self.timestamp))
		f = open(imagedatfile, "w")
		for imgdata in imgtree:
			imgpath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
			apix = apDatabase.getPixelSize(imgdata)
			mag = imgdata['scope']['magnification']
			defocus = imgdata['scope']['defocus']
			voltage = imgdata['scope']['high tension']
			outstr = ("%s\t%.3e\t%d\t%d\t%d\t%.3e\t%d\n"%(imgpath, apix*1e-10, 1, 1, mag, defocus, voltage))
			f.write(outstr)
		f.close()

		### run command
		script = os.path.join(self.appiondir, "bin", "imageloader.py ")
		params = (" --runname=%s --projectid=%d --session=%s --batch=%s --scopeid=%d --cameraid=%d --description='%s' "
			%(self.timestamp, self.params['projectid'], self.timestamp, 
			imagedatfile, 89, 90, 'running test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def dogPicker(self):
		if apDatabase.getSelectionIdFromName('dogrun1', self.timestamp) is not None:
			return

		script = os.path.join(self.appiondir, "bin", "dogPicker.py ")
		params = (" --runname=dogrun1 --projectid=%d --session=%s --diam=%d --thresh=%.2f --invert --no-wait --planereg --maxsize=%.2f"
			%(self.params['projectid'], self.timestamp, 200, 0.45, 0.02))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def aceTwo(self, bin):
		script = os.path.join(self.appiondir, "bin", "pyace2.py ")
		params = (" --runname=acetwo%d --projectid=%d --session=%s --no-wait --bin=%d"
			%(bin, self.params['projectid'], self.timestamp, bin))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def makeStack(self, stackname):
		if apStack.getStackIdFromRunName(stackname, self.timestamp) is not None:
			return

		selectid = apDatabase.getSelectionIdFromName('dogrun1', self.timestamp)

		script = os.path.join(self.appiondir, "bin", "makestack2.py ")
		params = ((" --runname=%s --projectid=%d --session=%s --no-wait --boxsize=%d --bin=%d --acecutoff=%.2f --invert --phaseflip --selectionid=%d --description='%s'")
			%(stackname, self.params['projectid'], self.timestamp, 320, 2, 0.7, selectid, 'running test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================
	def filterStack(self, stackname, substackname):
		if apStack.getStackIdFromSubStackName(substackname, self.timestamp) is not None:
			return

		stackid = apStack.getStackIdFromRunName(stackname, self.timestamp)

		script = os.path.join(self.appiondir, "bin", "stackFilter.py ")
		params = ((" --runname=%s --projectid=%d --old-stack-id=%d --minx=%d --maxx=%d --miny=%d --maxy=%d --description='%s'")
			%(substackname, self.params['projectid'], stackid, 
			600, 1000, 82, 105, 
			'filtering junk with test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

		return substackname

	#=====================
	def maxLike(self, substackname):
		stackid = apStack.getStackIdFromSubStackName(substackname, self.timestamp)

		print (self.params['projectid'], stackid, 10, 2000, 3, 1, 12, 'max like with test suite application')

		script = os.path.join(self.appiondir, "bin", "maxlikeAlignment.py")
		params = (" --runname=maxlike1 --projectid=%d --stack=%d --lowpass=%d --highpass=%d --num-ref=%d --bin=%d --savemem --converge=slow --mirror --fast --fast-mode=narrow --max-iter=%d --description='%s'"
			%(self.params['projectid'], stackid, 10, 2000, 3, 1, 12, 
			'max like with test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)

	#=====================.
	def start(self):
		self.timestamp = '10may07o04'
		#self.uploadImages()

		### Dog Picker
		self.dogPicker()

		### Ace 2
		self.aceTwo(bin=2)
		self.aceTwo(bin=4)

		### Make stack
		self.makeStack('stack1')

		### Filter stack
		self.filterStack('stack1', 'meanfilt2')

		### Maximum likelihood
		self.maxLike('meanfilt2')

		### Upload max like

		### Upload templates
		### Template pick
		### Make stack
		### Filter stack
		### Upload model
		### Do reconstruction
		### Upload recon
		return

#=====================
if __name__ == "__main__":
	tester = testScript()
	tester.start()
	tester.close()

