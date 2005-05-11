# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/matlabtargetfinder.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2005-05-11 23:50:31 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import numarray
import os.path
import threading
import data
import Mrc
import targetfinder
import gui.wx.MatlabTargetFinder
try:
	import pymat
except:
	pymat = None

class MatlabTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.MatlabTargetFinder.Panel
	settingsclass = data.MatlabTargetFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'module': '',
		'test image': '',
	})
	def __init__(self, *args, **kwargs):
		self.userpause = threading.Event()
		targetfinder.TargetFinder.__init__(self, *args, **kwargs)
		if pymat is None:
			self.logger.error('Loading Python Matlab interface (pymat) failed')
			return
		self.handle = None
		self.start()

	def matlabFindTargets(self):
		pymat.put(self.handle, 'focus', [])
		pymat.put(self.handle, 'acquisition', [])

		d, f = os.path.split(self.settings['module path'])

		if d:
			pymat.eval(self.handle, 'path(path, \'%s\')' % d)

		if not f[:-2]:
			raise RuntimeError

		pymat.eval(self.handle, '[acquisition, focus] = %s(image)' % f[:-2])

		focus = pymat.get(self.handle, 'focus')
		acquisition = pymat.get(self.handle, 'acquisition')

		self.setTargets(acquisition, 'acquisition')
		self.setTargets(focus, 'focus')

		if self.settings['user check']:
			self.panel.foundTargets()

	def findTargets(self, imdata, targetlist):
		image = imdata['image']

		self.setImage(image, 'Image')

		if self.handle is None:
			self.handle = pymat.open()
		pymat.put(self.handle, 'image', image)

		self.matlabFindTargets()

		if self.settings['user check']:
			# user now clicks on targets
			self.notifyUserSubmit()
			self.userpause.clear()
			self.setStatus('user input')
			self.userpause.wait()

		self.setStatus('processing')

		pymat.put(self.handle, 'image', [])
		pymat.put(self.handle, 'focus', [])
		pymat.put(self.handle, 'acquisition', [])

		self.publishTargets(imdata, 'focus', targetlist)
		self.publishTargets(imdata, 'acquisition', targetlist)

		self.logger.info('Targets have been submitted')

	def targetTestImage(self):
		usercheck = self.settings['user check']
		self.settings['user check'] = False
		filename = self.settings['test image']
		try:
			image = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
		except:
			self.logger.error('Failed to load test image')
			raise
			return

		self.setImage(image, 'Image')

		if self.handle is None:
			self.handle = pymat.open()
		pymat.put(self.handle, 'image', image)

		self.matlabFindTargets()

		self.settings['user check'] = usercheck
