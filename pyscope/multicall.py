#!/usr/bin/env python
'''
Mix this class in with yours to give the ability to make multiple calls
with one function call.  Optionally, you can define the methods
initMultiCall and finalizeMultiCall to be called before and after the
sequence of individual calls.

For example:

class MyClass(MultiCallHandler):
	def initMultiCall(self):
		self.cache = {}

	def finalizeMultiCall(self):
		self.doFinalWhatever()

mything = MyClass()

calls = [
	{'method': method, 'args': args, 'kwargs': kwargs},
	{'method': method, 'args': args, 'kwargs': kwargs},
	...
]

values = mything.multicall(calls)


'''

class MultiCallHandler(object):
	def __init__(self):
		self.isMultiCall = False

	def initMultiCall(self):
		pass

	def finalizeMultiCall(self, values):
		return values

	def multicall(self, calls):
		## setup for multiple calls
		self.isMultiCall = True
		self.initMultiCall()

		## make multiple calls
		values = []
		for call in calls:
			method = call['method']
			if 'args' in call:
				args = call['args']
			else:
				args = ()
			if 'kwargs' in call:
				kwargs = call['kwargs']
			else:
				kwargs = {}
			try:
				value = method(*args, **kwargs)
			except Exception, e:
				## if exception, return the exception object
				value = e
			values.append(value)

		## finalize multiple calls
		values = self.finalizeMultiCall(values)
		self.isMultiCall = False
		return values
