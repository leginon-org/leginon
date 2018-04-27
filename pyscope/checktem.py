#!/usr/bin/env python
import sys

from pyscope import config
classes = config.getTEMClasses()

from pyscope import checkmodule
app = checkmodule.TestInstrument(classes)
app.test('getStagePosition')
app.test('getApertureSelection', 'objective')
app.waitToClose()
