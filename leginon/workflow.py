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
		self.dep_values = {}
		self.depresults = {}
		self.params = {}
		self.params_old = {}
		self.result = None
		self.result_callback = result_callback

	def setDependencyStep(self, name, step):
		'''Set another Step as one of my dependencies'''
		self.dependencies[name] = step

	def setDependencyValue(self, name, value):
		self.dep_values[name] = value

	def runDependency(self, depname, memo):
		'''Run one of my dependencies, and store result in self.depresults.
		If result is different than last time, return True, else return False.'''
		dep = self.dependencies[depname]
		if isinstance(dep, Step):
			result = dep.run(memo)
		else:
			## dep is a special dep
			result = self.special_deps[dep]
		if depname in self.depresults and self.depresults[depname] is result:
			# not changed
			return False
		else:
			# changed
			self.depresults[name] = result
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

	def setExternal(self, value):
		self.external = value

	def setResult(self, result):
		'''setResult is used internally after running this step, but may also be called directly as a way to skip the run method'''
		self.result = result

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
				self.setResult(result)
				if self.result_callback is not None:
					self.result_callback(self, self.result)
			else:
				result = self.result
			memo[self] = result

		return result
