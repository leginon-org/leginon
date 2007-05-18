'''
This is a simple example showing some subclasses of sinedon.Data.  Each
will correspond to a table in a database.  The fields (columns) of the
table are defined by the typemap class attribute.  typemap must be a tuple
which extends the typemap of the base class.  In this example, an instance
of TData has a field that references an instance of AsdfData.  This
reference is between tables in the same database.  For an example of
referencing between two different databases, see mydata2.py.
'''

import sinedon

class AsdfData(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
		('aaaa', str),
		('bbbb', str),
	)
	typemap = classmethod(typemap)

class TData(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
		('ttt', str),
		('asdf', AsdfData),
	)
	typemap = classmethod(typemap)

class SData(TData):
	def typemap(cls):
		return TData.typemap() + (
		('sss', str),
	)
	typemap = classmethod(typemap)
