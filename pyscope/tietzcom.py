# -*- coding: mbcs -*-
# Created by makepy.py version 0.4.6
# By python version 2.3.2 (#49, Oct  2 2003, 20:02:00) [MSC v.1200 32 bit (Intel)]
# From type library 'CAMC4.exe'
# On Thu Dec 11 10:11:15 2003
"""CAMC4 1.0 Type Library"""
makepy_version = '0.4.6'
python_version = 0x20302f0

import win32com.client.CLSIDToClass, pythoncom
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{4AB9E74C-AC91-43D3-8973-5EE5F4467461}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	cpCameraName                  =0x2        # from enum CAMERAPARAMETER
	cpCameraPositionOnTem         =0x24       # from enum CAMERAPARAMETER
	cpChipName                    =0x1        # from enum CAMERAPARAMETER
	cpCurrentGainIndex            =0x11       # from enum CAMERAPARAMETER
	cpCurrentSpeedIndex           =0x12       # from enum CAMERAPARAMETER
	cpCurrentTemperature          =0x14       # from enum CAMERAPARAMETER
	cpDeadColumns                 =0xf        # from enum CAMERAPARAMETER
	cpDynamic                     =0x7        # from enum CAMERAPARAMETER
	cpGainFactors                 =0x9        # from enum CAMERAPARAMETER
	cpHWGainIndex                 =0x1c       # from enum CAMERAPARAMETER
	cpHWSpeedIndex                =0x1d       # from enum CAMERAPARAMETER
	cpIOState                     =0x21       # from enum CAMERAPARAMETER
	cpImageGeometry               =0x13       # from enum CAMERAPARAMETER
	cpImagePath                   =0x10       # from enum CAMERAPARAMETER
	cpIsRetractable               =0x1e       # from enum CAMERAPARAMETER
	cpLiveModeAvailable           =0xc        # from enum CAMERAPARAMETER
	cpMovePosition                =0x1f       # from enum CAMERAPARAMETER
	cpNumberOfDeadColumns         =0xe        # from enum CAMERAPARAMETER
	cpNumberOfGains               =0x8        # from enum CAMERAPARAMETER
	cpNumberOfReadoutSpeeds       =0xa        # from enum CAMERAPARAMETER
	cpPMode                       =0x1a       # from enum CAMERAPARAMETER
	cpPixelSizeX                  =0x5        # from enum CAMERAPARAMETER
	cpPixelSizeY                  =0x6        # from enum CAMERAPARAMETER
	cpPreampDelay                 =0x19       # from enum CAMERAPARAMETER
	cpReadoutMode                 =0x23       # from enum CAMERAPARAMETER
	cpReadoutSpeeds               =0xb        # from enum CAMERAPARAMETER
	cpSerialNumber                =0x18       # from enum CAMERAPARAMETER
	cpShutterBox                  =0x22       # from enum CAMERAPARAMETER
	cpShutterCloseDelay           =0x17       # from enum CAMERAPARAMETER
	cpShutterOpenDelay            =0x16       # from enum CAMERAPARAMETER
	cpTemperatureSetpoint         =0x15       # from enum CAMERAPARAMETER
	cpTotalDimensionX             =0x3        # from enum CAMERAPARAMETER
	cpTotalDimensionY             =0x4        # from enum CAMERAPARAMETER
	cpTriggerMode                 =0x20       # from enum CAMERAPARAMETER
	cpUseSpeedtabForGainSwitch    =0x1b       # from enum CAMERAPARAMETER
	cpreserved1                   =0xd        # from enum CAMERAPARAMETER
	crBusy                        =0x2        # from enum CAMERAREQUEST
	crDeny                        =0x1        # from enum CAMERAREQUEST
	crSucceed                     =0x0        # from enum CAMERAREQUEST
	ctATC6                        =0x6        # from enum CAMERATYPE
	ctF114_FW                     =0x5        # from enum CAMERATYPE
	ctFastScan                    =0x3        # from enum CAMERATYPE
	ctPVCam                       =0x2        # from enum CAMERATYPE
	ctPXL                         =0x1        # from enum CAMERATYPE
	ctSCX                         =0x4        # from enum CAMERATYPE
	ctSimulation                  =0x0        # from enum CAMERATYPE
	llHigh                        =0x3        # from enum LOGLEVEL
	llLow                         =0x1        # from enum LOGLEVEL
	llMedium                      =0x2        # from enum LOGLEVEL
	llOff                         =0x0        # from enum LOGLEVEL
	smBB                          =0x0        # from enum SHUTTERMODE
	smSH                          =0x2        # from enum SHUTTERMODE
	smSH_BB                       =0x1        # from enum SHUTTERMODE
	smSH_BB_Trigger               =0x3        # from enum SHUTTERMODE
	stBB                          =0x1        # from enum SHUTTERTYPE
	stSH                          =0x0        # from enum SHUTTERTYPE

from win32com.client import DispatchBaseClass
class ICAMCCallBack(DispatchBaseClass):
	"""ICAMCCallBack Interface"""
	CLSID = IID('{2A20A2ED-7E7D-4AA1-B943-F52A3BAC59B4}')
	coclass_clsid = None

	def LivePing(self):
		"""method LivePing"""
		return self._oleobj_.InvokeTypes(1, LCID, 1, (24, 0), (),)

	def RequestLock(self):
		"""method RequestLock"""
		return self._oleobj_.InvokeTypes(2, LCID, 1, (3, 0), (),)

	_prop_map_get_ = {
	}
	_prop_map_put_ = {
	}

class ICamera(DispatchBaseClass):
	"""ICamera Interface"""
	CLSID = IID('{3CF7ED98-2848-4594-B2CD-A792FF72D86C}')
	coclass_clsid = IID('{ADFA5865-1ACD-4A52-A2C3-65A4A2E6F23A}')

	def AcquireBias(self, lImageHandle=defaultNamedNotOptArg):
		"""method AcquireBias"""
		return self._oleobj_.InvokeTypes(8, LCID, 1, (24, 0), ((3, 1),),lImageHandle)

	def AcquireDark(self, lExpTime=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""method AcquireDark"""
		return self._oleobj_.InvokeTypes(7, LCID, 1, (24, 0), ((3, 1), (3, 1)),lExpTime, lImageHandle)

	def AcquireImage(self, lExpTime=defaultNamedNotOptArg, lImageHandle=defaultNamedNotOptArg):
		"""method AcquireImage"""
		return self._oleobj_.InvokeTypes(6, LCID, 1, (24, 0), ((3, 1), (3, 1)),lExpTime, lImageHandle)

	def AcquireReadout(self, lImageHandle=defaultNamedNotOptArg):
		"""method AcquireReadout"""
		return self._oleobj_.InvokeTypes(9, LCID, 1, (24, 0), ((3, 1),),lImageHandle)

	def Format(self, lXOff=defaultNamedNotOptArg, lYOff=defaultNamedNotOptArg, lXDim=defaultNamedNotOptArg, lYDim=defaultNamedNotOptArg, lXBin=defaultNamedNotOptArg, lYBin=defaultNamedNotOptArg):
		"""method Format"""
		return self._oleobj_.InvokeTypes(5, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1), (3, 1), (3, 1), (3, 1)),lXOff, lYOff, lXDim, lYDim, lXBin, lYBin)

	def Initialize(self, lWhatCamera=defaultNamedNotOptArg, lMode=defaultNamedNotOptArg):
		"""method Initialize"""
		return self._oleobj_.InvokeTypes(1, LCID, 1, (24, 0), ((3, 1), (3, 1)),lWhatCamera, lMode)

	# The method LParam is actually a property, but must be used as a method to correctly pass the arguments
	def LParam(self, lWhatParam=defaultNamedNotOptArg):
		"""property LParam"""
		return self._oleobj_.InvokeTypes(3, LCID, 2, (3, 0), ((3, 1),),lWhatParam)

	# The method QueryParameter is actually a property, but must be used as a method to correctly pass the arguments
	def QueryParameter(self, lWhatParam=defaultNamedNotOptArg):
		"""property QueryParameter"""
		return self._oleobj_.InvokeTypes(11, LCID, 2, (3, 0), ((3, 1),),lWhatParam)

	def RegisterCAMCCallBack(self, ptrCallBack=defaultNamedNotOptArg, bstrLocker=defaultNamedNotOptArg):
		"""method RegisterCAMCCallBack"""
		return self._oleobj_.InvokeTypes(15, LCID, 1, (24, 0), ((9, 0), (8, 1)),ptrCallBack, bstrLocker)

	def RequestLock(self):
		"""method RequestLock"""
		return self._oleobj_.InvokeTypes(13, LCID, 1, (3, 0), (),)

	# The method SParam is actually a property, but must be used as a method to correctly pass the arguments
	def SParam(self, lWhatParam=defaultNamedNotOptArg):
		"""property SParam"""
		# Result is a Unicode object - return as-is for this version of Python
		return self._oleobj_.InvokeTypes(4, LCID, 2, (8, 0), ((3, 1),),lWhatParam)

	# The method SetLParam is actually a property, but must be used as a method to correctly pass the arguments
	def SetLParam(self, lWhatParam=defaultNamedNotOptArg, arg1=defaultUnnamedArg):
		"""property LParam"""
		return self._oleobj_.InvokeTypes(3, LCID, 4, (24, 0), ((3, 1), (3, 1)),lWhatParam, arg1)

	# The method SetSParam is actually a property, but must be used as a method to correctly pass the arguments
	def SetSParam(self, lWhatParam=defaultNamedNotOptArg, arg1=defaultUnnamedArg):
		"""property SParam"""
		return self._oleobj_.InvokeTypes(4, LCID, 4, (24, 0), ((3, 1), (8, 1)),lWhatParam, arg1)

	def ShutterOverride(self, type=defaultNamedNotOptArg, bEnableOverride=defaultNamedNotOptArg, bBeamCanPass=defaultNamedNotOptArg):
		"""method ShutterOverride"""
		return self._oleobj_.InvokeTypes(10, LCID, 1, (24, 0), ((3, 1), (3, 1), (3, 1)),type, bEnableOverride, bBeamCanPass)

	def UnInitialize(self, lWhatCamera=defaultNamedNotOptArg):
		"""method UnInitialize"""
		return self._oleobj_.InvokeTypes(2, LCID, 1, (24, 0), ((3, 1),),lWhatCamera)

	def UnlockCAMC(self):
		"""method UnlockCAMC"""
		return self._oleobj_.InvokeTypes(14, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"ActiveCamera": (12, 2, (3, 0), (), "ActiveCamera", None),
		"IsLocked": (16, 2, (3, 0), ((16392, 2),), "IsLocked", None),
		"SHUTTERMODE": (17, 2, (3, 0), (), "SHUTTERMODE", None),
	}
	_prop_map_put_ = {
		"ActiveCamera": ((12, LCID, 4, 0),()),
		"SHUTTERMODE": ((17, LCID, 4, 0),()),
	}

class IMaintain(DispatchBaseClass):
	"""IMaintain Interface"""
	CLSID = IID('{C745F0BE-27F2-4D8A-B069-C1964CCF7B21}')
	coclass_clsid = IID('{ADFA5865-1ACD-4A52-A2C3-65A4A2E6F23A}')

	# The method RevisionInformation is actually a property, but must be used as a method to correctly pass the arguments
	def RevisionInformation(self, lWhatCamera=defaultNamedNotOptArg):
		"""property RevisionInformation"""
		return self._oleobj_.InvokeTypes(1, LCID, 2, (3, 0), ((3, 1),),lWhatCamera)

	def ShowDebugInfo(self, lWhatInfo=defaultNamedNotOptArg):
		"""method ShowDebugInfo"""
		return self._oleobj_.InvokeTypes(3, LCID, 1, (24, 0), ((3, 1),),lWhatInfo)

	_prop_map_get_ = {
		"ShowTrayIcon": (2, 2, (3, 0), (), "ShowTrayIcon", None),
		"lLogLevel": (4, 2, (3, 0), (), "lLogLevel", None),
	}
	_prop_map_put_ = {
		"ShowTrayIcon": ((2, LCID, 4, 0),()),
		"lLogLevel": ((4, LCID, 4, 0),()),
	}

class _ICameraEvents:
	"""_ICameraEvents Interface"""
	CLSID = CLSID_Sink = IID('{A5D1467A-56E4-4B84-8CF5-DE923199263E}')
	coclass_clsid = IID('{ADFA5865-1ACD-4A52-A2C3-65A4A2E6F23A}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		        1 : "OnCAMCLocked",
		        2 : "OnCAMCUnlocked",
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

	# Event Handlers
	# If you create handlers, they should have the following prototypes:
#	def OnCAMCLocked(self):
#		"""method CAMCLocked"""
#	def OnCAMCUnlocked(self):
#		"""method CAMCUnlocked"""


from win32com.client import CoClassBaseClass
# This CoClass is known by the name 'CAMC4.Camera.1'
class Camera(CoClassBaseClass): # A CoClass
	# Camera Class
	CLSID = IID('{ADFA5865-1ACD-4A52-A2C3-65A4A2E6F23A}')
	coclass_sources = [
		_ICameraEvents,
	]
	default_source = _ICameraEvents
	coclass_interfaces = [
		ICamera,
		IMaintain,
	]
	default_interface = ICamera

ICAMCCallBack_vtables_dispatch_ = 0
ICAMCCallBack_vtables_ = [
	(('LivePing',), 1, (1, (), [], 1, 1, 4, 0, 12, (3, 0, None, None), 0)),
	(('RequestLock', 'pVal'), 2, (2, (), [(16387, 10, None, None)], 1, 1, 4, 0, 16, (3, 0, None, None), 0)),
]

ICamera_vtables_dispatch_ = 1
ICamera_vtables_ = [
	(('Initialize', 'lWhatCamera', 'lMode'), 1, (1, (), [(3, 1, None, None), (3, 1, None, None)], 1, 1, 4, 0, 28, (3, 0, None, None), 0)),
	(('UnInitialize', 'lWhatCamera'), 2, (2, (), [(3, 1, None, None)], 1, 1, 4, 0, 32, (3, 0, None, None), 0)),
	(('LParam', 'lWhatParam', 'pVal'), 3, (3, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 36, (3, 0, None, None), 0)),
	(('LParam', 'lWhatParam', 'pVal'), 3, (3, (), [(3, 1, None, None), (3, 1, None, None)], 1, 4, 4, 0, 40, (3, 0, None, None), 0)),
	(('SParam', 'lWhatParam', 'pVal'), 4, (4, (), [(3, 1, None, None), (16392, 10, None, None)], 1, 2, 4, 0, 44, (3, 0, None, None), 0)),
	(('SParam', 'lWhatParam', 'pVal'), 4, (4, (), [(3, 1, None, None), (8, 1, None, None)], 1, 4, 4, 0, 48, (3, 0, None, None), 0)),
	(('Format', 'lXOff', 'lYOff', 'lXDim', 'lYDim', 'lXBin', 'lYBin'), 5, (5, (), [(3, 1, None, None), (3, 1, None, None), (3, 1, None, None), (3, 1, None, None), (3, 1, None, None), (3, 1, None, None)], 1, 1, 4, 0, 52, (3, 0, None, None), 0)),
	(('AcquireImage', 'lExpTime', 'lImageHandle'), 6, (6, (), [(3, 1, None, None), (3, 1, None, None)], 1, 1, 4, 0, 56, (3, 0, None, None), 0)),
	(('AcquireDark', 'lExpTime', 'lImageHandle'), 7, (7, (), [(3, 1, None, None), (3, 1, None, None)], 1, 1, 4, 0, 60, (3, 0, None, None), 0)),
	(('AcquireBias', 'lImageHandle'), 8, (8, (), [(3, 1, None, None)], 1, 1, 4, 0, 64, (3, 0, None, None), 0)),
	(('AcquireReadout', 'lImageHandle'), 9, (9, (), [(3, 1, None, None)], 1, 1, 4, 0, 68, (3, 0, None, None), 0)),
	(('ShutterOverride', 'type', 'bEnableOverride', 'bBeamCanPass'), 10, (10, (), [(3, 1, None, None), (3, 1, None, None), (3, 1, None, None)], 1, 1, 4, 0, 72, (3, 0, None, None), 0)),
	(('QueryParameter', 'lWhatParam', 'pVal'), 11, (11, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 76, (3, 0, None, None), 0)),
	(('ActiveCamera', 'pVal'), 12, (12, (), [(16387, 10, None, None)], 1, 2, 4, 0, 80, (3, 0, None, None), 0)),
	(('ActiveCamera', 'pVal'), 12, (12, (), [(3, 1, None, None)], 1, 4, 4, 0, 84, (3, 0, None, None), 0)),
	(('RequestLock', 'pVal'), 13, (13, (), [(16387, 10, None, None)], 1, 1, 4, 0, 88, (3, 0, None, None), 0)),
	(('UnlockCAMC',), 14, (14, (), [], 1, 1, 4, 0, 92, (3, 0, None, None), 0)),
	(('RegisterCAMCCallBack', 'ptrCallBack', 'bstrLocker'), 15, (15, (), [(9, 0, None, "IID('{2A20A2ED-7E7D-4AA1-B943-F52A3BAC59B4}')"), (8, 1, None, None)], 1, 1, 4, 0, 96, (3, 0, None, None), 0)),
	(('IsLocked', 'psLocker', 'pVal'), 16, (16, (), [(16392, 2, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 100, (3, 0, None, None), 0)),
	(('SHUTTERMODE', 'pVal'), 17, (17, (), [(16387, 10, None, None)], 1, 2, 4, 0, 104, (3, 0, None, None), 0)),
	(('SHUTTERMODE', 'pVal'), 17, (17, (), [(3, 1, None, None)], 1, 4, 4, 0, 108, (3, 0, None, None), 0)),
]

IMaintain_vtables_dispatch_ = 1
IMaintain_vtables_ = [
	(('RevisionInformation', 'lWhatCamera', 'pVal'), 1, (1, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 28, (3, 0, None, None), 0)),
	(('ShowTrayIcon', 'pVal'), 2, (2, (), [(16387, 10, None, None)], 1, 2, 4, 0, 32, (3, 0, None, None), 0)),
	(('ShowTrayIcon', 'pVal'), 2, (2, (), [(3, 1, None, None)], 1, 4, 4, 0, 36, (3, 0, None, None), 0)),
	(('ShowDebugInfo', 'lWhatInfo'), 3, (3, (), [(3, 1, None, None)], 1, 1, 4, 0, 40, (3, 0, None, None), 0)),
	(('lLogLevel', 'pVal'), 4, (4, (), [(16387, 10, None, None)], 1, 2, 4, 0, 44, (3, 0, None, None), 0)),
	(('lLogLevel', 'pVal'), 4, (4, (), [(3, 1, None, None)], 1, 4, 4, 0, 48, (3, 0, None, None), 0)),
]

RecordMap = {
}

CLSIDToClassMap = {
	'{3CF7ED98-2848-4594-B2CD-A792FF72D86C}' : ICamera,
	'{A5D1467A-56E4-4B84-8CF5-DE923199263E}' : _ICameraEvents,
	'{C745F0BE-27F2-4D8A-B069-C1964CCF7B21}' : IMaintain,
	'{ADFA5865-1ACD-4A52-A2C3-65A4A2E6F23A}' : Camera,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
	'{3CF7ED98-2848-4594-B2CD-A792FF72D86C}' : 'ICamera',
	'{C745F0BE-27F2-4D8A-B069-C1964CCF7B21}' : 'IMaintain',
	'{2A20A2ED-7E7D-4AA1-B943-F52A3BAC59B4}' : 'ICAMCCallBack',
}


NamesToIIDMap = {
	'ICAMCCallBack' : '{2A20A2ED-7E7D-4AA1-B943-F52A3BAC59B4}',
	'ICamera' : '{3CF7ED98-2848-4594-B2CD-A792FF72D86C}',
	'_ICameraEvents' : '{A5D1467A-56E4-4B84-8CF5-DE923199263E}',
	'IMaintain' : '{C745F0BE-27F2-4D8A-B069-C1964CCF7B21}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

