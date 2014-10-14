#!/usr/bin/env python

import os
import sys
import glob
import math
import time

#appion
from appionlib import apFile
from appionlib import apXmipp
from appionlib import apParam
from appionlib import apStack
from appionlib import starFile
from appionlib import apIMAGIC
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apFrealign
from appionlib import apDatabase
from appionlib import apScriptLog
from appionlib import apImagicFile
from appionlib import apPrepRefine
from appionlib.apCtf import ctfdb
from leginon import leginondata

''' There are 4 things we want to ensure for stacks used with Relion:
1. The particles must be white on a black background (this is not actually true according to Sjors)
2. The stack must be normalized (xmipp normalize is good for this)
3. The stack must NOT be ctf-corrected (aka ctf-phaseFlipped)
4. Relion prefers mrc stacks over Imagic and should be named .mrcs

The most efficient way to achieve this is:
1. If it needs to be inverted only (to make it whiteOnBlack), run proc2d.
2. If it needs to be normalized only, just run xmipp normalize.
3. If it needs to be inverted and normalized, run proc2d followed by xmipp normalize.
4. If it needs to be un-ctf-corrected run makestack2.py and do inversion and normalization at that time if needed.
5. After makestack, run ImagicStackToFrealignMrcStack(), rename to .mrcs in func, remove the .hed and .img that makestack made
6. Make sure star file has mrcs.
'''

#=====================
# TODO: Do these functions belong somewhere else or can they be made const?
def maxIfNotNone(numlist):
	sortset = list(set(numlist))
	return sortset[-1]

#=====================
def minIfNotNone(numlist):
	sortset = list(set(numlist))
	if len(sortset) > 1 and sortset[0] is None:
		return sortset[1]
	else:
		return sortset[0]

#=====================	
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

#=====================
#=====================
#=====================
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
	
		self.noClassification = 0
		self.mismatch = 0
		if self.params['reconiterid'] is not None:
			refIterData = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
			print refIterData.keys()
			self.symmetryName = refIterData['symmetry']['symmetry']
	
	#=====================							
	def setRefineMethod(self):
		self.refinemethod = 'relionrecon'

	#=====================
	def setupParserOptions(self):
		super(PrepRefineRelion,self).setupParserOptions()
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option('--paramonly', dest='paramonly', default=False, action='store_true',
			help="only create parameter file")
		self.parser.add_option("--xmipp-normalize", dest="xmipp-norm", default=4.5, type="float",
			help="Value used to normalize the entire stack using xmipp")
		self.ctfestopts = ('ace2', 'ctffind')
		self.parser.add_option('--ctfmethod', dest='ctfmethod',
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)
				
	#=====================	
	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("Relion projection match can only take one model")

	#=====================
	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	#=====================
	def preprocessModelWithProc3d(self):
		rescale = not self.params['paramonly']
		super(PrepRefineRelion,self).preprocessModelWithProc3d(rescale)
			
	#=====================		
	def runRelionPreprocess(self, newstackroot):
		'''
		1. Use stackIntoPicks.py to extract the particle locations from the selected stack.
		2. Run makestack2.py without ctf correction or normalization using the stackIntoPicks result as the Particles run.
		3. Run relion_preprocess with rescale and norm. Outputs .mrcs file.
		
		Neil: most of these steps could be done more generally
		'''
		apDisplay.printWarning("Making a new stack from original images")
		
		# Build the stackIntoPicks command
		apDisplay.printMsg('Extracting the particle locations from your selected stack.')
		newstackrunname   = self.params['runname']+"_particles"
		newstackrundir    = self.params['rundir']
		projectid         = self.params['projectid']
		stackid           = self.originalStackData.stackid
		sessionid         = int(self.params['expid'])

		cmd = "stackIntoPicks.py "
		cmd += (" --stackid=%d --projectid=%d --runname=%s --rundir=%s "%
			(stackid,projectid,newstackrunname,newstackrundir))
		cmd += (" --commit --expId=%d --jobtype=stackintopicks "%
			(sessionid))
	
		# Run the command
		logfilepath = os.path.join(newstackrundir,'relionstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('Error in Relion specific stack making')

		# Build the makestack2 command
		'''
		This is the command we want to make a stack from a stackIntoPicks run
		makestack2.py 
			--single=start.hed --selectionid=130 --invert --boxsize=320 --bin=2 
			--description="made from stackrun1 using stackintopicks" 
			--runname=stack66 --rundir=/ami/data00/appion/zz07jul25b/stacks/stack66 
			--commit --preset=en --projectid=303 --session=zz07jul25b 
			--no-rejects --no-wait --continue --expid=8556 --jobtype=makestack2 
			--ppn=1 --nodes=1 --walltime=240 --jobid=2016
		'''
		apDisplay.printMsg('Using selected stack particle locations to make a Relion ready stack....')

		# Get the ID of the stackIntoPicks run we just created
		#apParticle.getSelectionIdFromName(runname, sessionname)
	
		runq = appiondata.ApSelectionRunData()
		runq['name'] = newstackrunname
		runq['session'] = leginondata.SessionData.direct_query(self.params['expid'])
		rundatas = runq.query(results=1)
		print rundatas

		if rundatas:
			selectionid = rundatas[0].dbid
		else:
			apDisplay.printError("Error creating Relion ready stack. Could not find stackIntoPicks.py data in database.\n")
	
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
		cmd = "makestack2.py "
		cmd += (" --single=%s --selectionid=%d %s --boxsize=%d --bin=%d "%
			(os.path.basename(newstackimagicfile),selectionid,inverttext,
			unbinnedboxsize,bin))
		cmd += (" --description='Relion refinestack based on %s(id=%d)' --projectid=%d "%
			(stackpathname,stackid,projectid))
		cmd += (" --preset=%s --runname=%s --rundir=%s --session=%s --expId=%d "%
			(presetname,newstackrunname,newstackrundir,sessionname,sessionid))
		cmd += " --no-wait --no-commit --no-continue  --jobtype=makestack2 "
	
		# Run the command
		logfilepath = os.path.join(newstackrundir,'relionstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('Error in Relion specific stack making')

		# Clean up
		boxfiles = glob.glob("*.box")
		for boxfile in boxfiles:
			apFile.removeFile(boxfile)

		# Make sure our new stack params reflects the changes made
		# Use the same complex equation as in eman clip
		clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
		self.stack['boxsize']         = clipsize / self.params['bin']
		self.stack['apix']            = self.stack['apix'] * self.params['bin']
		self.stack['file']            = newstackroot+'.hed'		
		
		# Run Relion pre-process command
		'''
		Setup the follow relion preprocess command to normalize the new stack:
		relion_preprocess \
			 --o particles --norm --bg_radius 60 --white_dust -1 --black_dust -1 \
			 --operate_on /ami/data00/appion/zz07jul25b/stacks/stack63_no_xmipp_norm/start.hed
		'''
		apDisplay.printMsg('Running Relion preprocessing to normalize your Relion Ready stack....')
		bg_radius = math.floor((self.stack['boxsize'] / 2) - 1)
		
		relioncmd = "relion_preprocess "
		relioncmd += " --o particles --norm --bg_radius %d "%(bg_radius)
		relioncmd += " --white_dust -1 --black_dust -1 --operate_on %s "%(newstackimagicfile)
		apParam.runCmd(relioncmd, package="Relion", verbose=True, showcmd=True)
		self.stack['file'] = 'particles.mrcs'		

	#=====================
	def convertToRefineStack(self):
		'''
		The stack is remaked without ctf correction and inverted and normalized if needed
		'''
		newstackroot = os.path.join(self.params['rundir'],os.path.basename(self.stack['file'])[:-4])
		
		#self.runRelionPreprocess( newstackroot )
		
		self.ImagicStackToMrcStack(self.stack['file'])
		
		self.stack['file'] = 'particles.mrcs'
		return
        #TODO: clean up everything below here once this relion preprocess is proven out
		self.stackErrorCheck( self.stack['file'] )
		
		self.stack['phaseflipped']    = False
		self.stack['format']          = 'relion' #TODO: Where is this used? 
		
		# If we just want the frealign param file, skip this function
		if self.params['paramonly'] is True:
			print 'newstackroot', newstackroot
			return
		
		# If we just need to normalize, run xmipp_normalize
#		if self.normalize and not self.un_ctf_correct:
		if not self.un_ctf_correct:
			apDisplay.printMsg("Normalizing stack for use with Relion")
			extname,addformat = self.proc2dFormatConversion()
			stackfilenamebits = self.stack['file'].split('.')
			basestackname = stackfilenamebits[0]
			outstack = os.path.join(self.params['rundir'], "%s.%s" % (basestackname, extname) )
			#self.xmippNormStack(self.stack['file'], outstack)
			self.stack['file'] = outstack
		
		# If we don't need to un-ctf-correct, we are done
		if self.un_ctf_correct:
			self.undoCTFCorrect( newstackroot )
			
		# Convert the imagic stack to an MRC stack format
		# Relion preferes an mrc stack with .mrcs extension
		imagicStack = self.stack['file'] #os.path.join(self.params['rundir'],'start.hed')
		mrcStack = newstackroot+'.mrc'
		mrcsStack = newstackroot+'.mrcs' #TODO: why no dot here? Was adding double...
		self.ImagicStackToMrcStack( imagicStack )
		
		apDisplay.printMsg("Renaming %s to %s " % (mrcStack, mrcsStack) )
		os.rename(mrcStack, mrcsStack)		
		self.stack['file'] = mrcsStack

	#=====================		
	def undoCTFCorrect(self, newstackroot):
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
		cmd = "makestack2.py "
		cmd += (" --single=%s --fromstackid=%d %s %s %s %s %s %s "%
			(os.path.basename(newstackimagicfile),selectionid,stackid,lowpasstext,
			highpasstext,partlimittext,reversetext,defoctext,inverttext))
		cmd += (" --normalized %s --boxsize=%d --bin=%d "%
			(xmipp_normtext,unbinnedboxsize,bin))
		cmd += (" --description='Relion refinestack based on %s(id=%d)' --projectid=%d "%
			(stackpathname,stackid,projectid))
		cmd += (" --preset=%s --runname=%s --rundir=%s --session=%s --expId=%d "%
			(presetname,newstackrunname,newstackrundir,sessionname,sessionid))					
		cmd += ("  --no-wait --no-commit --no-continue  --jobtype=makestack2 ")	
		
		# Run the command
		logfilepath = os.path.join(newstackrundir,'relionstackrun.log')
		returncode = self.runAppionScriptInSubprocess(cmd,logfilepath)
		if returncode > 0:
			apDisplay.printError('Error in Relion specific stack making')

		# Make sure our new stack params reflects the changes made
		# Use the same complex equation as in eman clip
		clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
		self.stack['boxsize']         = clipsize / self.params['bin']
		self.stack['apix']            = self.stack['apix'] * self.params['bin']
		self.stack['file']            = newstackroot+'.hed'		
		
		# Clean up
		boxfiles = glob.glob("*.box")
		for boxfile in boxfiles:
			apFile.removeFile(boxfile)

	#=====================
	def stackErrorCheck(self,stackfile):
		"""
		# Check that the stackfile min and max densities make sense. 
		# Relion fails if min is greater than max.
		"""
		headerdict = apImagicFile.readImagicHeader(stackfile)
		
		if headerdict['min'] > headerdict['max']:
			min = headerdict['min']
			max = headerdict['max']
			headerdict['min'] = max
			headerdict['max'] = min
			apDisplay.printWarning('Relion will not process this stack because there is an error in the IMAGIC image header.'
				+'The minimum pixel density is a larger value than the maximum pixel density.')

	#=====================
	def ImagicStackToMrcStack(self, oldstackfile):
		'''
		Convert IMAGIC Stack into MRC stack with extension .mrcs
   		''' 	
		self.stackErrorCheck(oldstackfile)
		
		stackroot = oldstackfile[:-4]
		mrcstackfile = os.path.join(self.params['rundir'], 'particles.mrcs')
		apDisplay.printMsg('converting %s from default IMAGIC stack format to MRC as %s'% (stackroot, mrcstackfile))
		apIMAGIC.convertImagicStackToMrcStack(stackroot, mrcstackfile)
		# clean up non-mrc stack in rundir which may be left from preprocessing such as binning
		if not 'mrc' in oldstackfile and os.path.dirname(oldstackfile) == self.params['rundir']:
			#apFile.removeStack(oldstackfile)
			pass

	#=====================
	def createStarFilePlus(self, starfile, mrcStackFile):
		'''
		Create a file with the required constant strings in it
   		''' 
   		star = starFile.StarFile(starfile)
		labels = ['_rlnImageName', '_rlnMicrographName',
			'_rlnDefocusU', '_rlnDefocusV', '_rlnDefocusAngle', '_rlnVoltage',
			'_rlnSphericalAberration', '_rlnAmplitudeContrast', 
			'_rlnAngleRot', '_rlnAngleTilt', '_rlnAnglePsi', 
			'_rlnOriginX', '_rlnOriginY',
		]

		valueSets = [] #list of strings for star file
		partParamsList = self.getStackParticleParams()
		stackPath = os.path.join(self.params['rundir'], mrcStackFile)
		for partParams in partParamsList:
			relionDataLine = ("%d@%s %d %.6f %.6f %.6f %d %.6f %.6f %.6f %.6f %.6f %.6f %.6f"
				%( partParams['ptclnum'], stackPath, partParams['filmNum'],
					partParams['defocus2'], partParams['defocus1'], partParams['angle_astigmatism'], 
					partParams['kv'], self.params['cs'], partParams['amplitude_contrast'],
					partParams['psi'], partParams['theta'], partParams['phi'],
					partParams['shiftx'], partParams['shifty'], 					
									
				))
			valueSets.append(relionDataLine)
		star = starFile.StarFile(starfile)
		star.buildLoopFile( "data_", labels, valueSets )
		star.write()

	#=====================
	def createStarFile(self, starfile, mrcStackFile):
		'''
		Create a file with the required constant strings in it
   		''' 
   		star = starFile.StarFile(starfile)
		labels = ['_rlnImageName', '_rlnMicrographName',
			'_rlnDefocusU', '_rlnDefocusV', '_rlnDefocusAngle', '_rlnVoltage',
			'_rlnSphericalAberration', '_rlnAmplitudeContrast', ]

		valueSets = [] #list of strings for star file
		partParamsList = self.getStackParticleParams()
		stackPath = os.path.join(self.params['rundir'], mrcStackFile)
		for partParams in partParamsList:
			relionDataLine = ("%d@%s %d %.6f %.6f %.6f %d %.6f %.6f"
				%( partParams['ptclnum'], stackPath, partParams['filmNum'],
					partParams['defocus2'], partParams['defocus1'], partParams['angle_astigmatism'], 
					partParams['kv'], self.params['cs'], partParams['amplitude_contrast'],
				))
			valueSets.append(relionDataLine)
		star = starFile.StarFile(starfile)
		star.buildLoopFile( "data_", labels, valueSets )
		star.write()

	#=====================
	def getStackParticleParams(self):
		"""
		for each particle in the stack, get the information that RELION needs
		"""
		stackPartList = apStack.getStackParticlesFromId(self.params['stackid'])
		
		if 'last' not in self.params:
			self.params['last'] = len(stackPartList)

		firstImageId = stackPartList[0]['particle']['image'].dbid
		count = 0
		lastImageId = -1
		lastCtfData = None
		lastKv = -1
		partParamsList = []
		sys.stderr.write("reading stack particle data\n")
		t0 = time.time()
		for stackPart in stackPartList:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")
			if count % 10000 == 0:
				sys.stderr.write("\nparticle %d of %d\n"%(count, self.params['last']))
			
			# extra particle number information not read by Relion
			if count != stackPart['particleNumber']:
				apDisplay.printWarning("particle number in database is not in sync")
							
			if count > self.params['last']:
				break
				
			partParams = {}
			partParams['ptclnum'] = count
			partParams['filmNum'] = self.getFilmNumber(stackPart, firstImageId)
			#print partParams['filmNum']
			### get image data
			imagedata = stackPart['particle']['image']
			if self.originalStackData.defocpair is True:
				imagedata = apDefocalPairs.getDefocusPair(imagedata)

			if lastImageId == imagedata.dbid:
				ctfdata = lastCtfData
				partParams['kv'] = lastKv
			else:
				ctfdata = ctfdb.getBestCtfValue(imagedata, msg=False, method=self.params['ctfmethod'])
				partParams['kv'] = imagedata['scope']['high tension']/1000.0
			lastCtfData = ctfdata
			lastImageId = imagedata.dbid
			lastKv = partParams['kv']

			### get CTF data from image			
			if ctfdata is not None:
				# use defocus & astigmatism values
				partParams['defocus1'] = abs(ctfdata['defocus1']*1e10)
				partParams['defocus2'] = abs(ctfdata['defocus2']*1e10)
				partParams['angle_astigmatism'] = ctfdata['angle_astigmatism']
				partParams['amplitude_contrast'] = ctfdata['amplitude_contrast']
			else:
				apDisplay.printWarning("No ctf information for particle %d in image %d"%(count, imagedata.dbid))
				partParams['defocus1'] = 0.1
				partParams['defocus2'] = 0.1
				partParams['angle_astigmatism'] = 0.0
				partParams['amplitude_contrast'] = 0.07

			if self.params['reconiterid'] is not None:
				eulerDict = self.getStackParticleEulersForIteration(stackPart)
				partParams.update(eulerDict)

			partParamsList.append(partParams)
		print "no class %d ; mismatch %d"%(self.noClassification, self.mismatch)
		sys.stderr.write("\ndone in %s\n\n"%(apDisplay.timeString(time.time()-t0)))	
		return partParamsList			


	#===============
	def getStackParticleEulersForIteration(self, stackPart):
		"""
		find the eulers assigned to a stack particle
		during a refinement.  This function will first
		find the particle id for the given stack particle,
		then find its position in the reference stack, and
		will get the eulers for that particle in the recon
		
		assumes recon with FREALIGN
		"""

		# get stack particle id
		stackPartId = stackPart.dbid
		partId = stackPart['particle'].dbid

		# find particle in reference stack
		refStackId = apStack.getStackIdFromIterationId(self.params['reconiterid'], msg=False)
		refStackPart = apStack.getStackParticleFromParticleId(partId, refStackId)

		if not refStackPart:
			apDisplay.printWarning('No classification for stack particle %d in reconstruction iteration id: %d' % (refStackId, self.params['reconiterid']))
			self.noClassification += 1
			if self.noClassification > (float(params['last'])*0.10):
				apDisplay.printError('More than 10% of the particles have no classification, use a different reference reconstruction')
			eulerDict = {
				'psi': 0.0,
				'theta': 0.0, 
				'phi': 0.0, 
				'shiftx': 0.0,
				'shifty': 0.0,
				}
			return eulerDict

		refIterData = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
		if refStackPart.dbid != stackPartId:
			self.mismatch += 1
		refinePartQuery = appiondata.ApRefineParticleData()
		refinePartQuery['particle'] = refStackPart
		refinePartQuery['refineIter'] = refIterData
		refinePartDatas = refinePartQuery.query()
		refinePartData = refinePartDatas[0]
		emanEulerDict = {
			'alt': refinePartData['euler1'],
			'az': refinePartData['euler2'], 
			'phi': refinePartData['euler3'], 
			'shiftx': refinePartData['shiftx'],
			'shifty': refinePartData['shifty'],
			'mirror': refinePartData['mirror'],
		}
	
		eulerDict = apFrealign.convertAppionEmanEulersToFrealign(emanEulerDict, self.symmetryName)
		eulerDict['shiftx'] = emanEulerDict['shiftx']*self.params['bin']
		eulerDict['shifty'] = emanEulerDict['shifty']*self.params['bin']
		if refinePartData['mirror'] is True:
			eulerDict['shiftx'] *= -1
		return eulerDict

	#=====================
	def getFilmNumber(self, stackPart, firstImageId):
		"""
		group particles by image or helix
		"""
		imageId = stackPart['particle']['image'].dbid
		# for helical reconstructions, film is helix number
		if stackPart['particle']['helixnum']:
			helix = stackPart['particle']['helixnum']
			try:
				if self.params['lastimgid'] != imageId or self.params['lasthelix'] != helix:
					self.params['totalHelix'] += 1
			except KeyError:
				self.params['totalHelix'] = 1
			self.params['lastimgid'] = imageId
			self.params['lasthelix'] = helix
			filmNum = self.params['totalHelix']
		else:
			filmNum = imageId - firstImageId + 1
		return filmNum

	#=====================
	def preProcessPreparations(self):
		"""
		RELION needs an additional STAR file with CTF parameters
		"""	
		starfile = "all_images.star"
		stackfile = os.path.join(self.params['rundir'], 'particles.mrcs')
		if self.params['reconiterid'] is not None:
			self.createStarFilePlus(starfile, stackfile)
		else:
			self.createStarFile(starfile, stackfile)
		self.addToFilesToSend(starfile)
		

#=====================
if __name__ == "__main__":
	app = PrepRefineRelion()
	app.start()
	app.close()

