# Created by makepy.py version 0.4.0
# By python version 2.2 (#28, Dec 21 2001, 12:21:22) [MSC 32 bit (Intel)]
# From type library 'CAMC.exe'
# On Wed Mar 06 09:32:12 2002
"""CAMC 1.0 Type Library"""
makepy_version = '0.4.0'
python_version = 0x20200f0

import win32com.client.CLSIDToClass, pythoncom

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Missing
defaultNamedNotOptArg=pythoncom.Missing
defaultUnnamedArg=pythoncom.Missing

CLSID = pythoncom.MakeIID('{76853260-743F-11D5-BEDE-0010B5A75250}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	cfFrameTransfer               =0x0        # from enum CAMERAFEATURE
	cfFullFrame                   =0x1        # from enum CAMERAFEATURE
	cpCameraName                  =0x2        # from enum CAMERAPARAMETER
	cpChipName                    =0x1        # from enum CAMERAPARAMETER
	cpCurrentGainIndex            =0x11       # from enum CAMERAPARAMETER
	cpCurrentSpeedIndex           =0x12       # from enum CAMERAPARAMETER
	cpCurrentTemperature          =0x14       # from enum CAMERAPARAMETER
	cpDeadColumns                 =0xf        # from enum CAMERAPARAMETER
	cpDynamic                     =0x7        # from enum CAMERAPARAMETER
	cpGainFactors                 =0x9        # from enum CAMERAPARAMETER
	cpHWGainIndex                 =0x1c       # from enum CAMERAPARAMETER
	cpHWSpeedIndex                =0x1d       # from enum CAMERAPARAMETER
	cpImageGeometry               =0x13       # from enum CAMERAPARAMETER
	cpImagePath                   =0x10       # from enum CAMERAPARAMETER
	cpLiveModeAvailable           =0xc        # from enum CAMERAPARAMETER
	cpNumberOfDeadColumns         =0xe        # from enum CAMERAPARAMETER
	cpNumberOfGains               =0x8        # from enum CAMERAPARAMETER
	cpNumberOfReadoutSpeeds       =0xa        # from enum CAMERAPARAMETER
	cpPMode                       =0x1a       # from enum CAMERAPARAMETER
	cpPixelSizeX                  =0x5        # from enum CAMERAPARAMETER
	cpPixelSizeY                  =0x6        # from enum CAMERAPARAMETER
	cpPreampDelay                 =0x19       # from enum CAMERAPARAMETER
	cpReadoutSpeeds               =0xb        # from enum CAMERAPARAMETER
	cpSerialNumber                =0x18       # from enum CAMERAPARAMETER
	cpShutterCloseDelay           =0x17       # from enum CAMERAPARAMETER
	cpShutterOpenDelay            =0x16       # from enum CAMERAPARAMETER
	cpTemperatureSetpoint         =0x15       # from enum CAMERAPARAMETER
	cpTotalDimensionX             =0x3        # from enum CAMERAPARAMETER
	cpTotalDimensionY             =0x4        # from enum CAMERAPARAMETER
	cpUseSpeedtabForGainSwitch    =0x1b       # from enum CAMERAPARAMETER
	cpreserved1                   =0xd        # from enum CAMERAPARAMETER
	ctFastScan                    =0x3        # from enum CAMERATYPE
	ctPVCam                       =0x2        # from enum CAMERATYPE
	ctPXL                         =0x1        # from enum CAMERATYPE
	ctSimulation                  =0x0        # from enum CAMERATYPE
	llHigh                        =0x3        # from enum LOGLEVEL
	llLow                         =0x1        # from enum LOGLEVEL
	llMedium                      =0x2        # from enum LOGLEVEL
	llOff                         =0x0        # from enum LOGLEVEL

from win32com.client import DispatchBaseClass
class ICamera(DispatchBaseClass):
	"""Camera Interface"""
	CLSID = pythoncom.MakeIID('{7685326C-743F-11D5-BEDE-0010B5A75250}')

	def AcquireBias(self, lCamHandle=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""Take a bias exposure"""
		return self._oleobj_.InvokeTypes(0x8, LCID, 1, (24, 0), ((3, 1), (3, 1)),lCamHandle, lImageHandle)

	def AcquireDark(self, lCamHandle=defaultNamedNotOptArg, lExpTime=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""Take a dark exposure"""
		return self._oleobj_.InvokeTypes(0x7, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1)),lCamHandle, lExpTime, lImageHandle)

	def AcquireImage(self, lCamHandle=defaultNamedNotOptArg, lExpTime=defaultNamedNotOptArg, lShutterMode=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""Take an exposure"""
		return self._oleobj_.InvokeTypes(0x6, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1), (3, 1)),lCamHandle, lExpTime, lShutterMode, lImageHandle)

	def AcquireReadout(self, lCamHandle=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""Readout the chip contents"""
		return self._oleobj_.InvokeTypes(0x9, LCID, 1, (24, 0), ((3, 1), (3, 1)),lCamHandle, lImageHandle)

	def Format(self, lCamHandle=defaultNamedNotOptArg, lXOff=defaultNamedNotOptArg, lYOff=defaultNamedNotOptArg, lXDim=defaultNamedNotOptArg, lYDim=defaultNamedNotOptArg, lXBin=defaultNamedNotOptArg, lYBin=defaultNamedNotOptArg):
		"""Set camera acquisition format"""
		return self._oleobj_.InvokeTypes(0x5, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1), (3, 1), (3, 1), (3, 1), (3, 1)),lCamHandle, lXOff, lYOff, lXDim, lYDim, lXBin, lYBin)

	def Initialize(self, lWhatCamera=defaultNamedNotOptArg, lMode=defaultNamedNotOptArg):
		"""Initialize camera"""
		return self._oleobj_.InvokeTypes(0x1, LCID, 1, (3, 0), ((3, 1), (3, 1)),lWhatCamera, lMode)

	# The method LParam is actually a property, but must be used as a method to correctly pass the arguments
	def LParam(self, lCamHandle=defaultNamedNotOptArg, lWhatParam=defaultNamedNotOptArg):
		"""Get a camera integer parameter"""
		return self._oleobj_.InvokeTypes(0x3, LCID, 2, (3, 0), ((3, 1), (3, 1)),lCamHandle, lWhatParam)

	# The method QueryCamera is actually a property, but must be used as a method to correctly pass the arguments
	def QueryCamera(self, lCamHandle=defaultNamedNotOptArg, lWhatFeature=defaultNamedNotOptArg):
		"""Query the camera properties"""
		return self._oleobj_.InvokeTypes(0xc, LCID, 2, (3, 0), ((3, 1), (3, 1)),lCamHandle, lWhatFeature)

	# The method QueryParameter is actually a property, but must be used as a method to correctly pass the arguments
	def QueryParameter(self, lCamHandle=defaultNamedNotOptArg, lWhatParam=defaultNamedNotOptArg):
		"""Query the parameter properties"""
		return self._oleobj_.InvokeTypes(0xb, LCID, 2, (3, 0), ((3, 1), (3, 1)),lCamHandle, lWhatParam)

	# The method SParam is actually a property, but must be used as a method to correctly pass the arguments
	def SParam(self, lCamHandle=defaultNamedNotOptArg, lWhatParam=defaultNamedNotOptArg):
		"""Get a camera string parameter"""
		# Result is a Unicode object - return as-is for this version of Python
		return self._oleobj_.InvokeTypes(0x4, LCID, 2, (8, 0), ((3, 1), (3, 1)),lCamHandle, lWhatParam)

	# The method SetLParam is actually a property, but must be used as a method to correctly pass the arguments
	def SetLParam(self, lCamHandle=defaultNamedNotOptArg, lWhatParam=defaultNamedNotOptArg, arg2=defaultUnnamedArg):
		"""Get a camera integer parameter"""
		return self._oleobj_.InvokeTypes(0x3, LCID, 4, (24, 0), ((3, 1), (3, 1), (3, 1)),lCamHandle, lWhatParam, arg2)

	# The method SetSParam is actually a property, but must be used as a method to correctly pass the arguments
	def SetSParam(self, lCamHandle=defaultNamedNotOptArg, lWhatParam=defaultNamedNotOptArg, arg2=defaultUnnamedArg):
		"""Get a camera string parameter"""
		return self._oleobj_.InvokeTypes(0x4, LCID, 4, (24, 0), ((3, 1), (3, 1), (8, 1)),lCamHandle, lWhatParam, arg2)

	def SetShutter(self, lCamHandle=defaultNamedNotOptArg, lState=defaultNamedNotOptArg):
		"""Set the shutter"""
		return self._oleobj_.InvokeTypes(0xa, LCID, 1, (24, 0), ((3, 1), (3, 1)),lCamHandle, lState)

	def Uninitialize(self, lCamHandle=defaultNamedNotOptArg):
		"""Uninitialize camera"""
		return self._oleobj_.InvokeTypes(0x2, LCID, 1, (24, 0), ((3, 1),),lCamHandle)

	_prop_map_get_ = {
	}
	_prop_map_put_ = {
	}

class IMaintain(DispatchBaseClass):
	"""IMaintain Interface"""
	CLSID = pythoncom.MakeIID('{7685326F-743F-11D5-BEDE-0010B5A75250}')

	def ShowDebugInfo(self, lWhatInfo=defaultNamedNotOptArg):
		"""method ShowDebugInfo"""
		return self._oleobj_.InvokeTypes(0x2, LCID, 1, (24, 0), ((3, 1),),lWhatInfo)

	_prop_map_get_ = {
		"lLogLevel": (1, 2, (3, 0), (), "lLogLevel", None),
	}
	_prop_map_put_ = {
		"lLogLevel": ((1, LCID, 4, 0),()),
	}

class _ICameraEvents:
	"""_ICameraEvents Interface"""
	CLSID = CLSID_Sink = pythoncom.MakeIID('{7685326E-743F-11D5-BEDE-0010B5A75250}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
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

# This CoClass is known by the name 'CAMC.Camera.1'
class Camera(CoClassBaseClass): # A CoClass
	# Camera Class
	CLSID = pythoncom.MakeIID("{7685326D-743F-11D5-BEDE-0010B5A75250}")
	coclass_sources = [
		_ICameraEvents,
	]
	default_source = _ICameraEvents
	coclass_interfaces = [
		ICamera,
	]
	default_interface = ICamera

# This CoClass is known by the name 'CAMC.Maintain.1'
class Maintain(CoClassBaseClass): # A CoClass
	# Maintain Class
	CLSID = pythoncom.MakeIID("{76853270-743F-11D5-BEDE-0010B5A75250}")
	coclass_sources = [
	]
	coclass_interfaces = [
		IMaintain,
	]
	default_interface = IMaintain

ICamera_vtables_dispatch_ = 1
ICamera_vtables_ =  [('Initialize', 1, ((3, 1, None), (3, 1, None), (16387, 10, None)), (3, 0, None), ('lWhatCamera', 'lMode', 'lpCamHandle')), ('Uninitialize', 2, ((3, 1, None),), (3, 0, None), ('lCamHandle',)), ('LParam', 3, ((3, 1, None), (3, 1, None), (16387, 10, None)), (3, 0, None), ('lCamHandle', 'lWhatParam', 'pVal')), ('LParam', 3, ((3, 1, None), (3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lWhatParam', 'pVal')), ('SParam', 4, ((3, 1, None), (3, 1, None), (16392, 10, None)), (3, 0, None), ('lCamHandle', 'lWhatParam', 'pVal')), ('SParam', 4, ((3, 1, None), (3, 1, None), (8, 1, None)), (3, 0, None), ('lCamHandle', 'lWhatParam', 'pVal')), ('Format', 5, ((3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lXOff', 'lYOff', 'lXDim', 'lYDim', 'lXBin', 'lYBin')), ('AcquireImage', 6, ((3, 1, None), (3, 1, None), (3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lExpTime', 'lShutterMode', 'lImageHandle')), ('AcquireDark', 7, ((3, 1, None), (3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lExpTime', 'lImageHandle')), ('AcquireBias', 8, ((3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lImageHandle')), ('AcquireReadout', 9, ((3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lImageHandle')), ('SetShutter', 10, ((3, 1, None), (3, 1, None)), (3, 0, None), ('lCamHandle', 'lState')), ('QueryParameter', 11, ((3, 1, None), (3, 1, None), (16387, 10, None)), (3, 0, None), ('lCamHandle', 'lWhatParam', 'pVal')), ('QueryCamera', 12, ((3, 1, None), (3, 1, None), (16387, 10, None)), (3, 0, None), ('lCamHandle', 'lWhatFeature', 'pVal'))]

IMaintain_vtables_dispatch_ = 1
IMaintain_vtables_ =  [('ShowDebugInfo', 2, ((3, 1, None),), (3, 0, None), ('lWhatInfo',))]

RecordMap = {
}

CLSIDToClassMap = {
	'{7685326E-743F-11D5-BEDE-0010B5A75250}' : _ICameraEvents,
	'{7685326F-743F-11D5-BEDE-0010B5A75250}' : IMaintain,
	'{76853270-743F-11D5-BEDE-0010B5A75250}' : Maintain,
	'{7685326C-743F-11D5-BEDE-0010B5A75250}' : ICamera,
	'{7685326D-743F-11D5-BEDE-0010B5A75250}' : Camera,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
}


VTablesNamesToCLSIDMap = {
	'IMaintain' : '{7685326F-743F-11D5-BEDE-0010B5A75250}',
	'ICamera' : '{7685326C-743F-11D5-BEDE-0010B5A75250}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

