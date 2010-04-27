from sinedon import Data
import leginon.leginondata

class privileges(Data):
	def typemap(cls):
		return Data.typemap() + (
			('description', str),
			('groups', int),
			('users', int),
			('projects', int),
			('projectowners', int),
			('shareexperiments', int),
			('data', int),
		)
	typemap = classmethod(typemap)

"""
class projects(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('short_description', str),
			('long_description', str),
			('category', str),
			('funding', str),
			('db', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class projectexperiments(Data):
	def typemap(cls):
		return Data.typemap() + (
			('projectId', projects),
			('sessionId', leginon.leginondata.SessionData),
		)
	typemap = classmethod(typemap)
"""

