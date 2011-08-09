#!/usr/bin/env python

from leginon import leginondata
import sys
from sinedon import newdict

host = sys.argv[1]
i = leginondata.InstrumentData(hostname=host)
s = leginondata.StageModelCalibrationData(tem=i)
models = s.query()

labels = newdict.OrderedDict()
for model in models:
	label = model['label']
	labels[label] = None
for label in labels.keys():
	print label
