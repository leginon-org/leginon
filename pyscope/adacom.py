# -*- coding: mbcs -*-
# Created by makepy.py version 0.4.6
# By python version 2.3.2 (#49, Oct  2 2003, 20:02:00) [MSC v.1200 32 bit (Intel)]
# From type library 'adaExp.exe'
# On Wed Dec 17 12:23:59 2003
"""adaExp Library"""
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

CLSID = IID('{7116A70D-7497-499C-8E59-D72CDB13F379}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	eFeg                          =0x1        # from enum Gun
	eThermionic                   =0x0        # from enum Gun
	eInserted                     =0x1        # from enum Holder
	eNotInserted                  =0x0        # from enum Holder
	eOff                          =0x0        # from enum Tmp
	eOn                           =0x1        # from enum Tmp
	eClosed                       =0x0        # from enum Valves
	eOpen                         =0x1        # from enum Valves

from win32com.client import DispatchBaseClass
class ITAdaExp(DispatchBaseClass):
	"""Dispatch interface for TAdaExp Object"""
	CLSID = IID('{8D304182-1C3E-45A3-955D-3D81F7C82284}')
	coclass_clsid = IID('{549B8B80-8169-4908-B0E5-EAFA51153561}')

	# The method SetCurrentSpecimenHolder is actually a property, but must be used as a method to correctly pass the arguments
	def SetCurrentSpecimenHolder(self, Id=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(20, LCID, 2, (3, 0), ((3, 1),),Id)

	# The method SetFegExtractor is actually a property, but must be used as a method to correctly pass the arguments
	def SetFegExtractor(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(29, LCID, 2, (3, 0), ((5, 1),),Val)

	# The method SetFegGunLens is actually a property, but must be used as a method to correctly pass the arguments
	def SetFegGunLens(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(31, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetFilamentIndex is actually a property, but must be used as a method to correctly pass the arguments
	def SetFilamentIndex(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(23, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetFilamentLimit is actually a property, but must be used as a method to correctly pass the arguments
	def SetFilamentLimit(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(27, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetTmp is actually a property, but must be used as a method to correctly pass the arguments
	def SetTmp(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(18, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetWehneltIndex is actually a property, but must be used as a method to correctly pass the arguments
	def SetWehneltIndex(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(25, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SpecimenHolderName is actually a property, but must be used as a method to correctly pass the arguments
	def SpecimenHolderName(self, Id=defaultNamedNotOptArg):
		# Result is a Unicode object - return as-is for this version of Python
		return self._oleobj_.InvokeTypes(22, LCID, 2, (8, 0), ((3, 1),),Id)

	_prop_map_get_ = {
		"CloseShutter": (4, 2, (3, 0), (), "CloseShutter", None),
		"ConnectExternalShutter": (8, 2, (3, 0), (), "ConnectExternalShutter", None),
		"CurrentSpecimenHolderName": (34, 2, (8, 0), (), "CurrentSpecimenHolderName", None),
		"CurrentSpecimentHolder": (16, 2, (3, 0), (), "CurrentSpecimentHolder", None),
		"DisconnectExternalShutter": (7, 2, (3, 0), (), "DisconnectExternalShutter", None),
		"ExposePlateLabel": (10, 2, (3, 0), (), "ExposePlateLabel", None),
		"ExternalShutterStatus": (9, 2, (3, 0), (), "ExternalShutterStatus", None),
		"FegExtractor": (28, 2, (5, 0), (), "FegExtractor", None),
		"FegGunLens": (30, 2, (3, 0), (), "FegGunLens", None),
		"FilamentIndex": (21, 2, (3, 0), (), "FilamentIndex", None),
		"FilamentLimit": (26, 2, (3, 0), (), "FilamentLimit", None),
		"GetTmpStatus": (17, 2, (3, 0), (), "GetTmpStatus", None),
		"GonioLedStatus": (32, 2, (3, 0), (), "GonioLedStatus", None),
		"GunType": (19, 2, (3, 0), (), "GunType", None),
		"LoadPlate": (1, 2, (3, 0), (), "LoadPlate", None),
		"MainScreenDown": (13, 2, (3, 0), (), "MainScreenDown", None),
		"MainScreenStatus": (14, 2, (3, 0), (), "MainScreenStatus", None),
		"MainScreenUp": (12, 2, (3, 0), (), "MainScreenUp", None),
		"NumberOfSpecimenHolders": (15, 2, (3, 0), (), "NumberOfSpecimenHolders", None),
		"OpenShutter": (5, 2, (3, 0), (), "OpenShutter", None),
		"PlateLoadStatus": (3, 2, (3, 0), (), "PlateLoadStatus", None),
		"ShutterStatus": (6, 2, (3, 0), (), "ShutterStatus", None),
		"SpecimenHolderInserted": (33, 2, (3, 0), (), "SpecimenHolderInserted", None),
		"UnloadPlate": (2, 2, (3, 0), (), "UnloadPlate", None),
		"UpdateExposureNumber": (11, 2, (3, 0), (), "UpdateExposureNumber", None),
		"WehneltIndex": (24, 2, (3, 0), (), "WehneltIndex", None),
	}
	_prop_map_put_ = {
	}

class ITAdaExpEvents:
	"""Events interface for TAdaExp Object"""
	CLSID = CLSID_Sink = IID('{B0837CB1-2954-478C-BF84-541873BDFE58}')
	coclass_clsid = IID('{549B8B80-8169-4908-B0E5-EAFA51153561}')
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

	# Event Handlers
	# If you create handlers, they should have the following prototypes:


from win32com.client import CoClassBaseClass
# This CoClass is known by the name 'adaExp.TAdaExp'
class TAdaExp(CoClassBaseClass): # A CoClass
	# TAdaExp Object
	CLSID = IID('{549B8B80-8169-4908-B0E5-EAFA51153561}')
	coclass_sources = [
		ITAdaExpEvents,
	]
	default_source = ITAdaExpEvents
	coclass_interfaces = [
		ITAdaExp,
	]
	default_interface = ITAdaExp

ITAdaExp_vtables_dispatch_ = 1
ITAdaExp_vtables_ = [
	(('LoadPlate', 'Value'), 1, (1, (), [(16387, 10, None, None)], 1, 2, 4, 0, 28, (3, 0, None, None), 0)),
	(('UnloadPlate', 'Value'), 2, (2, (), [(16387, 10, None, None)], 1, 2, 4, 0, 32, (3, 0, None, None), 0)),
	(('PlateLoadStatus', 'Value'), 3, (3, (), [(16387, 10, None, None)], 1, 2, 4, 0, 36, (3, 0, None, None), 0)),
	(('CloseShutter', 'Value'), 4, (4, (), [(16387, 10, None, None)], 1, 2, 4, 0, 40, (3, 0, None, None), 0)),
	(('OpenShutter', 'Value'), 5, (5, (), [(16387, 10, None, None)], 1, 2, 4, 0, 44, (3, 0, None, None), 0)),
	(('ShutterStatus', 'Value'), 6, (6, (), [(16387, 10, None, None)], 1, 2, 4, 0, 48, (3, 0, None, None), 0)),
	(('DisconnectExternalShutter', 'Value'), 7, (7, (), [(16387, 10, None, None)], 1, 2, 4, 0, 52, (3, 0, None, None), 0)),
	(('ConnectExternalShutter', 'Value'), 8, (8, (), [(16387, 10, None, None)], 1, 2, 4, 0, 56, (3, 0, None, None), 0)),
	(('ExternalShutterStatus', 'Value'), 9, (9, (), [(16387, 10, None, None)], 1, 2, 4, 0, 60, (3, 0, None, None), 0)),
	(('ExposePlateLabel', 'Value'), 10, (10, (), [(16387, 10, None, None)], 1, 2, 4, 0, 64, (3, 0, None, None), 0)),
	(('UpdateExposureNumber', 'Value'), 11, (11, (), [(16387, 10, None, None)], 1, 2, 4, 0, 68, (3, 0, None, None), 0)),
	(('MainScreenUp', 'Value'), 12, (12, (), [(16387, 10, None, None)], 1, 2, 4, 0, 72, (3, 0, None, None), 0)),
	(('MainScreenDown', 'Value'), 13, (13, (), [(16387, 10, None, None)], 1, 2, 4, 0, 76, (3, 0, None, None), 0)),
	(('MainScreenStatus', 'Value'), 14, (14, (), [(16387, 10, None, None)], 1, 2, 4, 0, 80, (3, 0, None, None), 0)),
	(('GetTmpStatus', 'Value'), 17, (17, (), [(16387, 10, None, None)], 1, 2, 4, 0, 84, (3, 0, None, None), 0)),
	(('SetTmp', 'Val', 'Value'), 18, (18, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 88, (3, 0, None, None), 0)),
	(('GunType', 'Value'), 19, (19, (), [(16387, 10, None, None)], 1, 2, 4, 0, 92, (3, 0, None, None), 0)),
	(('FilamentIndex', 'Value'), 21, (21, (), [(16387, 10, None, None)], 1, 2, 4, 0, 96, (3, 0, None, None), 0)),
	(('SetFilamentIndex', 'Val', 'Value'), 23, (23, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 100, (3, 0, None, None), 0)),
	(('WehneltIndex', 'Value'), 24, (24, (), [(16387, 10, None, None)], 1, 2, 4, 0, 104, (3, 0, None, None), 0)),
	(('SetWehneltIndex', 'Val', 'Value'), 25, (25, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 108, (3, 0, None, None), 0)),
	(('FilamentLimit', 'Value'), 26, (26, (), [(16387, 10, None, None)], 1, 2, 4, 0, 112, (3, 0, None, None), 0)),
	(('SetFilamentLimit', 'Val', 'Value'), 27, (27, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 116, (3, 0, None, None), 0)),
	(('FegExtractor', 'Value'), 28, (28, (), [(16389, 10, None, None)], 1, 2, 4, 0, 120, (3, 0, None, None), 0)),
	(('SetFegExtractor', 'Val', 'Value'), 29, (29, (), [(5, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 124, (3, 0, None, None), 0)),
	(('FegGunLens', 'Value'), 30, (30, (), [(16387, 10, None, None)], 1, 2, 4, 0, 128, (3, 0, None, None), 0)),
	(('SetFegGunLens', 'Val', 'Value'), 31, (31, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 132, (3, 0, None, None), 0)),
	(('GonioLedStatus', 'Value'), 32, (32, (), [(16387, 10, None, None)], 1, 2, 4, 0, 136, (3, 0, None, None), 0)),
	(('SpecimenHolderInserted', 'Value'), 33, (33, (), [(16387, 10, None, None)], 1, 2, 4, 0, 140, (3, 0, None, None), 0)),
	(('NumberOfSpecimenHolders', 'Value'), 15, (15, (), [(16387, 10, None, None)], 1, 2, 4, 0, 144, (3, 0, None, None), 0)),
	(('CurrentSpecimentHolder', 'Value'), 16, (16, (), [(16387, 10, None, None)], 1, 2, 4, 0, 148, (3, 0, None, None), 0)),
	(('SetCurrentSpecimenHolder', 'Id', 'Value'), 20, (20, (), [(3, 1, None, None), (16387, 10, None, None)], 1, 2, 4, 0, 152, (3, 0, None, None), 0)),
	(('SpecimenHolderName', 'Id', 'Value'), 22, (22, (), [(3, 1, None, None), (16392, 10, None, None)], 1, 2, 4, 0, 156, (3, 0, None, None), 0)),
	(('CurrentSpecimenHolderName', 'Value'), 34, (34, (), [(16392, 10, None, None)], 1, 2, 4, 0, 160, (3, 0, None, None), 0)),
]

RecordMap = {
}

CLSIDToClassMap = {
	'{549B8B80-8169-4908-B0E5-EAFA51153561}' : TAdaExp,
	'{8D304182-1C3E-45A3-955D-3D81F7C82284}' : ITAdaExp,
	'{B0837CB1-2954-478C-BF84-541873BDFE58}' : ITAdaExpEvents,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
	'{8D304182-1C3E-45A3-955D-3D81F7C82284}' : 'ITAdaExp',
}


NamesToIIDMap = {
	'ITAdaExpEvents' : '{B0837CB1-2954-478C-BF84-541873BDFE58}',
	'ITAdaExp' : '{8D304182-1C3E-45A3-955D-3D81F7C82284}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

