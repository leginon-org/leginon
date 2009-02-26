#!/usr/bin/env python

import leginondata

def temp_add_drift(settingsclass):
	typetuple = settingsclass.typemap()
	def typemap(cls):
		return typetuple + (
			('adjust for drift', bool),
		)
	settingsclass.typemap = classmethod(typemap)

def drift2transform(settingsdata):
	print 'CLASS', settingsdata.__class__
	print 'USER', settingsdata['session']['user']
	print 'NAME', settingsdata['name']
	print 'AFD', settingsdata['adjust for drift']
	print 'AFTbefore', settingsdata['adjust for transform']
	aft = settingsdata['adjust for transform']
	if aft is not None:
		return
	afd = settingsdata['adjust for drift']
	newsettings = settingsdata.__class__(initializer=settingsdata)
	if afd:
		newsettings['adjust for transform'] = 'one'
	else:
		newsettings['adjust for transform'] = 'no'
	print 'AFTafter', newsettings['adjust for transform']
	newsettings.insert()

def updateAcquisitionSettings():
	settingsclasses = []
	for value in leginondata.__dict__.values():
		try:
			if issubclass(value, leginondata.AcquisitionSettingsData):
				settingsclasses.append(value)
		except:
			pass
	
	print 'Settings Classes:'
	for s in settingsclasses:
		print '	%s' % (s,)

	qusers = leginondata.UserData()
	users = qusers.query()
	for user in users:
		print 'USER', user['name']
		qsession = leginondata.SessionData(user=user)
		for cls in settingsclasses:
			print '=========================='
			print 'CLS', cls
			temp_add_drift(cls)
			qset = cls(session=qsession)
			settings = qset.query()
			recent = {}
			for s in settings:
				if s['name'] not in recent:
					recent[s['name']] = s
					drift2transform(s)

if __name__ == '__main__':
	updateAcquisitionSettings()
