import node

class DataServerNode(node.Node):
	def __init__(self, nodeid, managerloc, dh, dhargs, pushclientclass, pullclientclass):
		node.Node.__init__(self, nodeid, managerloc, dh, dhargs
												pushclientclass, pullclientclass)

