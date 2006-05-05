#!/usr/bin/env python

import data
import dbdatakeeper
import sys

label = sys.argv[1]
db = dbdatakeeper.DBDataKeeper()

sm = data.StageMeasurementData(label=label, axis='x')

points = db.query(sm)

for point in points:
	print '%(label)s	%(magnification)s	%(axis)s	%(x)s	%(y)s	%(delta)s	%(imagex)s	%(imagey)s' % point
