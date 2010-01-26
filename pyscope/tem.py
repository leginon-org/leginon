# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import time
import threading

class TEM(object):
	name = None
	def __init__(self):
		pass

	def getSystemTime(self):
		return time.time()
