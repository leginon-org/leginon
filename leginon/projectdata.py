from sinedon import Data

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
