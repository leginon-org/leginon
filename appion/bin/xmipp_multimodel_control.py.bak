#!/usr/bin/env python
#



import xmipp_protocol_multimodel_for_remote_control

#===============================================================================
# set variables
#===============================================================================

xmipp_protocol_multimodel_for_remote_control.SelFileName='partlist.doc'
xmipp_protocol_multimodel_for_remote_control.DocFileName=''
xmipp_protocol_multimodel_for_remote_control.ReferenceFileName='volume'
xmipp_protocol_multimodel_for_remote_control.WorkingDir='MultiModel/run1'
xmipp_protocol_multimodel_for_remote_control.DoDeleteWorkingDir=True
xmipp_protocol_multimodel_for_remote_control.NumberofIterations=10
xmipp_protocol_multimodel_for_remote_control.ContinueAtIteration=1
xmipp_protocol_multimodel_for_remote_control.CleanUpFiles=False
xmipp_protocol_multimodel_for_remote_control.ProjectDir='/ami/data00/appion/10aug27a/full-end-stack/arne-multimodel/groel'
xmipp_protocol_multimodel_for_remote_control.LogDir='Logs'
xmipp_protocol_multimodel_for_remote_control.ModelNumbers=2
xmipp_protocol_multimodel_for_remote_control.DoCtfCorrection=False
xmipp_protocol_multimodel_for_remote_control.CTFDatName='all_images.ctfdat'
xmipp_protocol_multimodel_for_remote_control.DoAutoCtfGroup=True
xmipp_protocol_multimodel_for_remote_control.CtfGroupMaxDiff=0.5
xmipp_protocol_multimodel_for_remote_control.CtfGroupMaxResol=15
xmipp_protocol_multimodel_for_remote_control.SplitDefocusDocFile=''
xmipp_protocol_multimodel_for_remote_control.PaddingFactor=1
xmipp_protocol_multimodel_for_remote_control.WienerConstant=-1
xmipp_protocol_multimodel_for_remote_control.DataArePhaseFlipped=True
xmipp_protocol_multimodel_for_remote_control.ReferenceIsCtfCorrected=True
xmipp_protocol_multimodel_for_remote_control.DoMask=False                        
xmipp_protocol_multimodel_for_remote_control.DoSphericalMask=False
xmipp_protocol_multimodel_for_remote_control.MaskRadius=32
xmipp_protocol_multimodel_for_remote_control.MaskFileName='mask.vol'
xmipp_protocol_multimodel_for_remote_control.DoProjectionMatching=True
xmipp_protocol_multimodel_for_remote_control.DisplayProjectionMatching=False
xmipp_protocol_multimodel_for_remote_control.InnerRadius=0
xmipp_protocol_multimodel_for_remote_control.OuterRadius=64
xmipp_protocol_multimodel_for_remote_control.AvailableMemory=2
xmipp_protocol_multimodel_for_remote_control.AngSamplingRateDeg='4x30 2x15 2x10 2x3 2x2'
xmipp_protocol_multimodel_for_remote_control.MaxChangeInAngles='4x1000 2x20 2x9 2x6'
xmipp_protocol_multimodel_for_remote_control.PerturbProjectionDirections=False
xmipp_protocol_multimodel_for_remote_control.MaxChangeOffset='1000 '
xmipp_protocol_multimodel_for_remote_control.Search5DShift='4x5 0'
xmipp_protocol_multimodel_for_remote_control.Search5DStep='2'
xmipp_protocol_multimodel_for_remote_control.DoRetricSearchbyTiltAngle=False
xmipp_protocol_multimodel_for_remote_control.Tilt0=40
xmipp_protocol_multimodel_for_remote_control.TiltF=90
xmipp_protocol_multimodel_for_remote_control.SymmetryGroup='c7'
xmipp_protocol_multimodel_for_remote_control.SymmetryGroupNeighbourhood=''
xmipp_protocol_multimodel_for_remote_control.OnlyWinner=False
xmipp_protocol_multimodel_for_remote_control.MinimumCrossCorrelation='-1'
xmipp_protocol_multimodel_for_remote_control.DiscardPercentage='10'
xmipp_protocol_multimodel_for_remote_control.ProjMatchingExtra=''
xmipp_protocol_multimodel_for_remote_control.DoAlign2D='0'
xmipp_protocol_multimodel_for_remote_control.Align2DIterNr=4
xmipp_protocol_multimodel_for_remote_control.Align2dMaxChangeOffset='2x1000 2x10'
xmipp_protocol_multimodel_for_remote_control.Align2dMaxChangeRot='2x1000 2x20'
xmipp_protocol_multimodel_for_remote_control.DoReconstruction=True
xmipp_protocol_multimodel_for_remote_control.DisplayReconstruction=False
xmipp_protocol_multimodel_for_remote_control.ReconstructionMethod='fourier'
xmipp_protocol_multimodel_for_remote_control.ARTLambda='0.2'
xmipp_protocol_multimodel_for_remote_control.ARTReconstructionExtraCommand='-k 0.5 -n 10 '
xmipp_protocol_multimodel_for_remote_control.FourierMaxFrequencyOfInterest='0.25'
xmipp_protocol_multimodel_for_remote_control.WBPReconstructionExtraCommand=' '
xmipp_protocol_multimodel_for_remote_control.FourierReconstructionExtraCommand=' '
xmipp_protocol_multimodel_for_remote_control.DoComputeResolution=True
xmipp_protocol_multimodel_for_remote_control.DoSplitReferenceImages=True
xmipp_protocol_multimodel_for_remote_control.ResolSam=9.6
xmipp_protocol_multimodel_for_remote_control.DisplayResolution=False
xmipp_protocol_multimodel_for_remote_control.DoLowPassFilter=True
xmipp_protocol_multimodel_for_remote_control.UseFscForFilter=True
xmipp_protocol_multimodel_for_remote_control.ConstantToAddToFiltration='0.1'
xmipp_protocol_multimodel_for_remote_control.NumberOfThreads=1
xmipp_protocol_multimodel_for_remote_control.DoParallel=False
xmipp_protocol_multimodel_for_remote_control.NumberOfMpiProcesses=5
xmipp_protocol_multimodel_for_remote_control.MpiJobSize='10'
xmipp_protocol_multimodel_for_remote_control.SystemFlavour=''
xmipp_protocol_multimodel_for_remote_control.AnalysisScript='visualize_projmatch.py'























my_projmatch=xmipp_protocol_multimodel_for_remote_control.projection_matching_class(
                                                                                    xmipp_protocol_multimodel_for_remote_control.NumberofIterations,     
                xmipp_protocol_multimodel_for_remote_control.ContinueAtIteration,  
                xmipp_protocol_multimodel_for_remote_control.CleanUpFiles,
                xmipp_protocol_multimodel_for_remote_control.DoMask,
                xmipp_protocol_multimodel_for_remote_control.ModelNumbers,   
                xmipp_protocol_multimodel_for_remote_control.DoSphericalMask,
                xmipp_protocol_multimodel_for_remote_control.MaskRadius,
                xmipp_protocol_multimodel_for_remote_control.ReferenceFileName,              
                xmipp_protocol_multimodel_for_remote_control.MaskFileName,                   
                xmipp_protocol_multimodel_for_remote_control.DoProjectionMatching,           
                xmipp_protocol_multimodel_for_remote_control.DisplayProjectionMatching,      
                xmipp_protocol_multimodel_for_remote_control.AngSamplingRateDeg,             
                xmipp_protocol_multimodel_for_remote_control.PerturbProjectionDirections,
                xmipp_protocol_multimodel_for_remote_control.DoRetricSearchbyTiltAngle,      
                xmipp_protocol_multimodel_for_remote_control.Tilt0,                          
                xmipp_protocol_multimodel_for_remote_control.TiltF,                          
                xmipp_protocol_multimodel_for_remote_control.ProjMatchingExtra,              
                xmipp_protocol_multimodel_for_remote_control.MaxChangeOffset,
                xmipp_protocol_multimodel_for_remote_control.MaxChangeInAngles,
                xmipp_protocol_multimodel_for_remote_control.MinimumCrossCorrelation,
                xmipp_protocol_multimodel_for_remote_control.DiscardPercentage,
                xmipp_protocol_multimodel_for_remote_control.DoAlign2D,                      
                xmipp_protocol_multimodel_for_remote_control.InnerRadius,                    
                xmipp_protocol_multimodel_for_remote_control.OuterRadius,                    
                xmipp_protocol_multimodel_for_remote_control.Search5DShift,
                xmipp_protocol_multimodel_for_remote_control.Search5DStep,
                xmipp_protocol_multimodel_for_remote_control.AvailableMemory,
                xmipp_protocol_multimodel_for_remote_control.Align2DIterNr,                  
                xmipp_protocol_multimodel_for_remote_control.Align2dMaxChangeOffset,
                xmipp_protocol_multimodel_for_remote_control.Align2dMaxChangeRot,            
                xmipp_protocol_multimodel_for_remote_control.DisplayReconstruction,
                xmipp_protocol_multimodel_for_remote_control.DisplayResolution,          
                xmipp_protocol_multimodel_for_remote_control.DoReconstruction,
                xmipp_protocol_multimodel_for_remote_control.ReconstructionMethod,
                xmipp_protocol_multimodel_for_remote_control.ARTLambda,
                xmipp_protocol_multimodel_for_remote_control.ARTReconstructionExtraCommand,
                xmipp_protocol_multimodel_for_remote_control.WBPReconstructionExtraCommand,
                xmipp_protocol_multimodel_for_remote_control.FourierReconstructionExtraCommand,
                xmipp_protocol_multimodel_for_remote_control.FourierMaxFrequencyOfInterest,
                xmipp_protocol_multimodel_for_remote_control.DoComputeResolution,
                xmipp_protocol_multimodel_for_remote_control.DoSplitReferenceImages,
                xmipp_protocol_multimodel_for_remote_control.ResolSam,
                xmipp_protocol_multimodel_for_remote_control.SelFileName,                    
                xmipp_protocol_multimodel_for_remote_control.DocFileName,                    
                xmipp_protocol_multimodel_for_remote_control.DoCtfCorrection,
                xmipp_protocol_multimodel_for_remote_control.CTFDatName,
                xmipp_protocol_multimodel_for_remote_control.WienerConstant,
                xmipp_protocol_multimodel_for_remote_control.DoAutoCtfGroup,
                xmipp_protocol_multimodel_for_remote_control.CtfGroupMaxDiff,
                xmipp_protocol_multimodel_for_remote_control.CtfGroupMaxResol,
                xmipp_protocol_multimodel_for_remote_control.SplitDefocusDocFile,
                xmipp_protocol_multimodel_for_remote_control.PaddingFactor,
                xmipp_protocol_multimodel_for_remote_control.DataArePhaseFlipped,
                xmipp_protocol_multimodel_for_remote_control.ReferenceIsCtfCorrected,
                xmipp_protocol_multimodel_for_remote_control.WorkingDir,                  
                xmipp_protocol_multimodel_for_remote_control.ProjectDir,                     
                xmipp_protocol_multimodel_for_remote_control.LogDir,                         
                xmipp_protocol_multimodel_for_remote_control.DoParallel,                     
                xmipp_protocol_multimodel_for_remote_control.NumberOfMpiProcesses,                   
                xmipp_protocol_multimodel_for_remote_control.SystemFlavour,
                xmipp_protocol_multimodel_for_remote_control.MpiJobSize,
                xmipp_protocol_multimodel_for_remote_control.NumberOfThreads,
                xmipp_protocol_multimodel_for_remote_control.SymmetryGroup,  
                xmipp_protocol_multimodel_for_remote_control.SymmetryGroupNeighbourhood,
                xmipp_protocol_multimodel_for_remote_control.OnlyWinner,
                xmipp_protocol_multimodel_for_remote_control.DoLowPassFilter,
                xmipp_protocol_multimodel_for_remote_control.UseFscForFilter,
                xmipp_protocol_multimodel_for_remote_control.ConstantToAddToFiltration
                )