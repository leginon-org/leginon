#!/usr/bin/env python

import data
import dbdatakeeper

initializer = {'name': 'mysession'}
session = data.SessionData(initializer=initializer)
d = dbdatakeeper.DBDataKeeper(('fake',), session)


imagetemp = data.NormImageData()
imagetemp['session'] = data.SessionData()
imagetemp['session']['user'] = data.UserData()
imagetemp['session']['user']['group'] = data.GroupData()
imagetemp['session']['instrument'] = data.InstrumentData()


result = d.query(imagetemp)
print 'RESULT'
print result
