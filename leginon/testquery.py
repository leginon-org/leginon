#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import dbdatakeeper

initializer = {'name': 'mysession'}
session = data.SessionData(initializer=initializer)
d = dbdatakeeper.DBDataKeeper(('fake',), session)


# Create data to insert #
# myinst = data.InstrumentData()
# myinst['name'] = "tecnai"
# usr = data.UserData()
# usr['name']="me"
# grp = data.GroupData()
# grp['name']="my group"
# 
# imagetempinsert = data.NormImageData()
# imagetempinsert['filename'] = "myfile.data"
# imagetempinsert['session'] = session
# imagetempinsert['session']['user'] = usr
# imagetempinsert['session']['user']['group'] = grp
# imagetempinsert['session']['instrument'] = myinst
# d.insert(imagetempinsert);


# Create data to query #

preset = data.PresetData()
acqimagetemp = data.AcquisitionImageData()
acqimagetemp['preset']= preset

imagetemp = acqimagetemp
imagetemp['session'] = data.SessionData()
imagetemp['session']['user'] = data.UserData()
imagetemp['session']['user']['group'] = data.GroupData()
imagetemp['session']['instrument'] = data.InstrumentData()


result = d.query(imagetemp)
print 'RESULT'
print result
