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
			('gridboxes', int),
		)
	typemap = classmethod(typemap)

class projects(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('short_description', str),
			('long_description', str),
			('category', str),
			('funding', str),
			('leginondb', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class projectexperiments(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project', projects),
			('session', leginon.leginondata.SessionData),
		)
	typemap = classmethod(typemap)

class processingdb(Data):
	def typemap(cls):
		return Data.typemap() + (
			('appiondb', str),
			('project', projects),
		)
	typemap = classmethod(typemap)

class projectowners(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project', projects),
			('user', leginon.leginondata.UserData),
		)
	typemap = classmethod(typemap)

class userdetails(Data):
	def typemap(cls):
		return Data.typemap() + (
			('user', leginon.leginondata.UserData),
			('title', str),
			('institution', str),
			('dept', str),
			('address', str),
			('city', str),
			('statecountry', str),
			('zip', str),
			('phone', str),
			('fax', str),
			('url', str),
		)
	typemap = classmethod(typemap)

class shareexperiments(Data):
	def typemap(cls):
		return Data.typemap() + (
			('user', leginon.leginondata.UserData),
			('experiment', leginon.leginondata.SessionData),
		)
	typemap = classmethod(typemap)

class schemaupdates(Data):
	def typemap(cls):
		return Data.typemap() + (
			('schematag', str),
			('schemaid', int),
			('schemacommitid', str),
			('branch', str),
			('commitcount', int),
			('gitversion', str),
			('recentcommitid', str),
			('modifyappiondb', bool),
			('modifyleginondb', bool),
			('modifyprojectdb', bool),
		)
	typemap = classmethod(typemap)

class autohosts(Data):
	def typemap(cls):
		return Data.typemap() + (
		('hostname', str),
		('appion_wrapper', str),
		('ddalign_gpus', list), # available gpuids for motion correction
		('loop_max', int),# maximal parallel runs for appionLoop
		)
	typemap = classmethod(typemap)
