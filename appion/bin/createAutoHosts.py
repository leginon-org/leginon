#!/usr/bin/env python
from leginon import projectdata

q = projectdata.autohosts()
for tmap in q.typemap():
	key = tmap[0]
	ttype = tmap[1]
	while True:
		answer = raw_input('%s (as %s) = ' % (tmap[0], tmap[1].__name__))
		if ttype == type(''):
			q[key] = answer
			break
		try:
			value = eval(answer)
		except TypeError:
			print('Type can not be evaluated. Please try again.')
			continue
		if type(value) == ttype:
			q[key] = value
			break
		print('Type evaluated (%s) not consistent. Please try again.' % type(value))
q.insert()


