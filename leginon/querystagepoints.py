#!/usr/bin/env python

from leginon import leginondata
import sys

label = sys.argv[1]
db = leginondata.db

sm = leginondata.StageMeasurementData(label=label, axis='x')
points = db.query(sm)
for point in points:
	print '%(label)s	%(magnification)s	%(axis)s	%(x)s	%(y)s	%(delta)s	%(imagex)s	%(imagey)s' % point
