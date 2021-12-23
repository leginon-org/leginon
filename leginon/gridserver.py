#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import os
try:
	import requests
	NO_REQUESTS=False
except:
	NO_REQUESTS=True
import json

from leginon import leginondata
from leginon import projectdata
import pyami.moduleconfig

# get configuration from gridhook.cfg
try:
	configs = pyami.moduleconfig.getConfigured('gridhook.cfg')
except:
	if not NO_REQUESTS:
		# Don't want it to crash here.
		print 'gridhook.cfg does not exist. Grid Management Hook disabled'

class GridHookServer(object):
	'''
	Similar request server as leginon remoteserver but simpler and generalized
	on the route and field used with a config file.
	'''
	def __init__(self, sessiondata, projdata):
		self.sessiondata = sessiondata
		self.project = projdata
		try:
			self.leg_gridhook_auth = (configs['rest auth']['user'],configs['rest auth']['password'])
			self.gridhook_server_active = True
		except:
			self.leg_gridhook_auth = ('','')
			self.gridhook_server_active = False
			return
		result = self.testQuery()
		if result is False:
			# connection or missing remote.cfg error.
			self.gridhook_server_active = False

		if 'weblink group' in configs and 'model' in configs['weblink group']:
			self.model = configs['weblink group']['model']
		else:
			self.model = None

	def testQuery(self):
		router_name = configs['test api router']['path']
		data = {}
		try:
			results = self.get(router_name, data)
		except requests.ConnectionError:
			return False
		return True

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
			if int(answer.status_code) == 400:
			# display in the terminal 
				raise RuntimeError('Error in request : %s %s' % (answer.status_code, answer.reason))
			return False

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
		if not self.gridhook_server_active or not pk:
			return
		url = self._makeUrl(router_name, pk=pk)
		answer = requests.delete(url=url, auth=self.leg_gridhook_auth)
		return self._processResponse(answer)

	def patch(self, router_name, pk, data):
		'''
		Patch causes an update of the data defined by the ModelViewSet
		'''
		if not self.gridhook_server_active or not pk or not data:
			return
		url = self._makeUrl(router_name, pk=pk)
		#print(url, data)
		answer = requests.patch(url=url, json=data, auth=self.leg_gridhook_auth)
		return self._processResponse(answer)

	def get(self, router_name, data):
		'''
		Get causes a filtered get of the data defined by the ModelViewSet
		Returns a list of filtered data dict
		'''
		if not self.gridhook_server_active:
			return False
		param_str = self._processParamsToSend(data)
		url = self._makeUrl(router_name, param_str=param_str)
		answer = requests.get(url=url, auth=self.leg_gridhook_auth)
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
		if not self.gridhook_server_active or not data:
			return False
		url = self._makeUrl(router_name)
		#print('post url ',url)
		answer = requests.post(url=url, json=data, auth=self.leg_gridhook_auth)
		#print 'got answer from post', url
		return self._processResponse(answer)

	def getGridGroupId(self):
		'''
		Get grid management grid group pk.  This is normally project
		but leaves room for different group, such as user to be used.
		'''
		if self.model:
			model_pk = getattr(self,'getGrid%s' % str.title(self.model))()
		else:
			model_pk = False
		return model_pk

	def getGridProject(self):
		'''
		Get grid management project pk.
		'''
		if 'project api router' not in configs:
			# this will make it not to attempt insertion of project referebce
			return False
		this_api = configs['project api router']
		router_name = this_api['path']
		if not 'name' in self.project.keys():
			raise ValueError('project data must have "name" field')
		project_name = self.project['name']
		field_name = this_api['name_field']
		# data
		data = {
			field_name:project_name,
		}
		results = self.get(router_name, data)
		if type(results) == type([]) and len(results) == 0:
			raise ValueError('Project name %s not found in grid management system' % project_name)
		if results == False:
			raise RuntimeError('Grid management system is not connected')
		pk = results[0]['id']
		return pk

	def getSession(self):
		'''
		return LeginonSession model primary key from grid management system
		rest api.  return False if not found or have trouble.
		'''
		this_api = configs['session api router']
		router_name = this_api['path']
		field_name = this_api['name_field']
		# data
		data = {
				field_name:self.sessiondata['name'],
		}
		# find out if session is already there
		try:
			results = self.get(router_name, data)
		except requests.ConnectionError:
			return False
		if not results:
			# False is returned from get if gridhook.cfg is not set, or unauthorized
			return False
		pk = results[0]['id']
		return pk

	def setSession(self, session_id=None):
		'''
		insert or updat LeginonSession model primary key on grid management system
		rest api.  It raises error if having trouble.
		'''
		this_api = configs['session api router']
		router_name = this_api['path']
		field_name = this_api['name_field']
		# data
		data = {
				field_name:self.sessiondata['name'],
		}
		patch_dict = {}
		if session_id:
			# add leginondata SessionData id
			field_name = this_api['id_field']
			patch_dict[field_name] = session_id
		# a grouping model that organizes the session.  It should
		# be a ForeignKey field in the LeginonSession model.
		# normally project
		group_model_pk = self.getGridGroupId()
		if group_model_pk:
			# add grid management system group primary key
			field_name = this_api['group_id_field']
			patch_dict[field_name] = group_model_pk
		result = self.getSession()
		if not result:
			data.update(patch_dict)
			p_result = self.post(router_name, data)
			if p_result is False:
				return False
			pk = p_result['id']
		else:
			pk = result
			if patch_dict:
				self.patch(router_name, pk, patch_dict)
		return pk

	def getWebLinkUrl(self):
		'''
		Return an url to show as hyperlink.  If the weblink group model is
		specified, it will point to the detail page rather than the default.
		'''
		url = configs['web server']['url']
		if self.model:
			model_pk = getattr(self,'getGrid%s' % str.title(self.model))()
			if model_pk:
					view_url = os.path.join(url,self.model,'%d' % model_pk)
					return view_url
		return url

	def getGridDisplay(self):
		'''
		Return a string to be displayed or recorded in Leginon that
		represents the grid.
		'''
		session_pk = self.getSession()
		if not session_pk:
			raise ValueError('Leginon session is not found on grid management system')
		this_api = configs['gridmap api router']
		router_name = this_api['path']
		field_name = this_api['session_field']
		# data
		data = {
				field_name:session_pk,
		}
		results = self.get(router_name, data)
		if not results:
			# nothing to display
			return 'no grid mapping set'
		field_name = this_api['grid_display_field']
		return results[0][field_name]

	def getGrid(self, grid_display_name):
		'''
		Get grid info from grid_display_name string that is found in grid management
		system through the api.
		'''
		this_api = configs['grid api router']
		router_name = this_api['path']
		field_name = this_api['grid_display_field']
		# data
		data = {
				field_name:grid_display_name,
		}
		results = self.get(router_name, data)
		if not results:
			raise ValueError('%s not found' % grid_display_name)
		if len(results) > 1:
			raise ValueError('More than one %s found' % grid_display_name)
		project_field_name = this_api['project_field']
		grid_proj_id = results[0][project_field_name]
		session_proj_pk = self.getGridProject()
		if session_proj_pk and grid_proj_id != session_proj_pk:
			raise ValueError('Mismatched grid management project id: %d vs %d' % (session_proj_pk,grid_proj_id))
		return results[0]
	
	def setGridSession(self,grid_display_name):
		session_pk = self.getSession()
		try:
			grid_info = self.getGrid(grid_display_name)
		except Exception as e:
			print('Error: %s' % e)
			return False
		this_api = configs['gridmap api router']
		router_name = this_api['path']
		session_field_name = this_api['session_field']
		grid_field_name = this_api['grid_field']
		grid_pk = grid_info['id']
		# data
		data = {
				session_field_name:session_pk,
				grid_field_name:grid_pk
		}
		p_result = self.post(router_name, data)
		if p_result is False:
			return False
		pk = p_result['id']
		return pk

if __name__=='__main__':
	sessionname = raw_input('session name to test=')
	s = leginondata.SessionData(name=sessionname).query(results=1)[0]
	pe=projectdata.projectexperiments(session=s).query(results=1)[0]
	app = GridHookServer(s,pe['project'])
	if app.gridhook_server_active:
		session_pk = app.setSession()
		gridsession_pk = app.setGridSession(s['comment'])
		print gridsession_pk
