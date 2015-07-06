'''
This module keeps track of all classes of Leginon Nodes.  Here you must
import your node class and then register it with the noderegistry module.
The order in this module determines the sort order for how the nodes
appear when applications start.
'''
import noderegistry

##############################
# Priority
##############################
classtype = 'Priority'
from presets import PresetsManager
noderegistry.registerNodeClass(PresetsManager,classtype)

##############################
# Pipeline
##############################
classtype = 'Pipeline'
from gridentry import GridEntry
noderegistry.registerNodeClass(GridEntry,classtype)

from plategridentry import PlateGridEntry
noderegistry.registerNodeClass(PlateGridEntry,classtype)

from targetmaker import MosaicTargetMaker
noderegistry.registerNodeClass(MosaicTargetMaker,classtype)

from rastertargetfilter import RasterTargetFilter
noderegistry.registerNodeClass(RasterTargetFilter,classtype)

from imageprocessorexample import FileNames
noderegistry.registerNodeClass(FileNames,classtype)

from regionfinder import RegionFinder
noderegistry.registerNodeClass(RegionFinder,classtype)

from imageprocessor import ImageProcessor
noderegistry.registerNodeClass(ImageProcessor,classtype)

from holefinder import HoleFinder
noderegistry.registerNodeClass(HoleFinder,classtype)

from rasterfinder import RasterFinder
noderegistry.registerNodeClass(RasterFinder,classtype)

from rasterfcfinder import RasterFCFinder
noderegistry.registerNodeClass(RasterFCFinder,classtype)

from stigacquisition import StigAcquisition
noderegistry.registerNodeClass(StigAcquisition,classtype)

from raptorprocessor import RaptorProcessor
noderegistry.registerNodeClass(RaptorProcessor,classtype)

from matlabtargetfinder import MatlabTargetFinder
noderegistry.registerNodeClass(MatlabTargetFinder,classtype)

from testtargetfinder import TestTargetFinder
noderegistry.registerNodeClass(TestTargetFinder,classtype)

from dtfinder import DTFinder
noderegistry.registerNodeClass(DTFinder,classtype)

from mosaictargetfinder import MosaicClickTargetFinder
noderegistry.registerNodeClass(MosaicClickTargetFinder,classtype)

from mosaicsectionfinder import MosaicSectionFinder
noderegistry.registerNodeClass(MosaicSectionFinder,classtype)

from mosaicspotfinder import MosaicSpotFinder
noderegistry.registerNodeClass(MosaicSpotFinder,classtype)

from robotatlastargetfinder import RobotAtlasTargetFinder
noderegistry.registerNodeClass(RobotAtlasTargetFinder,classtype)

from centertargetfilter import CenterTargetFilter
noderegistry.registerNodeClass(CenterTargetFilter,classtype)

from tiltrotate import TiltRotateRepeater
noderegistry.registerNodeClass(TiltRotateRepeater,classtype)

from robot import Robot
noderegistry.registerNodeClass(Robot,classtype)

# TargetFinder is registered for setting validataion only
from targetfinder import TargetFinder
noderegistry.registerNodeClass(TargetFinder,classtype)

from targetfinder import ClickTargetFinder
noderegistry.registerNodeClass(ClickTargetFinder,classtype)

from tomography.tomography import Tomography
noderegistry.registerNodeClass(Tomography,classtype)

from acquisition import Acquisition
noderegistry.registerNodeClass(Acquisition,classtype)

from focuser import Focuser
noderegistry.registerNodeClass(Focuser,classtype)

from rctacquisition import RCTAcquisition
noderegistry.registerNodeClass(RCTAcquisition,classtype)

from tilttracker import TiltTracker
noderegistry.registerNodeClass(TiltTracker,classtype)

from tomography.tomographysimu import TomographySimu
noderegistry.registerNodeClass(TomographySimu,classtype)

from beamtiltimager import BeamTiltImager
noderegistry.registerNodeClass(BeamTiltImager,classtype)

from beamtiltfixer import BeamTiltFixer
noderegistry.registerNodeClass(BeamTiltFixer,classtype)

from robot2 import Robot2
noderegistry.registerNodeClass(Robot2,classtype)

from sampletargetfilter import SampleTargetFilter
noderegistry.registerNodeClass(SampleTargetFilter,classtype)

from jahcfinder import JAHCFinder
noderegistry.registerNodeClass(JAHCFinder,classtype)

from atlastargetmaker import AtlasTargetMaker
noderegistry.registerNodeClass(AtlasTargetMaker,classtype)

from fftace import CTFAnalyzer
noderegistry.registerNodeClass(CTFAnalyzer,classtype)

from holedepth import HoleDepth
noderegistry.registerNodeClass(HoleDepth,classtype)

from fftmaker import FFTMaker
noderegistry.registerNodeClass(FFTMaker,classtype)

from autoexposure import AutoExposure
noderegistry.registerNodeClass(AutoExposure,classtype)

from baker import Baker
noderegistry.registerNodeClass(Baker,classtype)

from tiltacquisition import TiltAcquisition
noderegistry.registerNodeClass(TiltAcquisition,classtype)

from tiltalternater import TiltAlternater
noderegistry.registerNodeClass(TiltAlternater,classtype)

##############################
# Calibrations
##############################
classtype = 'Calibrations'
from magcalibrator import MagCalibrator
noderegistry.registerNodeClass(MagCalibrator,classtype)

from gonmodeler import GonModeler
noderegistry.registerNodeClass(GonModeler,classtype)

from matrixcalibrator import MatrixCalibrator
noderegistry.registerNodeClass(MatrixCalibrator,classtype)

from imagebeamcalibrator import ImageBeamCalibrator
noderegistry.registerNodeClass(ImageBeamCalibrator,classtype)

from beamtiltcalibrator import BeamTiltCalibrator
noderegistry.registerNodeClass(BeamTiltCalibrator,classtype)

from pixelsizecalibrator import PixelSizeCalibrator
noderegistry.registerNodeClass(PixelSizeCalibrator,classtype)

from dosecalibrator import DoseCalibrator
noderegistry.registerNodeClass(DoseCalibrator,classtype)

from beamsizecalibrator import BeamSizeCalibrator
noderegistry.registerNodeClass(BeamSizeCalibrator,classtype)

##############################
# Utility
##############################
classtype = 'Utility'
from clicktargettransformer import ClickTargetTransformer
noderegistry.registerNodeClass(ClickTargetTransformer,classtype)

from driftmanager import DriftManager
noderegistry.registerNodeClass(DriftManager,classtype)

from reference import AlignZeroLossPeak
noderegistry.registerNodeClass(AlignZeroLossPeak,classtype)

from reference import MeasureDose
noderegistry.registerNodeClass(MeasureDose,classtype)

from EM import EM
noderegistry.registerNodeClass(EM,classtype)

from alignmentmanager import AlignmentManager
noderegistry.registerNodeClass(AlignmentManager,classtype)

from conditioner import Conditioner
noderegistry.registerNodeClass(Conditioner,classtype)

from buffercycler import BufferCycler
noderegistry.registerNodeClass(BufferCycler,classtype)

from conditioner import AutoNitrogenFiller
noderegistry.registerNodeClass(AutoNitrogenFiller,classtype)

from maskassessor import MaskAssessor
noderegistry.registerNodeClass(MaskAssessor,classtype)

from beamfixer import BeamFixer
noderegistry.registerNodeClass(BeamFixer,classtype)

from exposurefixer import ExposureFixer
noderegistry.registerNodeClass(ExposureFixer,classtype)

from intensitymonitor import IntensityMonitor
noderegistry.registerNodeClass(IntensityMonitor,classtype)

from manualacquisition import ManualAcquisition
noderegistry.registerNodeClass(ManualAcquisition,classtype)

from corrector import Corrector
noderegistry.registerNodeClass(Corrector,classtype)

from transformmanager import TransformManager
noderegistry.registerNodeClass(TransformManager,classtype)

from manualimageloader import ManualImageLoader
noderegistry.registerNodeClass(ManualImageLoader,classtype)

from clickmaskmaker import ClickMaskMaker
noderegistry.registerNodeClass(ClickMaskMaker,classtype)

from navigator import Navigator
noderegistry.registerNodeClass(Navigator,classtype)

from imageassessor import ImageAssessor
noderegistry.registerNodeClass(ImageAssessor,classtype)

