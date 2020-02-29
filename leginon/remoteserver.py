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
import requests
import json

from leginon import leginondata
import pyami.moduleconfig
import pyami.fileutil
import pyami.jpg

SLEEP_TIME = 5

# get configuration from remote.cfg
configs = pyami.moduleconfig.getConfigured('remote.cfg')

class RemoteServerMaster(object):
	'''
	This is used to set up session wide parameters.
	'''
	def __init__(self, logger, sessiondata, node):
		self.logger = logger
		self.session = sessiondata
		self.node = node
		
		self.leginon_base = os.path.join(os.path.dirname(sessiondata['image path']),'remote')
		pyami.fileutil.mkdirs(self.leginon_base)

class RemoteServer(object):
	def __init__(self, logger, sessiondata, node):
		self.logger = logger
		self.session = sessiondata
		self.node = node
		self.node_name = node.name.replace(' ','_')
		self.remote_id_list = [sessiondata['name'],]
		self.leg_remote_auth = (configs['leginon auth']['username'],configs['leginon auth']['password'])

	def _makeUrl(self, router_name,pk=None,param_str=None):
		'''Make url according to the config and input.
		'''
		url = configs['web server']['url']
		if not router_name.endswith('/'):
			router_name += '/'
		url = os.path.join(url, router_name)
		if pk is not None:
			url += '%d/' % pk
		if param_str is not None:
			url += '?'+param_str
		return url

	def _processResponse(self, answer):
		'''Convert json string to json style data
		'''
		if answer.ok:
			if not answer.text:
				return None
			return json.loads(answer.text)
		else:
			self.logger.error('Error communicating with webserver for leginon-remote: code %s' % (answer.status_code))

	def _processDataToSend(self, data):
		'''
		Process data before sending. For example, add session_name.
		'''
		if not 'session_name' in data.keys():
			data['session_name'] = self.session['name']
		return data

	def _processParamsToSend(self, data):
		params = []
		for k in data.keys():
			v='%s=%s' % (k,data[k],)
			params.append(v)
		return '&'.join(params)

	def delete(self, router_name, pk):
		'''
		Delect causes a distroy of the data defined by the ModelViewSet and pk
		'''
		url = self._makeUrl(router_name, pk=pk)
		answer = requests.delete(url=url, auth=self.leg_remote_auth)
		return self._processResponse(answer)

	def patch(self, router_name, pk, data):
		'''
		Patch causes an update of the data defined by the ModelViewSet
		'''
		url = self._makeUrl(router_name, pk=pk)
		answer = requests.patch(url=url, json=data, auth=self.leg_remote_auth)
		return self._processResponse(answer)

	def get(self, router_name, data):
		'''
		Get causes a filtered get of the data defined by the ModelViewSet
		Returns a list of filtered data dict
		'''
		param_str = self._processParamsToSend(data)
		url = self._makeUrl(router_name, param_str=param_str)
		answer = requests.get(url=url, auth=self.leg_remote_auth)
		return self._processResponse(answer)

	def post(self, router_name, data):
		'''
		Post causes a create of the data defined by the ModelViewSet
		'''
		url = self._makeUrl(router_name)
		data = self._processDataToSend(data)
		answer = requests.post(url=url, json=data, auth=self.leg_remote_auth)
		return self._processResponse(answer)

class RemoteStatusbar(RemoteServer):
	router_name = 'status'
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteStatusbar,self).__init__(logger, sessiondata, node)
		self.data = {
				'session_name': self.session['name'],
				'node': self.node_name
		}

	def setStatus(self, status):
		if not issubclass(self.node.settingsclass, leginondata.AcquisitionSettingsData):
			return
		status_str='_'.join(status.split())
		results = self.get(self.router_name, self.data)
		if status in ('processing','user input','waiting'):
			if results:
				return self.patch(self.router_name, results[0]['pk'], {'value':status_str})
			data = self.data.copy()
			data.update({'value':status_str})
			return self.post(self.router_name, data)
		else:
			if results:
				self.delete(self.router_name, results[0]['pk'])

class RemoteToolbar(RemoteServer):
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteToolbar,self).__init__(logger, sessiondata, node)
		self.datafile_base = os.path.join(leginon_base,'toolbar')
		pyami.fileutil.mkdirs(self.datafile_base)
		self.node_dir = os.path.join(self.datafile_base, self.node_name)
		self.remote_id_list.extend(['toolbar', self.node_name])
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
		self.data_path = os.path.join(self.toolbar.node_dir,name)
		pyami.fileutil.mkdirs(self.data_path)
		# basic data for a tool in the toolbar to send to remote
		self.tool_data = {
				'session_name': self.toolbar.session['name'],
				'node': self.toolbar.node_name,
				'tool': self.name,
		}
			
class ClickTool(Tool):
	'''
	Click tool calls a handling attribute from the node when it is triggered
	by the existance of the file at triggerpath.
	'''
	router_name = 'click'
	trigger_file = 'click'
	def __init__(self, parent, name, handling_attr_name, help_string):
		super(ClickTool,self).__init__(parent, name, handling_attr_name, help_string)
		self.triggerpath = os.path.join(self.data_path, self.trigger_file)
		self.toolbar.logger.debug('click tracking initialized for %s tool triggered by the presence of %s' % (self.name,self.triggerpath))
		self.activate()
		response = self.toolbar.get(self.router_name,self.tool_data)

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
			if self.hasRemoteTrigger():
				self.handling_attr()
				time.sleep(1)
				self.resetTrigger()
				time.sleep(1)
			time.sleep(SLEEP_TIME)		

	def hasRemoteTrigger(self):
		'''
		Check if clicked is set on the remote tool using a web request.
		'''
		response = self.toolbar.get(self.router_name,self.tool_data)
		if response:
			return True
		return False

	def resetTrigger(self):
		'''
		Reset clicked-trigger on the remote tool using a web request.
		'''
		response = self.toolbar.get(self.router_name,self.tool_data)
		if not response:
			return False
		pk = response[0]['pk']
		response = self.toolbar.delete(self.router_name,pk)
		return False

class RemoteTargetingServer(RemoteServer):
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteTargetingServer,self).__init__(logger, sessiondata, node)
		self.targetnames = []
		self.datafile_base = os.path.join(leginon_base,'targeting',self.node_name)
		pyami.fileutil.mkdirs(self.datafile_base)
		self.remote_id_list.extend(['targeting', self.node_name])
		self.targefilepath = None
		self.excluded_targetnames = ['Blobs','preview']
		self.readonly_targetnames = ['done']
		self.writeonly_targetnames = []

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
		self.setTargetPermission(targetnames)
		self._writeTargetNames(targetnames)

	def setTargetPermission(self, targetnames):
		self.permissions = {}
		for name in targetnames:
			if name not in self.writeonly_targetnames:
				self.permissions[name]='r' # all are readable
			else:
				self.permissions[name]=''
			if name not in self.readonly_targetnames:
				self.permissions[name]+='w' # all are readable

	def _writeTargetNames(self, targetnames):
		'''
		Write target names and permission. File will be overwritten.
		'''
		f = open(self.out_targetnamesfilepath,'w')
		lines = []
		for name in targetnames:
			line = '%s,%s' % (name, self.permissions[name])
			lines.append(line)
		f.write('\n'.join(lines))
		f.close()
	
	def setImage(self, imagedata):
		'''
		set the image to define targets on.
		'''
		self.imagedata = imagedata
		image_base = os.path.join(self.datafile_base,'%06d' % imagedata.dbid)
		pyami.fileutil.mkdirs(image_base)
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
		pyami.jpg.write(self.imagedata['image'],self.out_jpgfilepath)

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
				line = ','.join([name,'%d' % xy[0],'%d' % xy[1]])
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

		xys = {}
		for n in self.targetnames:
			xys[n] = []

		for l in lines[:]:
			# strip one regardless of the form
			bits = l[:-1].split(',')
			if len(bits) != 3:
				continue
			tname = bits[0]
			x = int(float(bits[1]))
			y = int(float(bits[2]))
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
		xys = self.filterInTargets(xys)
		return xys

	def filterInTargets(self, xys):
		'''
		Remove non-writable targets
		'''
		for tname in xys.keys():
			if 'w' not in self.permissions[tname]:
				del xys[tname]
		return xys

	def resetTargets(self):
		'''
		Remove target file once they are handled by TargetFinder
		'''
		if not os.access(self.in_targetfilepath, os.W_OK):
			raise ValueError('%s not writable.' % self.in_targetfilepath)
		os.remove(self.in_targetfilepath)
