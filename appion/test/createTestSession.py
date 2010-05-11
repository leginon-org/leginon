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
			apDisplay.printWarning("could not run command: "+cmd)
			sys.exit(1)
			return False
		runtime = time.time() - t0
		if self.params['showcmd'] is True:
			apDisplay.printColor("###################################", "cyan")
			apDisplay.printColor("command ran in "+apDisplay.timeString(runtime), "cyan")
		if runtime < 10:
			apDisplay.printWarning("command runtime was very short: "
				+apDisplay.timeString(runtime))
			sys.exit(1)
			return False

		#self.timestamp = apParam.makeTimestamp()
		return True

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

		imgtree = apDatabase.getSpecificImagesFromDB(imglist)

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
			imagedatfile, 89, 90, self.params['description']+' running test suite application'))
		if self.params['commit'] is True:
			params += " --commit "
		else:
			params += " --no-commit "
		self.runCommand(script+" "+params)


	#=====================.
	def start(self):
		self.uploadImages()
		return

#=====================
if __name__ == "__main__":
	tester = testScript()
	tester.start()
	tester.close()

