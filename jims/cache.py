
import os
import pyami.resultcache
import pyami.fileutil

class Cache(pyami.resultcache.ResultCache):
	def put(self, pipeline, result):
		pyami.resultcache.ResultCache.put(self, pipeline, result)
		if pipeline[-1].cache_file:
			self.file_put(pipeline, result)

	def get(self, pipeline):
		## try memory cache
		result = pyami.resultcache.ResultCache.get(self, pipeline)

		if result is None:
			## try disk cache
			result = self.file_get(pipeline)
			if result is not None:
				pyami.resultcache.ResultCache.put(self, pipeline, result)
		else:
			## found in memory cache, but need to touch or rewrite disk cache
			if not self.file_touch(pipeline):
				self.file_put(pipeline, result)

		return result

	def file_put(self, pipeline, result, permanent=False):
		final_pipe = pipeline[-1]
		# some pipes specify not to be cached to disk
		if not final_pipe.cache_file:
			return
		resultfilename = self.result_filename(pipeline)
		path = os.path.dirname(resultfilename)
		pyami.fileutil.mkdirs(path)
		f = open(resultfilename, 'w')
		final_pipe.put_result(f, result)
		f.close()

	def file_get(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		try:
			f = open(resultfilename, 'r')
		except:
			return None
		result = pipeline[-1].get_result(f)
		f.close()
		return result

	def file_touch(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		exists = os.path.exists(resultfilename)
		if exists:
			os.utime(resultfilename, None)
		return exists

	def file_exists(self, pipeline):
		resultfilename = self.result_filename(pipeline)
		return os.path.exists(resultfilename)

	def result_filename(self, pipeline):
		cache_path = self.cache_path()
		pipeline_path = self.pipeline_path(pipeline)
		resultname = pipeline[-1].resultname()
		path = os.path.join(cache_path, pipeline_path, resultname)
		return path

	def cache_path(self):
		return '/tmp/jims'

	def pipeline_path(self, pipeline):
		parts = [pipe.dirname() for pipe in pipeline]
		parts = filter(None, parts)
		path = os.path.join(*parts)
		return path
