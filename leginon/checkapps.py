#!/usr/bin/env python

import dbdatakeeper
import data
import sys
import newdict
import getpass
import sets

#days = int(sys.argv[1])

user = raw_input('User: ')
passwd = getpass.getpass()
days = int(raw_input('Days: '))
db = dbdatakeeper.DBDataKeeper(user=user,passwd=passwd)

## make set of all application names
appquery = data.ApplicationData()
apps = db.query(appquery)
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
launchquery = data.LaunchedApplicationData()
timelimit = '-%d 0:0:0' % (days,)
launchedapps = db.query(launchquery, timelimit=timelimit)
recentapps = []
for launchedapp in launchedapps:
	appname = launchedapp['application']['name']
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
