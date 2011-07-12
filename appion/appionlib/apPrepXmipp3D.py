#!/usr/bin/env python

import os
#appion
from appionlib import apPrepRefine
from appionlib import apXmipp
from appionlib import apDisplay
from appionlib import apFile

class XmippPrep3DRefinement(apPrepRefine.Prep3DRefinement):
	def setRefineMethod(self):
		self.refinemethod = 'xmipp'

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = True

	def convertToRefineParticleStack(self):
		hedpath = self.stack['file']
		selfile = apXmipp.breakupStackIntoSingleFiles(hedpath)
		self.stack['file'] = os.path.join(self.params['rundir'],selfile)
		self.stack['format'] = 'xmipp'
		# remove EMAN Imagic Stack Files
		apFile.removeFile(hedpath, warn=True)
		imgpath = hedpath[:-3]+'img'
		apFile.removeFile(imgpath, warn=True)

	def createTarFileFromDirectory(self,dir, tarfile):
		cmd = 'tar -cvzf %s %s' % (tarfile, dir)
		logfilepath = os.path.join(self.params['rundir'],'tar.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('tar failed')

	def addStackToSend(self,selfilepath):
		self.addToFilesToSend(selfilepath)
		# Xmipp Format stack has 'selfile' and need to tar the folder it is pointing to
		inpartlistpath = selfilepath
		inlist = open(inpartlistpath,'r')
		lines = inlist.readlines()
		firstline = lines[0]
		firstpartpath = firstline.split(' ')
		partbasepath = '/'.join(firstpartpath[0].split('/')[:-2])
		tarfile = 'partfiles.tar.gz'
		self.createTarFileFromDirectory(partbasepath,tarfile)
		self.addToFilesToSend(tarfile)

#=====================
if __name__ == "__main__":
	app = XmippPrep3DRefinement()
	app.start()
	app.close()

