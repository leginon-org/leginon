# Created by makepy.py version 0.4.0
# By python version 2.2 (#28, Dec 21 2001, 12:21:22) [MSC 32 bit (Intel)]
# From type library 'stdscript.dll'
# On Tue Mar 05 15:13:05 2002
"""Tecnai Scripting"""
makepy_version = '0.4.0'
python_version = 0x20200f0

import win32com.client.CLSIDToClass, pythoncom

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Missing
defaultNamedNotOptArg=pythoncom.Missing
defaultUnnamedArg=pythoncom.Missing

CLSID = pythoncom.MakeIID('{BC0A2B03-10FF-11D3-AE00-00A024CBA50C}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	dfCartesian                   =0x2        # from enum DarkFieldMode
	dfConical                     =0x3        # from enum DarkFieldMode
	dfOff                         =0x1        # from enum DarkFieldMode
	plGaugePressurelevelHigh      =0x4        # from enum GaugePressureLevel
	plGaugePressurelevelLow       =0x1        # from enum GaugePressureLevel
	plGaugePressurelevelLowMedium =0x2        # from enum GaugePressureLevel
	plGaugePressurelevelMediumHigh=0x3        # from enum GaugePressureLevel
	plGaugePressurelevelUndefined =0x0        # from enum GaugePressureLevel
	gsInvalid                     =0x3        # from enum GaugeStatus
	gsOverflow                    =0x2        # from enum GaugeStatus
	gsUndefined                   =0x0        # from enum GaugeStatus
	gsUnderflow                   =0x1        # from enum GaugeStatus
	gsValid                       =0x4        # from enum GaugeStatus
	htDisabled                    =0x1        # from enum HightensionState
	htOff                         =0x2        # from enum HightensionState
	htOn                          =0x3        # from enum HightensionState
	imMicroProbe                  =0x1        # from enum IlluminationMode
	imNanoProbe                   =0x0        # from enum IlluminationMode
	nmAll                         =0x6        # from enum IlluminationNormalization
	nmCondenser                   =0x3        # from enum IlluminationNormalization
	nmIntensity                   =0x2        # from enum IlluminationNormalization
	nmMiniCondenser               =0x4        # from enum IlluminationNormalization
	nmObjectivePole               =0x5        # from enum IlluminationNormalization
	nmSpotsize                    =0x1        # from enum IlluminationNormalization
	lpEFTEM                       =0x2        # from enum LensProg
	lpRegular                     =0x1        # from enum LensProg
	dtDDMMYY                      =0x1        # from enum PlateLabelDateFormat
	dtMMDDYY                      =0x2        # from enum PlateLabelDateFormat
	dtNoDate                      =0x0        # from enum PlateLabelDateFormat
	dtYYMMDD                      =0x3        # from enum PlateLabelDateFormat
	pmDiffraction                 =0x2        # from enum ProjectionMode
	pmImaging                     =0x1        # from enum ProjectionMode
	pnmAll                        =0xc        # from enum ProjectionNormalization
	pnmObjective                  =0xa        # from enum ProjectionNormalization
	pnmProjector                  =0xb        # from enum ProjectionNormalization
	psmD                          =0x6        # from enum ProjectionSubMode
	psmLAD                        =0x5        # from enum ProjectionSubMode
	psmLM                         =0x1        # from enum ProjectionSubMode
	psmMh                         =0x4        # from enum ProjectionSubMode
	psmMi                         =0x2        # from enum ProjectionSubMode
	psmSA                         =0x3        # from enum ProjectionSubMode
	spDown                        =0x3        # from enum ScreenPosition
	spUnknown                     =0x1        # from enum ScreenPosition
	spUp                          =0x2        # from enum ScreenPosition
	axisA                         =0x8        # from enum StageAxes
	axisB                         =0x10       # from enum StageAxes
	axisX                         =0x1        # from enum StageAxes
	axisXY                        =0x3        # from enum StageAxes
	axisY                         =0x2        # from enum StageAxes
	axisZ                         =0x4        # from enum StageAxes
	hoDoubleTilt                  =0x2        # from enum StageHolderType
	hoInvalid                     =0x4        # from enum StageHolderType
	hoNone                        =0x0        # from enum StageHolderType
	hoSingleTilt                  =0x1        # from enum StageHolderType
	stDisabled                    =0x1        # from enum StageStatus
	stFree                        =0x6        # from enum StageStatus
	stGoing                       =0x3        # from enum StageStatus
	stMoving                      =0x4        # from enum StageStatus
	stNotReady                    =0x2        # from enum StageStatus
	stReady                       =0x0        # from enum StageStatus
	stWobbling                    =0x5        # from enum StageStatus
	E_NOT_OK                      =0x8004ffff # from enum TecnaiError
	E_OUT_OF_RANGE                =0x8004fffd # from enum TecnaiError
	E_VALUE_CLIP                  =0x8004fffe # from enum TecnaiError
	vsBusy                        =0x4        # from enum VacuumStatus
	vsCameraAir                   =0x3        # from enum VacuumStatus
	vsElse                        =0x6        # from enum VacuumStatus
	vsOff                         =0x2        # from enum VacuumStatus
	vsReady                       =0x5        # from enum VacuumStatus
	vsUnknown                     =0x1        # from enum VacuumStatus

from win32com.client import DispatchBaseClass
class Camera(DispatchBaseClass):
	"""Interface to the camera system"""
	CLSID = pythoncom.MakeIID('{9851BC41-1B8C-11D3-AE0A-00A024CBA50C}')

	def TakeExposure(self):
		"""Take a photo (uses current parameter settings)"""
		return self._oleobj_.InvokeTypes(0x5, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"ExposureNumber": (18, 2, (3, 0), (), "ExposureNumber", None),
		"FilmText": (14, 2, (8, 0), (), "FilmText", None),
		"IsSmallScreenDown": (12, 2, (11, 0), (), "IsSmallScreenDown", None),
		"MainScreen": (11, 2, (3, 0), (), "MainScreen", None),
		"ManualExposure": (21, 2, (11, 0), (), "ManualExposure", None),
		"ManualExposureTime": (15, 2, (5, 0), (), "ManualExposureTime", None),
		"MeasuredExposureTime": (13, 2, (5, 0), (), "MeasuredExposureTime", None),
		"PlateLabelDateType": (22, 2, (3, 0), (), "PlateLabelDateType", None),
		"PlateuMarker": (17, 2, (11, 0), (), "PlateuMarker", None),
		"ScreenCurrent": (25, 2, (5, 0), (), "ScreenCurrent", None),
		"ScreenDim": (23, 2, (11, 0), (), "ScreenDim", None),
		"ScreenDimText": (24, 2, (8, 0), (), "ScreenDimText", None),
		"Stock": (10, 2, (3, 0), (), "Stock", None),
		"Usercode": (19, 2, (8, 0), (), "Usercode", None),
	}
	_prop_map_put_ = {
		"ExposureNumber": ((18, LCID, 4, 0),()),
		"FilmText": ((14, LCID, 4, 0),()),
		"MainScreen": ((11, LCID, 4, 0),()),
		"ManualExposure": ((21, LCID, 4, 0),()),
		"ManualExposureTime": ((15, LCID, 4, 0),()),
		"PlateLabelDateType": ((22, LCID, 4, 0),()),
		"PlateuMarker": ((17, LCID, 4, 0),()),
		"ScreenDim": ((23, LCID, 4, 0),()),
		"ScreenDimText": ((24, LCID, 4, 0),()),
		"Usercode": ((19, LCID, 4, 0),()),
	}

class Gauge(DispatchBaseClass):
	"""Utility object: Vacuum system gauge data (pressure)"""
	CLSID = pythoncom.MakeIID('{52020820-18BF-11D3-86E1-00C04FC126DD}')

	def Read(self):
		"""Read gauge settings"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"Name": (10, 2, (8, 0), (), "Name", None),
		"Pressure": (11, 2, (5, 0), (), "Pressure", None),
		"PressureLevel": (13, 2, (3, 0), (), "PressureLevel", None),
		"Status": (12, 2, (3, 0), (), "Status", None),
	}
	_prop_map_put_ = {
	}

class Gauges(DispatchBaseClass):
	"""Vacuum system gauges collection"""
	CLSID = pythoncom.MakeIID('{6E6F03B0-2ECE-11D3-AE79-004095005B07}')

	# Result is of type Gauge
	# The method Item is actually a property, but must be used as a method to correctly pass the arguments
	def Item(self, index=defaultNamedNotOptArg):
		"""Get individual gauge"""
		ret = self._oleobj_.InvokeTypes(0x0, LCID, 2, (9, 0), ((12, 0),),index)
		if ret is not None: ret = win32com.client.Dispatch(ret, 'Item', '{52020820-18BF-11D3-86E1-00C04FC126DD}', UnicodeToString=0)
		return ret

	_prop_map_get_ = {
		"Count": (1, 2, (3, 0), (), "Count", None),
	}
	_prop_map_put_ = {
	}
	# Default method for this class is 'Item'
	def __call__(self, index=defaultNamedNotOptArg):
		"""Get individual gauge"""
		ret = self._oleobj_.InvokeTypes(0x0, LCID, 2, (9, 0), ((12, 0),),index)
		if ret is not None: ret = win32com.client.Dispatch(ret, '__call__', '{52020820-18BF-11D3-86E1-00C04FC126DD}', UnicodeToString=0)
		return ret

	# str(ob) and int(ob) will use __call__
	def __str__(self, *args):
		try:
			return str(apply( self.__call__, args))
		except pythoncom.com_error:
			return repr(self)
	def __int__(self, *args):
		return int(apply( self.__call__, args))
	def _NewEnum(self):
		"Create an enumerator from this object"
		return win32com.client.util.WrapEnum(self._oleobj_.InvokeTypes(-4,LCID,2,(13, 10),()),'{52020820-18BF-11D3-86E1-00C04FC126DD}')
	def __getitem__(self, index):
		"Allow this class to be accessed as a collection"
		if not self.__dict__.has_key('_enum_'):
			import win32com.client.util
			self.__dict__['_enum_'] = self._NewEnum()
		return self._enum_.__getitem__(index)
	#This class has Count() property - allow len(ob) to provide this
	def __len__(self):
		return apply(self._ApplyTypes_, (1, 2, (3, 0), (), "Count", None) )
	#This class has a __len__ - this is needed so 'if object:' always returns TRUE.
	def __nonzero__(self):
		return 1

class Gun(DispatchBaseClass):
	"""Gun Interface"""
	CLSID = pythoncom.MakeIID('{E6F00870-3164-11D3-B4C8-00A024CB9221}')

	_prop_map_get_ = {
		"HTMaxValue": (12, 2, (5, 0), (), "HTMaxValue", None),
		"HTState": (10, 2, (3, 0), (), "HTState", None),
		"HTValue": (11, 2, (5, 0), (), "HTValue", None),
		# Method 'Shift' returns object of type 'Vector'
		"Shift": (13, 2, (9, 0), (), "Shift", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		# Method 'Tilt' returns object of type 'Vector'
		"Tilt": (14, 2, (9, 0), (), "Tilt", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
	}
	_prop_map_put_ = {
		"HTState": ((10, LCID, 4, 0),()),
		"HTValue": ((11, LCID, 4, 0),()),
		"Shift": ((13, LCID, 4, 0),()),
		"Tilt": ((14, LCID, 4, 0),()),
	}

class IUserButton(DispatchBaseClass):
	"""User button"""
	CLSID = pythoncom.MakeIID('{E6F00871-3164-11D3-B4C8-00A024CB9221}')

	_prop_map_get_ = {
		"Assignment": (12, 2, (8, 0), (), "Assignment", None),
		"Label": (11, 2, (8, 0), (), "Label", None),
		"Name": (10, 2, (8, 0), (), "Name", None),
	}
	_prop_map_put_ = {
		"Assignment": ((12, LCID, 4, 0),()),
	}

class Illumination(DispatchBaseClass):
	"""Illumination Interface"""
	CLSID = pythoncom.MakeIID('{EF960690-1C38-11D3-AE0B-00A024CBA50C}')

	def Normalize(self, nm=defaultNamedNotOptArg):
		"""Normalization of illumination system"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), ((3, 0),),nm)

	_prop_map_get_ = {
		"BeamBlanked": (16, 2, (11, 0), (), "BeamBlanked", None),
		# Method 'CondenserStigmator' returns object of type 'Vector'
		"CondenserStigmator": (20, 2, (9, 0), (), "CondenserStigmator", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"DFMode": (21, 2, (3, 0), (), "DFMode", None),
		"Intensity": (13, 2, (5, 0), (), "Intensity", None),
		"IntensityLimitEnabled": (15, 2, (11, 0), (), "IntensityLimitEnabled", None),
		"IntensityZoomEnabled": (14, 2, (11, 0), (), "IntensityZoomEnabled", None),
		"Mode": (11, 2, (3, 0), (), "Mode", None),
		# Method 'RotationCenter' returns object of type 'Vector'
		"RotationCenter": (19, 2, (9, 0), (), "RotationCenter", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		# Method 'Shift' returns object of type 'Vector'
		"Shift": (17, 2, (9, 0), (), "Shift", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"SpotsizeIndex": (12, 2, (3, 0), (), "SpotsizeIndex", None),
		# Method 'Tilt' returns object of type 'Vector'
		"Tilt": (18, 2, (9, 0), (), "Tilt", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
	}
	_prop_map_put_ = {
		"BeamBlanked": ((16, LCID, 4, 0),()),
		"CondenserStigmator": ((20, LCID, 4, 0),()),
		"DFMode": ((21, LCID, 4, 0),()),
		"Intensity": ((13, LCID, 4, 0),()),
		"IntensityLimitEnabled": ((15, LCID, 4, 0),()),
		"IntensityZoomEnabled": ((14, LCID, 4, 0),()),
		"Mode": ((11, LCID, 4, 0),()),
		"RotationCenter": ((19, LCID, 4, 0),()),
		"Shift": ((17, LCID, 4, 0),()),
		"SpotsizeIndex": ((12, LCID, 4, 0),()),
		"Tilt": ((18, LCID, 4, 0),()),
	}

class InstrumentInterface(DispatchBaseClass):
	"""Instrument Interface"""
	CLSID = pythoncom.MakeIID('{BC0A2B11-10FF-11D3-AE00-00A024CBA50C}')

	def NormalizeAll(self):
		"""Normalize all lenses"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), (),)

	def ReturnError(self, TE=defaultNamedNotOptArg):
		"""Dummy to test error codes"""
		return self._oleobj_.InvokeTypes(0x3, LCID, 1, (24, 0), ((3, 1),),TE)

	_prop_map_get_ = {
		"AutoNormalizeEnabled": (2, 2, (11, 0), (), "AutoNormalizeEnabled", None),
		# Method 'Camera' returns object of type 'Camera'
		"Camera": (21, 2, (9, 0), (), "Camera", '{9851BC41-1B8C-11D3-AE0A-00A024CBA50C}'),
		# Method 'Gun' returns object of type 'Gun'
		"Gun": (25, 2, (9, 0), (), "Gun", '{E6F00870-3164-11D3-B4C8-00A024CB9221}'),
		# Method 'Illumination' returns object of type 'Illumination'
		"Illumination": (23, 2, (9, 0), (), "Illumination", '{EF960690-1C38-11D3-AE0B-00A024CBA50C}'),
		# Method 'Projection' returns object of type 'Projection'
		"Projection": (24, 2, (9, 0), (), "Projection", '{B39C3AE1-1E41-11D3-AE0E-00A024CBA50C}'),
		# Method 'Stage' returns object of type 'Stage'
		"Stage": (22, 2, (9, 0), (), "Stage", '{E7AE1E41-1BF8-11D3-AE0B-00A024CBA50C}'),
		"StagePosition": (12, 2, (9, 0), (), "StagePosition", None),
		# Method 'UserButtons' returns object of type 'UserButtons'
		"UserButtons": (26, 2, (9, 0), (), "UserButtons", '{50C21D10-317F-11D3-B4C8-00A024CB9221}'),
		# Method 'Vacuum' returns object of type 'Vacuum'
		"Vacuum": (20, 2, (9, 0), (), "Vacuum", '{C7646442-1115-11D3-AE00-00A024CBA50C}'),
		"Vector": (11, 2, (9, 0), (), "Vector", None),
	}
	_prop_map_put_ = {
		"AutoNormalizeEnabled": ((2, LCID, 4, 0),()),
	}

class Projection(DispatchBaseClass):
	"""Projection Interface"""
	CLSID = pythoncom.MakeIID('{B39C3AE1-1E41-11D3-AE0E-00A024CBA50C}')

	def ChangeProjectionIndex(self, addVal=defaultNamedNotOptArg):
		"""Change the currently available projection index"""
		return self._oleobj_.InvokeTypes(0x3, LCID, 1, (24, 0), ((3, 1),),addVal)

	def Normalize(self, norm=defaultNamedNotOptArg):
		"""Normalize lenses of projection system"""
		return self._oleobj_.InvokeTypes(0x2, LCID, 1, (24, 0), ((3, 1),),norm)

	def ResetDefocus(self):
		"""Reset Defocus"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"CameraLength": (13, 2, (5, 0), (), "CameraLength", None),
		"CameraLengthIndex": (15, 2, (3, 0), (), "CameraLengthIndex", None),
		"Defocus": (21, 2, (5, 0), (), "Defocus", None),
		# Method 'DiffractionShift' returns object of type 'Vector'
		"DiffractionShift": (18, 2, (9, 0), (), "DiffractionShift", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		# Method 'DiffractionStigmator' returns object of type 'Vector'
		"DiffractionStigmator": (19, 2, (9, 0), (), "DiffractionStigmator", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"Focus": (11, 2, (5, 0), (), "Focus", None),
		# Method 'ImageBeamShift' returns object of type 'Vector'
		"ImageBeamShift": (17, 2, (9, 0), (), "ImageBeamShift", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"ImageRotation": (29, 2, (5, 0), (), "ImageRotation", None),
		# Method 'ImageShift' returns object of type 'Vector'
		"ImageShift": (16, 2, (9, 0), (), "ImageShift", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"LensProgram": (28, 2, (3, 0), (), "LensProgram", None),
		"Magnification": (12, 2, (5, 0), (), "Magnification", None),
		"MagnificationIndex": (14, 2, (3, 0), (), "MagnificationIndex", None),
		"Mode": (10, 2, (3, 0), (), "Mode", None),
		"ObjectiveExcitation": (26, 2, (5, 0), (), "ObjectiveExcitation", None),
		# Method 'ObjectiveStigmator' returns object of type 'Vector'
		"ObjectiveStigmator": (20, 2, (9, 0), (), "ObjectiveStigmator", '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}'),
		"ProjectionIndex": (27, 2, (3, 0), (), "ProjectionIndex", None),
		"SubMode": (23, 2, (3, 0), (), "SubMode", None),
		"SubModeMaxIndex": (25, 2, (3, 0), (), "SubModeMaxIndex", None),
		"SubModeMinIndex": (24, 2, (3, 0), (), "SubModeMinIndex", None),
		"SubModeString": (22, 2, (8, 0), (), "SubModeString", None),
	}
	_prop_map_put_ = {
		"CameraLengthIndex": ((15, LCID, 4, 0),()),
		"Defocus": ((21, LCID, 4, 0),()),
		"DiffractionShift": ((18, LCID, 4, 0),()),
		"DiffractionStigmator": ((19, LCID, 4, 0),()),
		"Focus": ((11, LCID, 4, 0),()),
		"ImageBeamShift": ((17, LCID, 4, 0),()),
		"ImageShift": ((16, LCID, 4, 0),()),
		"LensProgram": ((28, LCID, 4, 0),()),
		"MagnificationIndex": ((14, LCID, 4, 0),()),
		"Mode": ((10, LCID, 4, 0),()),
		"ObjectiveStigmator": ((20, LCID, 4, 0),()),
		"ProjectionIndex": ((27, LCID, 4, 0),()),
	}

class Stage(DispatchBaseClass):
	"""Stage Interface"""
	CLSID = pythoncom.MakeIID('{E7AE1E41-1BF8-11D3-AE0B-00A024CBA50C}')

	def Goto(self, newPos=defaultNamedNotOptArg, mask=defaultNamedNotOptArg):
		"""Goto a position"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), ((9, 0), (3, 0)),newPos, mask)

	def MoveTo(self, newPos=defaultNamedNotOptArg, mask=defaultNamedNotOptArg):
		"""Move to a position"""
		return self._oleobj_.InvokeTypes(0x2, LCID, 1, (24, 0), ((9, 0), (3, 0)),newPos, mask)

	_prop_map_get_ = {
		"Holder": (12, 2, (3, 0), (), "Holder", None),
		# Method 'Position' returns object of type 'StagePosition'
		"Position": (11, 2, (9, 0), (), "Position", '{9851BC4A-1B8C-11D3-AE0A-00A024CBA50C}'),
		"Status": (10, 2, (3, 0), (), "Status", None),
	}
	_prop_map_put_ = {
	}

class StagePosition(DispatchBaseClass):
	"""Utility object: stage coordinates"""
	CLSID = pythoncom.MakeIID('{9851BC4A-1B8C-11D3-AE0A-00A024CBA50C}')

	def GetAsArray(self, pos=defaultNamedNotOptArg):
		"""Return position in an array"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (24, 0), ((16389, 0),),pos)

	def SetAsArray(self, pos=defaultNamedNotOptArg):
		"""Set position from an array"""
		return self._oleobj_.InvokeTypes(0x2, LCID, 1, (24, 0), ((16389, 0),),pos)

	_prop_map_get_ = {
		"A": (13, 2, (5, 0), (), "A", None),
		"B": (14, 2, (5, 0), (), "B", None),
		"X": (10, 2, (5, 0), (), "X", None),
		"Y": (11, 2, (5, 0), (), "Y", None),
		"Z": (12, 2, (5, 0), (), "Z", None),
	}
	_prop_map_put_ = {
		"A": ((13, LCID, 4, 0),()),
		"B": ((14, LCID, 4, 0),()),
		"X": ((10, LCID, 4, 0),()),
		"Y": ((11, LCID, 4, 0),()),
		"Z": ((12, LCID, 4, 0),()),
	}

class UserButtonEvent:
	"""Standard scripting event interface"""
	CLSID = CLSID_Sink = pythoncom.MakeIID('{02CDC9A2-1F1D-11D3-AE11-00A024CBA50C}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		        1 : "OnPressed",
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
#	def OnPressed(self):
#		"""Button pressed event"""


class UserButtons(DispatchBaseClass):
	"""User buttons collection"""
	CLSID = pythoncom.MakeIID('{50C21D10-317F-11D3-B4C8-00A024CB9221}')

	# Result is of type IUserButton
	# The method Item is actually a property, but must be used as a method to correctly pass the arguments
	def Item(self, index=defaultNamedNotOptArg):
		"""Get individual Button"""
		ret = self._oleobj_.InvokeTypes(0x0, LCID, 2, (9, 0), ((12, 0),),index)
		if ret is not None: ret = win32com.client.Dispatch(ret, 'Item', '{E6F00871-3164-11D3-B4C8-00A024CB9221}', UnicodeToString=0)
		return ret

	_prop_map_get_ = {
		"Count": (1, 2, (3, 0), (), "Count", None),
	}
	_prop_map_put_ = {
	}
	# Default method for this class is 'Item'
	def __call__(self, index=defaultNamedNotOptArg):
		"""Get individual Button"""
		ret = self._oleobj_.InvokeTypes(0x0, LCID, 2, (9, 0), ((12, 0),),index)
		if ret is not None: ret = win32com.client.Dispatch(ret, '__call__', '{E6F00871-3164-11D3-B4C8-00A024CB9221}', UnicodeToString=0)
		return ret

	# str(ob) and int(ob) will use __call__
	def __str__(self, *args):
		try:
			return str(apply( self.__call__, args))
		except pythoncom.com_error:
			return repr(self)
	def __int__(self, *args):
		return int(apply( self.__call__, args))
	def _NewEnum(self):
		"Create an enumerator from this object"
		return win32com.client.util.WrapEnum(self._oleobj_.InvokeTypes(-4,LCID,2,(13, 10),()),'{E6F00871-3164-11D3-B4C8-00A024CB9221}')
	def __getitem__(self, index):
		"Allow this class to be accessed as a collection"
		if not self.__dict__.has_key('_enum_'):
			import win32com.client.util
			self.__dict__['_enum_'] = self._NewEnum()
		return self._enum_.__getitem__(index)
	#This class has Count() property - allow len(ob) to provide this
	def __len__(self):
		return apply(self._ApplyTypes_, (1, 2, (3, 0), (), "Count", None) )
	#This class has a __len__ - this is needed so 'if object:' always returns TRUE.
	def __nonzero__(self):
		return 1

class Vacuum(DispatchBaseClass):
	"""Vacuum System interface"""
	CLSID = pythoncom.MakeIID('{C7646442-1115-11D3-AE00-00A024CBA50C}')

	def RunBufferCycle(self):
		"""Request a buffer cycle"""
		return self._oleobj_.InvokeTypes(0x3, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"ColumnValvesOpen": (13, 2, (11, 0), (), "ColumnValvesOpen", None),
		# Method 'Gauges' returns object of type 'Gauges'
		"Gauges": (12, 2, (9, 0), (), "Gauges", '{6E6F03B0-2ECE-11D3-AE79-004095005B07}'),
		"PVPRunning": (11, 2, (11, 0), (), "PVPRunning", None),
		"Status": (10, 2, (3, 0), (), "Status", None),
	}
	_prop_map_put_ = {
	}

class Vector(DispatchBaseClass):
	"""Utility object: Vector"""
	CLSID = pythoncom.MakeIID('{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}')

	_prop_map_get_ = {
		"X": (1, 2, (5, 0), (), "X", None),
		"Y": (2, 2, (5, 0), (), "Y", None),
	}
	_prop_map_put_ = {
		"X": ((1, LCID, 4, 0),()),
		"Y": ((2, LCID, 4, 0),()),
	}

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

# This CoClass is known by the name 'Tecnai.Instrument.1'
class Instrument(CoClassBaseClass): # A CoClass
	# Interface to access all subsystems
	CLSID = pythoncom.MakeIID("{02CDC9A1-1F1D-11D3-AE11-00A024CBA50C}")
	coclass_sources = [
	]
	coclass_interfaces = [
		InstrumentInterface,
	]
	default_interface = InstrumentInterface

class UserButton(CoClassBaseClass): # A CoClass
	# Tecnai user buttons
	CLSID = pythoncom.MakeIID("{3A4CE1F0-3A05-11D3-AE81-004095005B07}")
	coclass_sources = [
		UserButtonEvent,
	]
	default_source = UserButtonEvent
	coclass_interfaces = [
		IUserButton,
	]
	default_interface = IUserButton

Camera_vtables_dispatch_ = 1
Camera_vtables_ =  [('TakeExposure', 5, (), (3, 0, None), ())]

Gauge_vtables_dispatch_ = 1
Gauge_vtables_ =  [('Read', 1, (), (3, 0, None), ())]

Gauges_vtables_dispatch_ = 1
Gauges_vtables_ =  [('Item', 0, ((12, 0, None), (16393, 10, None)), (3, 0, None), ('index', 'pG')), ('_NewEnum', -4, ((16397, 10, None),), (3, 0, None), ('pVal',))]

Gun_vtables_dispatch_ = 1
Gun_vtables_ =  []

IUserButton_vtables_dispatch_ = 1
IUserButton_vtables_ =  []

Illumination_vtables_dispatch_ = 1
Illumination_vtables_ =  [('Normalize', 1, ((3, 0, None),), (3, 0, None), ('nm',))]

InstrumentInterface_vtables_dispatch_ = 1
InstrumentInterface_vtables_ =  [('NormalizeAll', 1, (), (3, 0, None), ()), ('ReturnError', 3, ((3, 1, None),), (3, 0, None), ('TE',))]

Projection_vtables_dispatch_ = 1
Projection_vtables_ =  [('ResetDefocus', 1, (), (3, 0, None), ()), ('Normalize', 2, ((3, 1, None),), (3, 0, None), ('norm',)), ('ChangeProjectionIndex', 3, ((3, 1, None),), (3, 0, None), ('addVal',))]

Stage_vtables_dispatch_ = 1
Stage_vtables_ =  [('Goto', 1, ((9, 0, None), (3, 0, None)), (3, 0, None), ('newPos', 'mask')), ('MoveTo', 2, ((9, 0, None), (3, 0, None)), (3, 0, None), ('newPos', 'mask'))]

StagePosition_vtables_dispatch_ = 1
StagePosition_vtables_ =  [('GetAsArray', 1, ((16389, 0, None),), (3, 0, None), ('pos',)), ('SetAsArray', 2, ((16389, 0, None),), (3, 0, None), ('pos',))]

UserButtons_vtables_dispatch_ = 1
UserButtons_vtables_ =  [('Item', 0, ((12, 0, None), (16393, 10, None)), (3, 0, None), ('index', 'pUB')), ('_NewEnum', -4, ((16397, 10, None),), (3, 0, None), ('pVal',))]

Vacuum_vtables_dispatch_ = 1
Vacuum_vtables_ =  [('RunBufferCycle', 3, (), (3, 0, None), ())]

Vector_vtables_dispatch_ = 1
Vector_vtables_ =  []

RecordMap = {
}

CLSIDToClassMap = {
	'{6E6F03B0-2ECE-11D3-AE79-004095005B07}' : Gauges,
	'{BC0A2B11-10FF-11D3-AE00-00A024CBA50C}' : InstrumentInterface,
	'{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}' : Vector,
	'{50C21D10-317F-11D3-B4C8-00A024CB9221}' : UserButtons,
	'{9851BC4A-1B8C-11D3-AE0A-00A024CBA50C}' : StagePosition,
	'{C7646442-1115-11D3-AE00-00A024CBA50C}' : Vacuum,
	'{E7AE1E41-1BF8-11D3-AE0B-00A024CBA50C}' : Stage,
	'{E6F00870-3164-11D3-B4C8-00A024CB9221}' : Gun,
	'{E6F00871-3164-11D3-B4C8-00A024CB9221}' : IUserButton,
	'{02CDC9A1-1F1D-11D3-AE11-00A024CBA50C}' : Instrument,
	'{02CDC9A2-1F1D-11D3-AE11-00A024CBA50C}' : UserButtonEvent,
	'{52020820-18BF-11D3-86E1-00C04FC126DD}' : Gauge,
	'{3A4CE1F0-3A05-11D3-AE81-004095005B07}' : UserButton,
	'{B39C3AE1-1E41-11D3-AE0E-00A024CBA50C}' : Projection,
	'{EF960690-1C38-11D3-AE0B-00A024CBA50C}' : Illumination,
	'{9851BC41-1B8C-11D3-AE0A-00A024CBA50C}' : Camera,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
}


VTablesNamesToCLSIDMap = {
	'Gauges' : '{6E6F03B0-2ECE-11D3-AE79-004095005B07}',
	'InstrumentInterface' : '{BC0A2B11-10FF-11D3-AE00-00A024CBA50C}',
	'Vector' : '{9851BC47-1B8C-11D3-AE0A-00A024CBA50C}',
	'UserButtons' : '{50C21D10-317F-11D3-B4C8-00A024CB9221}',
	'StagePosition' : '{9851BC4A-1B8C-11D3-AE0A-00A024CBA50C}',
	'Vacuum' : '{C7646442-1115-11D3-AE00-00A024CBA50C}',
	'Stage' : '{E7AE1E41-1BF8-11D3-AE0B-00A024CBA50C}',
	'Gun' : '{E6F00870-3164-11D3-B4C8-00A024CB9221}',
	'IUserButton' : '{E6F00871-3164-11D3-B4C8-00A024CB9221}',
	'Gauge' : '{52020820-18BF-11D3-86E1-00C04FC126DD}',
	'Projection' : '{B39C3AE1-1E41-11D3-AE0E-00A024CBA50C}',
	'Illumination' : '{EF960690-1C38-11D3-AE0B-00A024CBA50C}',
	'Camera' : '{9851BC41-1B8C-11D3-AE0A-00A024CBA50C}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

