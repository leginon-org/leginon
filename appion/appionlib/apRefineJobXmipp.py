#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apRefineJob
from appionlib import apXmipp

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
			help="Inner radius for alignment",default=2)
		self.parser.add_option("--outerAlignRadius", dest="outerAlignRadius", type="int",
			help="Outer radius for alignment")
		self.parser.add_option("--fourierMaxFrequencyOfInterest",
			dest="fouriermaxfrequencyofinterest", type="float",
			help="Maximum frequency of interest for Fourier", default=0.25)
		self.parser.add_option("--DoComputeResolution", dest="docomputeresolution", action="store_true",
			help="Compute resolution or not", default=True)
		self.parser.add_option("--DoLowPassFilter", dest="dolowpassfilter", action="store_true",
			help="This lowpass filter will be applied for the generation of the next reference", default=True)
		self.parser.add_option("--DontUseFscForFilter", dest="usefscforfilter", action="store_false",
			help="Use the FSC=0.5+Constant frequency for the filtration", default=True)

	#================
	def setIterationParamList(self):
		super(XmippSingleModelRefineJob,self).setIterationParamList()
		self.iterparams.extend([
				{'name':"AngularSteps",
					'help':"Angular steps (e.g. 4x10:2x5:2x3:2x2)",'default':"6x5:2x3:2x2"},
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
				{'name':"reconMethod",
					'help':"fourier, art, wbp", 'default':"fourier"},
				{'name':"ARTLambda",
					'help':"Relaxation factor for ART", 'default':"0.2"},
				{'name':"filterConstant",
					'help':"Use the FSC=0.5+Constant frequency for the filtration", 'default':"0.1"},
				])

	def checkIterationConflicts(self):
		super(XmippSingleModelRefineJob,self).checkIterationConflicts()
		pad = int(self.params['boxsize']*1.25/2.0)*2
		self.params['pad'] = map((lambda x: pad),range(self.params['numiter']))

	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
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

	def calcRefineMem(self,ppn,boxsize,sym,ang):
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
		protocolPrm["ReferenceFileName"]            =   "./reference_volume.spi"
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
		protocolPrm["MaskRadius"]                   =   self.params['outerMaskRadius'].split()[0]
		protocolPrm["MaskFileName"]                 =   self.params['maskvol']
		protocolPrm["DoProjectionMatching"]         =   True
		protocolPrm["DisplayProjectionMatching"]    =   False
		protocolPrm["InnerRadius"]                  =   self.params['innerAlignRadius']
		protocolPrm["OuterRadius"]                  =   self.params['outerAlignRadius']
		protocolPrm["AvailableMemory"]              =   '2'
		protocolPrm["AngSamplingRateDeg"]           =   self.params['AngularSteps']
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
		protocolPrm["DoReconstruction"]             =   True
		protocolPrm["DisplayReconstruction"]        =   False
		protocolPrm["ReconstructionMethod"]         =   self.params['reconMethod']
		protocolPrm["ARTLambda"]                    =   self.params['ARTLambda']
		protocolPrm["ARTReconstructionExtraCommand"]=   ''
		protocolPrm["FourierMaxFrequencyOfInterest"]=   self.params['fouriermaxfrequencyofinterest']
		protocolPrm["WBPReconstructionExtraCommand"]=''
		protocolPrm["FourierReconstructionExtraCommand"]=''
		protocolPrm["DoComputeResolution"]          =   self.params['docomputeresolution']
		protocolPrm["DoSplitReferenceImages"]       =   True
		protocolPrm["ResolSam"]                     =   self.params['apix']
		protocolPrm["DisplayResolution"]            =   False
		protocolPrm["DoLowPassFilter"]              =   self.params['dolowpassfilter']
		protocolPrm["UseFscForFilter"]              =   self.params['usefscforfilter']
		protocolPrm["ConstantToAddToFiltration"]    =   self.params['filterConstant']
		protocolPrm["NumberOfThreads"]              =   self.params['alwaysone']
		protocolPrm["DoParallel"]                   =   self.params['nproc']>1
		protocolPrm["NumberOfMpiProcesses"]         =   self.params['nproc']
		protocolPrm["MpiJobSize"]                   =   '10'
		protocolPrm["SystemFlavour"]                =   ''
		protocolPrm["AnalysisScript"]               =   'visualize_projmatch.py'

		protocolfile = os.path.join(self.params['remoterundir'],"%s.py" % protocolname)
		apXmipp.particularizeProtocol(protocol_projmatch,protocolPrm,protocolfile)
		return protocolfile

	def makePreIterationScript(self):
		super(XmippSingleModelRefineJob,self).makePreIterationScript()
		self.convertToXmippStyleIterParams()
		tasks = {}
		tasks = self.addToTasks(tasks,'ln %s reference_volume.spi' % self.params['modelnames'][0])
		protocolfile = self.setupXmippProtocol()
		tasks = self.addToTasks(tasks,'python %s' % protocolfile)
		tasks = self.addToTasks(tasks,'mv %s %s' % (protocolfile,self.params['recondir']))
		self.addJobCommands(tasks)

if __name__ == '__main__':
	app = XmippSingleModelRefineJob()
	app.start()
	app.close()
