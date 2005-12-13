#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

########################################################################
#  Leginon Dependency Checker
#  This script will check Python and the Python modules installed
#  on this system to see if all requirements are met.
########################################################################

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
print '--------------------------------------------------------------'
print 'Python:'

import sys

## location of executable and module path
print '    Python executable (if wrong, check PATH in your environment):'
print '        %s' % (sys.executable,)
print '    Python module search path (if wrong, check PYTHONPATH):'
for dir in sys.path:
	print '        %s' % (dir,)
if not sys.path:
	print '        (Empty)'

## minimum python version
minpyver = (2, 3, 4)
mypyver = sys.version_info[:3]
mystr = '.'.join(map(str,mypyver))
minstr = '.'.join(map(str,minpyver))
print '    Python version: %s' % (mystr,)
if versionAtLeast(mypyver, minpyver):
	print '        OK (at least %s required)' % (minstr ,)
else:
	print '        *** FAILED (at least %s required)' % (minstr,)
	print '        Upgrade before installing other packages.'

######################################################################
## Python Imaging Library
######################################################################
minpilver = (1, 1, 4)
minstr = '.'.join(map(str,minpilver))
print '--------------------------------------------------------------'
print 'Python Imaging Library (PIL):'
try:
	import Image
except:
	print '    *** Could not import Image module.'
	print '      You must install Python Imaging Library version %s or greater' % (minstr,)
else:
	mystr = Image.VERSION
	mypilver = map(int, mystr.split('.'))
	print '    PIL version: %s' % (mystr,)
	if versionAtLeast(mypilver, minpilver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

######################################################################
## Python MySQL client module
######################################################################

######################################################################
## numarray
######################################################################

######################################################################
## wxPython
######################################################################
minwxver = (2, 5, 2, 8)
minstr = '.'.join(map(str, minwxver))
print '--------------------------------------------------------------'
print 'wxPython:'
print '    importing wx module...'
try:
	import wx
except ImportError:
	print '    *** Failed to import wx.  Install wxPython version %s or greater' % (minstr,)

else:
	## check version
	mystr = wx.__version__
	if mystr[-1] == 'u':
		mystr = mystr[:-1]
	mywxver = map(int, mystr.split('.'))
	print '    wxPython version: %s' % (mystr,)
	if versionAtLeast(mywxver, minwxver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

	## test a wx app
	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'wxPython test window')
			self.sizer = wx.BoxSizer(wx.VERTICAL)
			#button = wx.Button(frame, -1)
			#self.sizer.Add(button, 1)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True
	
	print '    Testing a wxPython application.  Close the window that pops up...'
	app = MyApp(0)
	app.MainLoop()
	print '    wxPython test successful'

