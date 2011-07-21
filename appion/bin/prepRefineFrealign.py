#!/usr/bin/env python
import os
import sys
import glob

#appion
from appionlib import apPrepRefine
from appionlib import apStack
from appionlib import apFrealign
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apScriptLog

def maxIfNotNone(numlist):
	sortset = list(set(numlist))
	return sortset[-1]

def minIfNotNone(numlist):
	sortset = list(set(numlist))
	if len(sortset) > 1 and sortset[0] is None:
		return sortset[1]
	else:
		return sortset[0]

class FrealignPrep3DRefinement(apPrepRefine.Prep3DRefinement):
	def setupParserOptions(self):
		super(FrealignPrep3DRefinement,self).setupParserOptions()
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
			help="choose if frealign should not perform ctf correction")

	def setRefineMethod(self):
		self.refinemethod = 'emanrecon'

	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("EMAN projection match can only take one model")

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	def proc3dFormatConversion(self):
		extname = 'hed'
		return extname

	def getStackRunParams(self):
		stackruns = apStack.getStackRunsFromStack(self.stack['data'])
		stackrun = stackruns[0]
		self.stackparamdata = stackrun['stackParams']
		self.stackrunlogparams = apScriptLog.getScriptParamValuesFromRunname(stackrun['stackRunName'],jobdata=None)

	def preprocessParticleStackWithProc2d(self):
		self.getStackRunParams()
		# use original stackrun log parameters to create preparation parameters
		if 'defocpair' in self.stackrunlogparams.keys():
			self.params['defocpair'] = True
		else:
			self.params['defocpair'] = False
		if not self.stackparamdata['phaseFlipped']:
			# non-ctf-corrected stack can use proc2d to prepare
			self.no_ctf_correction = True
			if self.stackparamdata['inverted']:
				self.invert = True
			newstackfile = super(FrealignPrep3DRefinement,self).preprocessParticleStackWithProc2d()
			return newstackfile
		else:
			# Need to recreate the ctf-uncorrected stack.  preprocess is not useful
			self.no_ctf_correction = False
			return self.stack['file']

	def setArgText(self,key,numlist,getmax=False):
		text = ''
		if getmax:
			value = maxIfNotNone(list(numlist))
		else:
			value = minIfNotNone(list(numlist))
		if value is not None:
			if type(value) == type(1):
				text = '--%s=%d' % (key,value)
			else:
				text = '--%s=%.3f' % (key,value)
		return text
		
	def convertToRefineParticleStack(self):
		if self.no_ctf_correction:
			return
		stackdata = self.stack['data']
		stackid = stackdata.dbid
		stackruns = apStack.getStackRunsFromStack(self.stack['data'])
		stackrun = stackruns[0]
		stackpathname = os.path.basename(stackdata['path']['path'])
		numpart = apStack.getNumberStackParticlesFromId(stackid)
		newstackrunname = self.params['runname']
		newstackrundir = self.params['rundir']
		# use first particle image to get presetname
		oneparticle = apStack.getOneParticleFromStackId(stackid, particlenumber=1)
		preset =oneparticle['particle']['image']['preset']
		if preset:
			presetname = preset['name']
		else:
			presetname = 'manual'
		# use first stack run to get parameters
		paramdata = stackrun['stackParams']
		bin = paramdata['bin']*self.params['bin']
		unbinnedboxsize = self.stack['boxsize']*paramdata['bin']
		lowpasstext = self.setArgText('lowpass',(self.params['lowpass'],paramdata['lowpass']),False)
		highpasstext = self.setArgText('highpass',(self.params['highpass'],paramdata['highpass']),True)
		partlimittext = self.setArgText('partlimit',(numpart,self.params['last']),False)
		xmipp_normtext = self.setArgText('xmipp-normalize',(paramdata['xmipp-norm'],),True)
		sessionid = int(self.params['expid'])
		sessiondata = apDatabase.getSessionDataFromSessionId(sessionid)
		sessionname = sessiondata['name']
		projectid = self.params['projectid']

		# The assumption is that the image is from ice grid and digital camera (black particles on white background
		if 'reverse' in self.stackrunlogparams.keys():
			reversetext = '--reverse'
		else:
			reversetext = ''
		if 'defocpair' in self.stackrunlogparams.keys():
			defoctext = '--reverse'
		else:
			defoctext = ''
		cmd = '''
makestack2.py --single=start.hed --fromstackid=%d %s %s %s %s %s --no-invert --normalized %s --boxsize=%d --bin=%d --description="frealign refinestack based on %s(id=%d)" --projectid=%d --preset=%s --runname=%s --rundir=%s --no-wait --no-commit --no-continue --session=%s --expId=%d --jobtype=makestack2
		''' % (stackid,lowpasstext,highpasstext,partlimittext,reversetext,defoctext,xmipp_normtext,unbinnedboxsize,bin,stackpathname,stackid,projectid,presetname,newstackrunname,newstackrundir,sessionname,sessionid)
		logfilepath = os.path.join(newstackrundir,'frealignstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)

		if returncode > 0:
			apDisplay.printError('Error in Frealign specific stack making')
		self.stack['file'] = os.path.join(self.params['rundir'],'start.hed')
		self.stack['format'] = 'frealign'
		self.stack['bin'] = self.params['bin']
		# use the same complex equation as in eman clip
		clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
		self.stack['boxsize'] = clipsize / self.params['bin']
		self.stack['apix'] = self.stack['apix'] * self.params['bin']

		#clean up
		rmfiles = glob.glob("*.box")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

	def addStackToSend(self,hedfilepath):
		# Imagic Format stack has 'hed' and 'img' files
		self.addToFilesToSend(hedfilepath)
		imgfilepath = hedfilepath.replace('hed','img')
		self.addToFilesToSend(imgfilepath)

	def addModelToSend(self,hedfilepath):
		# Imagic Format stack has 'hed' and 'img' files
		self.addStackToSend(hedfilepath)

	def otherPreparations(self):
		if 'reconiterid' not in self.params.keys() or self.params['reconiterid'] == 0:
			self.params['reconiterid'] = None
		paramfile = 'params.0.par'
		apFrealign.generateParticleParams(self.params,paramfile)
		self.addToFilesToSend(paramfile)

#=====================
if __name__ == "__main__":
	app = FrealignPrep3DRefinement()
	app.start()
	app.close()

