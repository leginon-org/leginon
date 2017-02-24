#!/usr/bin/env python

import leginon.leginondata
import sys
import getpass
import sets

days = int(raw_input('Days: '))

## make set of all application names
appquery = leginon.leginondata.ApplicationData()
apps = appquery.query()
print 'APPS', len(apps)
allapps = sets.Set()
allappsdict = {}
for app in apps:
	appname = app['name']
	allapps.add(appname)
	if appname in allappsdict:
		allappsdict[appname].append(app)
	else:
		allappsdict[appname] = [app]
print 'ALL', len(allapps)

## make set off apps launched in last n days
launchquery = leginon.leginondata.LaunchedApplicationData()
timelimit = '-%d 0:0:0' % (days,)
launchedapps = launchquery.query(timelimit=timelimit)
recentapps = []
for launchedapp in launchedapps:
	try:
		appname = launchedapp['application']['name']
	except:
		continue
	if appname not in recentapps:
		recentapps.append(appname)
print 'RECENT', len(recentapps)

## make set off apps not launched in last n days
notrecentapps = allapps - sets.Set(recentapps)
print 'NOTRECENT', len(notrecentapps)

print 'Most Recently Launched (last %d days = %d apps):' % (days,len(recentapps))
for recent in recentapps:
	print '\t%s' % (recent,)

print 'Others Sorted Alphabetically'
others = list(notrecentapps)
others.sort()
for other in others:
	print '\t%s' % (other,)
