#!/usr/bin/env python

# standard library
import cStringIO
import sys

# local
import redux.pipes
import redux.pipelines

CACHE_ON = True

if CACHE_ON:
	import redux.cache
	disk_cache_path = '/tmp/redux'
	disk_cache_size = 200*1024*1024  # 100 MB
	mem_cache_size = 400*1024*1024  # 400 MB
	results = redux.cache.Cache(disk_cache_path, disk_cache_size, size_max=mem_cache_size)

def log(msg):
	sys.stderr.write(msg)
	sys.stderr.write('\n')

'''
pipe order specifier:
"r|s|p|c|s|f"
kwargs:
	"r0.asdf=asdf&s1.asdf=asdf"
'''

def pipeline_by_pipes(pipes):
	pl = Pipeline(pipes)
	return pl

def pipeline_by_preset(name):
	pipes = redux.pipelines.registered[name]
	pl = pipeline_by_pipes(pipes)
	return pl

def pipeline_by_string(pipestring):
	pipes = pipestring.split(',')
	pipes = [pipe.split(':') for pipe in pipes]
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
			pcls = redux.pipes.registered[pipe[1]]
			self.pipeorder.append(pcls)

	def getOrder(self):
		return self.pipeorder

	def kwargs_to_pipeline(self, **kwargs):
		pipeline = []
		for pipe_class in self.pipeorder:
			try:
				pipe = pipe_class(**kwargs)
			except redux.exceptions.PipeDisabled:
				continue
			pipeline.append(pipe)
		return tuple(pipeline)

	def help_string(self):
		'''generate a help string to describe the available pipes'''
		f = cStringIO.StringIO()
		for pipe_class in self.pipeorder:
			f.write(pipe_class.help_string())
		result = f.getvalue()
		f.close()
		return result

	def process(self, **kwargs):
		if 'help' in kwargs and kwargs['help']:
			return help_string()

		pipeline = self.kwargs_to_pipeline(**kwargs)

		### find all or part of the pipeline result in the cache
		n = len(pipeline)
		for i in range(n):
			done = pipeline[:n-i]
			if CACHE_ON:
				result = results.get(done)
			else:
				result = None
			if result is not None:
				remain = pipeline[n-i:]
				break

		if result is None:
			done = ()
			remain = pipeline

		### finish the remainder of the pipeline
		for pipe in remain:
			log('Running %s' % (pipe,))
			result = pipe(result)
			done = done + (pipe,)
			if CACHE_ON:
				results.put(done, result)

		return result
