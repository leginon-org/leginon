#!/usr/bin/env python
from appionlib import apDisplay
try:
	import deProcessFrames
except:
	apDisplay.printError('deProcessFrames.py not in PYTHONPATH')

deProcessFrames.main()
