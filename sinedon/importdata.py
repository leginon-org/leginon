
import sinedon.data

class ImportDBConfigData(sinedon.data.Data):
	def typemap(cls):
		return sinedon.data.Data.typemap() + (
			('host', str),
			('db', str),
		)
	typemap = classmethod(typemap)

class ImportMappingData(sinedon.data.Data):
	def typemap(cls):
		return sinedon.data.Data.typemap() + (
			('source_config', ImportDBConfigData),
			('destination_config', ImportDBConfigData),
			('class_name', str),
			('old_dbid', int),
			('new_dbid', int),
		)
	typemap = classmethod(typemap)

