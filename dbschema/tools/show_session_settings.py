#!/usr/bin/env python
'''
Display settings used in the last settings of a node from the session.
'''
import copy
from leginon import leginondata

class SettingsNode(object):
	def __init__(self, session_name,settings_class_name,inst_alias):
		self.session = leginondata.SessionData(name=session_name).query(results=1)[0]
		self.name = inst_alias
		self.settingsclass = getattr(leginondata, settings_class_name)
		self.defaultsettings = self.getDefaultSettings()
		self.getDBSessionSettings()

	def getDefaultSettings(self):
		# This won't really work with default
		return self.settingsclass()

	def initializeSettings(self, user=None):
		'''
		Initialize with settings from user and admin.  This block is copied from node.py
		'''
		if not hasattr(self, 'settingsclass'):
			return

		settings = self.reseachDBSettings(self.settingsclass, self.name, user)

		# if that failed, use hard coded defaults
		if not settings:
			self.settings = copy.deepcopy(self.defaultsettings)
		else:
			# get query result into usable form
			settings = settings[0]
			self.settings = settings.toDict(dereference=True)
			del self.settings['session']
			del self.settings['name']

		# get current admin settings
		admin_settings = self.getDBAdminSettings(self.settingsclass, self.name)

		# check if None in any fields
		for key,value in self.settings.items():
			if value is None:
				if key in admin_settings and admin_settings[key] is not None:
					# use current admin settings if possible
					self.settings[key] = copy.deepcopy(admin_settings[key])
				elif key in self.defaultsettings:
					# use default value of the node
					self.settings[key] = copy.deepcopy(self.defaultsettings[key])
			# The value is another Data class such as BlobFinderSettingsData
			if issubclass(value.__class__, dict):
				for skey, svalue in value.items():
					if svalue is None:
						if admin_settings is not None and key in admin_settings and admin_settings[key] is not None and skey in admin_settings[key] and admin_settings[key][skey] is not None:
							# use current admin settings if possible
							self.settings[key][skey] = copy.deepcopy(admin_settings[key][skey])
						elif skey in self.defaultsettings[key]:
								# use default value of the node
								self.settings[key][skey] = copy.deepcopy(self.defaultsettings[key][skey])

	def reseachDBSettings(self, settingsclass, inst_alias, user=None):
		'''
		Get Settings from the user or admin values before the session
		was created.
		'''
		# load the requested user settings
		if user is None:
			user = self.session['user']
		qsession = leginondata.SessionData(initializer={'user': user})
		qdata = settingsclass(initializer={'session': qsession,
																						'name': inst_alias})
		settings_list = qdata.query()
		# if that failed, try to load default settings from DB
		if not settings_list:
			# try admin settings.
			settings = self.getDBAdminSettings(settingsclass, inst_alias)
			if settings:
				settings_list = [settings,]
		else:
			for s in settings_list:
				# use settings from the one before the session in question
				if s.timestamp < self.session.timestamp:
					return [s,]
		return settings_list

	def getDBAdminSettings(self, settingsclass, inst_alias):
		"""
		Get one administrator settings for the node instance.
		Returns empty dictionary if not found.
		"""
		admin_settings = {}
		qdata = settingsclass(initializer={'isdefault': True, 'name': inst_alias})
		results = qdata.query()
		if results:
			admin_settings = results[0]
			for s in results:
				# use settings from the one before the session in question
				if s.timestamp < self.session.timestamp:
					return [s,]
		return admin_settings

	def getDBSessionSettings(self):
		"""
		Return Session Settings values.
		"""
		if not hasattr(self, 'settingsclass'):
			return

		inst_alias = self.name
		# load the requested row by session
		qdata = self.settingsclass(initializer={'session': self.session,
																						'name': inst_alias})
		settings_list = qdata.query(results=1)
		# if that failed, try to load user/admin settings from DB
		if not settings_list:
			return self.initializeSettings(self.session['user'])

		settings = settings_list[0]
		# get query result into usable form
		self.settings = settings.toDict(dereference=True)
		del self.settings['session']
		del self.settings['name']

		# check if None in any fields
		for key,value in self.settings.items():
			if value is None:
				if key in self.defaultsettings:
					self.settings[key] = copy.deepcopy(self.defaultsettings[key])

	def displaySettings(self):
		keys = self.settings.keys()
		keys.sort()
		for k in keys:
			print("%s\t%s" % (k,self.settings[k]))

if __name__=='__main__':
	import sys
	if len(sys.argv) != 4:
		print('Usage: python show_settings.py session_name settings_class_name node_name')
	session_name = sys.argv[1]
	class_name = sys.argv[2]
	alias = sys.argv[3]
	app =  SettingsNode(session_name, class_name, alias)
	app.displaySettings()
