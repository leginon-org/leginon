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

from presets import PresetsManager
noderegistry.registerNodeClass(PresetsManager)

##############################
# Pipeline
##############################

from gridentry import GridEntry
noderegistry.registerNodeClass(GridEntry)

from targetmaker import MosaicTargetMaker
noderegistry.registerNodeClass(MosaicTargetMaker)

from rastertargetfilter import RasterTargetFilter
noderegistry.registerNodeClass(RasterTargetFilter)

from imageprocessorexample import FileNames
noderegistry.registerNodeClass(FileNames)

from regionfinder import RegionFinder
noderegistry.registerNodeClass(RegionFinder)

from imageprocessor import ImageProcessor
noderegistry.registerNodeClass(ImageProcessor)

from holefinder import HoleFinder
noderegistry.registerNodeClass(HoleFinder)

from rasterfinder import RasterFinder
noderegistry.registerNodeClass(RasterFinder)

from stigacquisition import StigAcquisition
noderegistry.registerNodeClass(StigAcquisition)

from raptorprocessor import RaptorProcessor
noderegistry.registerNodeClass(RaptorProcessor)

from matlabtargetfinder import MatlabTargetFinder
noderegistry.registerNodeClass(MatlabTargetFinder)

from dtfinder import DTFinder
noderegistry.registerNodeClass(DTFinder)

from mosaictargetfinder import MosaicClickTargetFinder
noderegistry.registerNodeClass(MosaicClickTargetFinder)

from mosaicsectionfinder import MosaicSectionFinder
noderegistry.registerNodeClass(MosaicSectionFinder)

from robotatlastargetfinder import RobotAtlasTargetFinder
noderegistry.registerNodeClass(RobotAtlasTargetFinder)

from centertargetfilter import CenterTargetFilter
noderegistry.registerNodeClass(CenterTargetFilter)

from tiltrotate import TiltRotateRepeater
noderegistry.registerNodeClass(TiltRotateRepeater)

from robot import Robot
noderegistry.registerNodeClass(Robot)

from targetfinder import ClickTargetFinder
noderegistry.registerNodeClass(ClickTargetFinder)

from tomography.tomography import Tomography
noderegistry.registerNodeClass(Tomography)

from acquisition import Acquisition
noderegistry.registerNodeClass(Acquisition)

from focuser import Focuser
noderegistry.registerNodeClass(Focuser)

from rctacquisition import RCTAcquisition
noderegistry.registerNodeClass(RCTAcquisition)

from tomography.tomographysimu import TomographySimu
noderegistry.registerNodeClass(TomographySimu)

from beamtiltimager import BeamTiltImager
noderegistry.registerNodeClass(BeamTiltImager)

from robot2 import Robot2
noderegistry.registerNodeClass(Robot2)

from sampletargetfilter import SampleTargetFilter
noderegistry.registerNodeClass(SampleTargetFilter)

from jahcfinder import JAHCFinder
noderegistry.registerNodeClass(JAHCFinder)

from atlastargetmaker import AtlasTargetMaker
noderegistry.registerNodeClass(AtlasTargetMaker)

from fftace import CTFAnalyzer
noderegistry.registerNodeClass(CTFAnalyzer)

from holedepth import HoleDepth
noderegistry.registerNodeClass(HoleDepth)

from fftmaker import FFTMaker
noderegistry.registerNodeClass(FFTMaker)

##############################
# Calibrations
##############################

from magcalibrator import MagCalibrator
noderegistry.registerNodeClass(MagCalibrator)

from gonmodeler import GonModeler
noderegistry.registerNodeClass(GonModeler)

from matrixcalibrator import MatrixCalibrator
noderegistry.registerNodeClass(MatrixCalibrator)

from beamtiltcalibrator import BeamTiltCalibrator
noderegistry.registerNodeClass(BeamTiltCalibrator)

from pixelsizecalibrator import PixelSizeCalibrator
noderegistry.registerNodeClass(PixelSizeCalibrator)

from dosecalibrator import DoseCalibrator
noderegistry.registerNodeClass(DoseCalibrator)

##############################
# Utility
##############################

from clicktargettransformer import ClickTargetTransformer
noderegistry.registerNodeClass(ClickTargetTransformer)

from driftmanager import DriftManager
noderegistry.registerNodeClass(DriftManager)

from reference import AlignZeroLossPeak
noderegistry.registerNodeClass(AlignZeroLossPeak)

from reference import MeasureDose
noderegistry.registerNodeClass(MeasureDose)

from EM import EM
noderegistry.registerNodeClass(EM)

from maskassessor import MaskAssessor
noderegistry.registerNodeClass(MaskAssessor)

from beamfixer import BeamFixer
noderegistry.registerNodeClass(BeamFixer)

from intensitymonitor import IntensityMonitor
noderegistry.registerNodeClass(IntensityMonitor)

from manualacquisition import ManualAcquisition
noderegistry.registerNodeClass(ManualAcquisition)

from corrector import Corrector
noderegistry.registerNodeClass(Corrector)

from transformmanager import TransformManager
noderegistry.registerNodeClass(TransformManager)

from manualimageloader import ManualImageLoader
noderegistry.registerNodeClass(ManualImageLoader)

from clickmaskmaker import ClickMaskMaker
noderegistry.registerNodeClass(ClickMaskMaker)

from navigator import Navigator
noderegistry.registerNodeClass(Navigator)

from imageassessor import ImageAssessor
noderegistry.registerNodeClass(ImageAssessor)

