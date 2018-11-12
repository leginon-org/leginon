#!/usr/bin/env python

import sys
import MySQLdb
import getpass

print '''
LEGINON 1.3 DATABASE UPDATE SCRIPT

This script will update several tables in the Leginon database.
Older versions of Leginon will no longer work after this update.

*****************************************************************
* YOU SHOULD CREATE A BACKUP OF YOUR DATABASE BEFORE CONTINUING *
*****************************************************************
'''

## ask if a backup was made
text = raw_input('If you have created a backup, please enter YES at the prompt: ')
if text != 'YES':
	print 'aborted'
	sys.exit()

print ''
print 'Enter configuration information for the database you wish to update.'
print 'You must have alter, insert, and create privileges to update the tables.'
print ''
dbhost = raw_input('Database Host: ')
dbname = raw_input('Database Name: ')
dbuser = raw_input('User: ')
dbpass = getpass.getpass('Password: ')
print ''
print ''

db = MySQLdb.connect(host=dbhost, db=dbname, user=dbuser, passwd=dbpass)
db.autocommit(True)

## get list of tables
cur = db.cursor()
cur.execute('show tables')
tableresults = cur.fetchall()
tables = [row[0] for row in tableresults]
if not tables:
	print 'No tables in this database, so no update is necessary'
	sys.exit()

def get_fields_info(db, table):
	cur = db.cursor()
	cur.execute('DESCRIBE `%s`' % (table,))
	fields = cur.fetchall()
	return fields

def get_field_names(db, table):
	cur = db.cursor()
	cur.execute('DESCRIBE `%s`' % (table,))
	fields = cur.fetchall()
	return [field[0] for field in fields]

def field_is_null(db, table, field):
	'''This function checks if NULL is enabled for the given table and field'''
	try:
		results = get_fields_info(db, table)
	except:
		return False
	for res in results:
		if field == res[0]:
			if res[2] == 'YES':
				return True
	return False

# spot check if NULL has been enabled
# Make sure at least one exists and that those that exist pass the test
checkthese = (
	('UserData','name'),
	('ApplicationData', 'name'),
	('InstrumentData', 'hostname')
)
havenull = 0
exist = 0
for table,field in checkthese:
	if table in tables:
		exist += 1
		if field_is_null(db, table, field):
			havenull += 1
if exist == 0:
	## could not determine from our spot check, so need to assume it is not done
	nullenabled = False
else:
	if havenull == exist:
		## all passed the test, null is enabled
		nullenabled = True
	else:
		## one or more did not pass the test
		nullenabled = False

## alter the tables to enable the NULL flag on fields
if nullenabled:
	print 'NULL already enabled on tables.  Skipping this modification'
else:
	print 'Enabling NULL on tables...'

	for table in tables:
		print '  %s' % table
		fields = get_fields_info(db, table)
		for field in fields:
			if field[0] in ('DEF_id', 'DEF_timestamp',):
				continue
			cur = db.cursor()
			alter = 'ALTER TABLE `%s` MODIFY `%s` %s NULL' % (table,field[0],field[1])
			cur.execute(alter)
print ''

## update FocusSettingData 
if 'FocusSettingData' in tables:
	# tilt field
	fields = get_field_names(db, 'FocusSettingData')
	if 'tilt' in fields:
		print 'FocusSettingData already contains tilt field.  Skipping this modification'
	else:
		print 'Updating tilt field of FocusSettingData...'
		cur = db.cursor()
		cur.execute('ALTER TABLE `FocusSettingData` CHANGE `beam tilt` `tilt` DOUBLE')
		print '   done.'
	print ''

	# stig defocus min/max updated to be positive
	print 'Updating stig defocus min/max fields of FocusSettingData'
	cur = db.cursor()
	cur.execute("UPDATE `FocusSettingData` SET `stig defocus max`=ABS(`stig defocus max`), `stig defocus min`=ABS(`stig defocus min`) WHERE `stig defocus max` <0 OR `stig defocus min` <0")
	print '   done.'
	print ''

# rename CalibratorSettingsData to PixelSizeCalibratorSettingsData
if 'PixelSizeCalibratorSettingsData' in tables:
	print 'PixelSizeCalibratorSettingsData already exists.  Skipping this modification'
elif 'CalibratorSettingsData' in tables:
	print 'Renaming CalibratorSettingsData...'
	cur = db.cursor()
	cur.execute('ALTER TABLE `CalibratorSettingsData` RENAME `PixelSizeCalibratorSettingsData`')
	print '   done.'
