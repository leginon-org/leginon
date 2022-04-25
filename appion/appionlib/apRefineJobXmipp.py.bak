#!/usr/bin/env python
import os
import sys
import math
import time
import cPickle
#appion
from appionlib import apDisplay
from appionlib import apRefineJob
from appionlib import apSymmetry
from appionlib import apXmipp
from appionlib import apParam

#================
#================
class XmippSingleModelRefineJob(apRefineJob.RefineJob):
	#=====================
	def setupParserOptions(self):
		super(XmippSingleModelRefineJob,self).setupParserOptions()
		self.parser.add_option("--MaskVol", dest="maskvol", type="str",
			help="Arbitrary mask volume file (0 outside protein, 1 inside). Arbitrary and spherical masks "
			+"are mutually exclusive",default="")
		self.parser.add_option("--innerAlignRadius", dest="innerAlignRadius", type="int",
			help="Inner radius for alignment",default=0)
		self.parser.add_option("--outerAlignRadius", dest="outerAlignRadius", type="int",
			help="Outer radius for alignment",default=0)
		self.parser.add_option("--fourierMaxFrequencyOfInterest",
			dest="fouriermaxfrequencyofinterest", type="float",
			help="Maximum frequency of interest for Fourier", default=0.25)
		self.parser.add_option("--DoComputeResolution", dest="docomputeresolution", action="store_true",
			help="Compute resolution or not", default=True)
		self.parser.add_option("--DoLowPassFilter", dest="dolowpassfilter", action="store_true",
			help="This lowpass filter will be applied for the generation of the next reference", default=True)
		self.parser.add_option("--DontUseFscForFilter", dest="usefscforfilter", action="store_false",
			help="Use the FSC=0.5+Constant frequency for the filtration", default=True)
		self.parser.add_option("--filterResolution", dest="filterResolution", type="float", 
			help="just model to specified resolution (in Angstroms) after each iteration")
		self.parser.add_option("--reconMethod",dest="reconMethod", default="fourier",
			help="fourier, art, wbp")

	#================
	def setIterationParamList(self):
		super(XmippSingleModelRefineJob,self).setIterationParamList()
		self.iterparams.extend([
#				{'name':"AngularSteps",
#					'help':"Angular steps (e.g. 4x10:2x5:2x3:2x2)",'default':"6x5:2x3:2x2"},
				{'name':"maxAngularChange",
					'help':"Maximum angular change (e.g. 4x1000:2x20:2x9:2x6)", 'default':'4x1000:2x20:2x9:2x6'},
				{'name':"maxChangeOffset",
					'help':"Maximum shift in x and y", 'default':'1000'},
				{'name':"search5DShift",
					'help':"Search range for shift 5D searches (e.g. 3x5:2x3:0)", 'default':'4x5:0'},
				{'name':"search5DStep",
					'help':"Shift step for 5D searches", 'default':"2"},
				{'name':"percentDiscard",
					'help':"Percentage of images discarded with a CCF below X", 'default':"10"},
				{'name':"ARTLambda",
					'help':"Relaxation factor for ART", 'default':"0.2"},
				{'name':"filterConstant",
					'help':"Use the FSC=0.5+Constant frequency for the filtration, in Angstroms", 'default':"0.1"},
				])

	def checkIterationConflicts(self):
		super(XmippSingleModelRefineJob,self).checkIterationConflicts()
		pad = int(self.params['boxsize']*1.25/2.0)*2
		self.params['pad'] = map((lambda x: pad),range(self.params['numiter']))
		if self.params['usefscforfilter'] is True and self.params['filterResolution'] is not None:
			apDisplay.printWarning("cannot use FSC for filter AND specify a resolution to filter model, either set \
				--DontUseFscForFilter to True or remove --filterResolution ... setting --DontUseFscForFilter to True")
			self.params['usefscforfilter'] = False

		# outerAlignRaidus which is not iteration parameter in protocol but has to be smaller than mask radius if present
		min_outerMaskRadius = min(self.params['outerMaskRadius'])
		if self.params['outerAlignRadius'] == 0:
			apDisplay.printWarning("mask was not defined, setting to outer mask radius: %d"%(min_outerMaskRadius))
			self.params['outerAlignRadius'] = min_outerMaskRadius
		elif self.params['outerAlignRadius'] > min_outerMaskRadius:
			apDisplay.printWarning("mask too big, setting to outer mask radius: %d"%(min_outerMaskRadius))
			self.params['outerAlignRadius'] = min_outerMaskRadius
	
	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
		'''
		return apXmipp.convertSymmetryNameForPackage(inputname)
		'''
		xmipp_hedral_symm_names = {'oct':'O','icos':'I'}
		inputname = inputname.lower().split(' ')[0]
		if inputname[0] in ('c','d') or inputname in xmipp_hedral_symm_names.values():
			symm_name = inputname.lower()
		elif inputname in xmipp_hedral_symm_names.keys():
			symm_name = xmipp_hedral_symm_names[inputname]
		else:
			apDisplay.printWarning("unknown symmetry name conversion. Use it directly")
			symm_name = inputname.upper()
		return symm_name
		'''

	def calcRefineMem(self):
		numgig = 2
		return numgig

	def convertToXmippStyleIterParams(self):
		for iterparamdict in self.iterparams:
			name = iterparamdict['name']
			if self.params.keys():
				strings = map((lambda x: str(x)),self.params[name])
				self.params[name] = ' '.join(strings)

	def setupXmippProtocol(self):
		protocolname = 'xmipp_protocol_projmatch'
		# Locate protocol_projmatch
		protocol_projmatch=apXmipp.locateXmippProtocol(protocolname)

		#make threads and mpi processes compatible with the xmipprequirement
		self.params['alwaysone']=1
		
		protocolPrm={}
		protocolPrm["SelFileName"]                  =   "partlist.sel"
		protocolPrm["DocFileName"]                  =   ""
		protocolPrm["ReferenceFileName"]            =   self.params['modelnames'][0]
		protocolPrm["WorkingDir"]                   =   "ProjMatch"
		protocolPrm["DoDeleteWorkingDir"]           =   True
		protocolPrm["NumberofIterations"]           =   self.params['enditer']
		protocolPrm["ContinueAtIteration"]          =   self.params['startiter']
		protocolPrm["CleanUpFiles"]                 =   False
		protocolPrm["ProjectDir"]                   =   self.params['recondir']
		protocolPrm["LogDir"]                       =   "Logs"
		protocolPrm["DoCtfCorrection"]              =   False
		protocolPrm["CTFDatName"]                   =   ""
		protocolPrm["DoAutoCtfGroup"]               =   False
		protocolPrm["CtfGroupMaxDiff"]              =   0.5
		protocolPrm["CtfGroupMaxResol"]             =   15
		protocolPrm["SplitDefocusDocFile"]          =   ""
		protocolPrm["PaddingFactor"]                =   2
		protocolPrm["WienerConstant"]               =   -1
		protocolPrm["DataArePhaseFlipped"]          =   True
		protocolPrm["ReferenceIsCtfCorrected"]      =   True
		protocolPrm["DoMask"]                       =   self.params['maskvol']>0
		protocolPrm["DoSphericalMask"]              =   self.params['outerMaskRadius']>0
		# split is needed because refineJob base class defines outMaskRadius as iteration parameter but xmipp can
		# no accept such assignment	
		protocolPrm["MaskRadius"]                   =   self.convertAngstromToPixel( self.params['outerMaskRadius'].split()[0] )
		protocolPrm["MaskFileName"]                 =   self.params['maskvol']
		protocolPrm["DoProjectionMatching"]         =   True
		protocolPrm["DisplayProjectionMatching"]    =   False
		protocolPrm["InnerRadius"]                  =  self.convertAngstromToPixel( self.params['innerAlignRadius'] )
		protocolPrm["OuterRadius"]                  =  self.convertAngstromToPixel( self.params['outerAlignRadius'] )
		protocolPrm["AvailableMemory"]              =   self.calcRefineMem()
#		protocolPrm["AngSamplingRateDeg"]           =   self.params['AngularSteps']
		protocolPrm["AngSamplingRateDeg"]           =   self.params['angSampRate']
		protocolPrm["MaxChangeInAngles"]            =   self.params['maxAngularChange']
		protocolPrm["PerturbProjectionDirections"]  =   False
		protocolPrm["MaxChangeOffset"]              =   self.params['maxChangeOffset']
		protocolPrm["Search5DShift"]                =   self.params['search5DShift']
		protocolPrm["Search5DStep"]                 =   self.params['search5DStep']
		protocolPrm["DoRetricSearchbyTiltAngle"]    =   False
		protocolPrm["Tilt0"]                        =   0
		protocolPrm["TiltF"]                        =   0
		protocolPrm["SymmetryGroup"]                =   self.params['symmetry']
		protocolPrm["SymmetryGroupNeighbourhood"]   =   ''
		protocolPrm["OnlyWinner"]                   =   False
		protocolPrm["MinimumCrossCorrelation"]      =   '-1'
		protocolPrm["DiscardPercentage"]            =   self.params['percentDiscard']
		protocolPrm["ProjMatchingExtra"]            =   ''
		protocolPrm["DoAlign2D"]                    =   '0'
		protocolPrm["Align2DIterNr"]                =   4
		protocolPrm["Align2dMaxChangeOffset"]       =   '1000'
		protocolPrm["Align2dMaxChangeRot"]          =   '1000'
		if not self.params['refineonly']:
			protocolPrm["DoReconstruction"]             =   True
		else:
			protocolPrm["DoReconstruction"]             =   False
		protocolPrm["DisplayReconstruction"]        =   False
		protocolPrm["ARTLambda"]                    =   self.params['ARTLambda']
		protocolPrm["ARTReconstructionExtraCommand"]=   ''
		protocolPrm["FourierMaxFrequencyOfInterest"]=   self.params['fouriermaxfrequencyofinterest']
		protocolPrm["WBPReconstructionExtraCommand"]=''
		protocolPrm["FourierReconstructionExtraCommand"]=''
		if not self.params['refineonly']:
			protocolPrm["ReconstructionMethod"]         =   self.params['reconMethod']
			protocolPrm["DoComputeResolution"]          =   self.params['docomputeresolution']
			protocolPrm["DoSplitReferenceImages"]       =   True
			protocolPrm["DoLowPassFilter"]              =   self.params['dolowpassfilter']
			protocolPrm["UseFscForFilter"]              =   self.params['usefscforfilter']
		else:
			#Xmipp does not allow False SplitReferenceImage except the exact syntex of 'fourier' in ReconstructionMethod
			protocolPrm["ReconstructionMethod"]         =   'fourier'
			#These should never be used if reconstruction is not done
			protocolPrm["DoComputeResolution"]          =   False
			protocolPrm["DoSplitReferenceImages"]       =   False
			protocolPrm["DoLowPassFilter"]              =   False 
			protocolPrm["UseFscForFilter"]              =   False
		protocolPrm["ResolSam"]                     =   self.params['apix']
		protocolPrm["DisplayResolution"]            =   False
		if self.params['usefscforfilter'] is False and self.params['filterResolution']:
			protocolPrm["ConstantToAddToFiltration"] = str(self.params['apix'] / self.params['filterResolution'])
		else:
			protocolPrm["ConstantToAddToFiltration"]    =   str(self.params['filterConstant'])
		print protocolPrm["ConstantToAddToFiltration"]
		protocolPrm["NumberOfThreads"]              =   self.params['alwaysone']
		protocolPrm["DoParallel"]                   =   self.params['nproc']>1
		protocolPrm["NumberOfMpiProcesses"]         =   self.params['nproc']
		protocolPrm["MpiJobSize"]                   =   '10'
		protocolPrm["SystemFlavour"]                =   ''
		protocolPrm["AnalysisScript"]               =   'visualize_projmatch.py'

		### write out python protocol into run directory
		protocolfile = os.path.join(self.params['remoterundir'],"%s.py" % protocolname)
		if self.params['refineonly']:
			tempprotocolfile = os.path.join(self.params['remoterundir'],"%s.temp" % protocolname)
			apXmipp.fixRefineOnlyProtocol(protocol_projmatch,tempprotocolfile)
			apXmipp.particularizeProtocol(tempprotocolfile, protocolPrm, protocolfile)
			os.remove(tempprotocolfile)
		else:
			apXmipp.particularizeProtocol(protocol_projmatch, protocolPrm, protocolfile)
		os.chmod(os.path.join(self.params['rundir'], protocolfile), 0775)
				
		### Write the parameters for posterior uploading, both generic and specific
		self.runparams = {} ### these are generic params that includes a dictionary entry for package-specific params
#		self.runparams['symmetry'] = apSymmetry.getSymmetryDataFromName(self.params['symmetry'])

		#sym = apSymmetry.getSymmetryDataFromID(self.params['symmetry'])
		#sym2 = self.convertSymmetryNameForPackage(sym)
		
		sym = protocolPrm["SymmetryGroup"][0]
		if sym in ('i','I'):
			self.runparams['symmetry'] = "Icos (2 3 5) Viper/3DEM"
		else:
			self.runparams['symmetry'] = protocolPrm["SymmetryGroup"]
		self.runparams['numiter'] = protocolPrm['NumberofIterations']
		self.runparams['mask'] = protocolPrm["MaskRadius"] 
		self.runparams['imask'] = None
		self.runparams['alignmentInnerRadius'] = protocolPrm["InnerRadius"] 
		self.runparams['alignmentOuterRadius'] = protocolPrm["OuterRadius"]
		self.runparams['reconstruction_package'] = "Xmipp"
		self.runparams['remoterundir'] = self.params['remoterundir']
		self.runparams['reconstruction_working_dir'] = protocolPrm["WorkingDir"] 
		self.runparams['package_params'] = protocolPrm
		self.picklefile = os.path.join(self.params['remoterundir'], "xmipp_projection_matching_"+self.timestamp+"-params.pickle")
		apParam.dumpParameters(self.runparams, self.picklefile)
		
		### finished setup of input files, now run xmipp_protocols_ml3d.py from jobfile
		apDisplay.printMsg("finished setting up input files, now ready to run protocol")

		return protocolfile, protocolPrm

	def makeNewTrialScript(self):
		'''
		This starts and ends at recondir
		'''
		print self.params['modelnames'][0]
		self.addSimpleCommand('ln -s %s %s' % ( 
			os.path.join(self.params['remoterundir'], self.params['modelnames'][0]),self.params['modelnames'][0]))
		partar = os.path.join(self.params['remoterundir'],'partfiles.tar.gz')
		partpath = os.path.join(self.params['remoterundir'],'partfiles')
		if not os.path.isdir(partpath):
			# partfiles need to be untared in its directory
			self.addSimpleCommand('mkdir %s' % partpath)
			self.addSimpleCommand('cd %s' % partpath)
			self.addSimpleCommand('tar xvf %s' % partar)
			# return to recondir
			self.addSimpleCommand('cd %s' % self.params['recondir'])

	def makePreIterationScript(self):
		self.convertToXmippStyleIterParams()
		tasks = {}
		self.addToLog('....Setting up Xmipp Protocol....')
		protocolfile, protocolPrm = self.setupXmippProtocol()

		### check for variable root directories between file systems
		apXmipp.checkSelOrDocFileRootDirectoryInDirectoryTree(self.params['remoterundir'], self.params['rundir'], self.params['remoterundir'])
		
		self.addToLog('....Start running Xmipp Protocol....')
		tasks = self.addToTasks(tasks,'python %s' % protocolfile,self.calcRefineMem(),self.params['nproc'])
		protocol_pyname = os.path.basename(protocolfile)
		protocolname = protocol_pyname.split('.')[0]
		tasklogfilename = protocolname+'_'+protocolPrm['WorkingDir']+'.log'
		tasklogfile = os.path.join(self.params['recondir'],protocolPrm['LogDir'],tasklogfilename)
		tasks = self.logTaskStatus(tasks,'protocol_run',tasklogfile)
		tasks = self.addToTasks(tasks,'cp %s %s' % (protocolfile,self.params['recondir']))
		self.addJobCommands(tasks)

if __name__ == '__main__':
	app = XmippSingleModelRefineJob()
	app.start()
	app.close()
