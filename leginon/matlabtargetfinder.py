# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/matlabtargetfinder.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-01-18 23:33:10 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import numarray
import os.path
import threading
import data
import targetfinder
import gui.wx.MatlabTargetFinder
try:
	import pymat
except:
	pymat = None

handle = None

class MatlabTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.MatlabTargetFinder.Panel
	settingsclass = data.MatlabTargetFinderSettingsData
	defaultsettings = {
		'wait for done': True,
		'ignore images': False,
		'module': '',
		'user check': True,
	}
	def __init__(self, *args, **kwargs):
		self.userpause = threading.Event()
		targetfinder.TargetFinder.__init__(self, *args, **kwargs)
		if pymat is None:
			self.logger.error('Loading Python Matlab interface (pymat) failed')
		self.start()

	def matlab(self, image):
		if handle is None:
			handle = pymat.open()

		pymat.put(handle, 'image', image)
		pymat.put(handle, 'focus', [])
		pymat.put(handle, 'acquisition', [])

		d, f = os.path.split(self.settings['module path'])

		if d:
			pymat.eval(handle, 'path(path, %s)' % d)

		if not f[:-2]:
			raise RuntimeError

		pymat.eval(handle, '[acquisition, focus] = %s(image)' % f[:-2])

		focus = pymat.get(handle, 'focus')
		acquisition = pymat.get(handle, 'acquisition')

		pymat.put(handle, 'image', [])
		pymat.put(handle, 'focus', [])
		pymat.put(handle, 'acquisition', [])

		self.setTargets(acquisition, 'acquisition')
		self.setTargets(focus, 'focus')

	def findTargets(self, imdata, targetlist):
		image = imdata['image']

		self.setImage(image, 'Image')

		self.matlab(image)

		if self.settings['user check']:
			# user now clicks on targets
			self.notifyUserSubmit()
			self.userpause.clear()
			self.setStatus('user input')
			self.userpause.wait()
		self.setStatus('processing')
		self.logger.info('Targets have been submitted')
		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)

	def submitTargets(self):
		self.userpause.set()

