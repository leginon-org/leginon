

class ObjectProxy(object):
	def __init__(self, targetobject)
		if type(targetobject) == int



class ObjectServer(object):
	pass


class VirtualObject(object):
	def __init__(self, objectproxy):
		if type(objectproxy) == int:
			pass
		elif type(objectproxy) == ObjectProxy:
			pass

	def __getattr__(self, name):
		self.o



_id2obj = {}

def myid(obj):
	answer = id(obj)
	_id2obj[answer] = obj
	return answer

def mydi(an_id):
	# will raise KeyError if an_id isn't a tracked id
	return _id2obj[an_id] 
