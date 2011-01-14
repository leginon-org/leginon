#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import shutil
import re
import subprocess
import math
#pyami
from pyami import mrc
#appion
from appionlib import appionTiltSeriesLoop
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase

#=====================
#=====================
class TomoAlignReconLooper(appionTiltSeriesLoop.AppionTiltSeriesLoop):
	def setupParserOptions(self):
		self.alignmethods = ( "imod-shift", "protomo" )
		self.parser.add_option("--alignmethod", dest="alignmethod",
			type="choice", choices=self.alignmethods, default="protomo" )
		self.parser.add_option("--reconthickness", dest="reconthickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--reconbin", dest="reconbin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")
		return

	def checkConflicts(self):
		return

	def commitToDatabase(self,tiltseriesdata):
		# nothing to commit right now.
		return

	def isBadTiltSeries(self, tiltseriesdata):
		# no need to process if only a small number of images are taken
		imgtree = apDatabase.getImagesFromTiltSeries(tiltseriesdata,False)
		return len(imgtree) < 4

	def runAppionScriptInSubprocess(self,cmd,logfilepath):
		apDisplay.printMsg('running AppionScript:')
		apDisplay.printMsg('------------------------------------------------')
		apDisplay.printMsg(cmd)
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout_value = proc.communicate()[0]
		while proc.returncode is None:
			time.wait(60)
			stdout_value = proc.communicate()[0]
		try:
			file = open(logfilepath,'w')
		except:
			apDisplay.printError('Log file can not be created, process did not run.')
		file.write(stdout_value)
		file.close()
		if proc.returncode > 0:
			pieces = cmd.split(' ')
			apDisplay.printWarning('AppionScript %s had an error. Please check its log file: \n%s' % (pieces[0].upper(),outpath))
		else:
			apDisplay.printMsg('AppionScript ran successfully')
		apDisplay.printMsg('------------------------------------------------')
		return proc.returncode

	def processTiltSeries(self, tiltseriesdata):
		seriesnumber = tiltseriesdata['number']
		pieces = self.params['rundir'].split('/')
		tomobasepath = '/'.join(pieces[:-1])
		tiltseriesdirname = "tiltseries%d" % seriesnumber
		tiltseriespath = os.path.join(tomobasepath,tiltseriesdirname)
		if self.params['commit']:
			commitstr = '--commit'
		else:
			commitstr = '--no-commit'
		if self.params['description'] is None:
			self.params['description'] = 'auto recon '+self.params['runname']
		
		# align the tilt series
		alignrundir = os.path.join(tiltseriespath,'align',self.params['runname'])
		alignlogpath = os.path.join(alignrundir,self.params['runname']+'.appionsub.log')
		command = 'tomoaligner.py' + ' ' + '--projectid=%d' % (self.params['projectid']) + ' ' + '--session=' + self.params['sessionname'] + ' ' + '--runname=' + self.params['runname'] + ' ' + '--rundir=' + alignrundir + ' ' + '--tiltseriesnumber=%d' % (seriesnumber) + ' ' + '--alignmethod=%s' % self.params['alignmethod'] + ' ' + '--description="%s"' % (self.params['description'],) + ' ' + commitstr
		return_code = self.runAppionScriptInSubprocess(command,alignlogpath)

		# reconstruct full tomogram with the alignments
		aligners = apTomo.getAlignersFromTiltSeries(tiltseriesdata,self.params['runname'])
		for alignerdata in aligners:
			reconrunname = self.params['runname']+'_a%d'% alignerdata.dbid
			reconrundir = os.path.join(tiltseriespath,reconrunname)
			reconlogpath = os.path.join(reconrundir,reconrunname+'.appionsub.log')
			command = 'tomomaker.py' + ' ' + '--projectid=%d' % (self.params['projectid']) + ' ' + '--session=' + self.params['sessionname'] + ' ' + '--runname=' + reconrunname + ' ' + '--rundir=' + reconrundir + ' ' + '--alignerid=%d' % alignerdata.dbid + ' ' + '--bin=%d' % self.params['reconbin'] + ' ' + '--thickness=%d' % self.params['reconthickness'] + ' ' + '--description="%s using aligner %d"' % (self.params['description'],alignerdata.dbid) + ' ' + commitstr
			return_code = self.runAppionScriptInSubprocess(command,reconlogpath)

#=====================
if __name__ == '__main__':
	app = TomoAlignReconLooper()
	app.run()
	app.close()



