#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apRefineJob

#================
#================
class XmippSingleModelRefineJob(apRefineJob.RefineJob):
	#=====================
	def setupParserOptions(self):
		super(XmippSingleModelRefineJob,self).setupParserOptions()
		self.parser.add_option("--MaskVol", dest="maskvol", type="str",
			help="Arbitrary mask volume file (0 outside protein, 1 inside). Arbitrary and spherical masks "
			+"are mutually exclusive",default="")
		self.parser.add_option("--InnerRadius", dest="innerradius", type="int",
			help="Inner radius for alignment",default=2)
		self.parser.add_option("--OuterRadius", dest="outerradius", type="int",
			help="Outer radius for alignment")
		self.parser.add_option("--FourierMaxFrequencyOfInterest",
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
					'help':"Angular steps (e.g. 4x10:2x5:2x3:2x2)",'default':"6x5:2x3:2x2")
				{'name':"MaxAngularChange",
					'help':"Maximum angular change (e.g. 4x1000:2x20:2x9:2x6)", 'default':'4x1000:2x20:2x9:2x6')
				{'name':"MaxChangeOffset",
					'help':"Maximum shift in x and y", 'default':'1000')
				{'name':"Search5DShift",
					'help':"Search range for shift 5D searches (e.g. 3x5:2x3:0)", 'default':'4x5:0')
				{'name':"Search5DStep",
					'help':"Shift step for 5D searches", 'default':"2")
				{'name':"DiscardPercentage",
					'help':"Percentage of images discarded with a CCF below X", 'default':"10")
				{'name':"ReconstructionMethod",
					'help':"fourier, art, wbp", 'default':"fourier")
				{'name':"ARTLambda",
					'help':"Relaxation factor for ART", 'default':"0.2")
				{'name':"ConstantToAddToFiltration",
					'help':"Use the FSC=0.5+Constant frequency for the filtration", 'default':"0.1")
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
		inputname = inputname.lower()
		if inputname[0] in ('c','d') or inputname in eman_hedral_symm_names.values():
			symm_name = inputname.lower()
		elif inputname in eman_hedral_symm_names.keys():
			symm_name = xmipp_hedral_symm_names[inputname]
		else:
			apDisplay.printWarning("unknown symmetry name conversion. Use it directly")
			symm_name = inputname.upper()
		return symm_name

	def setXmippSingleModelRefineParams(self,iter):
		refineparams = ('ang','mask','sym','hard','pad', 'median', 'classiter', 'refine', 'amask', 'phasecls', 'shrink', 'euler2',  'classkeep', 'imask', 'maxshift', 'xfiles', 'tree', 'filt3d')
		eotestparams = ('ang','mask','sym','hard','pad', 'median', 'classiter', 'refine', 'amask', 'euler2',  'classkeep', 'imask', 'xfiles')
		return refineparams,eotestparams	
		
	def combineEmanParams(self,iter_index,valid_paramkeys):
		task_params = []
		for key in valid_paramkeys:
			if key in self.params.keys():
				if type(self.params[key]) == type([]):
					paramvalue = self.params[key][iter_index]
				else:
					paramvalue = self.params[key]
				paramtype = type(paramvalue)
				if paramtype == type(True):
					if paramvalue is True:
						task_params.append(key)
				elif paramtype == type(0.5):
					task_params.append('%s=%.3f' % (key,paramvalue))
				elif paramtype == type(1):
					task_params.append('%s=%d' % (key,paramvalue))
				elif paramvalue == '':
					continue
				else:
					task_params.append('%s=%s' % (key,paramvalue))
		return task_params

	def getSymmetryOrder(self,sym_name):
		'''
		This only covers chiral symmetry of 3d point group
		'''
		proper = sym_name[0]
		if proper.lower() == 'c':
			order = eval(sym_name[1:])
		elif proper.lower() == 'd':
			order = eval(sym_name[1:]) * 2
		elif proper.lower() == 't':
			order = 12
		elif proper.lower() == 'o':
			order = 24
		elif proper.lower() == 'i':
			order = 60
		return order

	def calcRefineMem(self,ppn,boxsize,sym,ang):
		foldsym = self.getSymmetryOrder(sym)
		endnumproj = 18000.0/(foldsym*ang*ang)
		#need to open all projections and 1024 particles in memory
		numpartinmem = endnumproj + 1024
		memneed = numpartinmem*boxsize*boxsize*16.0*ppn
		numgig = math.ceil(memneed/1073741824.0)
		return int(numgig)

	def setupXmippProtocol(self):
		protocolname = 'protocol_projmatch'
		# Locate protocol_projmatch
		protocol_projmatch=locateXmippProtocol(protocolname)

		#make threads and mpi processes compatible with the xmipprequirement
		self.params['alwaysone']=1
		
		protocolPrm={}
		protocolPrm["SelFileName"]                  =   "partlist.sel"
		protocolPrm["DocFileName"]                  =   ""
		protocolPrm["ReferenceFileName"]            =   "./threed0.spi"
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
		protocolPrm["DoSphericalMask"]              =   self.params['mask']>0
		protocolPrm["MaskRadius"]                   =   self.params['mask']
		protocolPrm["MaskFileName"]                 =   self.params['maskvol']
		protocolPrm["DoProjectionMatching"]         =   True
		protocolPrm["DisplayProjectionMatching"]    =   False
		protocolPrm["InnerRadius"]                  =   self.params['innerradius']
		protocolPrm["OuterRadius"]                  =   self.params['outerradius']
		protocolPrm["AvailableMemory"]              =   '2'
		protocolPrm["AngSamplingRateDeg"]           =   self.params['angularsteps']
		protocolPrm["MaxChangeInAngles"]            =   self.params['maxchangeinangles']
		protocolPrm["PerturbProjectionDirections"]  =   False
		protocolPrm["MaxChangeOffset"]              =   self.params['maxchangeoffset']
		protocolPrm["Search5DShift"]                =   self.params['search5dshift']
		protocolPrm["Search5DStep"]                 =   self.params['search5dstep']
		protocolPrm["DoRetricSearchbyTiltAngle"]    =   False
		protocolPrm["Tilt0"]                        =   0
		protocolPrm["TiltF"]                        =   0
		protocolPrm["SymmetryGroup"]                =   self.params['symm']
		protocolPrm["SymmetryGroupNeighbourhood"]   =   ''
		protocolPrm["OnlyWinner"]                   =   False
		protocolPrm["MinimumCrossCorrelation"]      =   '-1'
		protocolPrm["DiscardPercentage"]            =   self.params['discardpercentage']
		protocolPrm["ProjMatchingExtra"]            =   ''
		protocolPrm["DoAlign2D"]                    =   '0'
		protocolPrm["Align2DIterNr"]                =   4
		protocolPrm["Align2dMaxChangeOffset"]       =   '1000'
		protocolPrm["Align2dMaxChangeRot"]          =   '1000'
		protocolPrm["DoReconstruction"]             =   True
		protocolPrm["DisplayReconstruction"]        =   False
		protocolPrm["ReconstructionMethod"]         =   self.params['reconstructionmethod']
		protocolPrm["ARTLambda"]                    =   self.params['artlambda']
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
		protocolPrm["ConstantToAddToFiltration"]    =   self.params['constanttoaddtofiltration']
		protocolPrm["NumberOfThreads"]              =   self.params['alwaysone']
		protocolPrm["DoParallel"]                   =   self.params['numberofmpiprocesses']>1
		protocolPrm["NumberOfMpiProcesses"]         =   self.params['nproc']
		protocolPrm["MpiJobSize"]                   =   '10'
		protocolPrm["SystemFlavour"]                =   ''
		protocolPrm["AnalysisScript"]               =   'visualize_projmatch.py'

		protocolfile = os.path.join(self.params['recondir'],"xmipp_%s.py" % protocolname)
		particularizeProtocol(protocol_projmatch,protocolPrm,protocolfile)
		return protocolfile

	def runXmippProtocol(self,protocolfile):
		subprocess.call("python %s" % protocolfilexm,shell=True);

		# Write the run parameters for the posterior uploading
		protocolPrm["modelid"] = self.params['modelid']
		f = open("runParameters.txt","w")
		print >>f,protocolPrm
		f.close()

	def checkXmippSuccess(self,startiter):
		if os.path.exists("ProjMatch/Iter_%d/ReferenceLibrary/ref000001.xmp" % startiter):
			# Create a blank image
			subprocess.call("xmipp_operate -i recon/ProjMatch/Iter_%d/ReferenceLibrary/ref000001.xmp -mult 0 -o blank.xmp"% startuter,
				shell=True)
		else:
			''' TO DO: would be nice to notify appion that there is an error '''
			apDisplay.printError("No iteration has been performed")

	def gatherXmippResults(self):
		# Pickup results
		os.unlink("partlist.sel")
		shutil.rmtree("partfiles")
		os.unlink(fnRef)
		shutil.rmtree("ProjMatch/ReferenceLibrary")
		shutil.rmtree("ProjMatch/ProjMatchClasses")
		os.unlink("ProjMatch/xmipp_protocol_projmatch_backup.py")
		os.unlink("ProjMatch/original_angles.doc")
		os.unlink("ProjMatch/partlist.sel")


		Link the results of the last iteration
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"angles.doc")+" angles.doc", shell=True)
		proc.wait()
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"classAverages.hed")+" classAverages.hed", shell=True)
		proc.wait()
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"classAverages.img")+" classAverages.img", shell=True)
		proc.wait()
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"reconstruction.mrc")+" reconstruction.mrc", shell=True)
		proc.wait()
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"ref_angles.doc")+" ref_angles.doc", shell=True)
		proc.wait()
		proc = subprocess.Popen("ln -s "+os.path.join(lastIteration,"fsc.txt")+" fsc.txt",shell=True)
		proc.wait()

	def makePreIterationScript(self):
		super(XmippSingleModelRefineJob,self).makePreIterationScript()
		self.addJobCommands(self.addToTasks({},'mv %s threed.0a.mrc' % self.params['modelfile'],2,1))
		protocolfile = self.setupXmippProtocol()
		self.runXmippProtocol(protocolfile)
		self.checkXmippSuccess(self.params['startiter'])
		self.resfile=open("resolution.txt","w")

	def makeRefineScript(self,iter):
		'''
		Xmipp uses single protocol file to run all iteration.  This part is only for getting
		per iteration results
		'''
		lastIteration=iter
		i = iter
		iteration = "ProjMatch/Iter_%d" % iter
		if not os.path.exists(iteration):
			return
		rootname=iteration[iteration.find("/")+1:]

		# Remove some files
		os.unlink(os.path.join(iteration,rootname+"_filtered_reconstruction.vol"))
		os.unlink(os.path.join(iteration,rootname+"_reference_volume.vol"))
		os.unlink(os.path.join(iteration,"multi_align2d.sel"))
		os.unlink(os.path.join(iteration,"reconstruction.sel"))
		os.unlink(os.path.join(iteration,"reconstruction.doc"))
		fnAux=os.path.join(iteration,"find_closest_experimental_point.txt")
		if os.path.exists(fnAux):
			os.unlink(fnAux)

		# Keep the class averages
		shutil.copyfile(os.path.join(iteration,"ReferenceLibrary/ref_angles.doc"),
			os.path.join(iteration,"ref_angles.doc"))
		fhsel=open("classprojaverages.sel","w")
		for fileproj in glob.glob(iteration+"/ReferenceLibrary/ref*.xmp"):
			fhsel.write(fileproj+" 1\n")
			fileclass=fileproj.replace("ReferenceLibrary/ref",
				"ProjMatchClasses/proj_match_class")
			if os.path.exists(fileclass):
				fhsel.write(fileclass+" 1\n")
			else:
				fhsel.write("blank.xmp 1\n")
		fhsel.close()
		apXmipp.gatherSingleFilesIntoStack(
			"classprojaverages.sel",
			os.path.join(iteration,"classAverages.hed"))
		shutil.rmtree(iteration+"/ReferenceLibrary")
		shutil.rmtree(iteration+"/ProjMatchClasses")
		os.unlink("classprojaverages.sel")

		# Keep the angles
		os.rename(os.path.join(iteration,rootname+"_current_angles.doc"),
			os.path.join(iteration,"angles.doc"))

		
		# Keep the volume
		SPItoMRC(os.path.join(iteration,rootname+"_reconstruction.vol"),
			os.path.join(self.params['recondir'],"threed.%03da.mrc"%(iter)))
		os.unlink(os.path.join(iteration,rootname+"_reconstruction.vol"))

		# Keep the FSC
		FSCfromXmippToEMAN(os.path.join(iteration,rootname+"_resolution.fsc"),
			os.path.join(iteration,"fsc.txt"))
#		os.unlink(os.path.join(iteration,rootname+"_resolution.fsc"))
		res=apRecon.calcRes(os.path.join(iteration,"fsc.txt"),
			self.params['boxsize'],self.params['apix'])
		self.resfile.write("%s:\t%.3f\n" % (rootname,res))

	
		tasks = {}
		tasks = self.addToTasks(tasks,'')
		return tasks

	def makePostIterationScript(self):
		os.unlink("blank.xmp")
		self.resfile.close()
		self.gatherXmippResults()

		tasks = {}
		tasks = self.addToTasks(tasks,'# pack up the results and put back to safedir')
		tasks = self.addToTasks(tasks,'tar -cvzf model.tar.gz threed.*a.mrc',self.mem,1)
		tasks = self.addToTasks(tasks,'tar -cvzf results.tar.gz fsc* cls* refine.* particle.* classes_* classes_*.* proj.* sym.* *txt *.job',self.mem,1)
		tasks = self.addToTasks(tasks,'/bin/mv -v model.tar.gz %s' % (self.params['safedir']))
		tasks = self.addToTasks(tasks,'/bin/mv -v results.tar.gz %s' % (self.params['safedir']))
		tasks = self.addToTasks(tasks,'cd %s' % (self.params['safedir']))
		self.addJobCommands(tasks)

if __name__ == '__main__':
	app = XmippSingleModelRefineJob()
	app.start()
	app.close()
