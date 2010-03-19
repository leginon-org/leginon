#!/usr/bin/env python

import sys

if len(sys.argv) != 2:
	print '%s %s' % (sys.argv[0], 'session_name')
	sys.exit(1)

import leginondata
db = leginondata.db

# look up session with name given by user
session_name = sys.argv[1]
sessiondata = leginondata.SessionData(name=session_name)
sessions = db.query(sessiondata)
if not sessions:
	print 'No session named %s' % (session_name,)
	print 'asdf'
	sys.exit(0)
sessiondata = sessions[0]

# prompt user to confirm session before modifying database
prompt = """Found the following session:
	Name:  %s
	User:  %s %s
	Comment:  %s
Type "ok" if this is the correct session: """ % (sessiondata['name'], sessiondata['user']['firstname'], sessiondata['user']['lastname'], sessiondata['comment'])
response = raw_input(prompt)
if response != 'ok':
	print 'no change to database'
	sys.exit(1)

# find targets in this session
targetdata = leginondata.AcquisitionImageTargetData(session=sessiondata)
targets = db.query(targetdata)

print 'Found %d target records.  Searching for targets not done...' % (len(targets),)

# for each target, insert new target with status = 'done'
targetdict = {}
targetdatadict = {}
for target in targets:
	imref = target.special_getitem('image', dereference=False)
	if imref is None:
		filename = 'None'
	else:
		im = db.direct_query(imref.dataclass, imref.dbid, readimages=False)
		filename = im['filename']
	imageid = filename
	number = target['number']
	status = target['status']
	targetdatadict[imageid,number] = target
	if imageid not in targetdict:
		targetdict[imageid] = {}
	if number not in targetdict[imageid]:
		targetdict[imageid][number] = []
	if status not in targetdict[imageid][number]:
		targetdict[imageid][number].append(status)

# create a dict of only the not done targets
notdone = {}
notdonedata = {}
notdonecount = 0
for imageid in targetdict:
	for number in targetdict[imageid]:
		if 'done' not in targetdict[imageid][number] and 'aborted' not in targetdict[imageid][number]:
			notdonedata[imageid,number] = targetdatadict[imageid,number]
			if imageid not in notdone:
				notdone[imageid] = {}
			notdone[imageid][number] = targetdict[imageid][number]
			notdonecount += 1
print ''
if notdonecount:
	print 'The following %d targets are not done:' % (notdonecount,)
else:
	print 'All targets are already marked done.'
	sys.exit(0)

for imageid,numberdict in notdone.items():
	print imageid
	numbers = numberdict.keys()
	numbers.sort()
	for number in numbers:
		print '   %03d: %s' % (number, numberdict[number])

print ''
response = raw_input('Type "done" to mark them all done: ')
if response != 'done':
	print 'no change to database'
	sys.exit(1)

for target in notdonedata.values():
	newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
	newtarget['status'] = 'done'
	db.insert(newtarget)

print 'marked all as done'
