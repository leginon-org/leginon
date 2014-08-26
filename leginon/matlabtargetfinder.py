# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/matlabtargetfinder.py,v $
# $Revision: 1.8 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-21 23:17:17 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import os.path
import threading
import numpy
from leginon import leginondata
from pyami import mrc
import targetfinder
import gui.wx.MatlabTargetFinder
import calibrationclient

try:
	import mlabraw as pymat
except:
	pymat = None

class MatlabTargetFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.MatlabTargetFinder.Panel
	settingsclass = leginondata.MatlabTargetFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'module': '',
		'test image': '',
		'parametergui': '',
	})
	def __init__(self, *args, **kwargs):
		self.userpause = threading.Event()
		targetfinder.TargetFinder.__init__(self, *args, **kwargs)
		if pymat is None:
			self.logger.error('Loading Python Matlab interface (pymat) failed')
			return
		self.handle = None
		self.start()

	def readImage(self, filename):
		# convert to float
		image2 = mrc.read(filename)
		image = numpy.asarray(image2,dtype=numpy.float)
		
		if image.any():
			self.setImage(image, 'Image')
		else:
			self.logger.error('Can not load image')

	def matlabFindTargets(self):
		pymat.put(self.handle, 'focus', [])
		pymat.put(self.handle, 'acquisition', [])

		d, f = os.path.split(self.settings['module path'])

		if d:
			pymat.eval(self.handle, 'path(path, \'%s\')' % d)

		if not f[:-2]:
			raise RuntimeError

		pymat.eval(self.handle, '[acquisition, focus] = %s(image,image_id)' % f[:-2])

		focus = pymat.get(self.handle, 'focus')
		acquisition = pymat.get(self.handle, 'acquisition')

		self.setTargets(acquisition, 'acquisition')
		self.setTargets(focus, 'focus')
		import time
		time.sleep(1)

		if self.settings['user check']:
			self.panel.foundTargets()

	def findTargets(self, imdata, targetlist):
		imdata_id = imdata.dbid
		self.logger.info(imdata_id)

		# convert to float
		image2 = imdata['image']
		image = numpy.asarray(image2,dtype=numpy.float)
		
		self.setImage(image, 'Image')

		if self.handle is None:
			self.handle = pymat.open()

		pymat.put(self.handle, 'image', image)
		pymat.put(self.handle, 'image_id',imdata_id)

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
			image2 = mrc.read(filename)		
			image = numpy.asarray(image2,dtype=numpy.float)
			
		except:
			self.logger.error('Failed to load test image')
			raise
			return
		self.setImage(image, 'Image')

		if self.handle is None:
			self.handle = pymat.open()
		pymat.put(self.handle, 'image', image)

		imdata_id = 0

		pymat.put(self.handle, 'image_id',imdata_id)
	
		self.matlabFindTargets()

		self.settings['user check'] = usercheck
