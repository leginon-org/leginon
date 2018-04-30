#!/usr/bin/env python
import sys
try:
	import numpy
except:
	pass

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

class TestInstrument(object):
	def __init__(self, instrument_classes):
		self.inst = self.chooseInstrument(instrument_classes)
		self.ok_methods = {}
		self.not_ok_methods = {}

	def chooseInstrument(self, instrument_classes):
		for instr_class in instrument_classes:
			class_name = instr_class.__name__
			answer = raw_input('Is %s the class to test ? (Y/N)' % class_name)
			if answer.upper() == 'Y':
				f = instr_class()
				return f
		print 'Nothing is chosen'
		self.waitToClose()

	def logNotOK(self, method_name, e):
			message = '%s: %s' % (e.__class__.__name__, e)
			self.not_ok_methods[method_name] = message
			print colorString(' [NOT OK]','red')
			print '    '+message

	def logOK(self, method_name, result):
			if isinstance(result,type(numpy.ones((1,1)))):
				message = 'got array with shape %s' % (result.shape,)
			elif result is not None:
				message = 'got result: %s' % (result,)
			else:
				message = ''
			self.ok_methods[method_name]= message
			print colorString(' [OK]')
			if message:
				print '    ',message

	def test(self, method_name, *args):
		try:
			func = getattr(self.inst,method_name)
			print 'Running method %s with args %s' % (method_name, args),
			result = func(*args)
			self.logOK(method_name, result)
		except Exception, e:
			self.logNotOK(method_name, e)

	def waitToClose(self):
		print '----Finished-----'
		raw_input('Hit any key to end')
		sys.exit()

if __name__=='__main__':
	from pyscope import simtem

	app = TestInstrument([simtem.SimTEM,])
	app.test('getStagePosition')
	app.test('getApertureSelection', 'aobjective')
	app.waitToClose()
