# Created by makepy.py version 0.4.1
# By python version 2.2.1 (#34, Apr  9 2002, 19:34:33) [MSC 32 bit (Intel)]
# From type library 'tecnaiccd.dll'
# On Fri Aug 30 11:32:57 2002
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
"""TecnaiCCD 1.0 Type Library"""
makepy_version = '0.4.1'
python_version = 0x20201f0

import win32com.client.CLSIDToClass, pythoncom

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing and pythoncom.Empty
defaultNamedOptArg=pythoncom.Missing
defaultNamedNotOptArg=pythoncom.Missing
defaultUnnamedArg=pythoncom.Missing

CLSID = pythoncom.MakeIID('{A75976DB-9C1F-43EB-A5B9-F14FEE8D866C}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

class constants:
	AM_FOCUS                      =0x1        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0001
	AM_RECORD                     =0x2        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0001
	AM_SEARCH                     =0x0        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0001
	AS_CONTINUOUS                 =0x1        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0002
	AS_SINGLEFRAME                =0x2        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0002
	AS_TURBO                      =0x0        # from enum __MIDL___MIDL_itf_TecnaiCCD_0000_0002

from win32com.client import DispatchBaseClass
class IGatanCamera(DispatchBaseClass):
	"""IGatanCamera Interface"""
	CLSID = pythoncom.MakeIID('{18F3C374-2D04-4CEC-8F3F-B1CECDBA1068}')

	def AcquireAndShowImage(self, mode=defaultNamedNotOptArg):
		"""method AcquireAndShowImage"""
		return self._oleobj_.InvokeTypes(0x39, LCID, 1, (24, 0), ((3, 0),),mode)

	def AcquireFrontImage(self, pImageData=defaultNamedNotOptArg):
		"""method AcquireFrontImage"""
		return self._ApplyTypes_(0x3c, 1, (24, 0), ((24578, 2),), 'AcquireFrontImage', None,pImageData)

	def AcquireImage(self):
		"""method AcquireImage"""
		return self._ApplyTypes_(0x3a, 1, (12, 0), (), 'AcquireImage', None,)

	def AcquireImageShown(self, pImageData=defaultNamedNotOptArg):
		"""method AcquireImageShown"""
		return self._ApplyTypes_(0x3d, 1, (24, 0), ((24578, 2),), 'AcquireImageShown', None,pImageData)

	def AcquireRawImage(self):
		"""method AcquireRawImage"""
		return self._ApplyTypes_(0x3f, 1, (12, 0), (), 'AcquireRawImage', None,)

	# The method ExecuteScript is actually a property, but must be used as a method to correctly pass the arguments
	def ExecuteScript(self, script=defaultNamedNotOptArg):
		"""property ExecuteScript"""
		return self._oleobj_.InvokeTypes(0xd, LCID, 2, (4, 0), ((8, 0),),script)

	# The method ExecuteScriptFile is actually a property, but must be used as a method to correctly pass the arguments
	def ExecuteScriptFile(self, filename=defaultNamedNotOptArg):
		"""property ExecuteScript"""
		return self._oleobj_.InvokeTypes(0xe, LCID, 2, (4, 0), ((8, 0),),filename)

	# The method HasFeature is actually a property, but must be used as a method to correctly pass the arguments
	def HasFeature(self, f=defaultNamedNotOptArg):
		"""HasFeature"""
		return self._oleobj_.InvokeTypes(0x5, LCID, 2, (3, 0), ((2, 0),),f)

	def Insert(self):
		"""Insert camera"""
		return self._oleobj_.InvokeTypes(0x32, LCID, 1, (24, 0), (),)

	def LaunchAcquisition(self, mode=defaultNamedNotOptArg):
		"""LaunchAcquisition(mode)"""
		return self._oleobj_.InvokeTypes(0x35, LCID, 1, (24, 0), ((3, 0),),mode)

	def OpenShutter(self, newVal=defaultNamedNotOptArg):
		"""OpenShutter(bool) """
		return self._oleobj_.InvokeTypes(0x34, LCID, 1, (24, 0), ((3, 1),),newVal)

	def Retract(self):
		"""Retract camera"""
		return self._oleobj_.InvokeTypes(0x33, LCID, 1, (24, 0), (),)

	def SaveImageInDMFormat(self, filename=defaultNamedNotOptArg):
		"""method SaveImageInDMFormat"""
		return self._oleobj_.InvokeTypes(0x38, LCID, 1, (24, 0), ((8, 0),),filename)

	def SelectCameraParameters(self, mode=defaultNamedNotOptArg):
		"""method SelectCameraParameters"""
		return self._oleobj_.InvokeTypes(0x3b, LCID, 1, (24, 0), ((3, 0),),mode)

	def ShowAcquiredImage(self):
		"""method ShowAcquiredImage"""
		return self._oleobj_.InvokeTypes(0x3e, LCID, 1, (24, 0), (),)

	def StartAcquisition(self, mode=defaultNamedNotOptArg):
		"""method StartAcquistion"""
		return self._oleobj_.InvokeTypes(0x37, LCID, 1, (24, 0), ((3, 0),),mode)

	def StopAcquisition(self):
		"""StopAcquisition"""
		return self._oleobj_.InvokeTypes(0x36, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		"Binning": (8, 2, (2, 0), (), "Binning", None),
		"CameraBottom": (12, 2, (2, 0), (), "CameraBottom", None),
		"CameraLeft": (9, 2, (2, 0), (), "CameraLeft", None),
		"CameraName": (2, 2, (8, 0), (), "CameraName", None),
		"CameraRight": (10, 2, (2, 0), (), "CameraRight", None),
		"CameraTop": (11, 2, (2, 0), (), "CameraTop", None),
		"CurrentCamera": (6, 2, (2, 0), (), "CurrentCamera", None),
		"ExposureTime": (7, 2, (4, 0), (), "ExposureTime", None),
		"FrontImage": (17, 2, (12, 0), (), "FrontImage", None),
		"IsAcquiring": (15, 2, (3, 0), (), "IsAcquiring", None),
		"IsInserted": (3, 2, (3, 0), (), "IsInserted", None),
		"IsRetractable": (4, 2, (3, 0), (), "IsRetractable", None),
		"NumberOfCameras": (1, 2, (2, 0), (), "NumberOfCameras", None),
		"Speed": (16, 2, (3, 0), (), "Speed", None),
	}
	_prop_map_put_ = {
		"Binning": ((8, LCID, 4, 0),()),
		"CameraBottom": ((12, LCID, 4, 0),()),
		"CameraLeft": ((9, LCID, 4, 0),()),
		"CameraRight": ((10, LCID, 4, 0),()),
		"CameraTop": ((11, LCID, 4, 0),()),
		"CurrentCamera": ((6, LCID, 4, 0),()),
		"ExposureTime": ((7, LCID, 4, 0),()),
		"Speed": ((16, LCID, 4, 0),()),
	}

class _IGatanCameraEvents:
	"""_IGatanCameraEvents Interface"""
	CLSID = CLSID_Sink = pythoncom.MakeIID('{7BFB9F17-E672-4C37-A5F4-393FFA63DF88}')
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

# This CoClass is known by the name 'TecnaiCCD.GatanCamera.1'
class GatanCamera(CoClassBaseClass): # A CoClass
	# GatanCamera Class
	CLSID = pythoncom.MakeIID("{C634F718-4DA0-4974-988A-9BDB5D6D94D2}")
	coclass_sources = [
		_IGatanCameraEvents,
	]
	default_source = _IGatanCameraEvents
	coclass_interfaces = [
		IGatanCamera,
	]
	default_interface = IGatanCamera

IGatanCamera_vtables_dispatch_ = 1
IGatanCamera_vtables_ = [
	('HasFeature', 5, ((2,0,None), (16387,10,None), ), (3, 0, None), ('f', 'pVal')),
	('ExecuteScript', 13, ((8,0,None), (16388,10,None), ), (3, 0, None), ('script', 'pVal')),
	('ExecuteScriptFile', 14, ((8,0,None), (16388,10,None), ), (3, 0, None), ('filename', 'pVal')),
	('Insert', 50, (), (3, 0, None), ()),
	('Retract', 51, (), (3, 0, None), ()),
	('OpenShutter', 52, ((3,1,None), ), (3, 0, None), ('newVal',)),
	('LaunchAcquisition', 53, ((3,0,None), ), (3, 0, None), ('mode',)),
	('StopAcquisition', 54, (), (3, 0, None), ()),
	('StartAcquisition', 55, ((3,0,None), ), (3, 0, None), ('mode',)),
	('SaveImageInDMFormat', 56, ((8,0,None), ), (3, 0, None), ('filename',)),
	('AcquireAndShowImage', 57, ((3,0,None), ), (3, 0, None), ('mode',)),
	('AcquireImage', 58, ((16396,10,None), ), (3, 0, None), ('pImage',)),
	('SelectCameraParameters', 59, ((3,0,None), ), (3, 0, None), ('mode',)),
	('AcquireFrontImage', 60, ((24578,2,None), ), (3, 0, None), ('pImageData',)),
	('AcquireImageShown', 61, ((24578,2,None), ), (3, 0, None), ('pImageData',)),
	('ShowAcquiredImage', 62, (), (3, 0, None), ()),
	('AcquireRawImage', 63, ((16396,10,None), ), (3, 0, None), ('pImage',)),
]

RecordMap = {
}

CLSIDToClassMap = {
	'{7BFB9F17-E672-4C37-A5F4-393FFA63DF88}' : _IGatanCameraEvents,
	'{18F3C374-2D04-4CEC-8F3F-B1CECDBA1068}' : IGatanCamera,
	'{C634F718-4DA0-4974-988A-9BDB5D6D94D2}' : GatanCamera,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
}


VTablesNamesToCLSIDMap = {
	'IGatanCamera' : '{18F3C374-2D04-4CEC-8F3F-B1CECDBA1068}',
}

win32com.client.constants.__dicts__.append(constants.__dict__)

