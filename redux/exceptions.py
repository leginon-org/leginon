'''
Exceptions generated within redux.
'''

class ArgumentError(Exception):
	pass

class PipeInitError(Exception):
	def __init_(self, message, pipe):
		Exception.__init__(self, message)
		self.pipe = pipe
		self.message = message

	def detail(self):
		detail = 'Pipe init error:\n  Pipe class: %s\n  Message: %s' % (self.pipe_class, self.message)
		return detail

class PipeMissingArgs(PipeInitError):
	'''pipe init failed because some args given, but not all required args given'''
	def __init__(self, message, pipe, missing_args):
		PipeInitError.__init__(self, message, pipe)
		self.missing_args = missing_args

	def detail(self):
		detail = PipeInitError.detail(self)
		detail = detail + '\n  Missing args: %s' % (self.missing_args,)
		return detail

class PipeArgsValueError(PipeInitError):
	'''pipe init failed because some args have bad values'''
	def __init__(self, message, pipe, arg_name):
		PipeInitError.__init__(self, message, pipe)
		self.arg_name = arg_name
		self.arg_value = pipe.kwargs[arg_name]

	def detail(self):
		detail = PipeInitError.detail(self)
		detail = detail + '\n  Argument Name:  %s\n  Argument Value:  %s' % (self.arg_name, self.arg_value)
		return detail

class PipeDisabled(PipeInitError):
	pass

class PipeSwitchedOff(PipeDisabled):
	'''pipe disabled because of switch argument'''
	pass

class PipeNoArgs(PipeDisabled):
	'''pipe disabled because no args were present'''
	pass

