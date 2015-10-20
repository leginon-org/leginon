#!/usr/bin/env python
import os
import sys
import glob
import shutil

#appion
from appionlib import apPrepRefine
from appionlib import apStack
from appionlib import apFrealign
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apScriptLog
from appionlib import apIMAGIC

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
		self.ctfestopts = ('ace2', 'ctffind')
		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
			help="choose if frealign should not perform ctf correction")
		self.parser.add_option('--ctfmethod', dest='ctfmethod',
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)
		self.parser.add_option('--paramonly', dest='paramonly', default=False, action='store_true',
			help="only create parameter file")
		self.parser.add_option('--ctftilt', dest='ctftilt', default=False, action='store_true',
			help="Use ctftilt values")

	def setRefineMethod(self):
		self.refinemethod = 'frealignrecon'
		self.parentstacks = []

	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("EMAN projection match can only take one model")

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	def proc3dFormatConversion(self):
		#Imagic format used to be consistent with stack
		extname = 'mrc'
		return extname

	def getOriginalStackMadeByMakeStack(self):
		if self.parentstacks:
			return self.parentstacks[-1]
		stackdata = self.stack['data']
		#Handle Substack
		while stackdata['oldstack']:
			stackdata = stackdata['oldstack']
			self.parentstacks.append(stackdata)
		return stackdata

	def getStackRunParams(self):
		stackdata = self.getOriginalStackMadeByMakeStack()
		stackruns = apStack.getStackRunsFromStack(stackdata)
		# To Do: need to handle combined stack
		stackrun = stackruns[0]
		self.originalStackParamData = stackrun['stackParams']
		self.stackrunlogparams = apScriptLog.getScriptParamValuesFromRunname(stackrun['stackRunName'],stackdata['path'],jobdata=None)

	def preprocessModelWithProc3d(self):
		rescale = not self.params['paramonly']
		super(FrealignPrep3DRefinement,self).preprocessModelWithProc3d(rescale)

	def preprocessStack(self):
		self.getStackRunParams()
		# use original stackrun log parameters to create preparation parameters
		if 'defocpair' in self.stackrunlogparams.keys():
			self.params['defocpair'] = True
		else:
			self.params['defocpair'] = False
		if self.params['paramonly'] is True:
			return self.stack['file']
		if not self.originalStackParamData['phaseFlipped']:
			# non-ctf-corrected stack can use proc2d to prepare
			self.no_ctf_correction = True
			if self.originalStackParamData['inverted']:
				self.invert = True
			newstackfile = super(FrealignPrep3DRefinement,self).preprocessStack()
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

	def ImagicStackToFrealignMrcStack(self,stackfile):
		stackroot = stackfile[:-4]
		stackbaseroot = os.path.basename(stackfile).split('.')[0]
		apDisplay.printMsg('converting %s from default IMAGIC stack format to MRC as %s.mrc'% (stackroot,stackbaseroot))
		apIMAGIC.convertImagicStackToMrcStack(stackroot,stackbaseroot+'.mrc')
		# clean up non-mrc stack in rundir which may be left from preprocessing such as binning
		tmpstackdir = os.path.dirname(stackfile)
		stackext = os.path.basename(stackfile).split('.')[-1]
		if stackext != 'mrc' and tmpstackdir == self.params['rundir']:
			os.remove(stackfile)
			if stackext == 'hed':
				imgfilepath = stackfile.replace('hed','img')
				os.remove(imgfilepath)
		

	def convertToRefineStack(self):
		'''
		The stack is remaked without ctf correction and without invertion (ccd)
		'''
		newstackroot = os.path.join(self.params['rundir'],os.path.basename(self.stack['file'])[:-4])
		if self.params['paramonly'] is True:
			print 'newstackroot',newstackroot
			self.setFrealignStack(newstackroot)
			return
		# copy existing refined stack if possible
		existing_refine_stack = apStack.getExistingRefineStack(self.stack['data'],'frealign',False,self.params['last'],self.params['bin'],lowpass=self.params['lowpass'],highpass=self.params['highpass'])
		try:
			if existing_refine_stack:
				if existing_refine_stack != os.path.join(self.params['rundir'],newstackroot+'.mrc'):
					shutil.copyfile(existing_refine_stack,newstackroot+'.mrc')
				new_partorderfile = os.path.join(self.params['rundir'],'stackpartorder.list')
				existing_partorderfile = os.path.join(os.path.dirname(existing_refine_stack),'stackpartorder.list')
				# particle order list also need to be copied
				if not os.path.isfile(new_partorderfile) and os.path.isfile(existing_partorderfile):
					shutil.copyfile(existing_partorderfile,new_partorderfile)
				self.setFrealignStack(newstackroot)
				return
		except:
			# make one from scratch if there is error
			apDisplay.printMsg('Error copying existing refine stack, will regenerate')
		if self.no_ctf_correction:
			self.ImagicStackToFrealignMrcStack(self.stack['file'])
			self.setFrealignStack(newstackroot)
			return
		# stack need to be remade without ctf correction
		apDisplay.printWarning('Frealign needs a stack without ctf correction. A new stack is being made....')
		stackdata = self.stack['data']
		madestackdata = self.getOriginalStackMadeByMakeStack()
		stackid = stackdata.dbid
		stackruns = apStack.getStackRunsFromStack(madestackdata)
		# To Do: need to handle combined stack
		stackrun = stackruns[0]
		stackpathname = os.path.basename(stackdata['path']['path'])
		totalpart = apStack.getNumberStackParticlesFromId(stackid)
		if not self.params['last']:
			numpart = totalpart
		else:
			numpart = min(self.params['last'],totalpart)
		newstackrunname = self.params['runname']
		newstackrundir = self.params['rundir']
		newstackimagicfile = os.path.join(newstackrundir,'temp.hed')
		# use first particle image to get presetname
		oneparticle = apStack.getOneParticleFromStackId(stackid, particlenumber=1)
		preset =oneparticle['particle']['image']['preset']
		if preset:
			presetname = preset['name']
		else:
			presetname = 'manual'
		# use first stack run to get parameters
		paramdata = stackrun['stackParams']
		# binning is combination of the original binning of the stack and the preparation binnning
		bin = paramdata['bin']*self.params['bin']
		unbinnedboxsize = self.stack['boxsize']*paramdata['bin']
		lowpasstext = self.setArgText('lowpass',(self.params['lowpass'],paramdata['lowpass']),False)
		highpasstext = self.setArgText('highpass',(self.params['highpass'],paramdata['highpass']),True)
		partlimittext = self.setArgText('partlimit',(numpart,),False)
		
		#normalization
		normtext = ''
		if 'xmipp-norm' in paramdata.keys():
			# myami-3.1 or before
			normtext = self.setArgText('xmipp-normalize',(paramdata['xmipp-norm'],),True)
			normtext = '--normalized '+normtext
		elif 'normalizemethod' in paramdata.keys():
			# myami-3.2 or newer
			normtext = '--normalize-method=%s' % (paramdata['normalizemethod'],)
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
			defoctext = '--defocpair'
		else:
			defoctext = ''
		cmd = '''
makestack2.py --single=%s --fromstackid=%d %s %s %s %s %s --no-invert %s --boxsize=%d --bin=%d --description="frealign refinestack based on %s(id=%d)" --projectid=%d --preset=%s --runname=%s --rundir=%s --no-wait --no-commit --no-continue --session=%s --expId=%d --jobtype=makestack2
		''' % (os.path.basename(newstackimagicfile),stackid,lowpasstext,highpasstext,partlimittext,reversetext,defoctext,normtext,unbinnedboxsize,bin,stackpathname,stackid,projectid,presetname,newstackrunname,newstackrundir,sessionname,sessionid)
		logfilepath = os.path.join(newstackrundir,'frealignstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('Error in Frealign specific stack making')

		self.ImagicStackToFrealignMrcStack(newstackimagicfile)
		os.rename(newstackimagicfile[:-4]+'.mrc',newstackroot+'.mrc')
		self.setFrealignStack(newstackroot)
		# use the same complex equation as in eman clip
		clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
		self.stack['boxsize'] = clipsize / self.params['bin']
		self.stack['apix'] = self.stack['apix'] * self.params['bin']
		#clean up
		rmfiles = glob.glob("*.box")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

	def setFrealignStack(self,stackroot):
		self.stack['file'] = stackroot+'.mrc'
		self.stack['format'] = 'frealign'
		self.stack['bin'] = self.params['bin']
		self.stack['phaseflipped'] = False # the Frealign prepped stacks are NOT phase flipped

	def addStackToSend(self,mrcfilepath):
		# mrc Format
		self.addToFilesToSend(mrcfilepath)

	def addModelToSend(self,mrcfilepath):
		self.addStackToSend(mrcfilepath)

	def otherPreparations(self):
		if 'reconiterid' not in self.params.keys() or self.params['reconiterid'] == 0:
			self.params['reconiterid'] = None
		paramfile = 'params.000.par'
		apFrealign.generateParticleParams(self.params,self.model['data'],paramfile)
		self.addToFilesToSend(paramfile)

#=====================
if __name__ == "__main__":
	app = FrealignPrep3DRefinement()
	app.start()
	app.close()

