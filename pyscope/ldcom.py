# Created by makepy.py version 0.4.0
# By python version 2.2 (#28, Dec 21 2001, 12:21:22) [MSC 32 bit (Intel)]
# From type library 'LDSERVER.EXE'
# On Thu Mar 07 09:58:21 2002
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
"""Low Dose Server Library"""
makepy_version = '0.4.0'
python_version = 0x20200f0

import win32com.client.CLSIDToClass, pythoncom

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Missing
defaultNamedNotOptArg=pythoncom.Missing
defaultUnnamedArg=pythoncom.Missing

CLSID = pythoncom.MakeIID('{9BEC9751-A820-11D3-972E-81B6519D0DF8}')
MajorVersion = 1
MinorVersion = 1
LibraryFlags = 8
LCID = 0x0

class constants:
	eBtnCalBeamShift              =0x4        # from enum CalibrateControls
	eBtnCalBlanker                =0x0        # from enum CalibrateControls
	eBtnCalFocusIntensity         =0x5        # from enum CalibrateControls
	eBtnCalImageTilt              =0x1        # from enum CalibrateControls
	eBtnCalPeek                   =0x2        # from enum CalibrateControls
	eBtnCalPivotPoints            =0x3        # from enum CalibrateControls
	eBtnCalibrationCancel         =0x8        # from enum CalibrateControls
	eBtnCalibrationOk             =0x7        # from enum CalibrateControls
	eLblCalFilename               =0xa        # from enum CalibrateControls
	eMemCalibration               =0x6        # from enum CalibrateControls
	eScrCalibrationSpotscan       =0x9        # from enum CalibrateControls
	eAbsent                       =0x0        # from enum ControlStatus
	eActive                       =0x4        # from enum ControlStatus
	eChecked                      =0x8        # from enum ControlStatus
	eDisabled                     =0x1        # from enum ControlStatus
	eEnabled                      =0x2        # from enum ControlStatus
	eBtnAddDouble                 =0x2        # from enum DoubleControls
	eBtnDeleteDouble              =0x3        # from enum DoubleControls
	eBtnMoveDownDouble            =0x5        # from enum DoubleControls
	eBtnMoveUpDouble              =0x4        # from enum DoubleControls
	eEdDouble                     =0x0        # from enum DoubleControls
	eLstDouble                    =0x1        # from enum DoubleControls
	eBlankNotAvailable            =0x5        # from enum Errors
	eExposeNotEnabled             =0x4        # from enum Errors
	eLowDoseNotAvailable          =0x1        # from enum Errors
	eLowDoseNotEnabled            =0x3        # from enum Errors
	eNoError                      =0x0        # from enum Errors
	ePeekNotAvailable             =0x6        # from enum Errors
	eSpotscanNotAvailable         =0x2        # from enum Errors
	eBtnExpose                    =0x0        # from enum ExposeControls
	eChkDimScreen                 =0x6        # from enum ExposeControls
	eChkDouble                    =0x2        # from enum ExposeControls
	eChkPreExpWait                =0x5        # from enum ExposeControls
	eChkPreExposure               =0x4        # from enum ExposeControls
	eChkSeries                    =0x1        # from enum ExposeControls
	eChkSpotscan                  =0x3        # from enum ExposeControls
	eEdExpTime                    =0x7        # from enum ExposeControls
	eLblExpTime                   =0x8        # from enum ExposeControls
	eLblExpTimeLabel              =0xa        # from enum ExposeControls
	eSpinExpTime                  =0xb        # from enum ExposeControls
	eSpinPreExpose                =0xc        # from enum ExposeControls
	eSpinWaitAfterPreExp          =0xd        # from enum ExposeControls
	eSpinWaitTime                 =0x9        # from enum ExposeControls
	eScrAngle                     =0x1        # from enum FocusControls
	eScrDistance                  =0x0        # from enum FocusControls
	eExposure                     =0x3        # from enum LDState
	eFocus1                       =0x1        # from enum LDState
	eFocus2                       =0x2        # from enum LDState
	eSearch                       =0x0        # from enum LDState
	IsOff                         =0x0        # from enum LDStatus
	IsOn                          =0x1        # from enum LDStatus
	eNumber                       =0x4        # from enum ListChange
	eOrder                        =0x1        # from enum ListChange
	eSelection                    =0x2        # from enum ListChange
	eBtnBlank                     =0x1        # from enum MainControls
	eBtnExposure                  =0x8        # from enum MainControls
	eBtnFocus                     =0x5        # from enum MainControls
	eBtnFocusStart                =0x19       # from enum MainControls
	eBtnLowDose                   =0x0        # from enum MainControls
	eBtnPeek                      =0x2        # from enum MainControls
	eBtnSearch                    =0x4        # from enum MainControls
	eBtnSearchStart               =0x18       # from enum MainControls
	eLblExposureIntensity         =0x17       # from enum MainControls
	eLblExposureMagn              =0x15       # from enum MainControls
	eLblExposureMode              =0x14       # from enum MainControls
	eLblExposureSpot              =0x16       # from enum MainControls
	eLblFocusAngle                =0x13       # from enum MainControls
	eLblFocusDistance             =0x12       # from enum MainControls
	eLblFocusIntensity            =0x11       # from enum MainControls
	eLblFocusMagn                 =0xf        # from enum MainControls
	eLblFocusSpot                 =0x10       # from enum MainControls
	eLblSearchIntensity           =0xc        # from enum MainControls
	eLblSearchMagn                =0xa        # from enum MainControls
	eLblSearchMode                =0x9        # from enum MainControls
	eLblSearchSpot                =0xb        # from enum MainControls
	eLblSearchX                   =0xd        # from enum MainControls
	eLblSearchY                   =0xe        # from enum MainControls
	eLblStatus                    =0x3        # from enum MainControls
	eOptFocus1                    =0x6        # from enum MainControls
	eOptFocus2                    =0x7        # from enum MainControls
	eCCD                          =0x2        # from enum Media
	eScreenOrPlate                =0x0        # from enum Media
	eTV                           =0x1        # from enum Media
	eIntensity                    =0x2        # from enum Normalizations
	eObjective                    =0x14       # from enum Normalizations
	eProjection                   =0x8        # from enum Normalizations
	eSpotsize                     =0x1        # from enum Normalizations
	eBtnMeasure                   =0x12       # from enum OptionsControls
	eChkContinuously              =0x13       # from enum OptionsControls
	eChkEnablePeek                =0x0        # from enum OptionsControls
	eChkFocusShiftMf              =0x3        # from enum OptionsControls
	eChkNormC1                    =0x14       # from enum OptionsControls
	eChkNormC2                    =0x15       # from enum OptionsControls
	eChkNormFEC1                  =0xc        # from enum OptionsControls
	eChkNormFEC2                  =0xd        # from enum OptionsControls
	eChkNormFEProj                =0xe        # from enum OptionsControls
	eChkNormFSC1                  =0x8        # from enum OptionsControls
	eChkNormFSC2                  =0x9        # from enum OptionsControls
	eChkNormFSObj                 =0xa        # from enum OptionsControls
	eChkNormFSProj                =0xb        # from enum OptionsControls
	eChkNormObj                   =0x16       # from enum OptionsControls
	eChkNormProj                  =0x17       # from enum OptionsControls
	eChkNormSFC1                  =0x4        # from enum OptionsControls
	eChkNormSFC2                  =0x5        # from enum OptionsControls
	eChkNormSFObj                 =0x6        # from enum OptionsControls
	eChkNormSFProj                =0x7        # from enum OptionsControls
	eChkSFEF                      =0xf        # from enum OptionsControls
	eChkSearchShiftMf             =0x2        # from enum OptionsControls
	eChkUseTvCcd                  =0x1        # from enum OptionsControls
	eEdDiameter                   =0x11       # from enum OptionsControls
	eLblDose                      =0x10       # from enum OptionsControls
	eScreenDiameterLabel          =0x1d       # from enum OptionsControls
	eUserButtonBlank              =0x18       # from enum OptionsControls
	eUserButtonFocus              =0x1b       # from enum OptionsControls
	eUserButtonPeek               =0x19       # from enum OptionsControls
	eUserButtonSearch             =0x1a       # from enum OptionsControls
	eUserbuttonExposure           =0x1c       # from enum OptionsControls
	eAll                          =0x1        # from enum ResetFunctions
	eModeOnly                     =0x0        # from enum ResetFunctions
	eFullDisplay                  =0x1        # from enum ScreenDimDisplay
	ePartDisplay                  =0x0        # from enum ScreenDimDisplay
	eBtnAddSeries                 =0x2        # from enum SeriesControls
	eBtnDeleteSeries              =0x3        # from enum SeriesControls
	eBtnMoveDownSeries            =0x5        # from enum SeriesControls
	eBtnMoveUpSeries              =0x4        # from enum SeriesControls
	eEdSeries                     =0x0        # from enum SeriesControls
	eLstSeries                    =0x1        # from enum SeriesControls
	eCcdExposureTime              =0x27       # from enum Settings
	eDimScreen                    =0x36       # from enum Settings
	eDoDouble                     =0x33       # from enum Settings
	eDoSeries                     =0x34       # from enum Settings
	eExposureBeamShift            =0x24       # from enum Settings
	eExposureC2                   =0x21       # from enum Settings
	eExposureClIndex              =0x1c       # from enum Settings
	eExposureClValue              =0x1f       # from enum Settings
	eExposureDifLens              =0x23       # from enum Settings
	eExposureDiffractionShift     =0x25       # from enum Settings
	eExposureIndex                =0x1a       # from enum Settings
	eExposureIntensity            =0x20       # from enum Settings
	eExposureMagnIndex            =0x1b       # from enum Settings
	eExposureMagnValue            =0x1e       # from enum Settings
	eExposureMode                 =0x19       # from enum Settings
	eExposureObjLens              =0x22       # from enum Settings
	eExposureSpot                 =0x1d       # from enum Settings
	eFocusBeamShift               =0x17       # from enum Settings
	eFocusC2                      =0x16       # from enum Settings
	eFocusClIndex                 =0x11       # from enum Settings
	eFocusClValue                 =0x14       # from enum Settings
	eFocusImageShift              =0x18       # from enum Settings
	eFocusIndex                   =0xf        # from enum Settings
	eFocusIntensity               =0x15       # from enum Settings
	eFocusMagnIndex               =0x10       # from enum Settings
	eFocusMagnValue               =0x13       # from enum Settings
	eFocusSpot                    =0x12       # from enum Settings
	eFocusState                   =0xe        # from enum Settings
	eLowDoseStateChange           =0x2d       # from enum Settings
	ePlateExposureTime            =0x26       # from enum Settings
	ePreExpose                    =0x31       # from enum Settings
	ePreExposeTime                =0x2a       # from enum Settings
	ePreExposeWaitTime            =0x2b       # from enum Settings
	eSearchBeamShift              =0xb        # from enum Settings
	eSearchC2                     =0x8        # from enum Settings
	eSearchClIndex                =0x3        # from enum Settings
	eSearchClValue                =0x6        # from enum Settings
	eSearchDifLens                =0xa        # from enum Settings
	eSearchDiffractionShift       =0xd        # from enum Settings
	eSearchImageShift             =0xc        # from enum Settings
	eSearchIndex                  =0x1        # from enum Settings
	eSearchIntensity              =0x7        # from enum Settings
	eSearchMagnIndex              =0x2        # from enum Settings
	eSearchMagnValue              =0x5        # from enum Settings
	eSearchMode                   =0x0        # from enum Settings
	eSearchObjLens                =0x9        # from enum Settings
	eSearchSpot                   =0x4        # from enum Settings
	eSpotscanDwellTime            =0x28       # from enum Settings
	eSpotscanStemMagnification    =0x30       # from enum Settings
	eUseSpotscan                  =0x35       # from enum Settings
	eWaitAfterPreExpose           =0x32       # from enum Settings
	eWaitTime                     =0x29       # from enum Settings
	eBtnExposureReset             =0xc        # from enum SettingsControls
	eBtnFocusReset                =0x6        # from enum SettingsControls
	eBtnSearchReset               =0x0        # from enum SettingsControls
	eLblSettingsFilename          =0x11       # from enum SettingsControls
	eOptExposureAll               =0xe        # from enum SettingsControls
	eOptExposureCcd               =0x10       # from enum SettingsControls
	eOptExposureMode              =0xd        # from enum SettingsControls
	eOptExposurePlate             =0xf        # from enum SettingsControls
	eOptFocusAll                  =0x8        # from enum SettingsControls
	eOptFocusCcd                  =0xb        # from enum SettingsControls
	eOptFocusMode                 =0x7        # from enum SettingsControls
	eOptFocusScreen               =0x9        # from enum SettingsControls
	eOptFocusTv                   =0xa        # from enum SettingsControls
	eOptSearchAll                 =0x2        # from enum SettingsControls
	eOptSearchCcd                 =0x5        # from enum SettingsControls
	eOptSearchMode                =0x1        # from enum SettingsControls
	eOptSearchScreen              =0x3        # from enum SettingsControls
	eOptSearchTv                  =0x4        # from enum SettingsControls
	eBtnAcOff                     =0x18       # from enum SpotscanControls
	eBtnFaster                    =0x15       # from enum SpotscanControls
	eBtnShiftAway                 =0x17       # from enum SpotscanControls
	eBtnSlower                    =0x14       # from enum SpotscanControls
	eBtnTo0                       =0x16       # from enum SpotscanControls
	eBtnView                      =0x13       # from enum SpotscanControls
	eChkFocusCorrection           =0x3        # from enum SpotscanControls
	eEdFocusOffset                =0x4        # from enum SpotscanControls
	eEdOrientation                =0x2        # from enum SpotscanControls
	eEdSpotDwell                  =0x11       # from enum SpotscanControls
	eLblNoOfSpots                 =0x10       # from enum SpotscanControls
	eLblSpotDistance              =0xf        # from enum SpotscanControls
	eLblX                         =0xb        # from enum SpotscanControls
	eLblY                         =0xc        # from enum SpotscanControls
	eOptHexagonal                 =0x0        # from enum SpotscanControls
	eOptNone                      =0x5        # from enum SpotscanControls
	eOptOutline                   =0x6        # from enum SpotscanControls
	eOptSpotWobble                =0xd        # from enum SpotscanControls
	eOptSquare                    =0x1        # from enum SpotscanControls
	eOptStaticX                   =0x7        # from enum SpotscanControls
	eOptStaticY                   =0x8        # from enum SpotscanControls
	eProgressBar                  =0x12       # from enum SpotscanControls
	eScrSpotDistance              =0xe        # from enum SpotscanControls
	eScrX                         =0x9        # from enum SpotscanControls
	eScrY                         =0xa        # from enum SpotscanControls
	eSpinSpotDwell                =0x19       # from enum SpotscanControls
	eHexagonal                    =0x0        # from enum SpotscanPattern
	eSquare                       =0x1        # from enum SpotscanPattern
	eNoneActive                   =0x0        # from enum SpotscanSetup
	eOutline                      =0x3        # from enum SpotscanSetup
	eSpotWobble                   =0x4        # from enum SpotscanSetup
	eStaticX                      =0x1        # from enum SpotscanSetup
	eStaticY                      =0x2        # from enum SpotscanSetup
	eChkDetailedLog               =0x3        # from enum TestModeControls
	eChkSkipCloseShutter          =0x2        # from enum TestModeControls
	eChkSkipPlateIn               =0x1        # from enum TestModeControls
	eChkSkipScreenUp              =0x0        # from enum TestModeControls
	eTestModeEnabled              =0x4        # from enum TestModeControls
	eBelowProjection              =0x2        # from enum TvCcd
	eNoTvCcd                      =0x0        # from enum TvCcd
	eUnderneathAll                =0x3        # from enum TvCcd
	eWideAnglePosition            =0x1        # from enum TvCcd
	eChkCcd                       =0x1        # from enum TvControls
	eChkTvRate                    =0x0        # from enum TvControls
	eLstCameras                   =0x3        # from enum TvControls
	eLstControllers               =0x2        # from enum TvControls
	eOptCcdBelow                  =0x8        # from enum TvControls
	eOptCcdUnder                  =0x9        # from enum TvControls
	eOptCcdWide                   =0x7        # from enum TvControls
	eOptTvBelow                   =0x5        # from enum TvControls
	eOptTvUnder                   =0x6        # from enum TvControls
	eOptTvWide                    =0x4        # from enum TvControls
	eL1                           =0x1        # from enum UserButtons
	eL2                           =0x2        # from enum UserButtons
	eL3                           =0x3        # from enum UserButtons
	eNone                         =0x0        # from enum UserButtons
	eR1                           =0x4        # from enum UserButtons
	eR2                           =0x5        # from enum UserButtons
	eR3                           =0x6        # from enum UserButtons

from win32com.client import DispatchBaseClass
class ILdSrv(DispatchBaseClass):
	"""Dispatch interface for Low Dose Server """
	CLSID = pythoncom.MakeIID('{9BEC9752-A820-11D3-972E-81B6519D0DF8}')

	def CalibrateAcBeamShift(self):
		return self._oleobj_.InvokeTypes(0xef, LCID, 1, (24, 0), (),)

	def CalibrateAcPivotPoints(self):
		return self._oleobj_.InvokeTypes(0xee, LCID, 1, (24, 0), (),)

	def CalibrateBeamBlanker(self):
		return self._oleobj_.InvokeTypes(0xeb, LCID, 1, (24, 0), (),)

	def CalibrateCancel(self):
		return self._oleobj_.InvokeTypes(0xf2, LCID, 1, (24, 0), (),)

	def CalibrateFocusIntensity(self):
		return self._oleobj_.InvokeTypes(0xf0, LCID, 1, (24, 0), (),)

	def CalibrateImageTilt(self):
		return self._oleobj_.InvokeTypes(0xec, LCID, 1, (24, 0), (),)

	def CalibrateOk(self):
		return self._oleobj_.InvokeTypes(0xf1, LCID, 1, (24, 0), (),)

	def CalibratePeek(self):
		return self._oleobj_.InvokeTypes(0xed, LCID, 1, (24, 0), (),)

	def DoubleAdd(self):
		return self._oleobj_.InvokeTypes(0x127, LCID, 1, (24, 0), (),)

	def DoubleDelete(self):
		return self._oleobj_.InvokeTypes(0x128, LCID, 1, (24, 0), (),)

	def DoubleDown(self):
		return self._oleobj_.InvokeTypes(0x12a, LCID, 1, (24, 0), (),)

	def DoubleUp(self):
		return self._oleobj_.InvokeTypes(0x129, LCID, 1, (24, 0), (),)

	def FocusStartCcd(self, Value=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x143, LCID, 1, (24, 0), ((11, 1),),Value)

	def LoadCalFromFile(self, Filename=defaultNamedNotOptArg, Arr=defaultNamedNotOptArg):
		return self._ApplyTypes_(0xbe, 1, (24, 0), ((16392, 3), (16396, 3)), 'LoadCalFromFile', None,Filename, Arr)

	def LoadSettingsFromFile(self, Filename=defaultNamedNotOptArg, Arr=defaultNamedNotOptArg):
		return self._ApplyTypes_(0xba, 1, (24, 0), ((16392, 3), (16396, 3)), 'LoadSettingsFromFile', None,Filename, Arr)

	def MeasureDose(self, Start=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0xe0, LCID, 1, (24, 0), ((11, 1),),Start)

	def Normalize(self, Param=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0xd6, LCID, 1, (24, 0), ((3, 1),),Param)

	def ResetExposureSettings(self):
		return self._oleobj_.InvokeTypes(0xe4, LCID, 1, (24, 0), (),)

	def ResetFocusSettings(self):
		return self._oleobj_.InvokeTypes(0xe3, LCID, 1, (24, 0), (),)

	def ResetSearchSettings(self):
		return self._oleobj_.InvokeTypes(0xe2, LCID, 1, (24, 0), (),)

	def SaveCalToFile(self, Filename=defaultNamedNotOptArg, Arr=defaultNamedNotOptArg):
		return self._ApplyTypes_(0xbf, 1, (24, 0), ((16392, 3), (16396, 3)), 'SaveCalToFile', None,Filename, Arr)

	def SaveSettingsToFile(self, Filename=defaultNamedNotOptArg, Arr=defaultNamedNotOptArg):
		return self._ApplyTypes_(0xbb, 1, (24, 0), ((16392, 3), (16396, 3)), 'SaveSettingsToFile', None,Filename, Arr)

	def ScreenDimPosition(self, fDimDisplay=defaultNamedNotOptArg, fDimLeft=defaultNamedNotOptArg, fDimTop=defaultNamedNotOptArg, fDimWidth=defaultNamedNotOptArg, fDimHeight=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x10b, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1), (3, 1), (3, 1)),fDimDisplay, fDimLeft, fDimTop, fDimWidth, fDimHeight)

	def ScreenDimSet(self, Dim=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x10a, LCID, 1, (24, 0), ((3, 1),),Dim)

	def ScreenDimText(self, Txt1=defaultNamedNotOptArg, Txt2=defaultNamedNotOptArg, Txt3=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x10d, LCID, 1, (24, 0), ((8, 1), (8, 1), (8, 1)),Txt1, Txt2, Txt3)

	def ScreenDimTimeOut(self, DimTimeOut=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x10c, LCID, 1, (24, 0), ((3, 1),),DimTimeOut)

	def SearchStartCcd(self, Value=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x142, LCID, 1, (24, 0), ((11, 1),),Value)

	def SeriesAdd(self):
		return self._oleobj_.InvokeTypes(0x10e, LCID, 1, (24, 0), (),)

	def SeriesDelete(self):
		return self._oleobj_.InvokeTypes(0x10f, LCID, 1, (24, 0), (),)

	def SeriesDown(self):
		return self._oleobj_.InvokeTypes(0x111, LCID, 1, (24, 0), (),)

	def SeriesUp(self):
		return self._oleobj_.InvokeTypes(0x110, LCID, 1, (24, 0), (),)

	def SetTestMode(self, Param1=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x82, LCID, 1, (24, 0), ((8, 1),),Param1)

	def SpotscanAcOff(self):
		return self._oleobj_.InvokeTypes(0xf9, LCID, 1, (24, 0), (),)

	def SpotscanFaster(self):
		return self._oleobj_.InvokeTypes(0xf6, LCID, 1, (24, 0), (),)

	def SpotscanShiftAway(self):
		return self._oleobj_.InvokeTypes(0xf8, LCID, 1, (24, 0), (),)

	def SpotscanSlower(self):
		return self._oleobj_.InvokeTypes(0xf5, LCID, 1, (24, 0), (),)

	def SpotscanTo0(self):
		return self._oleobj_.InvokeTypes(0xf7, LCID, 1, (24, 0), (),)

	def SpotscanView(self, Start=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0xf4, LCID, 1, (24, 0), ((11, 1),),Start)

	_prop_map_get_ = {
		"BeamBlanked": (156, 2, (11, 0), (), "BeamBlanked", None),
		"BtnAcOffStatus": (73, 2, (3, 0), (), "BtnAcOffStatus", None),
		"BtnAddDoubleStatus": (43, 2, (3, 0), (), "BtnAddDoubleStatus", None),
		"BtnAddSeriesStatus": (37, 2, (3, 0), (), "BtnAddSeriesStatus", None),
		"BtnBlankStatus": (2, 2, (3, 0), (), "BtnBlankStatus", None),
		"BtnCaLBlankerStatus": (92, 2, (3, 0), (), "BtnCaLBlankerStatus", None),
		"BtnCalBeamShiftStatus": (96, 2, (3, 0), (), "BtnCalBeamShiftStatus", None),
		"BtnCalFocusIntensityStatus": (97, 2, (3, 0), (), "BtnCalFocusIntensityStatus", None),
		"BtnCalImageTiltStatus": (93, 2, (3, 0), (), "BtnCalImageTiltStatus", None),
		"BtnCalPeekStatus": (94, 2, (3, 0), (), "BtnCalPeekStatus", None),
		"BtnCalPivotPointsStatus": (95, 2, (3, 0), (), "BtnCalPivotPointsStatus", None),
		"BtnCalibrationCancelStatus": (109, 2, (3, 0), (), "BtnCalibrationCancelStatus", None),
		"BtnCalibrationOkStatus": (108, 2, (3, 0), (), "BtnCalibrationOkStatus", None),
		"BtnDeleteDoubleStatus": (44, 2, (3, 0), (), "BtnDeleteDoubleStatus", None),
		"BtnDeleteSeriesStatus": (38, 2, (3, 0), (), "BtnDeleteSeriesStatus", None),
		"BtnExposeStatus": (23, 2, (3, 0), (), "BtnExposeStatus", None),
		"BtnExposureResetStatus": (86, 2, (3, 0), (), "BtnExposureResetStatus", None),
		"BtnExposureStatus": (9, 2, (3, 0), (), "BtnExposureStatus", None),
		"BtnFasterStatus": (70, 2, (3, 0), (), "BtnFasterStatus", None),
		"BtnFocusResetStatus": (80, 2, (3, 0), (), "BtnFocusResetStatus", None),
		"BtnFocusStartStatus": (264, 2, (3, 0), (), "BtnFocusStartStatus", None),
		"BtnFocusStatus": (6, 2, (3, 0), (), "BtnFocusStatus", None),
		"BtnLowDoseStatus": (1, 2, (3, 0), (), "BtnLowDoseStatus", None),
		"BtnMeasureStatus": (131, 2, (3, 0), (), "BtnMeasureStatus", None),
		"BtnMoveDownDoubleStatus": (46, 2, (3, 0), (), "BtnMoveDownDoubleStatus", None),
		"BtnMoveDownSeriesStatus": (40, 2, (3, 0), (), "BtnMoveDownSeriesStatus", None),
		"BtnMoveUpDoubleStatus": (45, 2, (3, 0), (), "BtnMoveUpDoubleStatus", None),
		"BtnMoveUpSeriesStatus": (39, 2, (3, 0), (), "BtnMoveUpSeriesStatus", None),
		"BtnPeekStatus": (3, 2, (3, 0), (), "BtnPeekStatus", None),
		"BtnSearchResetStatus": (74, 2, (3, 0), (), "BtnSearchResetStatus", None),
		"BtnSearchStartStatus": (255, 2, (3, 0), (), "BtnSearchStartStatus", None),
		"BtnSearchStatus": (5, 2, (3, 0), (), "BtnSearchStatus", None),
		"BtnShiftAwayStatus": (72, 2, (3, 0), (), "BtnShiftAwayStatus", None),
		"BtnSlowerStatus": (69, 2, (3, 0), (), "BtnSlowerStatus", None),
		"BtnTo0Status": (71, 2, (3, 0), (), "BtnTo0Status", None),
		"BtnViewStatus": (68, 2, (3, 0), (), "BtnViewStatus", None),
		"CalibrationFilename": (193, 2, (8, 0), (), "CalibrationFilename", None),
		"CcdExposureTime": (165, 2, (5, 0), (), "CcdExposureTime", None),
		"CcdSelected": (338, 2, (3, 0), (), "CcdSelected", None),
		"ChkCcdStatus": (138, 2, (3, 0), (), "ChkCcdStatus", None),
		"ChkContinuouslyStatus": (132, 2, (3, 0), (), "ChkContinuouslyStatus", None),
		"ChkDetailedLogStatus": (334, 2, (3, 0), (), "ChkDetailedLogStatus", None),
		"ChkDimScreenStatus": (29, 2, (3, 0), (), "ChkDimScreenStatus", None),
		"ChkDoubleStatus": (25, 2, (3, 0), (), "ChkDoubleStatus", None),
		"ChkEnablePeekStatus": (113, 2, (3, 0), (), "ChkEnablePeekStatus", None),
		"ChkFocusCorrectionStatus": (50, 2, (3, 0), (), "ChkFocusCorrectionStatus", None),
		"ChkFocusShiftMfStatus": (116, 2, (3, 0), (), "ChkFocusShiftMfStatus", None),
		"ChkNormC1Status": (133, 2, (3, 0), (), "ChkNormC1Status", None),
		"ChkNormC2Status": (134, 2, (3, 0), (), "ChkNormC2Status", None),
		"ChkNormFEC1Status": (125, 2, (3, 0), (), "ChkNormFEC1Status", None),
		"ChkNormFEC2Status": (126, 2, (3, 0), (), "ChkNormFEC2Status", None),
		"ChkNormFEProjStatus": (127, 2, (3, 0), (), "ChkNormFEProjStatus", None),
		"ChkNormFSC1Status": (121, 2, (3, 0), (), "ChkNormFSC1Status", None),
		"ChkNormFSC2Status": (122, 2, (3, 0), (), "ChkNormFSC2Status", None),
		"ChkNormFSObjStatus": (123, 2, (3, 0), (), "ChkNormFSObjStatus", None),
		"ChkNormFSProjStatus": (124, 2, (3, 0), (), "ChkNormFSProjStatus", None),
		"ChkNormObjStatus": (135, 2, (3, 0), (), "ChkNormObjStatus", None),
		"ChkNormProjStatus": (136, 2, (3, 0), (), "ChkNormProjStatus", None),
		"ChkNormSFC1Status": (117, 2, (3, 0), (), "ChkNormSFC1Status", None),
		"ChkNormSFC2Status": (118, 2, (3, 0), (), "ChkNormSFC2Status", None),
		"ChkNormSFObjStatus": (119, 2, (3, 0), (), "ChkNormSFObjStatus", None),
		"ChkNormSFProjStatus": (120, 2, (3, 0), (), "ChkNormSFProjStatus", None),
		"ChkPreExpWaitStatus": (28, 2, (3, 0), (), "ChkPreExpWaitStatus", None),
		"ChkPreExposureStatus": (27, 2, (3, 0), (), "ChkPreExposureStatus", None),
		"ChkSFEFStatus": (128, 2, (3, 0), (), "ChkSFEFStatus", None),
		"ChkSearchShiftMfStatus": (115, 2, (3, 0), (), "ChkSearchShiftMfStatus", None),
		"ChkSeriesStatus": (24, 2, (3, 0), (), "ChkSeriesStatus", None),
		"ChkSkipCloseShutterStatus": (333, 2, (3, 0), (), "ChkSkipCloseShutterStatus", None),
		"ChkSkipPlateInStatus": (332, 2, (3, 0), (), "ChkSkipPlateInStatus", None),
		"ChkSkipScreenUpStatus": (331, 2, (3, 0), (), "ChkSkipScreenUpStatus", None),
		"ChkSpotscanStatus": (26, 2, (3, 0), (), "ChkSpotscanStatus", None),
		"ChkTvRateStatus": (137, 2, (3, 0), (), "ChkTvRateStatus", None),
		"ChkUseTvCcdStatus": (114, 2, (3, 0), (), "ChkUseTvCcdStatus", None),
		"ContinuousDose": (225, 2, (11, 0), (), "ContinuousDose", None),
		"Dose": (336, 2, (5, 0), (), "Dose", None),
		"Double1": (299, 2, (5, 0), (), "Double1", None),
		"Double10": (308, 2, (5, 0), (), "Double10", None),
		"Double11": (309, 2, (5, 0), (), "Double11", None),
		"Double12": (310, 2, (5, 0), (), "Double12", None),
		"Double13": (311, 2, (5, 0), (), "Double13", None),
		"Double14": (312, 2, (5, 0), (), "Double14", None),
		"Double15": (313, 2, (5, 0), (), "Double15", None),
		"Double16": (314, 2, (5, 0), (), "Double16", None),
		"Double17": (315, 2, (5, 0), (), "Double17", None),
		"Double18": (316, 2, (5, 0), (), "Double18", None),
		"Double19": (317, 2, (5, 0), (), "Double19", None),
		"Double2": (300, 2, (5, 0), (), "Double2", None),
		"Double20": (318, 2, (5, 0), (), "Double20", None),
		"Double3": (301, 2, (5, 0), (), "Double3", None),
		"Double4": (302, 2, (5, 0), (), "Double4", None),
		"Double5": (303, 2, (5, 0), (), "Double5", None),
		"Double6": (304, 2, (5, 0), (), "Double6", None),
		"Double7": (305, 2, (5, 0), (), "Double7", None),
		"Double8": (306, 2, (5, 0), (), "Double8", None),
		"Double9": (307, 2, (5, 0), (), "Double9", None),
		"EdDiameterStatus": (35, 2, (8, 0), (), "EdDiameterStatus", None),
		"EdDiameterVisible": (327, 2, (11, 0), (), "EdDiameterVisible", None),
		"EdDoubleStatus": (329, 2, (8, 0), (), "EdDoubleStatus", None),
		"EdExpTimeStatus": (41, 2, (8, 0), (), "EdExpTimeStatus", None),
		"EdFocusOffsetStatus": (51, 2, (8, 0), (), "EdFocusOffsetStatus", None),
		"EdOrientationStatus": (49, 2, (8, 0), (), "EdOrientationStatus", None),
		"EdSeriesStatus": (328, 2, (8, 0), (), "EdSeriesStatus", None),
		"EdSpotDwellStatus": (64, 2, (8, 0), (), "EdSpotDwellStatus", None),
		"ExposeStatus": (400, 2, (3, 0), (), "ExposeStatus", None),
		"ExposureBeamShiftX": (388, 2, (5, 0), (), "ExposureBeamShiftX", None),
		"ExposureBeamShiftY": (389, 2, (5, 0), (), "ExposureBeamShiftY", None),
		"ExposureC2": (383, 2, (5, 0), (), "ExposureC2", None),
		"ExposureClIndex": (378, 2, (3, 0), (), "ExposureClIndex", None),
		"ExposureClMode": (353, 2, (3, 0), (), "ExposureClMode", None),
		"ExposureClValue": (381, 2, (5, 0), (), "ExposureClValue", None),
		"ExposureDifLens": (387, 2, (5, 0), (), "ExposureDifLens", None),
		"ExposureDiffShiftX": (392, 2, (5, 0), (), "ExposureDiffShiftX", None),
		"ExposureDiffShiftY": (393, 2, (5, 0), (), "ExposureDiffShiftY", None),
		"ExposureInSeries": (185, 2, (3, 0), (), "ExposureInSeries", None),
		"ExposureIndex": (376, 2, (3, 0), (), "ExposureIndex", None),
		"ExposureIntensity": (382, 2, (5, 0), (), "ExposureIntensity", None),
		"ExposureMagnIndex": (377, 2, (3, 0), (), "ExposureMagnIndex", None),
		"ExposureMagnMode": (352, 2, (3, 0), (), "ExposureMagnMode", None),
		"ExposureMagnValue": (380, 2, (5, 0), (), "ExposureMagnValue", None),
		"ExposureMode": (375, 2, (3, 0), (), "ExposureMode", None),
		"ExposureObjLens": (386, 2, (5, 0), (), "ExposureObjLens", None),
		"ExposureSpot": (379, 2, (3, 0), (), "ExposureSpot", None),
		"Focus1ShiftAngle": (372, 2, (5, 0), (), "Focus1ShiftAngle", None),
		"Focus1ShiftDistance": (371, 2, (5, 0), (), "Focus1ShiftDistance", None),
		"Focus2ShiftAngle": (374, 2, (5, 0), (), "Focus2ShiftAngle", None),
		"Focus2ShiftDistance": (373, 2, (5, 0), (), "Focus2ShiftDistance", None),
		"FocusBeamShift1X": (367, 2, (5, 0), (), "FocusBeamShift1X", None),
		"FocusBeamShift1Y": (368, 2, (5, 0), (), "FocusBeamShift1Y", None),
		"FocusBeamShift2X": (369, 2, (5, 0), (), "FocusBeamShift2X", None),
		"FocusBeamShift2Y": (370, 2, (5, 0), (), "FocusBeamShift2Y", None),
		"FocusC2": (385, 2, (5, 0), (), "FocusC2", None),
		"FocusClIndex": (363, 2, (3, 0), (), "FocusClIndex", None),
		"FocusClValue": (366, 2, (5, 0), (), "FocusClValue", None),
		"FocusCorrectionOffset": (259, 2, (5, 0), (), "FocusCorrectionOffset", None),
		"FocusIndex": (361, 2, (3, 0), (), "FocusIndex", None),
		"FocusIntensity": (384, 2, (5, 0), (), "FocusIntensity", None),
		"FocusMagnIndex": (362, 2, (3, 0), (), "FocusMagnIndex", None),
		"FocusMagnValue": (365, 2, (5, 0), (), "FocusMagnValue", None),
		"FocusShiftMf": (218, 2, (11, 0), (), "FocusShiftMf", None),
		"FocusSpot": (364, 2, (3, 0), (), "FocusSpot", None),
		"FocusState": (324, 2, (11, 0), (), "FocusState", None),
		"IsCcdRetractable": (391, 2, (11, 0), (), "IsCcdRetractable", None),
		"IsInitialized": (354, 2, (11, 0), (), "IsInitialized", None),
		"LblCalFilenameStatus": (112, 2, (8, 0), (), "LblCalFilenameStatus", None),
		"LblDoseStatus": (129, 2, (8, 0), (), "LblDoseStatus", None),
		"LblExpTimeLabelStatus": (335, 2, (8, 0), (), "LblExpTimeLabelStatus", None),
		"LblExpTimeStatus": (31, 2, (8, 0), (), "LblExpTimeStatus", None),
		"LblExposureIntensityStatus": (22, 2, (8, 0), (), "LblExposureIntensityStatus", None),
		"LblExposureMagnStatus": (20, 2, (8, 0), (), "LblExposureMagnStatus", None),
		"LblExposureModeStatus": (19, 2, (8, 0), (), "LblExposureModeStatus", None),
		"LblExposureSpotStatus": (21, 2, (8, 0), (), "LblExposureSpotStatus", None),
		"LblFocusAngleStatus": (18, 2, (8, 0), (), "LblFocusAngleStatus", None),
		"LblFocusDistanceStatus": (17, 2, (8, 0), (), "LblFocusDistanceStatus", None),
		"LblFocusIntensityStatus": (16, 2, (8, 0), (), "LblFocusIntensityStatus", None),
		"LblFocusMagnStatus": (14, 2, (8, 0), (), "LblFocusMagnStatus", None),
		"LblFocusSpotStatus": (15, 2, (8, 0), (), "LblFocusSpotStatus", None),
		"LblNoOfSpotsStatus": (63, 2, (8, 0), (), "LblNoOfSpotsStatus", None),
		"LblSearchIntensityStatus": (13, 2, (8, 0), (), "LblSearchIntensityStatus", None),
		"LblSearchMagnStatus": (11, 2, (8, 0), (), "LblSearchMagnStatus", None),
		"LblSearchModeStatus": (10, 2, (8, 0), (), "LblSearchModeStatus", None),
		"LblSearchSpotStatus": (12, 2, (8, 0), (), "LblSearchSpotStatus", None),
		"LblSearchXStatus": (188, 2, (8, 0), (), "LblSearchXStatus", None),
		"LblSearchYStatus": (192, 2, (8, 0), (), "LblSearchYStatus", None),
		"LblSettingsFilenameStatus": (91, 2, (8, 0), (), "LblSettingsFilenameStatus", None),
		"LblSpotDistanceStatus": (62, 2, (8, 0), (), "LblSpotDistanceStatus", None),
		"LblStatusStatus": (4, 2, (8, 0), (), "LblStatusStatus", None),
		"LblWaitTimeStatus": (395, 2, (8, 0), (), "LblWaitTimeStatus", None),
		"LblXStatus": (58, 2, (8, 0), (), "LblXStatus", None),
		"LblYStatus": (59, 2, (8, 0), (), "LblYStatus", None),
		"LowDoseActive": (155, 2, (3, 0), (), "LowDoseActive", None),
		"LowDoseAvailable": (66, 2, (11, 0), (), "LowDoseAvailable", None),
		"LowDoseExpose": (159, 2, (11, 0), (), "LowDoseExpose", None),
		"LowDoseState": (158, 2, (3, 0), (), "LowDoseState", None),
		"LowDoseVersion": (201, 2, (5, 0), (), "LowDoseVersion", None),
		"LstCamerasChange": (326, 2, (3, 0), (), "LstCamerasChange", None),
		"LstCamerasItem": (253, 2, (3, 0), (), "LstCamerasItem", None),
		"LstCamerasItem1": (145, 2, (8, 0), (), "LstCamerasItem1", None),
		"LstCamerasItem2": (146, 2, (8, 0), (), "LstCamerasItem2", None),
		"LstCamerasItem3": (147, 2, (8, 0), (), "LstCamerasItem3", None),
		"LstCamerasItem4": (148, 2, (8, 0), (), "LstCamerasItem4", None),
		"LstCamerasNoOfItems": (144, 2, (3, 0), (), "LstCamerasNoOfItems", None),
		"LstControllersChange": (325, 2, (3, 0), (), "LstControllersChange", None),
		"LstControllersItem": (252, 2, (3, 0), (), "LstControllersItem", None),
		"LstControllersItem1": (140, 2, (8, 0), (), "LstControllersItem1", None),
		"LstControllersItem2": (141, 2, (8, 0), (), "LstControllersItem2", None),
		"LstControllersItem3": (142, 2, (8, 0), (), "LstControllersItem3", None),
		"LstControllersItem4": (143, 2, (8, 0), (), "LstControllersItem4", None),
		"LstControllersNoOfItems": (139, 2, (3, 0), (), "LstControllersNoOfItems", None),
		"LstDoubleChange": (320, 2, (3, 0), (), "LstDoubleChange", None),
		"LstDoubleNoOfItems": (42, 2, (3, 0), (), "LstDoubleNoOfItems", None),
		"LstDoubleSelected": (321, 2, (3, 0), (), "LstDoubleSelected", None),
		"LstSeriesChange": (274, 2, (3, 0), (), "LstSeriesChange", None),
		"LstSeriesNoOfItems": (36, 2, (3, 0), (), "LstSeriesNoOfItems", None),
		"LstSeriesSelected": (319, 2, (3, 0), (), "LstSeriesSelected", None),
		"MemCalibrationLine1": (100, 2, (8, 0), (), "MemCalibrationLine1", None),
		"MemCalibrationLine2": (101, 2, (8, 0), (), "MemCalibrationLine2", None),
		"MemCalibrationLine3": (102, 2, (8, 0), (), "MemCalibrationLine3", None),
		"MemCalibrationLine4": (103, 2, (8, 0), (), "MemCalibrationLine4", None),
		"MemCalibrationLine5": (104, 2, (8, 0), (), "MemCalibrationLine5", None),
		"MemCalibrationLine6": (105, 2, (8, 0), (), "MemCalibrationLine6", None),
		"MemCalibrationLine7": (106, 2, (8, 0), (), "MemCalibrationLine7", None),
		"MemCalibrationLine8": (107, 2, (8, 0), (), "MemCalibrationLine8", None),
		"MemCalibrationNoOfLines": (99, 2, (3, 0), (), "MemCalibrationNoOfLines", None),
		"MemCalibrationStatus": (98, 2, (3, 0), (), "MemCalibrationStatus", None),
		"OptCcdBelowStatus": (153, 2, (3, 0), (), "OptCcdBelowStatus", None),
		"OptCcdUnderStatus": (154, 2, (3, 0), (), "OptCcdUnderStatus", None),
		"OptCcdWideStatus": (152, 2, (3, 0), (), "OptCcdWideStatus", None),
		"OptExposureAllStatus": (88, 2, (3, 0), (), "OptExposureAllStatus", None),
		"OptExposureCcdStatus": (90, 2, (3, 0), (), "OptExposureCcdStatus", None),
		"OptExposureModeStatus": (87, 2, (3, 0), (), "OptExposureModeStatus", None),
		"OptExposurePlateStatus": (89, 2, (3, 0), (), "OptExposurePlateStatus", None),
		"OptFocus1Status": (7, 2, (3, 0), (), "OptFocus1Status", None),
		"OptFocus2Status": (8, 2, (3, 0), (), "OptFocus2Status", None),
		"OptFocusAllStatus": (82, 2, (3, 0), (), "OptFocusAllStatus", None),
		"OptFocusCcdStatus": (85, 2, (3, 0), (), "OptFocusCcdStatus", None),
		"OptFocusModeStatus": (81, 2, (3, 0), (), "OptFocusModeStatus", None),
		"OptFocusScreenStatus": (83, 2, (3, 0), (), "OptFocusScreenStatus", None),
		"OptFocusTvStatus": (84, 2, (3, 0), (), "OptFocusTvStatus", None),
		"OptHexagonalStatus": (47, 2, (3, 0), (), "OptHexagonalStatus", None),
		"OptNoneStatus": (52, 2, (3, 0), (), "OptNoneStatus", None),
		"OptOutlineStatus": (53, 2, (3, 0), (), "OptOutlineStatus", None),
		"OptSearchAllStatus": (76, 2, (3, 0), (), "OptSearchAllStatus", None),
		"OptSearchCcdStatus": (79, 2, (3, 0), (), "OptSearchCcdStatus", None),
		"OptSearchModeStatus": (75, 2, (3, 0), (), "OptSearchModeStatus", None),
		"OptSearchScreenStatus": (77, 2, (3, 0), (), "OptSearchScreenStatus", None),
		"OptSearchTvStatus": (78, 2, (3, 0), (), "OptSearchTvStatus", None),
		"OptSpotWobbleStatus": (60, 2, (3, 0), (), "OptSpotWobbleStatus", None),
		"OptSquareStatus": (48, 2, (3, 0), (), "OptSquareStatus", None),
		"OptStaticXStatus": (54, 2, (3, 0), (), "OptStaticXStatus", None),
		"OptStaticYStatus": (55, 2, (3, 0), (), "OptStaticYStatus", None),
		"OptTvBelowStatus": (150, 2, (3, 0), (), "OptTvBelowStatus", None),
		"OptTvUnderStatus": (151, 2, (3, 0), (), "OptTvUnderStatus", None),
		"OptTvWideStatus": (149, 2, (3, 0), (), "OptTvWideStatus", None),
		"OptionCcdPresent": (251, 2, (11, 0), (), "OptionCcdPresent", None),
		"OptionDimScreen": (160, 2, (11, 0), (), "OptionDimScreen", None),
		"OptionDoDouble": (162, 2, (11, 0), (), "OptionDoDouble", None),
		"OptionDoSeries": (161, 2, (11, 0), (), "OptionDoSeries", None),
		"OptionExposureMedium": (234, 2, (3, 0), (), "OptionExposureMedium", None),
		"OptionExposureReset": (233, 2, (3, 0), (), "OptionExposureReset", None),
		"OptionFEC1": (210, 2, (11, 0), (), "OptionFEC1", None),
		"OptionFEC2": (211, 2, (11, 0), (), "OptionFEC2", None),
		"OptionFEProj": (212, 2, (11, 0), (), "OptionFEProj", None),
		"OptionFSC1": (206, 2, (11, 0), (), "OptionFSC1", None),
		"OptionFSC2": (207, 2, (11, 0), (), "OptionFSC2", None),
		"OptionFSObj": (208, 2, (11, 0), (), "OptionFSObj", None),
		"OptionFSProj": (209, 2, (11, 0), (), "OptionFSProj", None),
		"OptionFocusCorrection": (258, 2, (11, 0), (), "OptionFocusCorrection", None),
		"OptionFocusMedium": (232, 2, (3, 0), (), "OptionFocusMedium", None),
		"OptionFocusReset": (231, 2, (3, 0), (), "OptionFocusReset", None),
		"OptionNormC1": (396, 2, (11, 0), (), "OptionNormC1", None),
		"OptionNormC2": (397, 2, (11, 0), (), "OptionNormC2", None),
		"OptionNormObj": (398, 2, (11, 0), (), "OptionNormObj", None),
		"OptionNormProj": (399, 2, (11, 0), (), "OptionNormProj", None),
		"OptionSFC1": (202, 2, (11, 0), (), "OptionSFC1", None),
		"OptionSFC2": (203, 2, (11, 0), (), "OptionSFC2", None),
		"OptionSFObj": (204, 2, (11, 0), (), "OptionSFObj", None),
		"OptionSFProj": (205, 2, (11, 0), (), "OptionSFProj", None),
		"OptionSearchMedium": (230, 2, (3, 0), (), "OptionSearchMedium", None),
		"OptionSearchReset": (229, 2, (3, 0), (), "OptionSearchReset", None),
		"OptionSpotscanSetup": (260, 2, (3, 0), (), "OptionSpotscanSetup", None),
		"OptionTvPresent": (250, 2, (11, 0), (), "OptionTvPresent", None),
		"OptionUseSpotscan": (163, 2, (11, 0), (), "OptionUseSpotscan", None),
		"PeekActive": (157, 2, (11, 0), (), "PeekActive", None),
		"PeekEnabled": (215, 2, (11, 0), (), "PeekEnabled", None),
		"PlateExposureTime": (164, 2, (5, 0), (), "PlateExposureTime", None),
		"PreExpose": (168, 2, (11, 0), (), "PreExpose", None),
		"PreExposeTime": (169, 2, (5, 0), (), "PreExposeTime", None),
		"ProgressBarStatus": (65, 2, (3, 0), (), "ProgressBarStatus", None),
		"ProgressBarValue": (67, 2, (3, 0), (), "ProgressBarValue", None),
		"ScrAngleLineSize": (177, 2, (3, 0), (), "ScrAngleLineSize", None),
		"ScrAnglePageSize": (178, 2, (3, 0), (), "ScrAnglePageSize", None),
		"ScrAnglePosition": (176, 2, (3, 0), (), "ScrAnglePosition", None),
		"ScrAngleStatus": (34, 2, (3, 0), (), "ScrAngleStatus", None),
		"ScrCalibrationSpotscanMax": (330, 2, (3, 0), (), "ScrCalibrationSpotscanMax", None),
		"ScrCalibrationSpotscanPosition": (111, 2, (3, 0), (), "ScrCalibrationSpotscanPosition", None),
		"ScrCalibrationSpotscanStatus": (110, 2, (3, 0), (), "ScrCalibrationSpotscanStatus", None),
		"ScrDistanceLineSize": (174, 2, (3, 0), (), "ScrDistanceLineSize", None),
		"ScrDistanceMaximum": (33, 2, (3, 0), (), "ScrDistanceMaximum", None),
		"ScrDistancePageSize": (175, 2, (3, 0), (), "ScrDistancePageSize", None),
		"ScrDistancePosition": (173, 2, (3, 0), (), "ScrDistancePosition", None),
		"ScrDistanceStatus": (32, 2, (3, 0), (), "ScrDistanceStatus", None),
		"ScrSpotDistanceMax": (184, 2, (3, 0), (), "ScrSpotDistanceMax", None),
		"ScrSpotDistancePosition": (183, 2, (3, 0), (), "ScrSpotDistancePosition", None),
		"ScrSpotDistanceStatus": (61, 2, (3, 0), (), "ScrSpotDistanceStatus", None),
		"ScrXMax": (180, 2, (3, 0), (), "ScrXMax", None),
		"ScrXPosition": (179, 2, (3, 0), (), "ScrXPosition", None),
		"ScrXStatus": (56, 2, (3, 0), (), "ScrXStatus", None),
		"ScrYMax": (182, 2, (3, 0), (), "ScrYMax", None),
		"ScrYPosition": (181, 2, (3, 0), (), "ScrYPosition", None),
		"ScrYStatus": (57, 2, (3, 0), (), "ScrYStatus", None),
		"ScreenDiameterLabelStatus": (390, 2, (8, 0), (), "ScreenDiameterLabelStatus", None),
		"SearchBeamShiftX": (355, 2, (5, 0), (), "SearchBeamShiftX", None),
		"SearchBeamShiftY": (356, 2, (5, 0), (), "SearchBeamShiftY", None),
		"SearchC2": (349, 2, (5, 0), (), "SearchC2", None),
		"SearchClIndex": (343, 2, (3, 0), (), "SearchClIndex", None),
		"SearchClMode": (344, 2, (3, 0), (), "SearchClMode", None),
		"SearchClValue": (347, 2, (5, 0), (), "SearchClValue", None),
		"SearchDifLens": (351, 2, (5, 0), (), "SearchDifLens", None),
		"SearchDiffShiftX": (359, 2, (5, 0), (), "SearchDiffShiftX", None),
		"SearchDiffShiftY": (360, 2, (5, 0), (), "SearchDiffShiftY", None),
		"SearchImageShiftX": (357, 2, (5, 0), (), "SearchImageShiftX", None),
		"SearchImageShiftY": (358, 2, (5, 0), (), "SearchImageShiftY", None),
		"SearchIndex": (340, 2, (3, 0), (), "SearchIndex", None),
		"SearchIntensity": (348, 2, (5, 0), (), "SearchIntensity", None),
		"SearchMagnIndex": (341, 2, (3, 0), (), "SearchMagnIndex", None),
		"SearchMagnMode": (342, 2, (3, 0), (), "SearchMagnMode", None),
		"SearchMagnValue": (346, 2, (5, 0), (), "SearchMagnValue", None),
		"SearchMode": (339, 2, (3, 0), (), "SearchMode", None),
		"SearchObjLens": (350, 2, (5, 0), (), "SearchObjLens", None),
		"SearchShiftMf": (217, 2, (11, 0), (), "SearchShiftMf", None),
		"SearchSpot": (345, 2, (3, 0), (), "SearchSpot", None),
		"Series1": (275, 2, (5, 0), (), "Series1", None),
		"Series10": (284, 2, (5, 0), (), "Series10", None),
		"Series11": (285, 2, (5, 0), (), "Series11", None),
		"Series12": (286, 2, (5, 0), (), "Series12", None),
		"Series13": (287, 2, (5, 0), (), "Series13", None),
		"Series14": (288, 2, (5, 0), (), "Series14", None),
		"Series15": (289, 2, (5, 0), (), "Series15", None),
		"Series16": (290, 2, (5, 0), (), "Series16", None),
		"Series17": (291, 2, (5, 0), (), "Series17", None),
		"Series18": (292, 2, (5, 0), (), "Series18", None),
		"Series19": (293, 2, (5, 0), (), "Series19", None),
		"Series2": (276, 2, (5, 0), (), "Series2", None),
		"Series20": (294, 2, (5, 0), (), "Series20", None),
		"Series3": (277, 2, (5, 0), (), "Series3", None),
		"Series4": (278, 2, (5, 0), (), "Series4", None),
		"Series5": (279, 2, (5, 0), (), "Series5", None),
		"Series6": (280, 2, (5, 0), (), "Series6", None),
		"Series7": (281, 2, (5, 0), (), "Series7", None),
		"Series8": (282, 2, (5, 0), (), "Series8", None),
		"Series9": (283, 2, (5, 0), (), "Series9", None),
		"SettingsFilename": (189, 2, (8, 0), (), "SettingsFilename", None),
		"SpinExpTimeIncrement": (195, 2, (3, 0), (), "SpinExpTimeIncrement", None),
		"SpinExpTimePosition": (194, 2, (3, 0), (), "SpinExpTimePosition", None),
		"SpinPreExposePosition": (199, 2, (3, 0), (), "SpinPreExposePosition", None),
		"SpinSpotDwellTimeIncrement": (197, 2, (3, 0), (), "SpinSpotDwellTimeIncrement", None),
		"SpinSpotDwellTimePosition": (196, 2, (3, 0), (), "SpinSpotDwellTimePosition", None),
		"SpinWaitAfterPreExpPosition": (200, 2, (3, 0), (), "SpinWaitAfterPreExpPosition", None),
		"SpinWaitTimePosition": (198, 2, (3, 0), (), "SpinWaitTimePosition", None),
		"SpinWaitTimeStatus": (394, 2, (3, 0), (), "SpinWaitTimeStatus", None),
		"SpotscanDwellTime": (166, 2, (5, 0), (), "SpotscanDwellTime", None),
		"SpotscanEnabled": (265, 2, (11, 0), (), "SpotscanEnabled", None),
		"SpotscanInSecurityKey": (401, 2, (11, 0), (), "SpotscanInSecurityKey", None),
		"SpotscanNoOfSpots": (170, 2, (3, 0), (), "SpotscanNoOfSpots", None),
		"SpotscanOrientation": (257, 2, (5, 0), (), "SpotscanOrientation", None),
		"SpotscanPattern": (256, 2, (3, 0), (), "SpotscanPattern", None),
		"SpotscanSpotDistance": (263, 2, (5, 0), (), "SpotscanSpotDistance", None),
		"SpotscanStemMagnification": (254, 2, (5, 0), (), "SpotscanStemMagnification", None),
		"SpotscanXRange": (261, 2, (5, 0), (), "SpotscanXRange", None),
		"SpotscanYRange": (262, 2, (5, 0), (), "SpotscanYRange", None),
		"SwitchSFEF": (213, 2, (11, 0), (), "SwitchSFEF", None),
		"TestModeEnabled": (30, 2, (11, 0), (), "TestModeEnabled", None),
		"TvSelected": (337, 2, (3, 0), (), "TvSelected", None),
		"UseTvCcd": (216, 2, (11, 0), (), "UseTvCcd", None),
		"UserButtonBlank": (219, 2, (3, 0), (), "UserButtonBlank", None),
		"UserButtonExposure": (223, 2, (3, 0), (), "UserButtonExposure", None),
		"UserButtonFocus": (222, 2, (3, 0), (), "UserButtonFocus", None),
		"UserButtonPeek": (220, 2, (3, 0), (), "UserButtonPeek", None),
		"UserButtonSearch": (221, 2, (3, 0), (), "UserButtonSearch", None),
		"WaitAfterPreExpose": (171, 2, (11, 0), (), "WaitAfterPreExpose", None),
		"WaitAfterPreExposeTime": (172, 2, (5, 0), (), "WaitAfterPreExposeTime", None),
		"WaitTime": (167, 2, (3, 0), (), "WaitTime", None),
	}
	_prop_map_put_ = {
		"BeamBlanked": ((156, LCID, 4, 0),()),
		"CalibrationFilename": ((193, LCID, 4, 0),()),
		"CcdExposureTime": ((165, LCID, 4, 0),()),
		"CcdSelected": ((338, LCID, 4, 0),()),
		"ChkDetailedLogStatus": ((334, LCID, 4, 0),()),
		"ChkSkipCloseShutterStatus": ((333, LCID, 4, 0),()),
		"ChkSkipPlateInStatus": ((332, LCID, 4, 0),()),
		"ChkSkipScreenUpStatus": ((331, LCID, 4, 0),()),
		"ContinuousDose": ((225, LCID, 4, 0),()),
		"Double1": ((299, LCID, 4, 0),()),
		"Double10": ((308, LCID, 4, 0),()),
		"Double11": ((309, LCID, 4, 0),()),
		"Double12": ((310, LCID, 4, 0),()),
		"Double13": ((311, LCID, 4, 0),()),
		"Double14": ((312, LCID, 4, 0),()),
		"Double15": ((313, LCID, 4, 0),()),
		"Double16": ((314, LCID, 4, 0),()),
		"Double17": ((315, LCID, 4, 0),()),
		"Double18": ((316, LCID, 4, 0),()),
		"Double19": ((317, LCID, 4, 0),()),
		"Double2": ((300, LCID, 4, 0),()),
		"Double20": ((318, LCID, 4, 0),()),
		"Double3": ((301, LCID, 4, 0),()),
		"Double4": ((302, LCID, 4, 0),()),
		"Double5": ((303, LCID, 4, 0),()),
		"Double6": ((304, LCID, 4, 0),()),
		"Double7": ((305, LCID, 4, 0),()),
		"Double8": ((306, LCID, 4, 0),()),
		"Double9": ((307, LCID, 4, 0),()),
		"EdDiameterStatus": ((35, LCID, 4, 0),()),
		"EdDoubleStatus": ((329, LCID, 4, 0),()),
		"EdExpTimeStatus": ((41, LCID, 4, 0),()),
		"EdSeriesStatus": ((328, LCID, 4, 0),()),
		"ExposureBeamShiftX": ((388, LCID, 4, 0),()),
		"ExposureBeamShiftY": ((389, LCID, 4, 0),()),
		"ExposureDiffShiftX": ((392, LCID, 4, 0),()),
		"ExposureDiffShiftY": ((393, LCID, 4, 0),()),
		"Focus1ShiftAngle": ((372, LCID, 4, 0),()),
		"Focus1ShiftDistance": ((371, LCID, 4, 0),()),
		"Focus2ShiftAngle": ((374, LCID, 4, 0),()),
		"Focus2ShiftDistance": ((373, LCID, 4, 0),()),
		"FocusBeamShift1X": ((367, LCID, 4, 0),()),
		"FocusBeamShift1Y": ((368, LCID, 4, 0),()),
		"FocusBeamShift2X": ((369, LCID, 4, 0),()),
		"FocusBeamShift2Y": ((370, LCID, 4, 0),()),
		"FocusCorrectionOffset": ((259, LCID, 4, 0),()),
		"FocusShiftMf": ((218, LCID, 4, 0),()),
		"LowDoseActive": ((155, LCID, 4, 0),()),
		"LowDoseExpose": ((159, LCID, 4, 0),()),
		"LowDoseState": ((158, LCID, 4, 0),()),
		"LstCamerasItem": ((253, LCID, 4, 0),()),
		"LstControllersItem": ((252, LCID, 4, 0),()),
		"LstDoubleSelected": ((321, LCID, 4, 0),()),
		"LstSeriesSelected": ((319, LCID, 4, 0),()),
		"OptionCcdPresent": ((251, LCID, 4, 0),()),
		"OptionDimScreen": ((160, LCID, 4, 0),()),
		"OptionDoDouble": ((162, LCID, 4, 0),()),
		"OptionDoSeries": ((161, LCID, 4, 0),()),
		"OptionExposureMedium": ((234, LCID, 4, 0),()),
		"OptionExposureReset": ((233, LCID, 4, 0),()),
		"OptionFEC1": ((210, LCID, 4, 0),()),
		"OptionFEC2": ((211, LCID, 4, 0),()),
		"OptionFEProj": ((212, LCID, 4, 0),()),
		"OptionFSC1": ((206, LCID, 4, 0),()),
		"OptionFSC2": ((207, LCID, 4, 0),()),
		"OptionFSObj": ((208, LCID, 4, 0),()),
		"OptionFSProj": ((209, LCID, 4, 0),()),
		"OptionFocusCorrection": ((258, LCID, 4, 0),()),
		"OptionFocusMedium": ((232, LCID, 4, 0),()),
		"OptionFocusReset": ((231, LCID, 4, 0),()),
		"OptionNormC1": ((396, LCID, 4, 0),()),
		"OptionNormC2": ((397, LCID, 4, 0),()),
		"OptionNormObj": ((398, LCID, 4, 0),()),
		"OptionNormProj": ((399, LCID, 4, 0),()),
		"OptionSFC1": ((202, LCID, 4, 0),()),
		"OptionSFC2": ((203, LCID, 4, 0),()),
		"OptionSFObj": ((204, LCID, 4, 0),()),
		"OptionSFProj": ((205, LCID, 4, 0),()),
		"OptionSearchMedium": ((230, LCID, 4, 0),()),
		"OptionSearchReset": ((229, LCID, 4, 0),()),
		"OptionSpotscanSetup": ((260, LCID, 4, 0),()),
		"OptionTvPresent": ((250, LCID, 4, 0),()),
		"OptionUseSpotscan": ((163, LCID, 4, 0),()),
		"PeekActive": ((157, LCID, 4, 0),()),
		"PeekEnabled": ((215, LCID, 4, 0),()),
		"PlateExposureTime": ((164, LCID, 4, 0),()),
		"PreExpose": ((168, LCID, 4, 0),()),
		"PreExposeTime": ((169, LCID, 4, 0),()),
		"ScrAnglePosition": ((176, LCID, 4, 0),()),
		"ScrCalibrationSpotscanPosition": ((111, LCID, 4, 0),()),
		"ScrDistancePosition": ((173, LCID, 4, 0),()),
		"ScrSpotDistancePosition": ((183, LCID, 4, 0),()),
		"ScrXPosition": ((179, LCID, 4, 0),()),
		"ScrYPosition": ((181, LCID, 4, 0),()),
		"SearchBeamShiftX": ((355, LCID, 4, 0),()),
		"SearchBeamShiftY": ((356, LCID, 4, 0),()),
		"SearchDiffShiftX": ((359, LCID, 4, 0),()),
		"SearchDiffShiftY": ((360, LCID, 4, 0),()),
		"SearchImageShiftX": ((357, LCID, 4, 0),()),
		"SearchImageShiftY": ((358, LCID, 4, 0),()),
		"SearchShiftMf": ((217, LCID, 4, 0),()),
		"Series1": ((275, LCID, 4, 0),()),
		"Series10": ((284, LCID, 4, 0),()),
		"Series11": ((285, LCID, 4, 0),()),
		"Series12": ((286, LCID, 4, 0),()),
		"Series13": ((287, LCID, 4, 0),()),
		"Series14": ((288, LCID, 4, 0),()),
		"Series15": ((289, LCID, 4, 0),()),
		"Series16": ((290, LCID, 4, 0),()),
		"Series17": ((291, LCID, 4, 0),()),
		"Series18": ((292, LCID, 4, 0),()),
		"Series19": ((293, LCID, 4, 0),()),
		"Series2": ((276, LCID, 4, 0),()),
		"Series20": ((294, LCID, 4, 0),()),
		"Series3": ((277, LCID, 4, 0),()),
		"Series4": ((278, LCID, 4, 0),()),
		"Series5": ((279, LCID, 4, 0),()),
		"Series6": ((280, LCID, 4, 0),()),
		"Series7": ((281, LCID, 4, 0),()),
		"Series8": ((282, LCID, 4, 0),()),
		"Series9": ((283, LCID, 4, 0),()),
		"SettingsFilename": ((189, LCID, 4, 0),()),
		"SpinExpTimePosition": ((194, LCID, 4, 0),()),
		"SpinPreExposePosition": ((199, LCID, 4, 0),()),
		"SpinSpotDwellTimePosition": ((196, LCID, 4, 0),()),
		"SpinWaitAfterPreExpPosition": ((200, LCID, 4, 0),()),
		"SpinWaitTimePosition": ((198, LCID, 4, 0),()),
		"SpotscanDwellTime": ((166, LCID, 4, 0),()),
		"SpotscanOrientation": ((257, LCID, 4, 0),()),
		"SpotscanPattern": ((256, LCID, 4, 0),()),
		"SpotscanStemMagnification": ((254, LCID, 4, 0),()),
		"SwitchSFEF": ((213, LCID, 4, 0),()),
		"TvSelected": ((337, LCID, 4, 0),()),
		"UseTvCcd": ((216, LCID, 4, 0),()),
		"UserButtonBlank": ((219, LCID, 4, 0),()),
		"UserButtonExposure": ((223, LCID, 4, 0),()),
		"UserButtonFocus": ((222, LCID, 4, 0),()),
		"UserButtonPeek": ((220, LCID, 4, 0),()),
		"UserButtonSearch": ((221, LCID, 4, 0),()),
		"WaitAfterPreExpose": ((171, LCID, 4, 0),()),
		"WaitAfterPreExposeTime": ((172, LCID, 4, 0),()),
		"WaitTime": ((167, LCID, 4, 0),()),
	}

class ILdSrvEvents:
	"""Events interface for Low Dose Server"""
	CLSID = CLSID_Sink = pythoncom.MakeIID('{9BEC9754-A820-11D3-972E-81B6519D0DF8}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		        7 : "OnSettingsControlChanged",
		       22 : "OnDoubleControlError",
		       24 : "OnSettingsControlError",
		       30 : "OnSettingChanged",
		        2 : "OnExposeControlChanged",
		       14 : "OnLowDoseStateChanged",
		        5 : "OnDoubleControlChanged",
		       16 : "OnExposeStatusChanged",
		       18 : "OnMainControlError",
		        8 : "OnCalibrateControlChanged",
		       28 : "OnTestModeControlChanged",
		        9 : "OnOptionsControlChanged",
		       27 : "OnTvControlError",
		       21 : "OnSeriesControlError",
		       26 : "OnOptionsControlError",
		       19 : "OnExposeControlError",
		       32 : "OnSetMessageBox",
		        4 : "OnSeriesControlChanged",
		       10 : "OnTvControlChanged",
		       15 : "OnServerIsClosing",
		       31 : "OnSettingError",
		        6 : "OnSpotscanControlChanged",
		        3 : "OnFocusControlChanged",
		       29 : "OnTestModeControlError",
		       11 : "OnLowDoseActiveChanged",
		       23 : "OnSpotscanControlError",
		       20 : "OnFocusControlError",
		       12 : "OnBeamBlankChanged",
		        1 : "OnMainControlChanged",
		       25 : "OnCalibrateControlError",
		       13 : "OnPeekChanged",
		       17 : "OnErrorStateChanged",
		}

	def __init__(self, oobj = None):
		if oobj is None:
			self._olecp = None
		else:
			import win32com.server.util
			from win32com.server.policy import EventHandlerPolicy
			cpc=oobj._oleobj_.QueryInterface(pythoncom.IID_IConnectionPointContainer)
			cp=cpc.FindConnectionPoint(self.CLSID_Sink)
			cookie=cp.Advise(win32com.server.util.wrap(self, usePolicy=EventHandlerPolicy))
			self._olecp,self._olecp_cookie = cp,cookie
	def __del__(self):
		try:
			self.close()
		except pythoncom.com_error:
			pass
	def close(self):
		if self._olecp is not None:
			cp,cookie,self._olecp,self._olecp_cookie = self._olecp,self._olecp_cookie,None,None
			cp.Unadvise(cookie)
	def _query_interface_(self, iid):
		import win32com.server.util
		if iid==self.CLSID_Sink: return win32com.server.util.wrap(self)

	# Handlers for the control
	# If you create handlers, they should have the following prototypes:
#	def OnSettingsControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnDoubleControlError(self, Data=defaultNamedNotOptArg):
#	def OnSettingsControlError(self, Data=defaultNamedNotOptArg):
#	def OnSettingChanged(self, Data=defaultNamedNotOptArg):
#	def OnExposeControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnLowDoseStateChanged(self, Data=defaultNamedNotOptArg):
#	def OnDoubleControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnExposeStatusChanged(self, Data=defaultNamedNotOptArg):
#	def OnMainControlError(self, Data=defaultNamedNotOptArg):
#	def OnCalibrateControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnTestModeControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnOptionsControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnTvControlError(self, Data=defaultNamedNotOptArg):
#	def OnSeriesControlError(self, Data=defaultNamedNotOptArg):
#	def OnOptionsControlError(self, Data=defaultNamedNotOptArg):
#	def OnExposeControlError(self, Data=defaultNamedNotOptArg):
#	def OnSetMessageBox(self, BoxText=defaultNamedNotOptArg, BoxTitle=defaultNamedNotOptArg, BoxButtons=defaultNamedNotOptArg):
#	def OnSeriesControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnTvControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnServerIsClosing(self):
#	def OnSettingError(self, Data=defaultNamedNotOptArg):
#	def OnSpotscanControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnFocusControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnTestModeControlError(self, Data=defaultNamedNotOptArg):
#	def OnLowDoseActiveChanged(self, Data=defaultNamedNotOptArg):
#	def OnSpotscanControlError(self, Data=defaultNamedNotOptArg):
#	def OnFocusControlError(self, Data=defaultNamedNotOptArg):
#	def OnBeamBlankChanged(self, Data=defaultNamedNotOptArg):
#	def OnMainControlChanged(self, Data=defaultNamedNotOptArg):
#	def OnCalibrateControlError(self, Data=defaultNamedNotOptArg):
#	def OnPeekChanged(self, Data=defaultNamedNotOptArg):
#	def OnErrorStateChanged(self, Data=defaultNamedNotOptArg):


class CoClassBaseClass:
	def __init__(self, oobj=None):
		if oobj is None: oobj = pythoncom.new(self.CLSID)
		self.__dict__["_dispobj_"] = self.default_interface(oobj)
	def __repr__(self):
		return "<win32com.gen_py.%s.%s>" % (__doc__, self.__class__.__name__)

	def __getattr__(self, attr):
		d=self.__dict__["_dispobj_"]
		if d is not None: return getattr(d, attr)
		raise AttributeError, attr
	def __setattr__(self, attr, value):
		if self.__dict__.has_key(attr): self.__dict__[attr] = value; return
		try:
			d=self.__dict__["_dispobj_"]
			if d is not None:
				d.__setattr__(attr, value)
				return
		except AttributeError:
			pass
		self.__dict__[attr] = value

# This CoClass is known by the name 'LDServer.LdSrv'
class LdSrv(CoClassBaseClass): # A CoClass
	# Low Dose Server Object
	CLSID = pythoncom.MakeIID("{9BEC9756-A820-11D3-972E-81B6519D0DF8}")
	coclass_sources = [
		ILdSrvEvents,
	]
	default_source = ILdSrvEvents
	coclass_interfaces = [
		ILdSrv,
	]
	default_interface = ILdSrv

ILdSrv_vtables_dispatch_ = 1
ILdSrv_vtables_ =  [('LoadSettingsFromFile', 186, ((16392, 3, None), (16396, 3, None)), (3, 0, None), ('Filename', 'Arr')), ('SaveSettingsToFile', 187, ((16392, 3, None), (16396, 3, None)), (3, 0, None), ('Filename', 'Arr')), ('LoadCalFromFile', 190, ((16392, 3, None), (16396, 3, None)), (3, 0, None), ('Filename', 'Arr')), ('SaveCalToFile', 191, ((16392, 3, None), (16396, 3, None)), (3, 0, None), ('Filename', 'Arr')), ('Normalize', 214, ((3, 1, None),), (3, 0, None), ('Param',)), ('MeasureDose', 224, ((11, 1, None),), (3, 0, None), ('Start',)), ('ResetSearchSettings', 226, (), (3, 0, None), ()), ('ResetFocusSettings', 227, (), (3, 0, None), ()), ('ResetExposureSettings', 228, (), (3, 0, None), ()), ('CalibrateBeamBlanker', 235, (), (3, 0, None), ()), ('CalibrateImageTilt', 236, (), (3, 0, None), ()), ('CalibratePeek', 237, (), (3, 0, None), ()), ('CalibrateAcPivotPoints', 238, (), (3, 0, None), ()), ('CalibrateAcBeamShift', 239, (), (3, 0, None), ()), ('CalibrateFocusIntensity', 240, (), (3, 0, None), ()), ('CalibrateOk', 241, (), (3, 0, None), ()), ('CalibrateCancel', 242, (), (3, 0, None), ()), ('SpotscanView', 244, ((11, 1, None),), (3, 0, None), ('Start',)), ('SpotscanSlower', 245, (), (3, 0, None), ()), ('SpotscanFaster', 246, (), (3, 0, None), ()), ('SpotscanTo0', 247, (), (3, 0, None), ()), ('SpotscanShiftAway', 248, (), (3, 0, None), ()), ('SpotscanAcOff', 249, (), (3, 0, None), ()), ('ScreenDimSet', 266, ((3, 1, None),), (3, 0, None), ('Dim',)), ('ScreenDimPosition', 267, ((3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None)), (3, 0, None), ('fDimDisplay', 'fDimLeft', 'fDimTop', 'fDimWidth', 'fDimHeight')), ('ScreenDimTimeOut', 268, ((3, 1, None),), (3, 0, None), ('DimTimeOut',)), ('SeriesAdd', 270, (), (3, 0, None), ()), ('SeriesDelete', 271, (), (3, 0, None), ()), ('SeriesUp', 272, (), (3, 0, None), ()), ('SeriesDown', 273, (), (3, 0, None), ()), ('DoubleAdd', 295, (), (3, 0, None), ()), ('DoubleDelete', 296, (), (3, 0, None), ()), ('DoubleUp', 297, (), (3, 0, None), ()), ('DoubleDown', 298, (), (3, 0, None), ()), ('SearchStartCcd', 322, ((11, 1, None),), (3, 0, None), ('Value',)), ('FocusStartCcd', 323, ((11, 1, None),), (3, 0, None), ('Value',)), ('SetTestMode', 130, ((8, 1, None),), (3, 0, None), ('Param1',)), ('ScreenDimText', 269, ((8, 1, None), (8, 1, None), (8, 1, None)), (3, 0, None), ('Txt1', 'Txt2', 'Txt3'))]

RecordMap = {
}

CLSIDToClassMap = {
	'{9BEC9752-A820-11D3-972E-81B6519D0DF8}' : ILdSrv,
	'{9BEC9754-A820-11D3-972E-81B6519D0DF8}' : ILdSrvEvents,
	'{9BEC9756-A820-11D3-972E-81B6519D0DF8}' : LdSrv,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
}


VTablesNamesToCLSIDMap = {
	'ILdSrv' : '{9BEC9752-A820-11D3-972E-81B6519D0DF8}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

