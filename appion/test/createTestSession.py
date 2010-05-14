#!/usr/bin/python -O

#python
import os
import sys
import time
import random
import subprocess
#appion
import leginon.leginondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apStack
from appionlib import apParam
from appionlib import apFile

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
	def downloadImagesFromAMI(self):
		imglist = []
		from urllib import urlretrieve
		imgdict = {
			110: '06jul12a_00022gr_00037sq_00025hl_00005en.mrc',
			111: '06jul12a_00035gr_00063sq_00012hl_00004en.mrc',
			112: '06jul12a_00015gr_00028sq_00004hl_00002en.mrc',
			113: '06jul12a_00015gr_00028sq_00023hl_00002en.mrc',
			114: '06jul12a_00015gr_00028sq_00023hl_00004en.mrc',
			115: '06jul12a_00022gr_00013sq_00002hl_00004en.mrc',
			116: '06jul12a_00022gr_00013sq_00003hl_00005en.mrc',
		}
		for key in imgdict.keys():
			imgfile = os.path.join(self.params['rundir'], imgdict[key])
			url = ("http://ami.scripps.edu/redmine/attachments/download/%d/%s"
				%(key, imgdict[key]))
			apDisplay.printMsg("Downloading image '%s'"%(imgdict[key]))
			urlretrieve(url, imgfile)
			if not os.path.isfile(imgfile):
				apDisplay.printError("could not download file: %s"%(url))
			if apFile.fileSize(imgfile) < 30e6:
				apDisplay.printError("error in downloaded file: %s"%(url))
			imglist.append(imgfile)
		return imglist

	#=====================
	def createImageBatchFile(self, imglist):
		imgstats = {
			'pixelsize': 0.815e-10,
			'binx': 1,
			'biny': 1,
			'mag': 100000,
			'defocus': -2.0e-6,
			'voltage': 120000,
		}

		imagedatfile = os.path.join(self.params['rundir'], "image%s.dat"%(self.timestamp))
		f = open(imagedatfile, "w")
		for imgfile in imglist:
			outstr = ("%s\t%.3e\t%d\t%d\t%d\t%.3e\t%d\n"
				%(imgfile, imgstats['pixelsize'], imgstats['binx'], imgstats['biny'], 
				imgstats['mag'], imgstats['defocus'], imgstats['voltage']))
			f.write(outstr)
		f.close()
		return imagedatfile

	#=====================
	def getInstrumentIds(self):
		### get scope
		scopeq = leginon.leginondata.InstrumentData()
		print scopeq
		scopeq['name'] = 'SimTEM'
		scopedatas = scopeq.query(results=1)
		if not scopedatas or len(scopedatas) < 1:
			apDisplay.printError("Could not find simulated scope")
		random.shuffle(scopedatas)
		scopeid = scopedatas[0].dbid
		apDisplay.printMsg("Selected scope %d from host %s"	
			%(scopeid, scopedatas[0]['hostname']))

		### get camera
		cameraq = leginon.leginondata.InstrumentData()
		cameraq['name'] = 'SimCCDCamera'
		cameradatas = cameraq.query(results=1)
		if not cameradatas or len(cameradatas) < 1:
			apDisplay.printError("Could not find simulated CCD camera")
		random.shuffle(scopedatas)
		carmeraid = cameradatas[0].dbid
		apDisplay.printMsg("Selected camera %d from host %s"	
			%(carmeraid, cameradatas[0]['hostname']))
		return scopeid, carmeraid

	#=====================
	def uploadImages(self):
		### Download images
		imglist = self.downloadImagesFromAMI()

		### create batch file
		imagedatfile = self.createImageBatchFile(imglist)

		### get simulated instrument ids
		scopeid, cameraid = self.getInstrumentIds()

		### run command
		script = os.path.join(self.appiondir, "bin", "imageloader.py ")
		params = (" --runname=%s --projectid=%d --session=%s --batch=%s --scopeid=%d --cameraid=%d --description='%s' "
			%(self.timestamp, self.params['projectid'], self.timestamp, 
			imagedatfile, scopeid, cameraid, self.params['description']+' running test suite application'))
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

