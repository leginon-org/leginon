#!/usr/bin/env python
import os
import sys
import glob

#appion
from appionlib import apPrepRefine
from appionlib import apFrealign
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apScriptLog
from appionlib import apIMAGIC
from appionlib import apXmipp

''' There are 3 things we want to ensure for stacks used with Relion:
1. The particles must be white on a black background (this is not actually true)
2. The stack must be normalized (xmipp normalize is good for this)
3. The stack must NOT be ctf-corrected (aka ctf-phaseFlipped)

The most efficient way to achieve this is:
1. If it needs to be inverted only (to make it whiteOnBlack), run proc2d.
2. If it needs to be normalized only, just run xmipp normalize.
3. If it needs to be inverted and normalized, run proc2d followed by xmipp normalize.
4. If it needs to be un-ctf-corrected run makestack2.py and do inversion and normalization at that time if needed.
'''

# TODO: Do these functions belong somewhere else or can they be made const?
def maxIfNotNone(numlist):
	sortset = list(set(numlist))
	return sortset[-1]

def minIfNotNone(numlist):
	sortset = list(set(numlist))
	if len(sortset) > 1 and sortset[0] is None:
		return sortset[1]
	else:
		return sortset[0]
	
def setArgText( key, numlist, getmax=False ):
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

class PrepRefineRelion(apPrepRefine.Prep3DRefinement):
	def onInit(self):
		#TODO: should be able to do something like setStackReqirement("normalized")
		super(PrepRefineRelion,self).onInit()
		
		# initialize values 
		self.invert           = False
		self.un_ctf_correct   = False
		self.normalize        = False
		
		# Determine what needs to be done to the stack
		# Check for inversion, normalization and phaseFlipped
		if not self.originalStackData.inverted:
			self.invert = True		
		if self.originalStackData.phaseFlipped:
			self.un_ctf_correct = True		
		if not self.originalStackData.normalized:
			self.normalize = True	
								
	def setRefineMethod(self):
		self.refinemethod = 'relionrecon'

	def setupParserOptions(self):
		super(PrepRefineRelion,self).setupParserOptions()
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option('--paramonly', dest='paramonly', default=False, action='store_true',
			help="only create parameter file")
		self.parser.add_option("--xmipp-normalize", dest="xmipp-norm", default=4.5, type="float",
			help="Value used to normalize the entire stack using xmipp")
		
	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("Relion projection match can only take one model")

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	def preprocessModelWithProc3d(self):
		rescale = not self.params['paramonly']
		super(PrepRefineRelion,self).preprocessModelWithProc3d(rescale)

	def preprocessStack(self):
		# if the user has selected to only create a param file, return at this point
		if self.params['paramonly'] is True:
			return self.stack['file']
		
		# non-ctf-corrected stack can use proc2d to prepare
		# otherwise, changes are made in convertToRefineStack()
		if not self.un_ctf_correct:
			# Call the base class to run proc2d and copy the stack to the rundir
			newstackfile = super(PrepRefineRelion,self).preprocessStack()
			return newstackfile
		else:
			return self.stack['file']
		
	# TODO: THis function belongs somewhere else
	def xmippNormStack(self, inStackPath, outStackPath):
		### convert stack into single spider files
		selfile = apXmipp.breakupStackIntoSingleFiles(inStackPath)	

		### setup Xmipp command
		xmippexe = apParam.getExecPath("xmipp_normalize", die=True)
		apDisplay.printMsg("Using Xmipp to normalize particle stack")
		normtime = time.time()
		xmippopts = ( " "
			+" -i %s"%os.path.join(self.params['rundir'],selfile)
			+" -method Ramp "
			+" -background circle %i"%(self.stack['boxsize']/self.params['bin']*0.4)
			+" -remove_black_dust"
			+" -remove_white_dust"
			+" -thr_black_dust -%.2f"%(self.params['xmipp-norm'])
			+" -thr_white_dust %.2f"%(self.params['xmipp-norm'])
		)
		xmippcmd = xmippexe+" "+xmippopts
		apParam.runCmd(xmippcmd, package="Xmipp", verbose=True, showcmd=True)
		normtime = time.time() - normtime
		apDisplay.printMsg("Xmipp normalization time: "+apDisplay.timeString(normtime))

		### recombine particles to a single imagic stack
		tmpstack = "tmp.xmippStack.hed"
		apXmipp.gatherSingleFilesIntoStack(selfile,tmpstack)
		apFile.moveStack(tmpstack,outStackPath)

		### clean up directory
		apFile.removeFile(selfile)
		apFile.removeDir("partfiles")
			
	def convertToRefineStack(self):
		'''
		The stack is remaked without ctf correction and inverted and normalized if needed
		'''
		newstackroot = os.path.join(self.params['rundir'],os.path.basename(self.stack['file'])[:-4])
		self.stack['phaseflipped']    = False
		self.stack['format']          = 'relion' #TODO: Where is this used? 
		
		# If we just want the frealign param file, skip this function
		if self.params['paramonly'] is True:
			print 'newstackroot',newstackroot
			return
		
		# If we just need to normalize, run xmipp_normalize
		if self.normalize and not self.un_ctf_correct:
			extname,addformat = self.proc2dFormatConversion()
			outstack = os.path.join(self.params['rundir'], "start.%s" % extname)
			self.xmippNormStack(self.stack['file'], outstack)
			self.stack['file'] = outstack
		
		# If we don't need to un-ctf-correct, we are done
		if not self.un_ctf_correct:
			return
		
		# At this point, the stack needs to be remade un-ctf-corrected, and possibly normalized and/or inverted		
		apDisplay.printWarning('Relion needs a stack without ctf correction. A new stack is being made....')
		
		# Gather all the makestack parameters
		totalpart             = self.originalStackData.numpart
		numpart               = totalpart if not self.params['last'] else min(self.params['last'],totalpart)
		stackpathname         = os.path.basename( self.originalStackData.path )
		newstackrunname       = self.params['runname']
		newstackrundir        = self.params['rundir']
		newstackimagicfile    = os.path.join(newstackrundir,'start.hed')
		presetname            = self.originalStackData.preset
		
		# binning is combination of the original binning of the stack and the preparation binnning
		bin               = self.originalStackData.bin * self.params['bin']
		unbinnedboxsize   = self.stack['boxsize'] * self.originalStackData.bin
		lowpasstext       = setArgText( 'lowpass', ( self.params['lowpass'], self.originalStackData.lowpass ), False)
		highpasstext      = setArgText( 'highpass', ( self.params['highpass'], self.originalStackData.highpass ), True)
		partlimittext     = setArgText('partlimit',(numpart,),False)
		xmipp_normtext    = setArgText('xmipp-normalize', (self.params['xmipp-norm'],), True)
		sessionid         = int(self.params['expid'])
		sessiondata       = apDatabase.getSessionDataFromSessionId(sessionid)
		sessionname       = sessiondata['name']
		projectid         = self.params['projectid']
		stackid           = self.originalStackData.stackid
		reversetext       = '--reverse' if self.originalStackData.reverse else ''
		defoctext         = '--defocpair' if self.originalStackData.defocpair else ''
		inverttext        = '--no-invert' if not self.invert else ''  

		# Build the makestack2 command
		cmd = '''
makestack2.py --single=%s --fromstackid=%d %s %s %s %s %s %s --normalized %s --boxsize=%d --bin=%d --description="frealign refinestack based on %s(id=%d)" --projectid=%d --preset=%s --runname=%s --rundir=%s --no-wait --no-commit --no-continue --session=%s --expId=%d --jobtype=makestack2
		''' % (os.path.basename(newstackimagicfile),stackid,lowpasstext,highpasstext,partlimittext,reversetext,defoctext,inverttext,xmipp_normtext,unbinnedboxsize,bin,stackpathname,stackid,projectid,presetname,newstackrunname,newstackrundir,sessionname,sessionid)
		
		# Run the command
		logfilepath = os.path.join(newstackrundir,'relionstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('Error in Relion specific stack making')

		# Convert the imagic stack to an MRC stack format
		# Relion preferes an mrc stack with .mrcs extension
		#self.ImagicStackToMrcStack(newstackimagicfile)
		#os.rename(newstackimagicfile[:-4]+'.mrc',newstackroot+'.mrc')

		# Make sure our new stack params reflects the changes made
		# Use the same complex equation as in eman clip
		clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
		self.stack['boxsize']         = clipsize / self.params['bin']
		self.stack['apix']            = self.stack['apix'] * self.params['bin']
		self.stack['file']            = newstackroot+'.hed'		
		
		# Clean up
		rmfiles = glob.glob("*.box")
		for rmfile in rmfiles:
			apFile.removeFile(rmfile)

	def ImagicStackToMrcStack(self,stackfile):
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
				
	def otherPreparations(self):
		if 'reconiterid' not in self.params.keys() or self.params['reconiterid'] == 0:
			self.params['reconiterid'] = None
		self.params['defocpair'] = self.originalStackData.defocpair
		paramfile = 'params.000.par'
		self.params['noctf'] = False
		self.params['ctftilt'] = False
		apFrealign.generateParticleParams(self.params,self.model['data'],paramfile)
		self.addToFilesToSend(paramfile)

#=====================
if __name__ == "__main__":
	app = PrepRefineRelion()
	app.start()
	app.close()

