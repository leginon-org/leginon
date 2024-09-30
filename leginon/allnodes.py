'''
This module keeps track of all classes of Leginon Nodes.  Here you must
import your node class and then register it with the noderegistry module.
The order in this module determines the sort order for how the nodes
appear when applications start.
'''
from leginon import noderegistry

##############################
# Priority
##############################
classtype = 'Priority'
from leginon.presets import PresetsManager
noderegistry.registerNodeClass(PresetsManager,classtype)

##############################
# Pipeline
##############################
classtype = 'Pipeline'
from leginon.gridentry import GridEntry
noderegistry.registerNodeClass(GridEntry,classtype)

from leginon.plategridentry import PlateGridEntry
noderegistry.registerNodeClass(PlateGridEntry,classtype)

from leginon.targetmaker import MosaicTargetMaker
noderegistry.registerNodeClass(MosaicTargetMaker,classtype)

from leginon.rastertargetfilter import RasterTargetFilter
noderegistry.registerNodeClass(RasterTargetFilter,classtype)

from leginon.imageprocessorexample import FileNames
noderegistry.registerNodeClass(FileNames,classtype)

from leginon.regionfinder import RegionFinder
noderegistry.registerNodeClass(RegionFinder,classtype)

from leginon.imageprocessor import ImageProcessor
noderegistry.registerNodeClass(ImageProcessor,classtype)

from leginon.holefinder import HoleFinder
noderegistry.registerNodeClass(HoleFinder,classtype)

from leginon.rasterfinder import RasterFinder
noderegistry.registerNodeClass(RasterFinder,classtype)

from leginon.rasterfcfinder import RasterFCFinder
noderegistry.registerNodeClass(RasterFCFinder,classtype)

from leginon.stigacquisition import StigAcquisition
noderegistry.registerNodeClass(StigAcquisition,classtype)

from leginon.raptorprocessor import RaptorProcessor
noderegistry.registerNodeClass(RaptorProcessor,classtype)

from leginon.matlabtargetfinder import MatlabTargetFinder
noderegistry.registerNodeClass(MatlabTargetFinder,classtype)

from leginon.stitchtargetfinder import StitchTargetFinder
noderegistry.registerNodeClass(StitchTargetFinder,classtype)

from leginon.testtargetfinder import TestTargetFinder
noderegistry.registerNodeClass(TestTargetFinder,classtype)

from leginon.dtfinder import DTFinder
noderegistry.registerNodeClass(DTFinder,classtype)

from leginon.mosaictargetfinder import MosaicClickTargetFinder
noderegistry.registerNodeClass(MosaicClickTargetFinder,classtype)

from leginon.mosaicexternalfinder import MosaicScoreTargetFinder
noderegistry.registerNodeClass(MosaicScoreTargetFinder,classtype)

from leginon.mosaiclearnfinder import MosaicLearnTargetFinder
noderegistry.registerNodeClass(MosaicLearnTargetFinder,classtype)

from leginon.mosaicquiltfinder import MosaicQuiltFinder
noderegistry.registerNodeClass(MosaicQuiltFinder,classtype)

from leginon.mosaicsectionfinder import MosaicSectionFinder
noderegistry.registerNodeClass(MosaicSectionFinder,classtype)

from leginon.mosaicspotfinder import MosaicSpotFinder
noderegistry.registerNodeClass(MosaicSpotFinder,classtype)

from leginon.robotatlastargetfinder import RobotAtlasTargetFinder
noderegistry.registerNodeClass(RobotAtlasTargetFinder,classtype)

from leginon.centertargetfilter import CenterTargetFilter
noderegistry.registerNodeClass(CenterTargetFilter,classtype)

from leginon.tiltrotate import TiltRotateRepeater
noderegistry.registerNodeClass(TiltRotateRepeater,classtype)

from leginon.robot import Robot
noderegistry.registerNodeClass(Robot,classtype)

# TargetFinder is registered for setting validataion only
from leginon.targetfinder import TargetFinder
noderegistry.registerNodeClass(TargetFinder,classtype)

from leginon.targetfinder import ClickTargetFinder
noderegistry.registerNodeClass(ClickTargetFinder,classtype)

from leginon.tomotargetfinder import TomoClickTargetFinder
noderegistry.registerNodeClass(TomoClickTargetFinder,classtype)

from leginon.tomography.tomography import Tomography
noderegistry.registerNodeClass(Tomography,classtype)

from leginon.tomography.tomography2 import Tomography2
noderegistry.registerNodeClass(Tomography2,classtype)

from leginon.batchacquisition import BatchAcquisition
noderegistry.registerNodeClass(BatchAcquisition,classtype)

from leginon.acq import Acquisition
noderegistry.registerNodeClass(Acquisition,classtype)

from leginon.focuser import Focuser
noderegistry.registerNodeClass(Focuser,classtype)

from leginon.singlefocuser import SingleFocuser
noderegistry.registerNodeClass(SingleFocuser,classtype)

from leginon.diffrfocuser import DiffrFocuser
noderegistry.registerNodeClass(DiffrFocuser,classtype)

from leginon.rctacquisition import RCTAcquisition
noderegistry.registerNodeClass(RCTAcquisition,classtype)

from leginon.phaseplatetester import PhasePlateTestImager
noderegistry.registerNodeClass(PhasePlateTestImager,classtype)

from leginon.phaseplatetester import PhasePlateTester
noderegistry.registerNodeClass(PhasePlateTester,classtype)

from leginon.tilttracker import TiltTracker
noderegistry.registerNodeClass(TiltTracker,classtype)

from leginon.tomography.tomographysimu import TomographySimu
noderegistry.registerNodeClass(TomographySimu,classtype)

from leginon.beamtiltimager import BeamTiltImager
noderegistry.registerNodeClass(BeamTiltImager,classtype)

from leginon.beamtiltfixer import BeamTiltFixer
noderegistry.registerNodeClass(BeamTiltFixer,classtype)

from leginon.robot2 import Robot2
noderegistry.registerNodeClass(Robot2,classtype)

from leginon.sampletargetfilter import SampleTargetFilter
noderegistry.registerNodeClass(SampleTargetFilter,classtype)

from leginon.jahcfinder import JAHCFinder
noderegistry.registerNodeClass(JAHCFinder,classtype)

from leginon.scorefinder import ScoreTargetFinder
noderegistry.registerNodeClass(ScoreTargetFinder,classtype)

from leginon.extholefinder import ExtHoleFinder
noderegistry.registerNodeClass(ExtHoleFinder,classtype)

from leginon.ptolemyfinder import PtolemyMmTargetFinder
noderegistry.registerNodeClass(PtolemyMmTargetFinder,classtype)

from leginon.dogfinder import DoGFinder
noderegistry.registerNodeClass(DoGFinder,classtype)

from leginon.atlastargetmaker import AtlasTargetMaker
noderegistry.registerNodeClass(AtlasTargetMaker,classtype)

from leginon.fftace import CTFAnalyzer
noderegistry.registerNodeClass(CTFAnalyzer,classtype)

from leginon.holedepth import HoleDepth
noderegistry.registerNodeClass(HoleDepth,classtype)

from leginon.fftmaker import FFTMaker
noderegistry.registerNodeClass(FFTMaker,classtype)

from leginon.autoexposure import AutoExposure
noderegistry.registerNodeClass(AutoExposure,classtype)

from leginon.baker import Baker
noderegistry.registerNodeClass(Baker,classtype)

from leginon.movealphaacquisition import MoveAlphaAcquisition
noderegistry.registerNodeClass(MoveAlphaAcquisition,classtype)

from leginon.movexyacquisition import MoveXYAcquisition
noderegistry.registerNodeClass(MoveXYAcquisition,classtype)

from leginon.tiltlistalternater import TiltListAlternater
noderegistry.registerNodeClass(TiltListAlternater,classtype)

from leginon.tiltalternater import TiltAlternater
noderegistry.registerNodeClass(TiltAlternater,classtype)

from leginon.defocussequence import DefocusSequence
noderegistry.registerNodeClass(DefocusSequence,classtype)

##############################
# Calibrations
##############################
classtype = 'Calibrations'
from leginon.magcalibrator import MagCalibrator
noderegistry.registerNodeClass(MagCalibrator,classtype)

from leginon.gonmodeler import GonModeler
noderegistry.registerNodeClass(GonModeler,classtype)

from leginon.matrixcalibrator import MatrixCalibrator
noderegistry.registerNodeClass(MatrixCalibrator,classtype)

from leginon.imagebeamcalibrator import ImageBeamCalibrator
noderegistry.registerNodeClass(ImageBeamCalibrator,classtype)

from leginon.beamtiltcalibrator import BeamTiltCalibrator
noderegistry.registerNodeClass(BeamTiltCalibrator,classtype)

from leginon.pixelsizecalibrator import PixelSizeCalibrator
noderegistry.registerNodeClass(PixelSizeCalibrator,classtype)

from leginon.cameralengthcalibrator import CameraLengthCalibrator
noderegistry.registerNodeClass(CameraLengthCalibrator,classtype)

from leginon.scalerotationcalibrator import ScaleRotationCalibrator
noderegistry.registerNodeClass(ScaleRotationCalibrator,classtype)

from leginon.dosecalibrator import DoseCalibrator
noderegistry.registerNodeClass(DoseCalibrator,classtype)

from leginon.beamsizecalibrator import BeamSizeCalibrator
noderegistry.registerNodeClass(BeamSizeCalibrator,classtype)

##############################
# Utility
##############################
classtype = 'Utility'
from leginon.clicktargettransformer import ClickTargetTransformer
noderegistry.registerNodeClass(ClickTargetTransformer,classtype)

from leginon.driftmanager import DriftManager
noderegistry.registerNodeClass(DriftManager,classtype)

from leginon.referencetimer import ReferenceTimer
noderegistry.registerNodeClass(ReferenceTimer,classtype)

from leginon.referencetimer import AlignZeroLossPeak
noderegistry.registerNodeClass(AlignZeroLossPeak,classtype)

from leginon.referencetimer import MeasureDose
noderegistry.registerNodeClass(MeasureDose,classtype)

from leginon.EM import EM
noderegistry.registerNodeClass(EM,classtype)

from leginon.alignmentmanager import AlignmentManager
noderegistry.registerNodeClass(AlignmentManager,classtype)

from leginon.conditioner import Conditioner
noderegistry.registerNodeClass(Conditioner,classtype)

from leginon.buffercycler import BufferCycler
noderegistry.registerNodeClass(BufferCycler,classtype)

from leginon.conditioner import AutoNitrogenFiller
noderegistry.registerNodeClass(AutoNitrogenFiller,classtype)

from leginon.cfegconditioner import ColdFegFlasher
noderegistry.registerNodeClass(ColdFegFlasher,classtype)

from leginon.phaseplatealigner import PhasePlateAligner
noderegistry.registerNodeClass(PhasePlateAligner,classtype)

from leginon.screencurrentlogger import ScreenCurrentLogger
noderegistry.registerNodeClass(ScreenCurrentLogger,classtype)

from leginon.maskassessor import MaskAssessor
noderegistry.registerNodeClass(MaskAssessor,classtype)

from leginon.beamfixer import BeamFixer
noderegistry.registerNodeClass(BeamFixer,classtype)

from leginon.exposurefixer import ExposureFixer
noderegistry.registerNodeClass(ExposureFixer,classtype)

from leginon.intensitymonitor import IntensityMonitor
noderegistry.registerNodeClass(IntensityMonitor,classtype)

from leginon.manualacquisition import ManualAcquisition
noderegistry.registerNodeClass(ManualAcquisition,classtype)

from leginon.corrector import Corrector
noderegistry.registerNodeClass(Corrector,classtype)

from leginon.transformmanager import TransformManager
noderegistry.registerNodeClass(TransformManager,classtype)

from leginon.manualimageloader import ManualImageLoader
noderegistry.registerNodeClass(ManualImageLoader,classtype)

from leginon.clickmaskmaker import ClickMaskMaker
noderegistry.registerNodeClass(ClickMaskMaker,classtype)

from leginon.imageassessor import ImageAssessor
noderegistry.registerNodeClass(ImageAssessor,classtype)

from leginon.temcontroller import TEMController
noderegistry.registerNodeClass(TEMController,classtype)

from leginon.icethicknessEF import IcethicknessEF
noderegistry.registerNodeClass(IcethicknessEF,classtype)

from leginon.blackstripedetector import BlackStripeDetector
noderegistry.registerNodeClass(BlackStripeDetector,classtype)
##############################
# Finale
##############################
classtype = 'Finale'
from leginon.navigator import Navigator
noderegistry.registerNodeClass(Navigator,classtype)


