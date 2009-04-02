# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyScope/tem.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-29 22:33:48 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import time
import threading

class TEM(object):
	name = None
	def __init__(self):
		pass

	def getSystemTime(self):
		return time.time()
