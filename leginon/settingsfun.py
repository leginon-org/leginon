#!/usr/bin/env python
"""
Settings functions available outside node class.
"""
from leginon import leginondata

def researchDBSettings(settingsclass, inst_alias, session=None, user=None, extra=None):
	'''
	return settings in the order of session, user, admin
	'''
	# load the session settings in case the same user is operating more than one scope.
	alias_fieldname = 'name'
	if settingsclass.__name__ in ('FocusSequenceData',):
		alias_fieldname = 'node name'
	if extra:
		k,v = extra
	if session:
		qdata = settingsclass(initializer={'session': session})
		qdata[alias_fieldname] = inst_alias
		if extra:
			qdata[k] = v
		settings_list = qdata.query(results=1)
		if settings_list:
			return settings_list
		if not user:
			user = session['user']
	if user:
		# load the most recent requested user settings
		qsession = leginondata.SessionData(initializer={'user': user})
		qdata = settingsclass(initializer={'session': qsession})
		qdata[alias_fieldname] = inst_alias
		if extra:
			qdata[k] = v
		settings_list = qdata.query(results=1)
	else:
		settings_list = []
	# if that failed, try to load default settings from DB
	if not settings_list:
		# try admin settings.
		settings = getDBAdminSettings(settingsclass, inst_alias)
		if settings:
			settings_list = [settings,]
	return settings_list

def getDBAdminSettings(settingsclass, inst_alias, extra=None):
	"""
	Get one administrator settings for the node instance.
	Returns empty dictionary if not found.
	"""
	admin_settings = {}
	alias_fieldname = 'name'
	if settingsclass.__name__ in ('FocusSequenceData',):
		alias_fieldname = 'node name'
	qdata = settingsclass()
	qdata[alias_fieldname] = inst_alias
	qdata['isdefault'] = True
	if extra:
		k,v = extra
		qdata[k] = v
	results = qdata.query(results=1)
	if results:
		admin_settings = results[0]
	return admin_settings

def getSettingsName(classname):
	unusual_settingsnames = {
			'AlignZeroLossPeak': 'AlignZLPSettingsData',
			'MeasureDose':None,
			'IntensityCalibrator':None,
			'AutoNitrogenFiller':'AutoFillerSettingsData',
			'BufferCycler':'BufferCyclerSettingsData',
			'EM':None,
			'FileNames':'ImageProcessorSettingsData',
			'IcethicknessEF': 'ZeroLossIceThicknessSettingsData',
	}

	settingsname = classname+'SettingsData'
	if classname in unusual_settingsnames.keys():
		settingsname = unusual_settingsnames[classname]
	return settingsname

def setSettings(d, settingsclass, session, node_alias, isdefault=False):
	sd = settingsclass.fromDict(d)
	sd['session'] = session
	sd['name'] = node_alias
	if session['user']['username'] == 'administrator':
		sd['isdefault'] = True
	else:
		sd['isdefault'] = isdefault
	sd.insert(force=True)
	return sd
