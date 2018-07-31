#!/usr/bin/env python
import sys

from pyscope import config
classes = config.getCameraClasses()

from pyscope import checkmodule
app = checkmodule.TestInstrument(classes)
app.test('getDimension')
app.test('getImage')
print 'Testing frame saving'
app.test('setSaveRawFrames',True)
app.test('getImage')
app.waitToClose()
