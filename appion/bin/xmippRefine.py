#!/usr/bin/env python

#python
import glob
import os
import re
import shutil
import subprocess
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import appiondata
from appionlib import apXmipp
from appionlib import apRecon
from appionlib import apModel
from appionlib import apVolume

#======================
#======================
def particularizeProtocol(protocolIn, parameters, protocolOut):
	fileIn = open(protocolIn)
	fileOut = open(protocolOut,'w')
	endOfHeader=False
	for line in fileIn:
		if not line.find("{end-of-header}")==-1:
			endOfHeader=True
		if endOfHeader:
			fileOut.write(line)
		else:
			for key in parameters.keys():
				if not re.match('^'+key,line) is None:
					line=key+'='+repr(parameters[key])+'\n'
					break
			fileOut.write(line)
	fileIn.close()
	fileOut.close()

def locateXmippProtocol(protocolname):
	proc = subprocess.Popen('which xmipp_protocols',
		   shell=True,stdout=subprocess.PIPE)
	stdout_value = proc.communicate()[0]
	i = stdout_value.find("bin/xmipp_protocols");
	if (i==-1):
		apDisplay.printError("Cannot locate Xmipp");
	XmippDir=stdout_value[0:i]
	return (XmippDir+"protocols/xmipp_"+protocolname+".py")

def SPItoMRC(infile,outfile):
	emancmd = "proc3d %s %s" %(infile,outfile)
	apEMAN.executeEmanCmd(emancmd, verbose=True)

def FSCfromXmippToEMAN(infile,outfile):
	fileIn = open(infile)
	fileOut = open(outfile,'w')
	i=0
	for line in fileIn:
		if not line[0]=='#':
			fileOut.write(str(i)+"\t"+line.split()[1]+"\n")
		i=i+1
	fileIn.close()
	fileOut.close()

class xmippRefineScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ options ]")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--modelid", dest="modelid", type="int",
			help="Initial model id from database")
		self.parser.add_option("--pixelSize", dest="pixelSize", type="float",
			help="Pixel Size (Angstroms)")
		self.parser.add_option("--boxSize", dest="boxSize", type="int",
			help="Box Size")
		self.parser.add_option("-N", "--NumberOfIterations", dest="numberofiterations", type="int",
			help="Number of iterations",default=10)
		self.parser.add_option("--MaskRadius", dest="maskradius", type="int",
			help="Spherical mask radius",default=0)
		self.parser.add_option("--Mask", dest="mask", type="str",
			help="Arbitrary mask (0 outside protein, 1 inside). Arbitrary and spherical masks "
			+"are mutually exclusive",default="")
		self.parser.add_option("--InnerRadius", dest="innerradius", type="int",
			help="Inner radius for alignment",default=2)
		self.parser.add_option("--OuterRadius", dest="outerradius", type="int",
			help="Outer radius for alignment")
		self.parser.add_option("--AngularSteps", dest="angularsteps", type="string",
			help="Angular steps (e.g. 4x10 2x5 2x3 2x2)",default="6x5 2x3 2x2")
		self.parser.add_option("--MaxAngularChange", dest="maxchangeinangles", type="string",
			help="Maximum angular change (e.g. 4x1000 2x20 2x9 2x6)", default='4x1000 2x20 2x9 2x6')
		self.parser.add_option("--MaxChangeOffset", dest="maxchangeoffset", type="string",
			help="Maximum shift in x and y", default='1000')
		self.parser.add_option("--Search5DShift", dest="search5dshift", type="string",
			help="Search range for shift 5D searches (e.g. 3x5 2x3 0)", default='4x5 0')
		self.parser.add_option("--Search5DStep", dest="search5dstep", type="string",
			help="Shift step for 5D searches", default="2")
		self.parser.add_option("--SymmetryGroup", dest="symmetrygroup", type="string",
			help="c1, c2, d1, d2, ... See http://xmipp.cnb.uam.es/twiki/bin/view/Xmipp/Symmetry",
			default="c1")
		self.parser.add_option("--DiscardPercentage", dest="discardpercentage", type="string",
			help="Percentage of images discarded with a CCF below X", default="10")
		self.parser.add_option("--ReconstructionMethod", dest="reconstructionmethod", type="string",
			help="fourier, art, wbp", default="fourier")
		self.parser.add_option("--ARTLambda", dest="ARTLambda", type="string",
			help="Relaxation factor for ART", default="0.2")
		self.parser.add_option("--FourierMaxFrequencyOfInterest",
			dest="fouriermaxfrequencyofinterest", type="float",
			help="Maximum frequency of interest for Fourier", default=0.25)
		self.parser.add_option("--DoComputeResolution", dest="docomputeresolution", action="store_true",
			help="Compute resolution or not", default=True)
		self.parser.add_option("--DoLowPassFilter", dest="dolowpassfilter", action="store_true",
			help="This lowpass filter will be applied for the generation of the next reference", default=True)
		self.parser.add_option("--DontUseFscForFilter", dest="usefscforfilter", action="store_false",
			help="Use the FSC=0.5+Constant frequency for the filtration", default=True)
		self.parser.add_option("--ConstantToAddToFiltration", dest="constanttoaddtofiltration", type="string",
			help="Use the FSC=0.5+Constant frequency for the filtration", default="0.1")
		self.parser.add_option("--NumberOfMPIProcesses", dest="numberofmpiprocesses", type="int",
			help="Number of MPI Processes (needs mpirun installed)", default=1)
		self.parser.add_option("--NumberOfThreads", dest="numberofthreads", type="int",
			help="Number of threads for each process", default=1)

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if self.params['outerradius'] is None:
			apDisplay.printError("outer radius was not defined")
		if self.params['pixelSize'] is None:
			apDisplay.printError("Pixel size was not defined")
		if self.params['boxSize'] is None:
			apDisplay.printError("Box size was not defined")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "recons/xmipp", self.params['runname'])

	#=====================
	def start(self):
		# Locate protocol_projmatch
		protocol_projmatch=locateXmippProtocol("protocol_projmatch")

		# Convert input images to Spider
		if os.path.exists("start.hed"):
			fnStack="start.hed";
		else:
			stackData = apStack.getOnlyStackData(self.params['stackid'])
			fnStack=os.path.join(stackData['path']['path'], stackData['name'])
		apXmipp.breakupStackIntoSingleFiles(fnStack)
		
		# Convert input volume to Spider
		modelData = apModel.getModelFromId(self.params['modelid'])
		if os.path.exists("start.img"):
			fnRefMrc="threed.0a.mrc"
		if modelData['pixelsize'] != self.params['pixelSize']:
			fnRef = apParam.randomString(8)+".spi"
			apModel.rescaleModel(self.params['modelid'], fnRef, self.params['boxSize'], self.params['pixelSize'], spider=True)

		# Convert mask if it exists
		fnMask=""
		if not self.params['mask']=="":
			modelData = apModel.getModelFromId(self.params['mask'])
			fnMaskMrc = os.path.join(modelData['path']['path'],modelData['name'])
			fnMask = apVolume.MRCtoSPI(fnMaskMrc, self.params['rundir'])

		protocolPrm={}
		protocolPrm["SelFileName"]                  =   "partlist.doc"
		protocolPrm["DocFileName"]                  =   ""
		protocolPrm["ReferenceFileName"]            =   fnRef
		protocolPrm["WorkingDir"]                   =   "ProjMatch"
		protocolPrm["DoDeleteWorkingDir"]           =   True
		protocolPrm["NumberofIterations"]           =   self.params['numberofiterations']
		protocolPrm["ContinueAtIteration"]          =   1
		protocolPrm["CleanUpFiles"]                 =   False
		protocolPrm["ProjectDir"]                   =   self.params['rundir']
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
		protocolPrm["DoMask"]                       =   self.params['mask']>0
		protocolPrm["DoSphericalMask"]              =   self.params['maskradius']>0
		protocolPrm["MaskRadius"]                   =   self.params['maskradius']
		protocolPrm["MaskFileName"]                 =   fnMask
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
		protocolPrm["SymmetryGroup"]                =   self.params['symmetrygroup']
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
		protocolPrm["ARTLambda"]                    =   self.params['ARTLambda']
		protocolPrm["ARTReconstructionExtraCommand"]=   ''
		protocolPrm["FourierMaxFrequencyOfInterest"]=   self.params['fouriermaxfrequencyofinterest']
		protocolPrm["WBPReconstructionExtraCommand"]=''
		protocolPrm["FourierReconstructionExtraCommand"]=''
		protocolPrm["DoComputeResolution"]          =   self.params['docomputeresolution']
		protocolPrm["DoSplitReferenceImages"]       =   True
		protocolPrm["ResolSam"]                     =   self.params['pixelSize']
		protocolPrm["DisplayResolution"]            =   False
		protocolPrm["DoLowPassFilter"]              =   self.params['dolowpassfilter']
		protocolPrm["UseFscForFilter"]              =   self.params['usefscforfilter']
		protocolPrm["ConstantToAddToFiltration"]    =   self.params['constanttoaddtofiltration']
		protocolPrm["NumberOfThreads"]              =   self.params['numberofthreads']
		protocolPrm["DoParallel"]                   =   self.params['numberofmpiprocesses']>1
		protocolPrm["NumberOfMpiProcesses"]         =   self.params['numberofmpiprocesses']
		protocolPrm["MpiJobSize"]                   =   '10'
		protocolPrm["SystemFlavour"]                =   ''
		protocolPrm["AnalysisScript"]               =   'visualize_projmatch.py'

		particularizeProtocol(protocol_projmatch,protocolPrm,
			os.path.join(self.params['rundir'],"protocol_projmatch.py"))
		subprocess.call("python protocol_projmatch.py",shell=True);

		# Write the run parameters for the posterior uploading
		protocolPrm["modelid"] = self.params['modelid']
		f = open("runParameters.txt","w")
		print >>f,protocolPrm
		f.close()

		# Pickup results
		os.unlink("partlist.doc")
		shutil.rmtree("partfiles")
		os.unlink(fnRef)
		shutil.rmtree("ProjMatch/ReferenceLibrary")
		shutil.rmtree("ProjMatch/ProjMatchClasses")
		os.unlink("ProjMatch/protocol_projmatch_backup.py")
		os.unlink("ProjMatch/original_angles.doc")
		os.unlink("ProjMatch/partlist.doc")
		if os.path.exists("ProjMatch/Iter_1/ReferenceLibrary/ref000001.xmp"):
			# Create a blank image
			subprocess.call("xmipp_operate -i ProjMatch/Iter_1/ReferenceLibrary/ref000001.xmp -mult 0 -o blank.xmp",
				shell=True)
		else:
			apDisplay.printError("No iteration has been performed")
		if fnStack=="start.img":
			os.unlink("start.img")
			os.unlink("start.hed")
		if fnRefMrc=="threed.0a.mrc":
			os.unlink("threed.0a.mrc")

		lastIteration=""
		resfile=open("resolution.txt","w")
		for iteration in glob.glob("ProjMatch/Iter_*"):
			lastIteration=iteration
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
				os.path.join(iteration,"reconstruction.mrc"))
			os.unlink(os.path.join(iteration,rootname+"_reconstruction.vol"))

			# Keep the FSC
			FSCfromXmippToEMAN(os.path.join(iteration,rootname+"_resolution.fsc"),
				os.path.join(iteration,"fsc.txt"))
			os.unlink(os.path.join(iteration,rootname+"_resolution.fsc"))
			res=apRecon.calcRes(os.path.join(iteration,"fsc.txt"),
				self.params['boxSize'],self.params['pixelSize'])
			resfile.write("%s:\t%.3f\n" % (rootname,res))

		os.unlink("blank.xmp")
		resfile.close()

		# Link the results of the last iteration
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

#=====================
if __name__ == "__main__":
	refine3d = xmippRefineScript()
	refine3d.start()
	refine3d.close()

