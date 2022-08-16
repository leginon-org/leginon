#!/usr/bin/env python
'''
Display settings used in the last settings of a node from the session.
'''
import copy
from leginon import leginondata
from leginon import settingsfun
class SettingsNode(object):
	def __init__(self, session_name,node_class_name,inst_alias):
		self.session = leginondata.SessionData(name=session_name).query(results=1)[0]
		self.name = inst_alias
		settings_class_name = settingsfun.getSettingsName(node_class_name)
		self.settingsclass = getattr(leginondata, settings_class_name)
		self.getDBSessionSettings()

	def getDBSessionSettings(self):
		"""
		Return Session Settings values.
		"""
		if not hasattr(self, 'settingsclass'):
			return

		inst_alias = self.name
		# load the requested row by session
		settings_list = settingsfun.researchDBSettings(self.settingsclass, inst_alias, self.session)

		if len(settings_list) == 0:
			raise ValueError('Error: %s:%s settings not found' % (self.settingsclass.__name__, inst_alias))
		settings = settings_list[0]
		# get query result into usable form
		self.settings = settings.toDict(dereference=True)
		del self.settings['session']
		del self.settings['name']

	def displaySettings(self):
		keys = self.settings.keys()
		keys.sort()
		for k in keys:
			print("%s\t%s" % (k,self.settings[k]))

if __name__=='__main__':
	import sys
	if len(sys.argv) != 4:
		print('Usage: python show_settings.py session_name node_class_name node_name')
	session_name = sys.argv[1]
	class_name = sys.argv[2]
	alias = sys.argv[3]
	try:
		app =  SettingsNode(session_name, class_name, alias)
		app.displaySettings()
	except ValueError as e:
		print(e)
	except Exception:
		raise
