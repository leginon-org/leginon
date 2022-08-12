#!/usr/bin/env python
from leginon import projectdata
from pyami import mysocket
print(('running autohost creation on %s' % mysocket.gethostname()))
q = projectdata.autohosts()
for tmap in q.typemap():
	key = tmap[0]
	ttype = tmap[1]
	while True:
		answer = input('%s (as %s) = ' % (tmap[0], tmap[1].__name__))
		if ttype == type(''):
			q[key] = answer
			break
		try:
			value = eval(answer)
		except TypeError:
			print('Type can not be evaluated. Please try again.')
			continue
		except SyntaxError:
			print('Invalid entry. Please try again.')
			continue
		if type(value) == ttype:
			q[key] = value
			break
		print(('Type evaluated (%s) not consistent. Please try again.' % type(value)))
# required field: hostname
if not q['hostname']:
	print('Error: "hostname" can not be empty. creation aborted.')
else:
	# Force insert so that query of the most recent can contain reverted values.
	q.insert(force=True)


