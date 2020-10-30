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
try:
	import requests
	NO_REQUESTS=False
except:
	NO_REQUESTS=True
import json

from leginon import leginondata
import pyami.moduleconfig
import pyami.fileutil
import pyami.numpil

SLEEP_TIME = 2

# get configuration from remote.cfg
try:
	configs = pyami.moduleconfig.getConfigured('remote.cfg')
except:
	if not NO_REQUESTS:
		# Don't want it to crash here.
		print 'remote.cfg does not exist. Remote disabled'

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
		# django media

class RemoteSessionServer(object):
	def __init__(self, logger, sessiondata):
		self.logger = logger # if logger is not valid, it will print to terminal
		self.session = sessiondata
		try:
			self.leg_remote_auth = (configs['leginon auth']['username'],configs['leginon auth']['password'])
			self.remote_server_active = True
			self.media_maps = configs['media maps']
		except:
			self.leg_remote_auth = ('','')
			self.media_maps = {}
			self.remote_server_active = False
		# This is the first attempt to connect to remote.
		self.session_pk = self.setSession()
		if self.session_pk is False:
			# connection or missing remote.cfg error.
			self.remote_server_active = False

	def setSession(self):
		router_name = 'api/sessions'
		media_session_path = self.getMediaSessionPath()
		self.media_base = os.path.join(media_session_path,'remote')
		# data
		data = {
				'name':self.session['name'],
				'leginon_session_db_id': self.session.dbid,
		}
		# find out if session is already there
		try:
			results = self.get(router_name, data)
		except requests.ConnectionError:
			return False
		if results is False:
			# False is returned from get if remote.cfg is not set, or unauthorized
			return False
		patch_dict ={'path':media_session_path}
		data.update({'path':media_session_path})
		if not results:
			p_result = self.post(router_name, data)
			if p_result is False:
				return False
			pk = p_result['id']
		else:
			pk = results[0]['id']
			self.patch(router_name, pk, patch_dict)
		return pk

	def getMediaSessionPath(self):
		media_session_rawdata_path = self.session['image path']
		for k in self.media_maps.keys():
			# a bit complicated because module config key is all lower case
			pattern_index = self.session['image path'].lower().find(k)
			if pattern_index < 0:
				continue
			elif pattern_index == 0:
				pref = ''
			else:
				pref = self.session['image path'][:pattern_index]
			media_session_rawdata_path = pref+self.media_maps[k]+self.session['image path'][pattern_index+len(k):]
		media_session_path = os.path.dirname(media_session_rawdata_path)
		return media_session_path

	def clearRemoteNodes(self):
		'''
		Clear date in the session so that it can restart cleanly.
		'''
		# remove images first because it uses references of targeting session_nodes
		self._clearRemoteImages()
		self._clearRemoteTargetingNodes()
		routers = ['remote/status','remote/toolbar','remote/click','remote/pmlock']
		for name in routers:
			self._clearRemoteByPk(name)

	def _clearRemoteByPk(self, router_name):
		results = self.get(router_name,{'session_name':self.session['name']})
		if not results:
			return
		for r in results:
			self.delete(router_name, r['pk'])

	def _clearRemoteTargetingNodes(self):
		router_name = 'api/session_nodes'
		s_results = self.get('api/sessions',{'name':self.session['name']})
		if not s_results:
			return
		session_pk = s_results[0]['id']
		results = self.get(router_name,{'session':session_pk})
		if not results:
			return
		for r in results:
			self.delete(router_name, r['id'])

	def _clearRemoteImages(self):
		router_name = 'api/images'
		results = self.get(router_name,{})
		if not results:
			return
		for r in results:
			if r['name'].startswith(self.session['name']):
				self.delete(router_name,r['id'])

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
				return False
			return json.loads(answer.text)
		else:
			try:
				self.logger.error('Error communicating with webserver for leginon-remote: code %s' % (answer.status_code))
			except AttributeError:
				# display in the terminal if logger is not ready
				print('Error before logger is up in communication to leginon-remote: %s %s' % (answer.status_code, answer.reason))
			return False

	def _processDataToSend(self, data):
		'''
		Process data before sending for POST. For example, add session_name.
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
		Delete causes a distroy of the data defined by the ModelViewSet and pk
		'''
		if not self.remote_server_active or not pk:
			return
		url = self._makeUrl(router_name, pk=pk)
		answer = requests.delete(url=url, auth=self.leg_remote_auth)
		return self._processResponse(answer)

	def patch(self, router_name, pk, data):
		'''
		Patch causes an update of the data defined by the ModelViewSet
		'''
		if not self.remote_server_active or not pk or not data:
			return
		url = self._makeUrl(router_name, pk=pk)
		#print(url, data)
		answer = requests.patch(url=url, json=data, auth=self.leg_remote_auth)
		return self._processResponse(answer)

	def get(self, router_name, data):
		'''
		Get causes a filtered get of the data defined by the ModelViewSet
		Returns a list of filtered data dict
		'''
		if not self.remote_server_active:
			return False
		param_str = self._processParamsToSend(data)
		url = self._makeUrl(router_name, param_str=param_str)
		answer = requests.get(url=url, auth=self.leg_remote_auth)
		#print 'got answer from ', url
		queryset = self._processResponse(answer)
		if hasattr(queryset,'keys') and 'results' in queryset.keys():
			# success results
			return queryset['results']
		# with error this will be False
		return queryset

	def post(self, router_name, data):
		'''
		Post causes a create of the data defined by the ModelViewSet
		'''
		if not self.remote_server_active or not data:
			return False
		url = self._makeUrl(router_name)
		if router_name in ('remote/click','remote/status'):
			data = self._processDataToSend(data)
		#print('post url ',url)
		answer = requests.post(url=url, json=data, auth=self.leg_remote_auth)
		#print 'got answer from post', url
		return self._processResponse(answer)

	def userHasControl(self, log_error=False):
		try:
			if self.remote_server_active:
				session_pk = self.get('api/sessions',{'name':self.session['name']})[0]['id']
				controlled_by_user = self.get('api/microscopes',{'session':session_pk})[0]['controlled_by_user']
				return controlled_by_user
			else:
				return False
		except IndexError:
			if log_error:
				self.logger.error('Session not assigned for remote')
			return False
		except requests.ConnectionError:
			# always want to pass to leginon log
			if log_error:
				e = 'Connection to remote is lost'
				self.logger.error(e)
			return None
		except TypeError:
			if log_error:
				self.logger.error('Failed to determinine microscope control')
			return False

class RemoteNodeServer(RemoteSessionServer):
	def __init__(self, logger, sessiondata, node):
		super(RemoteNodeServer,self).__init__(logger, sessiondata)
		self.node = node
		self.node_name = node.name.replace(' ','_')

class PresetsManagerLock(RemoteNodeServer):
	router_name = 'remote/pmlock'
	def __init__(self, logger, sessiondata, node):
		super(PresetsManagerLock,self).__init__(logger, sessiondata, node)
		self.data = {
				'session_name': self.session['name'],
				'node_order': self.node.node_order,
		}

	def setLock(self):
		if not self.userHasControl(log_error=False):
			# do nothing
			return
		results = self.get(self.router_name, self.data)
		if results:
			return
		else:
			return self.post(self.router_name, self.data)

	def setUnlock(self):
		if not self.userHasControl(log_error=False):
			# do nothing
			return
		results = self.get(self.router_name, self.data)
		if results:
			self.logger.debug(results)
			self.delete(self.router_name, results[0]['pk'])

class RemoteStatusbar(RemoteNodeServer):
	router_name = 'remote/status'
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteStatusbar,self).__init__(logger, sessiondata, node)
		self.data = {
				'session_name': self.session['name'],
				'node': self.node_name,
		}

	def _isThisSubClass(self):
		settingsdata_prefixes = ['Acquisition','TargetFinder','Conditioner','Reference','ZeroLossIceThickness','PresetsManager']
		for name in settingsdata_prefixes:
			if issubclass(self.node.settingsclass, getattr(leginondata, '%sSettingsData' % name)):
				return name

	def setStatus(self, status):
		this_subclass = self._isThisSubClass()
		if this_subclass is None:
			return
		if not self.userHasControl(log_error=False):
			# do nothing
			return
		try:
			self._setStatus(status, this_subclass)
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			# not to log as this is not critical and has too many occurance.
			#self.logger.error(e)

	def _setStatus(self, status, this_subclass):
		status_str='_'.join(status.split())
		# map to different strings to put them at the front of alpha beta sort
		if status == 'remote':
			status_str='need_remote_input'
		if this_subclass == 'Acquisition' and status == 'user input':
			# user input status in acquisition node means paused locally.
			status_str='paused'
		if this_subclass not in ('Acquisition', 'TargetFinder') and status == 'processing':
			status_str='busy'
		results = self.get(self.router_name, self.data)
		if status in ('processing','user input','waiting','remote'):
			if results:
				return self.patch(self.router_name, results[0]['pk'], {'value':status_str, 'node_order':self.node.node_order})
			data = self.data.copy()
			data.update({'value':status_str, 'node_order':self.node.node_order})
			return self.post(self.router_name, data)
		else:
			if results:
				self.logger.debug(results)
				self.delete(self.router_name, results[0]['pk'])

class RemoteQueueCount(RemoteNodeServer):
	router_name = 'remote/queue'
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteQueueCount,self).__init__(logger, sessiondata, node)

	def setQueueCount(self, count):
		try:
			self._setQueueCount(count)
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			# not to log as this is not critical and has too many occurance.
			#self.logger.error(e)

	def _setQueueCount(self, count):
		self.data = {
				'session_name': self.session['name'],
				'node': self.node_name,
		}
		patch_dict = {'count':count}
		results = self.get(self.router_name, self.data)
		if results:
			# patch existing toolbar
			return self.patch(self.router_name, results[0]['pk'], patch_dict)
		# insert new toolbar
		data = self.data.copy()
		data.update(patch_dict)
		return self.post(self.router_name, data)

class RemoteToolbar(RemoteNodeServer):
	router_name = 'remote/toolbar'
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteToolbar,self).__init__(logger, sessiondata, node)
		self.tools = {}
		self.tool_configs = {}

	def addClickTool(self,name, handling_attr_name, help_string='',block_rule='none'):
		if not name in self.tools.keys():
			self.tools[name] = ClickTool(self, name, handling_attr_name, help_string, block_rule)
			self.tool_configs[name] = self.tools[name].tool_config
		else:
			# reconnect after leginon-remote restarted
			if not self.tools[name].active:
				self.tools[name].activate()

	def removeClickTool(self, name):
		if name in self.tools:
			self.tools[name].deActivate()
			time.sleep(1)
			self.tools.pop(name)
			self.tool_configs.pop(name)

	def finalizeToolbar(self):
		self.data = {
				'session_name': self.session['name'],
				'node': self.node_name,
		}
		patch_dict = {'tools':self.tool_configs,'node_order':self.node.node_order}
		results = self.get(self.router_name, self.data)
		if results:
			# patch existing toolbar
			return self.patch(self.router_name, results[0]['pk'], patch_dict)
		# insert new toolbar
		data = self.data.copy()
		data.update(patch_dict)
		return self.post(self.router_name, data)

	def exit(self):
		for name in self.tools.keys():
			# deactivate first to stop tracking
			self.tools[name].deActivate()
			time.sleep(1)

class Tool(object):
	def __init__(self, parent, name, handling_attr_name, help_string):
		self.toolbar = parent
		self.name = name
		self.handling_attr = getattr(self.toolbar.node, handling_attr_name)
		self.help_string = help_string
		# tool configuration to be included in NodeToolbar post
		self.tool_config = {'type': None, 'choices':(), 'help':self.help_string}
		# basic data for a tool in the toolbar to query on
		self.tool_data = {
				'session_name': self.toolbar.session['name'],
				'node': self.toolbar.node_name,
				'tool': self.name,
		}

class ClickTool(Tool):
	'''
	Click tool calls a handling attribute from the node when it is triggered
	by the existance of the specified ClickToolValue in leginon-remote
	'''
	router_name = 'remote/click'
	def __init__(self, parent, name, handling_attr_name, help_string, block_rule='none'):
		super(ClickTool,self).__init__(parent, name, handling_attr_name, help_string)
		self.tool_config.update({'type':'click','choices':(False, True),'block_rule':block_rule})
		self.toolbar.logger.debug('click tracking config: %s' % self.tool_config)
		self.active = False
		self.activate()
		response = self.toolbar.get(self.router_name,self.tool_data)

	def deActivate(self):
		self.active = False

	def activate(self):
		if not self.active:
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
		try:
			self._clickTracking()
		except requests.ConnectionError:
			self.deActivate()
			e = 'Connection to remote is lost'
			self.toolbar.logger.error(e)

	def _clickTracking(self):
		while self.active:
			if self.hasRemoteTrigger():
				self.handling_attr()
				self.resetTrigger()
			time.sleep(SLEEP_TIME)
		#print "click tracking of %s.%s deactivated" % (self.toolbar.node_name, self.name)

	def hasRemoteTrigger(self):
		'''
		Check if clicked is set on the remote tool using a web request.
		'''
		if self.toolbar.userHasControl(log_error=False) is False:
			# slow down clickTracking, This reduces remote webserver activities
			time.sleep(SLEEP_TIME)
			return False
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

class RemoteTargetingServer(RemoteNodeServer):
	route_name = 'api/images'
	def __init__(self, logger, sessiondata, node, leginon_base):
		super(RemoteTargetingServer,self).__init__(logger, sessiondata, node)
		self.target_types = []
		# where leginon saves the image
		self.datafile_base = os.path.join(leginon_base,'targeting',self.node_name)
		# where leginon-remote thinks it is looking for the image
		self.media_datafile_base = os.path.join(self.media_base,'targeting',self.node_name)
		pyami.fileutil.mkdirs(self.datafile_base)
		self.targefilepath = None
		self.excluded_target_types = ['Blobs','preview']
		self.readonly_target_types = ['done']
		self.writeonly_target_types = []
		self.router_name = 'api/images'
		self.session_node_pk = None
		self.image_pk = None
		self.active = False

	def setTargetTypes(self,target_types):
		'''
		set names of target types to be displayed and edited by the remote client.
		This is called from leginon.TargetFinder instances.
		'''
		if not self.remote_server_active:
			return
		# remove those not useful to be picked remotely
		route_name = 'api/session_nodes'
		for name in self.excluded_target_types:
			if name in target_types:
				target_types.remove(name)

		for target_name in target_types:
				target_type_data = {}
				target_type_data['name']=target_name
				target_type_data['access_type']= self.getAccessType(target_name)
				self.target_types.append(target_type_data)
		data = {}
		data['target_types'] = self.target_types
		data['node_order'] = self.node.node_order
		r = self.get(route_name,{'session':self.session_pk,'name':self.node_name})
		if r:
			session_node_pk = r[0]['id']
			response = self.patch(route_name, r[0]['id'], data)
		else:
			# insert new one
			data['name'] = self.node_name
			data['session'] = self.session_pk
			result = self.post(route_name, data)
			session_node_pk = result['id']
		# save for later use
		self.session_node_pk = session_node_pk
		return

	def getAccessType(self, name):
			permission='r' # all are readable
			if name not in self.readonly_target_types:
				permission+='w' # all are readable
			return permission

	def setImage(self, imagedata, msg=''):
		'''
		set the image to define targets on.
		'''
		self.imagedata = imagedata
		# write image
		image_base = os.path.join(self.datafile_base,'%06d' % imagedata.dbid)
		pyami.fileutil.mkdirs(image_base)
		self.out_jpgfilepath = os.path.join(image_base,'image.jpg')
		self._writeOutJpgFile()
		# set path for leginon-remote to find
		media_image_base = os.path.join(self.media_datafile_base,'%06d' % imagedata.dbid)
		self.media_out_jpgfilepath = os.path.join(media_image_base,'image.jpg')

		try:
			self._setImage(imagedata, msg)
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			self.logger.error(e)

	def _setImage(self, imagedata, msg=''):
		# create data
		data = {
				'name': imagedata['filename'],
				'targets': {},
				'targets_confirmed': False,
				'node': self.session_node_pk,
		}
		r = self.get(self.route_name,{'node':data['node'],'name':data['name']})
		patch_dict = {'path': self.media_out_jpgfilepath,'message':msg}
		if r:
			pk = r[0]['id']
			result = self.patch(self.route_name, pk, patch_dict)
			# do nothing. setTargets will do the patch
		else:
			# insert new one
			data.update(patch_dict)
			result = self.post(self.route_name, data)
			pk = result['id']
		self.image_pk = pk
		self.active = True

	def getImagePk(self):
		'''
		get current image primary key (id) in leginon-remote database.
		'''
		return self.image_pk

	def unsetImage(self, imagedata):
		'''
		Remove image_base directory and its content. This is called after
		the confirmed targets are handled by leginon.
		'''
		try:
			result = self.delete(self.route_name, self.image_pk)
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			self.logger.error(e)
		# remove file regardless
		image_base = os.path.join(self.datafile_base,'%06d' % imagedata.dbid)
		try:
			shutil.rmtree(image_base)
		except:
			# ok if file does not exist. Something else has already removed it.
			pass
		self.imagedata = None

	def _writeOutJpgFile(self):
		pyami.numpil.write(self.imagedata['image'],self.out_jpgfilepath, 'JPEG')

	def setOutTargets(self, xytargets):
		'''
		Set xy coordinates of targets to send to the remote client
		'''
		try:
			# dictionary { targetname:(x,y), }. x,y are floats to keep the precision
			self.outtargets = xytargets
			target_data = self._makeTargetData(xytargets)
			self.patch(self.router_name, self.image_pk, {'targets': target_data,'targets_confirmed':False})
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			self.logger.error(e)

	def getJpgFilePath(self):
		t = self.out_jpgfilepath
		if t is None:
			raise ValueError('Image JPG File Path not set')
		return t

	def _makeTargetData(self, xy_tuple_targets):
		'''
		make target data for leginon-remote Image object
		'''
		target_data = {}
		# dictionary { targetname:(x,y), }. x,y are floats to keep the precision
		for name in xy_tuple_targets.keys():
			target_data[name] = []
			for xy in xy_tuple_targets[name]:
				targetdict = {'x':xy[0],'y':xy[1]}
				target_data[name].append(targetdict)
		return target_data

	def _getTargetData(self):
		'''
		wait for leginon-remote Image object targets_confirmed to be True
		and read targets from it.
		'''
		filter_params = {
				'node__id': self.session_node_pk,
				'targets_confirmed': True,
		}
		while self.active and not self.get(self.route_name, filter_params):
			if not self.userHasControl():
				# stop waiting
				return False
			time.sleep(SLEEP_TIME)
		if not self.active:
			return False
		# get image object. Should always have one result.
		# NOTE this does not filter for the image.  It assumes the right image is there.
		results = self.get(self.route_name, filter_params)
		try:
			# convert coordinates to tuple
			target_data = results[0]['targets']
			xy_tuple_targets = {}
			for name in target_data.keys():
				xy_tuple_targets[name] = []
				for targetdict in target_data[name]:
					xy_tuple = (targetdict['x'], targetdict['y'])
					xy_tuple_targets[name].append(targetdict)
			return xy_tuple_targets
		except Exception,e:
			self.logger.error(e)
			# return False causes this function to be called again
			return False

	def getInTargets(self):
		'''
		Wait until it gets a list of xy tuple for each targetname
		'''
		try:
			return self._getInTargets()
		except requests.ConnectionError:
			e = 'Connection to remote is lost'
			self.logger.error(e)
			return False
		except AttributeError:
			e = 'Connection to remote is lost'
			self.logger.error(e)
			return False

	def _getInTargets(self):
		xys = False
		while xys is False or not self.active:
			xys = self._getTargetData()
			if not self.userHasControl():
				# control taken away while waiting for target.
				# stop waiting and declare failed
				return False
			# FIX ME: This will keep looping
			# if node is exited but still waiting for remote InTargets.
			time.sleep(0.5)
			# print 'looping checking targetdata and user has control with self.active=', self.active
		xys = self.filterInTargets(xys)
		return xys

	def filterInTargets(self, xys):
		'''
		Remove non-writable targets
		'''
		if xys is False:
			return
		for tname in xys.keys():
			if 'w' not in self.getAccessType(tname):
				del xys[tname]
		return xys

	def exit(self):
		self.active = False
