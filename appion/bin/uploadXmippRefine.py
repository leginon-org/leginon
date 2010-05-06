#!/usr/bin/env python

#python
import glob
import os
import re
import shutil
import subprocess
import sys
#appion
from appionlib import appionScript
from appionlib import apChimera
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import appiondata
from appionlib import apXmipp
from appionlib import apRecon
from appionlib import apModel
from appionlib import apSymmetry
from appionlib import apEulerDraw

#======================
#======================
class uploadXmippRefineScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ options ]")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--mass", dest="mass", type="float",
			help="Mass of the reconstructed volume in kDa")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['mass'] is None:
			apDisplay.printError("mass was not defined")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "recon/xmipp", self.params['runname'])

	#=====================
	def start(self):
		# Add xmipp python files to the Python path
		scriptdir=os.path.split(os.path.dirname(os.popen('which xmipp_protocols','r').read()))[0]+'/protocols'
		sys.path.append(scriptdir)
		import arg

		# Get the stack
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.pixelSize=self.stack['apix'];
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		total=apFile.numImagesInStack(self.stack['file'])

		# Read the run parameters
		protocolPrm = eval(open("runParameters.txt").read())

		# Insert the fixed parameters
		fixedq = appiondata.ApXmippRefineFixedParamsData()
		fixedq['Niter']			  = protocolPrm["NumberofIterations"]
		fixedq['maskFilename']    = protocolPrm["MaskFileName"]
		fixedq['maskRadius']      = protocolPrm["MaskRadius"]
		fixedq['innerRadius']     = protocolPrm["InnerRadius"]
		fixedq['outerRadius']     = protocolPrm["OuterRadius"]
		fixedq['symmetryGroup']   = apSymmetry.findSymmetry(protocolPrm["SymmetryGroup"])
		fixedq['fourierMaxFrequencyOfInterest']=protocolPrm['FourierMaxFrequencyOfInterest']
		fixedq['computeResol']    = protocolPrm["DoComputeResolution"]
		fixedq['dolowpassfilter'] = protocolPrm["DoLowPassFilter"]
		fixedq['usefscforfilter'] = protocolPrm["UseFscForFilter"]
		fixedq.insert()

		# Insert this run in the table of runs
		runq=appiondata.ApRefineRunData()
		runq['name']=self.params['runname']
		runq['stack']=apStack.getOnlyStackData(self.params['stackid'])
		earlyresult=runq.query(results=1)
		if earlyresult:
			apDisplay.printWarning("Run already exists in the database.\nIdentical data will not be reinserted")
		runq['initialModel']=apModel.getModelFromId(protocolPrm['modelid'])
		runq['package']="Xmipp"
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['description']=self.params['description']
		result=runq.query(results=1)
		if earlyresult and not result:
			apDisplay.printError("Refinement Run parameters have changed")
		apDisplay.printMsg("inserting Refinement Run into database")
		runq.insert()

		# Insert now the information for each iteration
		for i in range(1,protocolPrm["NumberofIterations"]+1):
			apDisplay.printMsg("Processing iteration "+str(i))
			iterDir="ProjMatch/Iter_"+str(i)

			# Insert the resolution
			resolq=appiondata.ApResolutionData()
			resolq['fscfile']=os.path.join(iterDir,"fsc.txt")
			resolq['half']=apRecon.calcRes(resolq['fscfile'],
				self.stack['boxsize'], self.stack['apix'])
			apDisplay.printMsg("inserting FSC resolution data into database")
			resolq.insert()

			# Insert the R measure
			rmeasure=appiondata.ApRMeasureData()
			rmeasure['volume']=os.path.join(iterDir,"reconstruction.mrc")
			rmeasure['rMeasure']=apRecon.runRMeasure(self.stack['apix'],
				os.path.join(self.params['rundir'],rmeasure['volume']))
			rmeasure.insert()

			# Fill the iteration dependent parameters
			iterparamq=appiondata.ApXmippRefineIterData()
			iterparamq['angularStep']=float(arg.getComponentFromVector(protocolPrm['AngSamplingRateDeg'],i-1))
			iterparamq['maxChangeInAngles']=float(arg.getComponentFromVector(protocolPrm['MaxChangeInAngles'],i-1))
			iterparamq['maxChangeOffset']=float(arg.getComponentFromVector(protocolPrm['MaxChangeOffset'],i-1))
			iterparamq['search5dShift']=float(arg.getComponentFromVector(protocolPrm['Search5DShift'],i-1))
			iterparamq['search5dStep']=float(arg.getComponentFromVector(protocolPrm['Search5DStep'],i-1))
			iterparamq['discardPercentage']=float(arg.getComponentFromVector(protocolPrm['DiscardPercentage'],i-1))
			iterparamq['reconstructionMethod']=arg.getComponentFromVector(protocolPrm['ReconstructionMethod'],i-1)
			if (iterparamq['reconstructionMethod']=='art'):
				iterparamq['ARTLambda']=float(arg.getComponentFromVector(protocolPrm['ARTLambda'],i-1))
			iterparamq['constantToAddToFiltration']=float(arg.getComponentFromVector(protocolPrm['ConstantToAddToFiltration'],i-1))
			iterparamq.insert()

			# Insert the main information for this iteration
			mainq=appiondata.ApRefineIterData()
			mainq['volumeDensity']=rmeasure['volume']
			mainq['refineRun']=runq
			mainq['xmippParams']=iterparamq
			mainq['iteration']=i
			mainq['resolution']=resolq
			mainq['rMeasure']=rmeasure
			mainq['refineClassAverages']=os.path.join(iterDir,"classAverages.img")
			mainq['refineClassAverages']=mainq['refineClassAverages']
			apDisplay.printMsg("inserting main iteration data into database")
			mainq.insert()

			# Insert the FSC
			fhFSC = open(resolq['fscfile'])
			for line in fhFSC:
				tokens=line.split()
				point=appiondata.ApFSCData()
				point['refinementData']=mainq
				point['pix']=int(tokens[0])
				point['value']=float(tokens[1])
				point.insert()

			# Insert the Euler angles of each particle
			fhAngles = open(os.path.join(iterDir,"angles.doc"))
			lineNo=0
			particleNo=0
			apDisplay.printMsg("inserting Euler data into database")
			for line in fhAngles:
				if lineNo==0:
					lineNo+=1
					continue
				if lineNo%2 == 1:
					projectionName=(line.split())[1]
				else:
					docline=line.split()
					particleq=appiondata.ApRefineParticleData()
					particleq['refineIter']=mainq
					particleq['particle']=apStack.getStackParticle(
						self.params['stackid'], particleNo+1)
					particleq['euler1']=docline[2]
					particleq['euler2']=docline[3]
					particleq['euler3']=docline[4]
					particleq['shiftx']=docline[5]
					particleq['shifty']=docline[6]
					particleq['mirror']=docline[8]
					particleq['quality_factor']=docline[9]
					particleq['euler_convention']="ZYZ"
					particleq.insert()
					particleNo +=1
					if particleNo % 100 == 0:
						sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
						sys.stderr.write(str(particleNo)+" of "+(str(total))+" complete")

				lineNo+=1
			fhAngles.close()
			sys.stderr.write("\n"+(str(total))+" particles have been introduced\n")

			# Generate the Euler plots
			apEulerDraw.createEulerImages(int(runq.dbid), i, path=self.params['rundir'])

			# Generate the reconstruction plots
			#proc = subprocess.Popen("ln -s "+mainq['volumeDensity']+" tmp.mrc", shell=True)
			#proc.wait()
			#print os.getcwd()
			densityfile = os.path.join(self.params['rundir'], mainq['volumeDensity'])
			apChimera.filterAndChimera(density=densityfile,
				res=resolq['half'], apix=self.stack['apix'],
				chimtype='snapshot', sym=protocolPrm["SymmetryGroup"],
				mass=self.params['mass'])
			#os.unlink("tmp.mrc")

#=====================
if __name__ == "__main__":
	upload3D = uploadXmippRefineScript()
	upload3D.start()
	upload3D.close()

