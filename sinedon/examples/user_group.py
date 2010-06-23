'''
This is a simple example showing some subclasses of sinedon.Data.  Each
will correspond to a table in a database.  The fields (columns) of the
table are defined by the typemap class attribute.  typemap must be a tuple
which extends the typemap of the base class.  In this example, an instance
of TData has a field that references an instance of AsdfData.  This
reference is between tables in the same database.  For an example of
referencing between two different databases, see mydata2.py.
'''


"""
Setup of the database
"""
import sinedon

class User(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
		('user name', str),
		('group', Group),
	)
	typemap = classmethod(typemap)

class Group(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
		('group name', str),
	)
	typemap = classmethod(typemap)

"""
Usage of the database
"""
if __name__ == "__main__":
	""" case 1: new instance exists """
	groupq = Group()
	groupq['group name'] = "ami"
	groupq.insert()

	userq = User()
	userq['user name'] = "Arne"
	userq['group'] = groupq
	userq.insert()

	""" case 2: group exists """
	groupq = Group()
	groupq['group name'] = "ami"
	groupdatas = groupq.query(results=1)
	if not groupdatas:
		apDisplay.printError("group not found")
	if len(groupdatas) > 1:
		print "too many ami groups"
	groupdata = groupdatas[0]











