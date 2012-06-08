#!/usr/bin/env python

import pyscope.registry

# param name, help string
params = [
	('TemperatureStatus', 'Cool Down or Warm Up', str),
	('Temperature', 'Degrees celsius', float),
	('ReadoutDelay', 'Miliseconds, negative means readout before shutter', int),
	('FrameRate', 'Frames Per Second', int),
	('Inserted', 'True or False', eval),
]

de12 = pyscope.registry.getClass('DE12')()

def print_params():
	print ''
	for i,param in enumerate(params):
		name = param[0]
		val = getattr(de12, 'get'+name)()
		print '%d) %s:  %s' % (i, name, val)
	print ''

def update_param(num):
	name, help, validate = params[num]
	value = raw_input('%s (%s): ' % (name, help,))
	value = validate(value)
	try:
		getattr(de12, 'set'+name)(value)
	except:
		getattr(de12, 'set_'+name)(value)

n = len(params)
print_params()
while True:
	num = raw_input('Which value to change? (0-%d):  ' % (n-1,))
	if num:
		num = int(num)
		update_param(num)
	print_params()
