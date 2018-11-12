#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import os
import shutil
import time
import threading

from leginon import leginondata
from pyami import fileutil, jpg
import gui.wx.ClickTargetFinder

SLEEP_TIME = 5

class RemoteServerMaster(object):
	def __init__(self, logger, sessiondata, node):
		self.logger = logger
		self.session = sessiondata
		self.node = node
		self.node_name = node.name.replace(' ','_')
		self.remote_passcode = sessiondata['remote passcode']
		
		self.remotedata_base = os.path.join(os.path.dirname(sessiondata['image path']),'remote',self.node_name)
		fileutil.mkdirs(self.remotedata_base)
		self.toolbar = RemoteToolbar(logger, sessiondata, node, self.remotedata_base)
		self.targets = RemoteTargetServer(logger, sessiondata, node, self.remotedata_base)

class RemoteServer(object):
	def __init__(self, logger, sessiondata, node):
		self.logger = logger
		self.session = sessiondata
		self.node = node
		self.remote_passcode = sessiondata['remote passcode']

class RemoteToolbar(RemoteServer):
	def __init__(self, logger, sessiondata, node, remotedata_base):
		super(RemoteToolbar,self).__init__(logger, sessiondata, node)
		self.datafile_base = os.path.join(remotedata_base,'tools')
		fileutil.mkdirs(self.datafile_base)
		self.tools = {}

	def addClickTool(self,name, handling_attr_name, help_string=''):
		if name not in self.tools:
			self.tools[name] = ClickTool(self, name, handling_attr_name, help_string)
		else:
			self.tools[name].activate()

	def removeClickTool(self, name):
		if name in self.tools:
			self.tools[name].deActivate()
			time.sleep(SLEEP_TIME)
			self.tools.pop(name)

class Tool(object):
	def __init__(self, parent, name, handling_attr_name, help_string):
		self.toolbar = parent
		self.name = name
		self.handling_attr = getattr(self.toolbar.node, handling_attr_name)
		self.help_string = help_string
		self.data_path = os.path.join(self.toolbar.datafile_base,name)
			
class ClickTool(Tool):
	'''
	Click tool calls a handling attribute from the node when it is triggered
	by the existance of the file at triggerpath.
	'''
	def __init__(self, parent, name, handling_attr_name, help_string):
		super(ClickTool,self).__init__(parent, name, handling_attr_name, help_string)
		triggerfile = 'click'
		self.triggerpath = os.path.join(self.data_path, triggerfile)
		self.activate()

	def deActivate(self):
		self.active = False

	def activate(self):
		self.active = True
		self.startWaiting()

	def startWaiting(self):
		t = threading.Thread(target=self.clickTracking)
		t.setDaemon(True)
		t.start()

	def clickTracking(self):
		'''
		Track triggerpath existance if active
		'''
		while self.active:
			print 'click tracking active'
			if os.path.isfile(self.triggerpath):
				self.handling_attr()
				os.remove(self.triggerpath)
			time.sleep(SLEEP_TIME)		

class RemoteTargetServer(RemoteServer):
	def __init__(self, logger, sessiondata, node, remotedata_base):
		super(RemoteTargetServer,self).__init__(logger, sessiondata, node)
		self.targetnames = []
		self.datafile_base = os.path.join(remotedata_base,'targets')
		fileutil.mkdirs(self.datafile_base)
		self.targefilepath = None
		self.excluded_targetnames = ['Blob']

	def setTargetNames(self,targetnames):
		'''
		set names of target types to be displayed and edited by the remote client.
		'''
		self.targetnames = targetnames
		# remove those not useful to be picked remotely
		for name in self.excluded_targetnames:
			if name in targetnames:
				targetnames.remove(name)

		self.out_targetnamesfilepath = os.path.join(self.datafile_base,'targetnames')
		self._writeTargetNames(targetnames)

	def _writeTargetNames(self, targetnames):
		f = open(self.out_targetnamesfilepath,'w')
		f.write('\n'.join(targetnames))
		f.close()
	
	def setImage(self, imagedata):
		'''
		set the image to define targets on.
		'''
		self.imagedata = imagedata
		image_base = os.path.join(self.datafile_base,'%06d' % imagedata.dbid)
		fileutil.mkdirs(image_base)
		self.out_jpgfilepath = os.path.join(image_base,'image.jpg')
		self.out_targetfilepath = os.path.join(image_base,'outtargets')
		self.in_targetfilepath = os.path.join(image_base,'intargets')

		self._writeOutJpgFile()

	def unsetImage(self, imagedata):
		self.resetTargets()
		image_base = os.path.join(self.datafile_base,'%06d' % imagedata.dbid)
		shutil.rmtree(image_base)
		self.imagedata = None

	def _writeOutJpgFile(self):
		jpg.write(self.imagedata['image'],self.out_jpgfilepath)

	def setOutTargets(self, xytargets):
		'''
		Set xy coordinates of targets to send to the remote client
		'''
		# dictionary { targetname:(x,y), }. x,y are floats to keep the precision
		self.outtargets = xytargets
		self._writeTargetsToFile(xytargets)

	def getJpgFilePath(self):
		t = self.out_jpgfilepath
		if t is None:
			raise ValueError('Image JPG File Path not set')
		return t

	def getOutTargetFilePath(self):
		t = self.out_targetfilepath
		if t is None:
			raise ValueError('Target File Path not set')
		return t

	def getInTargetFilePath(self):
		t = self.in_targetfilepath
		if t is None:
			raise ValueError('Target File Path not set')
		return t

	def _writeTargetsToFile(self, targets):
		'''
		Write targets to file
		'''
		f = open(self.out_targetfilepath,'w')
		for name in targets.keys():
			for xy in targets[name]:
				line = '\t'.join([name,'%d' % xy[0],'%d' % xy[1]])
				line +='\n'
				f.write(line)
		f.close()

	def _readTargetsFromFile(self):
		'''
		wait for target file to appear and read targets from it.
		'''
		while not os.path.isfile(self.in_targetfilepath):
			time.sleep(SLEEP_TIME)
		print 'Found file'
		if not os.access(self.in_targetfilepath, os.R_OK):
			raise ValueError('%s not readable' % self.in_targetfilepath)
		try:
			xys = self._readTargetNameXYs()
			return xys
		except Exception,e:
			self.logger.error(e)
			raise
			# return False causes this function to be called again
			return False

	def _readTargetNameXYs(self):
		'''
		Read targets from file and organize them into a dictionary
		according to targetnames.
		'''
		infile = open(self.in_targetfilepath)
		lines = infile.readlines()
		infile.close()

		passcode_in_file = lines[0][:-1]
		if passcode_in_file != self.remote_passcode:
			self.resetTargets()
			raise ValueError('Passcode not matching. Targets removed')
		xys = {}
		for n in self.targetnames:
			xys[n] = []

		for l in lines[1:]:
			# strip one regardless of the form
			bits = l[:-1].split('\t')
			tname = bits[0]
			x = int(bits[1])
			y = int(bits[2])
			if tname in self.targetnames:
				xys[tname].append((x,y)) 		
		return xys

	def getInTargets(self):
		'''
		Wait until it gets a list of xy tuple for each targetname
		'''
		xys = False
		while xys is False:
			xys = self._readTargetsFromFile()
		return xys

	def resetTargets(self):
		'''
		Remove target file
		'''
		if not os.access(self.in_targetfilepath, os.W_OK):
			raise ValueError('%s not writable.' % self.in_targetfilepath)
		os.remove(self.in_targetfilepath)
