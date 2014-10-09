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
class RelionSingleModelRefineJob(apRefineJob.RefineJob):
	#=====================
	def setupParserOptions(self):
		super(RelionSingleModelRefineJob,self).setupParserOptions()

	#================
	def setIterationParamList(self):
		super(RelionSingleModelRefineJob,self).setIterationParamList()
		self.iterparams.extend([
				{'name':"ctf", 'help':"Do CTF-correction", 'default':"False", 'action':"store_true"},
				{'name':"ctf_intact_first_peak", 'help':"Ignore CTFs until first peak", 'default':"False", 'action':"store_true"},
				{'name':"ctf_corrected_ref", 'help':"Has reference been CTF corrected?", 'default':"False", 'action':"store_true"},
				{'name':"ini_high", 'help':"Initial low-pass filter", 'default':"60"},
				{'name':"healpix_order", 'help':"Angular sampling interval", 'default':"7.5"},
				{'name':"auto_local_healpix_order", 'help':"Local searches from auto-sampling", 'default':"1.8"},
				{'name':"offset_range", 'help':"Offset search range", 'default':"5"},
				{'name':"offset_step", 'help':"Offset search step", 'default':"1"},
				])
				
	def checkIterationConflicts(self):
		super(RelionSingleModelRefineJob,self).checkIterationConflicts()
		
	
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

	def convertDegToOrder(self, degrees):
		''' 
		Relion specific function to do this conversion:
		30 deg - 0 order
		15     - 1
		7.5    - 2
		3.7    - 3
		1.8    - 4
		.9     - 5
		.5     - 6
		.2     - 7     
		.1     - 8
		'''
		# use a list, the index starts at zero.
		degreeToOrderMap = {30:0,15:1,7.5:2,3.7:4,1.8:5,.9:6,.5:7,.2:8,.1:9}
		print degreeToOrderMap
		print degrees, type(degrees)
		degrees = float(degrees)
		return degreeToOrderMap[degrees]

	def setRelionParameters(self):
		# Add relion command parameters to a parameter dictionary
		# self.params is designed to handle multiple models, so some of the params may be stored as a list.
		# For these params just take the value at index 0 since this file is only for single model cases.
		
#		for (key, value) in self.params.items():
#			print 'param: ' + key + ', '
#			print value
		relionParams={}
		if isinstance(self.params['symmetry'], (list, tuple)):
			relionParams["sym"] = self.params['symmetry'][0]
		else:
			relionParams["sym"] = self.params['symmetry']

		if isinstance(self.params['ini_high'], (list, tuple)):
			relionParams["ini_high"] = self.params['ini_high'][0]
		else:
			relionParams["ini_high"] = self.params['ini_high']

		relionParams["angpix"]                   = self.params['apix']
		relionParams["healpix_order"]            = self.convertDegToOrder( self.params['healpix_order'][0] )
		relionParams["auto_local_healpix_order"] = self.convertDegToOrder( self.params['auto_local_healpix_order'][0] )
		relionParams["offset_range"]             = self.params['offset_range'][0]
		relionParams["offset_step"]              = self.params['offset_step'][0]
		relionParams["ctf"]                      = self.params['ctf'][0]
		relionParams["ctf_corrected_ref"]        = self.params['ctf_corrected_ref'][0] # has ref been ctf corrected?
		relionParams["ctf_phase_flipped"]        = self.params['phaseflipped'] # have data been phase flipped?
		relionParams["ctf_intact_first_peak"]    = self.params['ctf_intact_first_peak'][0] 
		relionParams["o"]                        = self.params['recondir'] # output rootname
		relionParams["i"]                        = os.path.join( self.params['remoterundir'], "all_images.star" ) # input star file
		relionParams["ref"]                      = os.path.join( self.params['remoterundir'], self.params['modelnames'][0] ) # input model file
		relionParams["particle_diameter"]        = self.params['outerMaskRadius'] * 2 # diameter is twice the radius
		
		return relionParams

	def createRelionCommand(self, relionParams):
		''' 
		The relion program runs with a command similar to this example:
		 mpirun -np 6 /usr/local/relion-1.1/bin/relion_refine_mpi --o run1-multi/9-17-multi1-pa63 
		 --i /ami/data00/appion/12may14a/9-17-full-pa63-dataset/all_images.star --particle_diameter 250 
		 --angpix 2.17 --ref /ami/data00/appion/12may14a/9-17-full-pa63-dataset/pa63-class4-3dmsk.mrc 
		 --firstiter_cc --ini_high 60 --iter 25 --tau2_fudge 1 --flatten_solvent --zero_mask --ctf 
		 --ctf_corrected_ref --sym C7 --K 10 --oversampling 1 --healpix_order 2 --offset_range 5 
		 --offset_step 2 --norm --scale   --j 2
		 '''
#		for (key, value) in relionParams.items():
#			print 'relion param: ' + key + ', ' 
#			print value
#		 
		 ### TODO: add --continue
		 ### TODO: // For C-point group symmetries, join half-reconstructions up to 40A to prevent diverging orientations
		 ###		if (sym_group.getValue() == "C")
		 ###			cline += " --low_resol_join_halves 40";
		
		# -np is the number of MPI processors which should match the number of requested nodes.
		# It is best to request an odd number of nodes
		command = "mpirun -np " + str(self.nodes) + " " 
		relionProgramLocation = "`which relion_refine_mpi` "
		#relionProgramLocation = "`which relion_refine_mpi` " #"/usr/local/relion-1.2/bin/relion_refine_mpi "
		
		command += relionProgramLocation
		
		for (key, value) in relionParams.items():
			if ( value is True):
				command += "--" + key + " "
			elif ( value is False):
				pass				
			elif type(value) is list:
				command += "--" + key + " " + str(value[0]) + " "
			else:
				command += "--" + key + " " + str(value) + " "

		# --j is the number of threads per node, and should match the number of processors per node selected by the user.
		command += " --j " + str(self.ppn)
		
		# Always add these flags for 3D Auto Refine
		# TODO: remove --auto_sampling??
		command += " --flatten_solvent  --oversampling 1 --split_random_halves --dont_check_norm"
		
		return command

	def saveRunParamsToFile(self, methodParams):
		### Write out the run parameters, both generic and method specific, for posterior uploading
		
		self.runparams = {} ### these are generic params that includes a dictionary entry for package-specific params
#		self.runparams['symmetry'] = apSymmetry.getSymmetryDataFromName(self.params['symmetry'])

		#sym = apSymmetry.getSymmetryDataFromID(self.params['symmetry'])
		#sym2 = self.convertSymmetryNameForPackage(sym)
		self.runparams['symmetry'] = methodParams["sym"]
		self.runparams['numiter'] = 1
		self.runparams['mask'] = methodParams["particle_diameter"][0] / 2
		self.runparams['reconstruction_package'] = "Relion"
		self.runparams['remoterundir'] = self.params['remoterundir']
		self.runparams['reconstruction_working_dir'] = methodParams["o"] 
		self.runparams['package_params'] = methodParams
		self.picklefile = os.path.join(self.params['remoterundir'], "relion_"+self.timestamp+"-params.pickle")
		apParam.dumpParameters(self.runparams, self.picklefile)
		
		### finished setup of input files, now run xmipp_protocols_ml3d.py from jobfile
		apDisplay.printMsg("finished setting up input files, now ready to run protocol")

#	def makeNewTrialScript(self):
#		print self.params['modelnames'][0]
#		self.addSimpleCommand('ln -s %s %s' % (self.params['modelnames'][0], 
#			os.path.join(self.params['remoterundir'], self.params['modelnames'][0])))
#		partar = os.path.join(self.params['remoterundir'],'partfiles.tar.gz')
#		partpath = os.path.join(self.params['remoterundir'],'partfiles')
#		if not os.path.isdir(partpath):
#			# partfiles need to be untared in its directory
#			self.addSimpleCommand('mkdir %s' % partpath)
#			self.addSimpleCommand('cd %s' % partpath)
#			self.addSimpleCommand('tar xvf %s' % partar)
#			# return to recondir
#			self.addSimpleCommand('cd %s' % self.params['recondir'])


	def makePreIterationScript(self):
		tasks = {}
		self.addToLog('....Setting up Relion Parameters....')
		relionParams = self.setRelionParameters()
		self.addToLog('....Saving Relion Parameters for use during Upload step....')
		self.saveRunParamsToFile( relionParams )
		
		self.addToLog('....Creating Relion Command....')
		command = self.createRelionCommand( relionParams )		
		self.addToLog('....Start running Relion Single Model Refinement....')
		tasks = self.addToTasks( tasks, command, self.calcRefineMem(), self.params['nproc'] )
		
		#tasklogfilename = 'relionTaskLog.log'
		#tasklogfile = os.path.join(self.params['recondir'],tasklogfilename)
		#tasks = self.logTaskStatus(tasks,'protocol_run',tasklogfile)

		self.addJobCommands(tasks)

if __name__ == '__main__':
	app = RelionSingleModelRefineJob()
	app.start()
	app.close()
	
