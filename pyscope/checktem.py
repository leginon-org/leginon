#!/usr/bin/env python
SIMULATION = False

if not SIMULATION:
	from pyscope import fei
	answer = raw_input('Is the scope in EF-TEM mode ? (Y/N)')
	if answer == 'Y':
		f = fei.EFKrios()
	else:
		f = fei.Krios()
else:
	from pyscope import simtem
	f = simtem.SimTEM()

def colorString(text, fg=None, bg=None):
	import os
	import types
	colors = {
		"red"   :"0;31",
	}
	if fg is None:
		return text
	if type(fg) in (types.TupleType, types.ListType):
		fg, bg = fg
	if not fg:
		return text
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	xterm = 0
	if os.environ.get("TERM") is not None and os.environ.get("TERM") == "xterm": 
		xterm = True
	else:
		xterm = False
	b = ''
	# In xterm, brown comes out as yellow..
	if xterm and fg == "yellow": 
		fg = "brown"
	f = opencol + colors[fg] + closecol
	if bg:
		if bg == "yellow" and xterm: 
			bg = "brown"
		try: 
			b = colors[bg].replace('3', '4', 1)
			b = opencol + b + closecol
		except KeyError: 
			pass
	return "%s%s%s%s" % (b, f, text, clear)

ok_methods = {}
not_ok_methods = {}
def testFunction(tem_inst, method_name, has_result,*args):
	func = getattr(tem_inst,method_name)
	print 'Running method %s with args %s' % (method_name, args),
	if args:
		argv = args[0]
		try:
			result = func(argv)
			if has_result:
				message = 'got result: %s' % (result)
			else:
				message = ''
			ok_methods[method_name]= message
			print colorString(' [OK]')
		except Exception, e:
			message = '%s: %s' % (e.__class__.__name__, e)
			not_ok_methods[method_name] = message
			print colorString(' [NOT OK]','red')
			print '    '+message
	else:
		try:
			result = func()
			if has_result:
				message = 'got result: %s' % (result)
			else:
				message = ''
			ok_methods[method_name]= message
			print colorString(' [OK]')
		except Exception, e:
			message = '%s: %s' % (e.__class__.__name__, e)
			not_ok_methods[method_name] = message
			print colorString(' [NOT OK]','red')
			print '    '+message

testFunction(f,'getStagePosition', False)
testFunction(f,'getApertureSelection', True, 'aobjective')
print '----Finished-----'
raw_input('Hit any key to end')

