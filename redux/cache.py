#!/usr/bin/env python

import os
import sys
import pyami.resultcache
import pyami.fileutil
import cachefs
import threading

debug = True
def debug(s):
	if debug:
		sys.stderr.write(s)
		sys.stderr.write('\n')


class Cache(pyami.resultcache.ResultCache):
	def __init__(self, disk_cache_path, disk_cache_size, *args, **kwargs):
		self.diskcache = cachefs.CacheFS(disk_cache_path, disk_cache_size)
		pyami.resultcache.ResultCache.__init__(self, *args, **kwargs)
		self.lock = threading.Lock()

	def check_disable(self, pipeline):
		for pipe in pipeline:
			if pipe.disable_cache:
				return True
		return False

	def _put(self, pipeline, result):
		if self.check_disable(pipeline):
			return
		pyami.resultcache.ResultCache.put(self, pipeline, result)
		if pipeline[-1].cache_file:
			self.file_put(pipeline, result)

	def put(self, pipeline, result):
		self.lock.acquire()
		try:
			return self._put(pipeline, result)
		finally:
			self.lock.release()

	def _get(self, pipeline):
		if self.check_disable(pipeline):
			return
		## try memory cache
		result = pyami.resultcache.ResultCache.get(self, pipeline)

		if result is None:
			debug('NOT IN MEMORY: %s' %(pipeline[-1],))
			## try disk cache
			result = self.file_get(pipeline)
			if result is not None:
				debug('IN FILE: %s' %(pipeline[-1],))
				pyami.resultcache.ResultCache.put(self, pipeline, result)
		else:
			debug('IN MEMORY: %s' % (pipeline[-1],))
			## found in memory cache, but need to touch or rewrite disk cache
			if not self.file_touch(pipeline):
				debug('NOT IN FILE: %s' % (pipeline[-1],))
				self.file_put(pipeline, result)

		return result

	def get(self, pipeline):
		self.lock.acquire()
		try:
			return self._get(pipeline)
		finally:
			self.lock.release()

	def file_put(self, pipeline, result, permanent=False):
		final_pipe = pipeline[-1]
		# some pipes specify not to be cached to disk
		if not final_pipe.cache_file:
			return
		resultfilename = self.result_filename(pipeline)
		path = os.path.dirname(resultfilename)
		self.diskcache.makedir(path, recursive=True, allow_recreate=True)
		f = self.diskcache.open(resultfilename, 'wb')
		final_pipe.put_result(f, result)
		f.close()

	def file_get(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		try:
			f = self.diskcache.open(resultfilename, 'rb')
		except:
			return None
		result = pipeline[-1].get_result(f)
		f.close()
		return result

	def file_touch(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		exists = self.diskcache.exists(resultfilename)
		if exists:
			self.diskcache.settimes(resultfilename)
		return exists

	def result_filename(self, pipeline):
		pipeline_path = self.pipeline_path(pipeline)
		resultname = pipeline[-1].resultname()
		path = os.path.join(os.sep, pipeline_path, resultname)
		return path

	def pipeline_path(self, pipeline):
		parts = [pipe.dirname() for pipe in pipeline]
		parts = filter(None, parts)
		path = os.path.join(*parts)
		return path


if __name__ == '__main__':
	test_disk_cache_manager()
