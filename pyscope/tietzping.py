#
# COPYRIGHT:
#      The Leginon software is Copyright 2003
#      The Scripps Research Institute, La Jolla, CA
#      For terms of the license agreement
#      see  http://ami.scripps.edu/software/leginon-license
#

import win32com.server.register
try:
	import tietzcom
except:
	from pyscope import tietzcom

class Ping(object):
	_typelib_guid_ = tietzcom.CLSID
	_typelib_version = 1, 0
	_com_interfaces_ = ['ICAMCCallBack'] #[tietzcom.ICAMCCallBack.CLSID]
	_public_methods_ = ['LivePing', 'RequestLock']
	_reg_clsid_ = '{939120E3-FE5B-4AED-A945-1B8D4382EB71}'
	_reg_progid_ = 'pyscope.CAMCCallBack'
	_reg_desc_ = 'pyscope CAMC Callback'

	def LivePing(self):
		return 0

	def RequestLock(self):
		return False

def register():
	win32com.server.register.UseCommandLine(Ping)

if __name__ == '__main__':
	register()

