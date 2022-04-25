#!/usr/bin/env python
#------------------------------------------------------------------------------------------------
# This is partly taken and modified from the Xmipp protocol for projection matching
#
# Original Authors: Roberto Marabini,
#          Sjors Scheres,    March 2008
# Modified: Dmitry Lyumkis, May 2012
#
# This script has not been thoroughly tested
#

#------------------------------------------------------------------------
# projection-matching protocol
#------------------------------------------------------------------------
def projection_matching_protocol_basic(
			_SelFileName,
			_ReferenceFileName,
			_WorkingDir,
			_ProjectDir,
			_MaskRadius,
			_InnerRadius,
			_OuterRadius,
			_AvailableMemory,
			_ResolSam,
			_NumberOfMpiProcesses,
			_NumberofIterations=30,
			_ContinueAtIteration=1,
			_CleanUpFiles=True,
			_LogDir="Logs",
			_DoMask=True,
			_DoSphericalMask=True,
			_MaskFileName='',
			_AngSamplingRateDeg='20x10 5x5 5x3',
			_MaxChangeInAngles='20x1000 5x20 5x9',
			_MaxChangeOffset='20x1000 10x10',
			_Search5DShift='20x5 1',
			_Search5DStep='20x2 1',
			_DocFileName='',
			_SymmetryGroup='c1',  
			_MinimumCrossCorrelation='-1',
			_DiscardPercentage='0',
			_DoReconstruction=True,
			_PaddingFactor=1.0,
			_FourierMaxFrequencyOfInterest='0.35',
			_ConstantToAddToFiltration='0.35',
			_NumberOfThreads=1,
			_DoParallel=True,
			_MpiJobSize='10',
			_SystemFlavour=''
			):
			
	# Import libraries and add Xmipp libs to default search path
	import os,sys,shutil
	scriptdir=os.path.split(os.path.dirname(os.popen('which xmipp_protocols','r').read()))[0]+'/protocols'
	sys.path.append(scriptdir)
	import arg,log,logging,selfile
	import launch_job

	# global variables
	_ReferenceVolumeName='reference_volume.vol'
	_LibraryDir = "ReferenceLibrary"
	_ProjectLibraryRootName= _LibraryDir + "/ref"
	_ProjMatchDir = "ProjMatchClasses"
	_ProjMatchName = 'proj_match'
	_ProjMatchRootName= _ProjMatchDir + "/" + _ProjMatchName
	_DocFileWithOriginalAngles='original_angles.doc'
	_docfile_with_current_angles='current_angles.doc'
	_ReconstructedVolumeBase="reconstruction"
	_FilteredReconstruction="filtered_reconstruction"
	_WorkingDir=os.getcwd()+'/'+os.path.basename(_WorkingDir)
	_ReferenceFileName=os.path.abspath(_ReferenceFileName)
	_user_suplied_ReferenceVolume=_ReferenceFileName
	selfile_without_ext=(os.path.splitext(str(os.path.basename(_SelFileName))))[0]
	globalFourierMaxFrequencyOfInterest=float(_FourierMaxFrequencyOfInterest)
	_MySystemFlavour=_SystemFlavour
	_MyNumberOfMpiProcesses=_NumberOfMpiProcesses
	_MyMpiJobSize =_MpiJobSize
	_MyNumberOfThreads =_NumberOfThreads

	# Set up logging
	_mylog=log.init_log_system(_ProjectDir, _LogDir, sys.argv[0], _WorkingDir)
	# Uncomment next line to get Debug level logging
	_mylog.setLevel(logging.DEBUG)
	_mylog.debug("Debug level logging enabled")
	#input files should exists
	check_file_exists(_ReferenceFileName,_mylog)
								  
	_NumberofIterations +=1;
	create_working_directory(_mylog, _WorkingDir, _ProjMatchDir, _LibraryDir)

	# Create a selfile with absolute pathname in the WorkingDir
	mysel=selfile.selfile()
	mysel.read(os.path.basename(_SelFileName))
	newsel=mysel.make_abspath()
	_SelFileName=os.path.abspath(_WorkingDir + '/' + os.path.basename(_SelFileName))
	newsel.write(_SelFileName)

	# Set _OuterRadius
	if (_OuterRadius < 0):
		xdim,ydim=newsel.imgSize()
		_OuterRadius = (xdim/2) - 1 
		comment = " Outer radius set to: " + str(_OuterRadius)
		print '* ' + comment
		_mylog.info(comment)
	else:   
		_OuterRadius=_OuterRadius

	# Create a docfile with the current angles in the WorkingDir
	if (_DocFileName==''):
		params=' -i ' + _SelFileName + \
			' -o ' + _WorkingDir + '/' + \
			_DocFileWithOriginalAngles
		launch_job.launch_job("xmipp_header_extract", params, _mylog, False,1,1,'')

	# Change to working dir
	os.chdir(_WorkingDir)
	_SelFileName=_WorkingDir+'/' + str(os.path.basename(_SelFileName))

	##
	##LOOP
	##
	#output of reconstruction cycle
	#first value given by user
	#these names are the input of the mask program
	#in general is the output of the reconstruction plus filtration
	_ReconstructedVolume=[]
	fill_name_vector("",
		_ReconstructedVolume,
		_NumberofIterations,
		_ReconstructedVolumeBase)
					
	_ReconstructedandfilteredVolume=[]
	fill_name_vector(_user_suplied_ReferenceVolume,
		_ReconstructedandfilteredVolume,
		_NumberofIterations,
		_FilteredReconstruction)

	# Optimal angles from previous iteration or user-provided at the beginning
	_DocFileInputAngles=[]
	fill_name_vector('../'+_DocFileWithOriginalAngles,
		_DocFileInputAngles,
		_NumberofIterations+1,
		_docfile_with_current_angles)

	# Reconstructed and filtered volume of n-1 after masking called reference volume
	_ReferenceVolume=[]
	fill_name_vector("",
		_ReferenceVolume,
		_NumberofIterations,
		_ReferenceVolumeName)

	for _iteration_number in range(_ContinueAtIteration, _NumberofIterations):
		debug_string =  "ITERATION: " +  str(_iteration_number)
		print "*", debug_string
		_mylog.info(debug_string)

		# Create working dir for this iteration and go there
		Iteration_Working_Directory=_WorkingDir+'/Iter_' + str(_iteration_number)
		create_working_directory(_mylog, Iteration_Working_Directory, _ProjMatchDir, _LibraryDir)
		os.chdir(Iteration_Working_Directory)

		#### changed here for this stack -- Dmitry
		# Mask reference volume
		if _iteration_number == 1:
			execute_mask(_DoMask,
				_mylog,
				_ProjectDir,
				_ReconstructedandfilteredVolume[_iteration_number],#in
				_MaskFileName,
				_DoSphericalMask,
				_MaskRadius,
				_iteration_number,
				_ReferenceVolume[_iteration_number])#out
		elif _DoReconstruction is True:
			execute_mask(_DoMask,
				_mylog,
				_ProjectDir,
				os.path.join("../Iter_%d" % (_iteration_number-1), "Iter_%d_reconstruction" % (_iteration_number-1)),
				_MaskFileName,
				_DoSphericalMask,
				_MaskRadius,
				_iteration_number,
				os.path.join("../Iter_%d" % (_iteration_number), "Iter_%d_reference_volume.vol" % (_iteration_number)))
		else: 
			print "skipped masking, no reconstructed volume"

		if _DoReconstruction is False and (_iteration_number > 1):
			shutil.move(os.path.join("../Iter_%d" % (_iteration_number-1), "Iter_%d_reference_volume.vol" % (_iteration_number-1)), \
			os.path.join("../Iter_%d" % (_iteration_number), "Iter_%d_reference_volume.vol" % (_iteration_number))) 

		# Parameters for projection matching
		_AngSamplingRateDeg=arg.getComponentFromVector(_AngSamplingRateDeg, _iteration_number-1)
		_MaxChangeOffset=arg.getComponentFromVector(_MaxChangeOffset, _iteration_number-1)
		_MaxChangeInAngles=arg.getComponentFromVector(_MaxChangeInAngles, _iteration_number-1)
		_Search5DShift=arg.getComponentFromVector(_Search5DShift, _iteration_number-1)
		_Search5DStep=arg.getComponentFromVector(_Search5DStep, _iteration_number-1)
		_MinimumCrossCorrelation=arg.getComponentFromVector(_MinimumCrossCorrelation, _iteration_number-1)
		_DiscardPercentage=arg.getComponentFromVector(_DiscardPercentage, _iteration_number-1)

		execute_projection_matching(_mylog,
								 _ProjectDir,
								 _ReferenceVolume[_iteration_number],
								 _MaskFileName,
								 _DocFileInputAngles[_iteration_number],
								 _DocFileInputAngles[_iteration_number+1],
								 _AngSamplingRateDeg,
								 _InnerRadius,
								 _OuterRadius,
								 _Search5DShift,
								 _Search5DStep,
								 _MaxChangeOffset, 
								 _MaxChangeInAngles,
								 _MinimumCrossCorrelation,
								 _DiscardPercentage,
								 _DoParallel,
								 _MyNumberOfMpiProcesses,
								 _MyNumberOfThreads,
								 _MySystemFlavour,
								 _MyMpiJobSize,
								 _WorkingDir,
								 _SymmetryGroup,
								 _AvailableMemory,
								 _iteration_number,
								 _ProjectLibraryRootName,
								 _ProjMatchRootName
								 )

		if _DoReconstruction is True:
			execute_reconstruction(_mylog, 
								_SelFileName,
								_iteration_number,
								_DoParallel,
								_MyNumberOfMpiProcesses,
								_MyNumberOfThreads,
								_MySystemFlavour,
								_MyMpiJobSize,
								globalFourierMaxFrequencyOfInterest,
								_SymmetryGroup,
								_ReconstructedVolume[_iteration_number],
								_PaddingFactor
								)
		else: 
			print "skipped reconstruction"	

		_ConstantToAddToFiltration=arg.getComponentFromVector(_ConstantToAddToFiltration, _iteration_number-1)

		# Remove all class averages and reference projections
		if (_CleanUpFiles):
			execute_cleanup(_mylog, True, True, _ProjMatchDir, _LibraryDir)

#------------------------------------------------------------------------
# delete_working directory
#------------------------------------------------------------------------
def delete_working_directory(_mylog, _WorkingDir):
    import os
    import shutil
    print '*********************************************************************'
    print '* Delete working directory tree'
    _mylog.info("Delete working directory tree")

    if os.path.exists(_WorkingDir):
       shutil.rmtree(_WorkingDir)
       
#------------------------------------------------------------------------
# create_working directory
#------------------------------------------------------------------------
def create_working_directory(_mylog, _WorkingDir, _ProjMatchDir, _LibraryDir):
    import os
    print '*********************************************************************'
    print '* Create directory ' + _WorkingDir 
    _mylog.info("Create working directory " + _WorkingDir )

    if not os.path.exists(_WorkingDir):
       os.makedirs(_WorkingDir)
    # Also create subdirectories
    if not os.path.exists(_WorkingDir + "/" + _LibraryDir):
       os.makedirs(_WorkingDir + "/" + _LibraryDir)
    if not os.path.exists(_WorkingDir + "/" + _ProjMatchDir):
       os.makedirs(_WorkingDir + "/" + _ProjMatchDir)


#------------------------------------------------------------------------
# execute_mask
#------------------------------------------------------------------------
def execute_mask(_DoMask,
                 _mylog,
                 _ProjectDir,
                 _ReferenceFileName,
                 _MaskFileName,
                 _DoSphericalMask,
                 _MaskRadius,
                 _iteration_number,
                 _ReferenceVolume):
	import os,shutil
	import launch_job
	_mylog.debug("execute_mask")
	if(_iteration_number==1):
		InPutVolume=_ReferenceFileName
	else:   
		InPutVolume=_ReferenceFileName+".vol"
	if (_DoMask):
		MaskedVolume=_ReferenceVolume
		print '*********************************************************************'
		print '* Mask the reference volume'
		if (_DoSphericalMask):
			command=' -i '    + InPutVolume + \
				' -o '    + _ReferenceVolume + \
				' -mask circular -' + str(_MaskRadius)
		else:
			command=' -i '    + InPutVolume + \
				' -o '    + _ReferenceVolume + \
				' -mask ' + _MaskFileName
		launch_job.launch_job("xmipp_mask",
					command,
					_mylog,
					False,1,1,'')

	else:
		shutil.copy(InPutVolume,_ReferenceVolume)
		_mylog.info("Skipped Mask")
		_mylog.info("cp" + InPutVolume +\
				   " "  + _ReferenceVolume )
		print '*********************************************************************'
		print '* Skipped Mask'

#------------------------------------------------------------------------
# execute_projection_matching
#------------------------------------------------------------------------
def execute_projection_matching(_mylog,
                                _ProjectDir,
                                _ReferenceVolume,
                                _MaskFileName,
                                _InputDocFileName,
                                _OutputDocFileName,
                                _AngSamplingRateDeg,
                                _Ri,
                                _Ro,
                                _Search5DShift,
                                _Search5DStep,
                                _MaxChangeOffset,
                                _MaxChangeInAngles,
                                _MinimumCrossCorrelation,
                                _DiscardPercentage,
                                _DoParallel,
                                _MyNumberOfMpiProcesses,
                                _MyNumberOfThreads,
                                _MySystemFlavour,
                                _MyMpiJobSize,
                                _WorkingDir,
                                _SymmetryGroup,
                                _AvailableMemory,
                                _iteration_number, 
								_ProjectLibraryRootName,
								_ProjMatchRootName 
								):
                                           
	_mylog.debug("execute_projection_matching")
	import os, shutil, string, glob, math
	import launch_job, selfile, docfiles, utils_xmipp
	  
	# Project all references
	print '*********************************************************************'
	print '* Create projection library'
	parameters=' -i '                   + _ReferenceVolume + \
				' -experimental_images ' +  _InputDocFileName + \
				' -o '                   + _ProjectLibraryRootName + \
				' -sampling_rate '       + _AngSamplingRateDeg  + \
				' -sym '                 + _SymmetryGroup + 'h' + \
				' -compute_neighbors '

	if ( string.atof(_MaxChangeInAngles) < 181.):
		parameters+= \
			' -near_exp_data -angular_distance '    + str(_MaxChangeInAngles)
	else:
		parameters+= \
			' -angular_distance -1'

	if (_DoParallel):
		parameters = parameters + ' -mpi_job_size ' + str(_MyMpiJobSize)

	launch_job.launch_job('xmipp_angular_project_library',
					parameters,
					_mylog,
					_DoParallel,
					_MyNumberOfMpiProcesses*_MyNumberOfThreads,
					1,
					_MySystemFlavour)

	outputname   = _ProjMatchRootName
	inputdocfile = _InputDocFileName

	print '*********************************************************************'
	print '* Perform projection matching'
	
	parameters= ' -i '              + inputdocfile + \
				' -o '              + outputname + \
				' -ref '            + _ProjectLibraryRootName + \
				' -Ri '             + str(_Ri)           + \
				' -Ro '             + str(_Ro)           + \
				' -max_shift '      + str(_MaxChangeOffset) + \
				' -search5d_shift ' + str(_Search5DShift) + \
				' -search5d_step  ' + str(_Search5DStep) + \
				' -mem '            + str(_AvailableMemory * _MyNumberOfThreads) + \
				' -thr '            + str(_MyNumberOfThreads) + \
				' -sym '            + _SymmetryGroup + 'h'

	if (_DoParallel):
		parameters = parameters + ' -mpi_job_size ' + str(_MyMpiJobSize)

	launch_job.launch_job('xmipp_angular_projection_matching',
					parameters,
					_mylog,
					_DoParallel,
					_MyNumberOfMpiProcesses,
					_MyNumberOfThreads,
					_MySystemFlavour)
	outputdocfile =  _ProjMatchRootName + '.doc'

	# Move outputdocfile to standard name
	shutil.move(outputdocfile, _OutputDocFileName)

#------------------------------------------------------------------------
# execute_reconstruction
#------------------------------------------------------------------------

def execute_reconstruction(_mylog,
							_SelFileName,
							_iteration_number,
							_DoParallel,
							_MyNumberOfMpiProcesses,
							_MyNumberOfThreads,
							_MySystemFlavour,
							_MyMpiJobSize,
							_FourierMaxFrequencyOfInterest,
							_SymmetryGroup,
							_ReconstructedandfilteredVolume,
							_PaddingFactor):

	_mylog.debug("execute_reconstruction")

	import os,shutil,math
	import launch_job

	Outputvolume = _ReconstructedandfilteredVolume

	if ( _MyNumberOfMpiProcesses ==1):
		_DoParallel=False
	program = 'xmipp_reconstruct_fourier'
	parameters=' -i '    + _SelFileName + \
		' -o '    + Outputvolume + '.vol ' + \
		' -sym '  + _SymmetryGroup + \
		' -doc '  + "Iter_%d_current_angles.doc" % _iteration_number + \
		' -thr '  + str(_MyNumberOfThreads) + \
		' -max_resolution ' + str(_FourierMaxFrequencyOfInterest) +\
		' -pad_proj ' + str(_PaddingFactor) +\
		' -pad_vol ' + str(_PaddingFactor)
	if (_DoParallel):
		parameters = parameters + ' -mpi_job_size ' + str(_MyMpiJobSize)

	launch_job.launch_job(program, parameters, _mylog, _DoParallel, _MyNumberOfMpiProcesses, _MyNumberOfThreads, _MySystemFlavour)

#------------------------------------------------------------------------
# Miscellaneous
#------------------------------------------------------------------------

def execute_cleanup(_mylog,
                    _DeleteClassAverages,
                    _DeleteReferenceProjections,
					_ProjMatchDir,
					_LibraryDir):
   import os,glob
   import utils_xmipp
   
   if (_DeleteClassAverages):
      message=' CleanUp: deleting directory '+ _ProjMatchDir
      print '* ',message
      _mylog.info(message)
      os.system(' rm -r ' + _ProjMatchDir + ' &')

   if (_DeleteReferenceProjections):
      message=' CleanUp: deleting directory '+ _LibraryDir
      print '* ',message
      _mylog.info(message)
      os.system(' rm -r ' + _LibraryDir + ' &')

def  fill_name_vector(_user_suplied_name,
                      _volume_name_list,
                      _NumberofIterations,
                      _root_name):
     _volume_name_list.append("dummy")
     if (len(_user_suplied_name)>1):
        _volume_name_list.append(_user_suplied_name)
     for _iteration_number in range(1, _NumberofIterations):
         _volume_name_list.append("../"+'Iter_'+\
                                   str(_iteration_number)+'/'+ 'Iter_'+\
                                   str(_iteration_number)+'_'+\
                                   _root_name)
                  
def check_file_exists(name,log):
    import os,sys
    if not os.path.exists(name):
        message='Error: File '+name+' does not exist, exiting...'
        print '*',message
        log.error(message)
        sys.exit()

#------------------------------------------------------------------------
# main
#------------------------------------------------------------------------

if __name__ == '__main__':
	
	### test parameters
	SelFileName = "partlist.sel"
	ReferenceFileName = "3d1_ordered1_filt.vol"
	WorkingDir = "refine_3d1"
	ProjectDir = "/ami/data17/appion/11jan08a/angrecon/bar_rib/angular_reconstitution/"
	MaskRadius = 32
	InnerRadius = 0
	OuterRadius = 26
	AvailableMemory = '2gb'
	ResolSam = 5.48
	NumberOfMpiProcesses = 32

	projection_matching_protocol_basic(
				SelFileName,
				ReferenceFileName,
				WorkingDir,
				ProjectDir,
				MaskRadius,
				InnerRadius,
				OuterRadius,
				AvailableMemory,
				ResolSam,
				NumberOfMpiProcesses,
				_NumberofIterations=2
		)
