# redux.__init__.py

registered = {}
def register(name, pipes):
	global registered
	registered[name] = pipes

import standard
register('standard', standard.pipes)
import allpipes
register('all', allpipes.pipes)
import histdata
register('histdata', histdata.pipes)
import leginon
register('leginon', leginon.pipes)
