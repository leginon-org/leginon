# Created by makepy.py version 0.4.1
# By python version 2.2.2 (#37, Oct 14 2002, 17:02:34) [MSC 32 bit (Intel)]
# From type library 'adaExp.exe'
# On Thu Jul 10 17:14:15 2003
"""adaExp Library"""
makepy_version = '0.4.1'
python_version = 0x20202f0

import win32com.client.CLSIDToClass, pythoncom

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Missing
defaultNamedNotOptArg=pythoncom.Missing
defaultUnnamedArg=pythoncom.Missing

CLSID = pythoncom.MakeIID('{7116A70D-7497-499C-8E59-D72CDB13F379}')
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
	CLSID = pythoncom.MakeIID('{8D304182-1C3E-45A3-955D-3D81F7C82284}')

	# The method SetCurrentSpecimenHolder is actually a property, but must be used as a method to correctly pass the arguments
	def SetCurrentSpecimenHolder(self, Id=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x14, LCID, 2, (3, 0), ((3, 1),),Id)

	# The method SetFegExtractor is actually a property, but must be used as a method to correctly pass the arguments
	def SetFegExtractor(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x1d, LCID, 2, (3, 0), ((5, 1),),Val)

	# The method SetFegGunLens is actually a property, but must be used as a method to correctly pass the arguments
	def SetFegGunLens(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x1f, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetFilamentIndex is actually a property, but must be used as a method to correctly pass the arguments
	def SetFilamentIndex(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x17, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetFilamentLimit is actually a property, but must be used as a method to correctly pass the arguments
	def SetFilamentLimit(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x1b, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetTmp is actually a property, but must be used as a method to correctly pass the arguments
	def SetTmp(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x12, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SetWehneltIndex is actually a property, but must be used as a method to correctly pass the arguments
	def SetWehneltIndex(self, Val=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(0x19, LCID, 2, (3, 0), ((3, 1),),Val)

	# The method SpecimenHolderName is actually a property, but must be used as a method to correctly pass the arguments
	def SpecimenHolderName(self, Id=defaultNamedNotOptArg):
		# Result is a Unicode object - return as-is for this version of Python
		return self._oleobj_.InvokeTypes(0x16, LCID, 2, (8, 0), ((3, 1),),Id)

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
	CLSID = CLSID_Sink = pythoncom.MakeIID('{B0837CB1-2954-478C-BF84-541873BDFE58}')
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

# This CoClass is known by the name 'adaExp.TAdaExp'
class TAdaExp(CoClassBaseClass): # A CoClass
	# TAdaExp Object
	CLSID = pythoncom.MakeIID("{549B8B80-8169-4908-B0E5-EAFA51153561}")
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
	('SetTmp', 18, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetFilamentIndex', 23, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetWehneltIndex', 25, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetFilamentLimit', 27, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetFegExtractor', 29, ((5,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetFegGunLens', 31, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Val', 'Value')),
	('SetCurrentSpecimenHolder', 20, ((3,1,None), (16387,10,None), ), (3, 0, None), ('Id', 'Value')),
	('SpecimenHolderName', 22, ((3,1,None), (16392,10,None), ), (3, 0, None), ('Id', 'Value')),
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
}


VTablesNamesToCLSIDMap = {
	'ITAdaExp' : '{8D304182-1C3E-45A3-955D-3D81F7C82284}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

