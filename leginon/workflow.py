#!/usr/bin/env python
'''
A workflow is composed of several steps that may be interdependent.
A given step cannot be run until its dependency steps have been run.
'''

class Step(object):
	'''
A Step object manages one step of a workflow.
The main interface to run the step is the run() method.  The customizable
portion of this method is to be defined in the _run() method in subclasses.
Calling run() will automatically run any dependency steps.  If no dependency
results or input parameters have changed, the _run() method will not be
called.
	'''
	def __init__(self, name, result_callback=None):
		self.name = name
		## perhaps some of these should be weak dicts...
		self.dependencies = {}
		self.depresults = {}
		self.setParamDefaults()
		self.params_old = dict(self.params)
		self.result = None
		self.result_callback = result_callback

	def setParamDefaults(self):
		items = [(p['name'],p['default']) for p in self.param_def]
		self.params = dict(items)

	def setDependency(self, name, value):
		self.dependencies[name] = value

	def runDependency(self, depname, memo):
		'''Run one of my dependencies, and store result in self.depresults.
		If result is different than last time, return True, else return False.'''
		dep = self.dependencies[depname]
		if isinstance(dep, Step):
			result = dep.run(memo)
		else:
			## dep is an object
			result = dep
		if depname in self.depresults and self.depresults[depname] is result:
			# not changed
			return False
		else:
			# changed
			self.depresults[depname] = result
			return True

	def runDependencies(self, memo):
		'''Run all of my dependencies.  Store the results in self.depresults.  Return only the subset of results that have actually changed since the last run'''
		changed = False
		for name,dep in self.dependencies.items():
			if self.runDependency(name, memo):
				changed = True
		return changed

	def setParam(self, name, value):
		'''set a parameter by name and value'''
		self.params[name] = value

	def checkParams(self):
		'''Check the current set of parameters and return only the subset of them which have changed since the last time they were checked.'''
		changed = False
		for name,value in self.params.items():
			if name in self.params_old and self.params_old[name] == value:
				# not changed
				pass
			else:
				# changed
				changed = True
				self.params_old[name] = value
		return changed

	def run(self, memo=None):
		'''
		Run this step, which may include running dependency steps.

		Each step in the workflow can only be run once, even if there are
		multiple calls to the same step.

		If none of the dependencies and none of the parameters have changed,
		then do not re-run this step, just return the previous result.

		WARNING: currenly not thread safe!
		'''

		# if no memo specified, then this step is the root of the run
		if memo is None:
			memo = {}

		# if this step is in the memo, then a result has already been calculated
		if self in memo:
			result = memo[self]
		else:
			# run dependencies first, check if they are changed
			newresults = self.runDependencies(memo)
			# check for changed parameters since last run
			newparams = self.checkParams()

			# only run this step if dependencies or params changed,
			# else return last result
			if newparams or newresults:
				self.result = self._run()
				if self.result_callback is not None:
					self.result_callback(self, self.result)
				memo[self] = self.result

		return self.result

################### TEST CODE ######################

def test():
	# create classes for two workflow steps
	class ParamPlusParamOrExt(Step):
		def _run(self):
			a = self.params['a']
			switch = self.params['switch']
			if switch == 'param':
				b = self.params['b']
			elif switch == 'ext':
				b = self.depresults['ext']
			else:
				raise ValueError('%s switch param must be "param" or "ext"' % (self.name,))

			return a + b

	class ParamTimesDep(Step):
		def _run(self):
			a = self.params['a']
			b = self.depresults['mydep']
			return a * b

	def debugCallback(step, result):
		print 'Ran step %s, result = %s' % (step.name, result)

	# create instances
	s1 = ParamPlusParamOrExt('S1', result_callback=debugCallback)
	s2 = ParamTimesDep('S2', result_callback=debugCallback)

	# make s1 depend on external object
	s1.setDependency('ext', None)
	# make s2 depend on s1
	s2.setDependency('mydep', s1)

	# configure the steps
	s1.setParam('a', 3)
	s1.setParam('b', 4)
	s1.setParam('switch', 'param')
	s2.setParam('a', 8)

	# run
	s2.run()

	# reconfig s2 and run again
	s2.setParam('a', 9)
	s2.run()

	# reconfig s1 and run again
	s1.setParam('a', 5)
	s2.run()

	# switch to ext
	s1.setParam('switch', 'ext')
	s1.setDependency('ext', 10)
	s2.run()

	# update ext
	s1.setDependency('ext', 11)
	s2.run()

class WorkflowCLI(object):
	'''Simple way to test workflows using command line interface.'''
	def __init__(self, steps):
		'''steps must be OrderedDict object'''
		self.steps = steps

	def configureStep(self, stepname):
		step = self.steps[stepname]
		print 'Configure %s...' % (stepname,)
		for pdef in step.param_def:
			pname = pdef['name']
			ptype = pdef['type']
			if 'choices' in pdef:
				choices = str(pdef['choices'])
			else:
				choices = ''
			entered = raw_input('    %s%s: ' % (pname, choices))
			if not entered:
				continue
			if ptype is bool:
				entered = int(entered)
			pvalue = ptype(entered)
			step.setParam(pname, ptype(entered))

	def mainPrompt(self):
		while True:
			try:
				entered = raw_input('Command (run or config): ')
			except EOFError:
				return None
			if entered not in ('run', 'config'):
				continue
			else:
				return entered

	def stepPrompt(self):
		choices = '[' + ','.join(self.steps.keys()) + ']'
		while True:
			entered = raw_input('  Step %s: ' % (choices,))
			if entered in self.steps.keys() or entered == '':
				return entered

	def loop(self):
		while True:
			entered = self.mainPrompt()
			if entered is None:
				print ''
				break
			if entered == 'run':
				stepname = self.stepPrompt()
				if stepname:
					self.runStep(stepname)
				else:
					continue
			elif entered == 'config':
				stepname = self.stepPrompt()
				if stepname:
					self.configureStep(stepname)
				else:
					continue

	def runStep(self, stepname):
		self.steps[stepname].run()

if __name__ == '__main__':
	test()

