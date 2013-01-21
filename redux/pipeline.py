#!/usr/bin/env python

# standard library
import cStringIO
import sys

# local
import redux.pipe
import redux.pipes
import redux.pipelines
import redux.reduxconfig

CACHE_ON = redux.reduxconfig.config['cache on']

if CACHE_ON:
	import redux.cache
	disk_cache_path = redux.reduxconfig.config['cache path']
	disk_cache_size = redux.reduxconfig.config['cache disk size'] * 1024 * 1024
	mem_cache_size = redux.reduxconfig.config['cache mem size'] * 1024 * 1024
	results = redux.cache.Cache(disk_cache_path, disk_cache_size, size_max=mem_cache_size)

def log(msg):
	sys.stderr.write(msg+'\n')

'''
pipe order specifier:
"r|s|p|c|s|f"
kwargs:
	"r0.asdf=asdf&s1.asdf=asdf"
'''

def pipeline_by_pipes(pipes):
	pl = Pipeline(pipes)
	return pl

def pipes_by_preset(name):
	pipes = redux.pipelines.registered[name]
	return pipes

def pipeline_by_preset(name):
	pipes = pipes_by_preset(name)
	pl = pipeline_by_pipes(pipes)
	return pl

def pipes_by_string(pipestring):
	pipes = pipestring.split(',')
	pipes = [pipe.split(':') for pipe in pipes]
	return pipes

def pipeline_by_string(pipestring):
	pipes = pipes_by_string(pipestring)
	pl = pipeline_by_pipes(pipes)
	return pl

## you have to create subclass with pipeorder attribute
## or instantiate Pipeline class directly, giving it pipeorder arg
class Pipeline(object):
	def __init__(self, pipes):
		# pipeorder currenly list of pipe classes, but likely to change
		# into something more descriptive (names, etc)
		self.pipeorder = []
		for pipe in pipes:
			pname = pipe[0]
			pcls = redux.pipes.registered[pipe[1]]
			self.pipeorder.append((pname,pcls))

	def filter_pipe_kwargs(self, pipename, kwargs):
		result = {}
		pipename_args = {}
		for key,value in kwargs.items():
			parts = key.split('.')
			if len(parts) == 1:
				result[key] = value
			else:
				argpipe = parts[0]
				argname = parts[1]
				if argpipe != pipename:
					continue
				pipename_args[argname] = value
		# specifically named args will override any other
		result.update(pipename_args)
		return result

	def kwargs_to_pipeline(self, **kwargs):
		pipeline = []
		for pipe_name, pipe_class in self.pipeorder:
			pipe_kwargs = self.filter_pipe_kwargs(pipe_name, kwargs)
			try:
				pipe = pipe_class(**pipe_kwargs)
				pipe.name = pipe_name
			except redux.exceptions.PipeDisabled:
				continue
			pipeline.append(pipe)
		return tuple(pipeline)

	def help_string(self):
		'''generate a help string to describe the available pipes'''
		f = cStringIO.StringIO()
		done = {}
		for pipe_name, pipe_class in self.pipeorder:
			if pipe_class in done:
				continue
			f.write(pipe_class.help_string())
			done[pipe_class] = None

		result = f.getvalue()
		f.close()
		return result

	def process(self, **kwargs):
		if 'help' in kwargs and kwargs['help']:
			return help_string()

		# use cache if config file enabled it, unless request
		# disables it
		cache_on = CACHE_ON
		if 'cache' in kwargs:
			if not redux.pipe.bool_converter(kwargs['cache']):
				cache_on = False

		pipeline = self.kwargs_to_pipeline(**kwargs)

		### find all or part of the pipeline result in the cache
		n = len(pipeline)
		for i in range(n):
			done = pipeline[:n-i]
			if cache_on:
				result = results.get(done)
			else:
				result = None
			if result is not None:
				remain = pipeline[n-i:]
				break

		if result is None:
			done = ()
			remain = pipeline
			if 'initial_input' in kwargs:
				result = kwargs['initial_input']

		### finish the remainder of the pipeline
		for pipe in remain:
			log('Running %s' % (pipe,))
			result = pipe(result)
			done = done + (pipe,)
			if cache_on:
				results.put(done, result)

		return result
