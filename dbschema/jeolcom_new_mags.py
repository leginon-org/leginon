#!/usr/bin/env python
'''
The module find the list of magnifications for jeolcom class
and force insert to database.  Useful when new magnification
is added or replaced by service engineers.
'''

import sys

from leginon import leginondata
from pyscope import jeolcom

ok_msg = 'Success'

def msgExit(msg=''):
	if msg:
		print msg
	format_input('Hit Enter to exit')
	if msg != ok_msg:
		sys.exit(1)

def format_input(msg=''):
	print ''
	return raw_input(msg)

jeolcom_classname = format_input('Enter scope classname in instruments.cfg (Case sensitive): ')
scopes = leginondata.InstrumentData(name=jeolcom_classname).query()

if len(scopes) > 1:
	print ''
	print "There are more than one instrument using jeolcom class"
	jeolcom_hostname = format_input('Enter the hostname where the magnifications need registering: ')
	scopes = leginondata.InstrumentData(name=jeolcom_classname,hostname=jeolcom_hostname).query()
if not scopes:
	msg = "Error: Can not find a scope matching the description"
	msgExit(msg)

# There should be only one scope now.
j = jeolcom.Jeol()
j.findMagnifications()
new_mags = j.getMagnifications()

answer = 'n'
while answer.lower() != 'y':
	print new_mags
	answer = format_input('O.K. to insert ? (Y/N) ')

	if answer.lower()[0] != 'y':
		mags_str = format_input('Enter all magnifications, separated by ",":')
		new_mags = mags_str.split(',')
		new_mags = map((lambda x: int(x)),new_mags)

q = leginondata.MagnificationsData(instrument=scopes[0],magnifications=new_mags)
q.insert(force=True)
msgExit(ok_msg)

