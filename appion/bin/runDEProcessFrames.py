#!/usr/bin/env python
from appionlib import apDisplay
try:
	import deProcessFrames
except Exception as e:
	apDisplay.printError(str(e))

deProcessFrames.main()
