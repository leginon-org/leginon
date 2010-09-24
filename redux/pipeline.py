#!/usr/bin/env python

# standard library
import cStringIO
import sys

# local
import redux.cache
import redux.pipe

cache_size = 400*1024*1024  # 400 MB
results = redux.cache.Cache(cache_size)

def log(msg):
	sys.stderr.write(msg)
	sys.stderr.write('\n')

## you have to create subclass with pipeorder attribute
class Pipeline(object):
	def __init__(self):
		pass

	def getOrder(self):
		return self.pipeorder

	def kwargs_to_pipeline(self, **kwargs):
		pipeline = []
		for pipe_class in self.pipeorder:
			try:
				pipe = pipe_class(**kwargs)
			except redux.pipe.PipeDisabled:
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
			result = results.get(done)
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
			results.put(done, result)

		return result
