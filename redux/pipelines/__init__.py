# redux.__init__.py

registered = {}
def register(name, pipes):
	global registered
	registered[name] = pipes

from . import standard
register('standard', standard.pipes)
from . import allpipes
register('all', allpipes.pipes)
from . import histdata
register('histdata', histdata.pipes)
from . import leginon
register('leginon', leginon.pipes)
