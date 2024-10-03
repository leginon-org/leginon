#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

########################################################################
#  Leginon Dependency Checker
#  This script will check Python and the Python modules installed
#  on this system to see if all requirements are met.
########################################################################

import leginon.version

print('Leginon version: ', leginon.version.getVersion())

def leginonInstalled():
	'''print info about if Leginon is already installed'''

	print('Looking for previously installed Leginon...')
	try:
		import leginon
	except:
		print('    None found.')
		return

	print('    Leginon found here:  ', leginon.__path__[0])
	print('''    *** It is best to uninstall your previous Leginon before installing
    the new one.  The best way to uninstall is to move it to a backup
    location, just in case you need to revert to the old version.''')

def versionAtLeast(version, minimum):
	'return True if version is at least minimum'

	# pad shortest one with zeros to make lengths equal
	version = list(version)
	minimum = list(minimum)
	lenv = len(version)
	lenm = len(minimum)
	diff = lenv-lenm
	if diff < 0:
		version = version + [0 for i in range(diff)]
	else:
		minimum = minimum + [0 for i in range(diff)]
	n = max(lenv,lenm)
	for i in range(n):
		if version[i] > minimum[i]:
			return True
		if version[i] < minimum[i]:
			return False
		# else equal, so check next digit
	return True

######################################################################
## Python
######################################################################
print('--------------------------------------------------------------')
leginonInstalled()
print('')

######################################################################
## Python
######################################################################
print('--------------------------------------------------------------')
print('Python:')

import sys
import os

## location of executable and module path
print('    Python executable (if wrong, check PATH in your environment):')
print('        %s' % (sys.executable,))
print('    Python module search path (if wrong, check PYTHONPATH):')
for dir in sys.path:
	print('        %s' % (dir,))
if not sys.path:
	print('        (Empty)')

## config files

## minimum python version
minpyver = (3, 8, 10)
mypyver = sys.version_info[:3]
mystr = '.'.join(map(str,mypyver))
minstr = '.'.join(map(str,minpyver))
print('    Python version: %s' % (mystr,))
if versionAtLeast(mypyver, minpyver):
	print('        OK (at least %s required)' % (minstr ,))
else:
	print('        *** FAILED (at least %s required)' % (minstr,))
	print('        Upgrade before installing other packages.')

print('    Python says home directory is:  %s' % (os.path.expanduser('~'),))

######################################################################
## Python Imaging Library
######################################################################
minpilver = (8, 0, 0)
minstr = '.'.join(map(str,minpilver))
print('--------------------------------------------------------------')
print('Python Imaging Library (PIL):')
print('    importing Image module...')
try:
	from PIL import Image
except:
	print('    *** Could not import PIL Image module.')
	print('      You must install Python Imaging Library version %s or greater' % (minstr,))
else:
	if hasattr(Image, 'VERSION'):
		mystr = Image.VERSION
	else:
		mystr = Image.__version__
	mypilver = list(map(int, mystr.split('.')))
	print('    PIL version: %s' % (mystr,))
	if versionAtLeast(mypilver, minpilver):
		print('        OK (at least %s required)' % (minstr ,))
	else:
		print('        *** FAILED (at least %s required)' % (minstr,))

######################################################################
## Python MySQL client module
######################################################################
minmysqlver = (1, 0, 2)
minstr = '.'.join(map(str,minmysqlver))
print('--------------------------------------------------------------')
print('pyMySQL Python client:')
print('    importing pymysql module...')
try:
	import pymysql
except:
	print('    *** Could not import PyMySQL module.')
	print('      You must install PyMySQL version %s or greater' % (minstr,))
else:
	mystr = pymysql.__version__
	mymysqlver = pymysql.version_info[:3]
	print('    Python MySQL version: %s' % (mystr,))
	if versionAtLeast(mymysqlver, minmysqlver):
		print('        OK (at least %s required)' % (minstr ,))
	else:
		print('        *** FAILED (at least %s required)' % (minstr,))

######################################################################
## numpy
######################################################################
minnumpyver = (1, 19)
minstr = '.'.join(map(str,minnumpyver))
print('--------------------------------------------------------------')
print('numpy:')
print('    importing numpy module...')
try:
	import numpy
except ImportError:
	print('    *** Failed to import numpy.  Install numpy first.')
else:
	mystr = numpy.__version__
	mynumpyver = list(map((lambda x:int(x)),mystr.split('.')[:2]))
	print('    numpy version: %s' % (mystr,))
	if versionAtLeast(mynumpyver, minnumpyver):
		print('        OK (at least %s required)' % (minstr ,))
	else:
		print('        *** FAILED (at least %s required)' % (minstr,))

######################################################################
## scipy
######################################################################
print('--------------------------------------------------------------')
print('scipy:')
print('    importing scipy.optimize module...')
try:
	import scipy.optimize
except ImportError:
	print('    *** Failed to import scipy.optimize.  Install scipy first')
else:
	try:
		print('      testing for leastsq function...')
		scipy.optimize.leastsq
		print('       OK')
	except:
		print('        *** FAILED: need version of scipy.optimize with leastsq')
		

######################################################################
## tifffile
######################################################################
mintifffilever = (2024, 8)
minstr = '.'.join(map(str,mintifffilever))
print('--------------------------------------------------------------')
print('tifffile:')
print('    importing tifffile module...')
try:
	import tifffile
except ImportError:
	print('    *** Failed to import tifffile.  Install tifffile first.')
else:
	mystr = tifffile.__version__
	mytifffilever = list(map((lambda x:int(x)),mystr.split('.')[:2]))
	print('    tifffile version: %s' % (mystr,))
	if versionAtLeast(mytifffilever, mintifffilever):
		print('        OK (at least %s required)' % (minstr ,))
	else:
		print('        *** FAILED (at least %s required)' % (minstr,))
######################################################################
## numextension
######################################################################
print('--------------------------------------------------------------')
print('numextension:')
print('    importing numextension module...')
try:
	import numextension
except ImportError:
	print('    *** Failed to import numextension.  Install and Build numextension first')
else:
	try:
		print('      testing for minmax function...')
		numextension.minmax
		print('       OK')
	except:
		print('        *** FAILED: could not find minmax.')


######################################################################
## wxPython
######################################################################
minwxver = (4, 1, 1)
minstr = '.'.join(map(str, minwxver))
print('--------------------------------------------------------------')
print('wxPython:')
print('    importing wx module...')
try:
	import wx
except ImportError:
	print('    *** Failed to import wx.  Install wxPython version %s or greater' % (minstr,))

else:
	## check version
	try:
		## NEWER VERSIONS
		mystr = wx.__version__
		if mystr[-1] == 'u':
			mystr = mystr[:-1]
		mywxver = list(map(int, mystr.split('.')))
	except:
		## OLDER VERSIONS
		mywxver = wx.VERSION[:4]
		mystr = '.'.join(map(str, mywxver))

	print('    wxPython version: %s' % (mystr,))
	if not versionAtLeast(mywxver, minwxver):
		print('        *** FAILED (at least %s required)' % (minstr,))

	else:
		print('        OK (at least %s required)' % (minstr ,))

	## test a wx app
		class MyApp(wx.App):
			def OnInit(self):
				frame = wx.Frame(None, -1, 'wxPython test window')
				self.sizer = wx.BoxSizer()

				button = wx.Button(frame, -1, 'TEST')
				button.SetBackgroundColour(wx.RED)
				self.sizer.Add(button, 1, border=50, flag=wx.ALL)
				self.Bind(wx.EVT_BUTTON, self.test, button)
				
				self.extlist = wx.ListBox(frame, -1, style=wx.LB_EXTENDED)
				self.extlist.InsertItems(['test1','test2','test3','test4','test5'],0)
				sz = wx.GridBagSizer(2, 0)
				label = wx.StaticText(frame, -1, 'A Scrollable Listbox')
				sz.Add(label, (1, 0), (1, 4), wx.ALIGN_CENTER)
				sz.Add(self.extlist, (2, 0), (1, 4), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

				self.szmain = wx.GridBagSizer(2, 2)
				self.szmain.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
				self.szmain.Add(self.sizer, (1, 0), (1, 1),wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)
							
				frame.SetSizerAndFit(self.szmain)
				self.SetTopWindow(frame)
				frame.Show(True)
				return True

			def test(self, evt):
				print('TEST')
				
		print('    Testing a wxPython application.  Close the window that pops up...')
		try:
			app = MyApp(0)
			app.MainLoop()
		except:
			raise
			print('        Failed to start wx application.  This is usually because you do not have display permission')
		print('    wxPython test successful')


