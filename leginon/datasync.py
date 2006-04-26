#!/usr/bin/env python
import data
import dbdatakeeper
db = dbdatakeeper.DBDataKeeper()

dataclasses = {}

## check for Data classes
for key,value in data.__dict__.items():
	try:
		if issubclass(value, data.Data):
			dataclasses[key] = value
	except:
		pass

## check if Data class has a table in DB
tables = []
notables = []
for key,value in dataclasses.items():
	instance = value()
	results = db.query(instance, results=1, readimages=False)
	if results:
		print 'TABLE:', key
		tables.append(key)
	else:
		print 'NO TABLE:', key
		notables.append(key)
		
