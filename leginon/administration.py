import node
import data
import uidata

class Administration(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.groupdatadict = {}
		self.updateGroupDataDict()
		self.start()

	def updateGroupDataDict(self):
		groupdata = self.research(datainstance=data.GroupData())
		for i in groupdata:
			if 'name' in i and i['name'] is not None:
				self.groupdatadict[i['name']] = i
		self.selectgroup.set(self.groupdatadict.keys(), 0)

	def addGroup(self)
		groupname = self.addgroupname.get()
		groupdata = data.GroupData(name=groupname)
		self.publish(groupdata, database=True)

	def addUser(self):
		username = self.addusername.get()
		groupname = self.selectgroup.getSelectedValue()
		if groupname is not None and groupname in self.groupdatadict:
			groupdata = self.groupdatadict[groupname]
			userdata = data.UserData(name=username, group=groupdata)
			self.publish(userdata, database=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.addgroupname = uidata.String('Name', '', 'rw')
		addgroup = uidata.Method('Add', self.addGroup)
		groupscontainer = uidata.Container('Groups')
		groupscontainer.addObjects((self.addgroupname, addgroup))

		self.addusername = uidata.String('Name', '', 'rw')
		self.selectgroup = uidata.SingleSelectFromList('Group', [], 0)
		adduser = uidata.Method('Add', self.addUser)
		userscontainer = uidata.Container('Users')
		userscontainer.addObjects((self.addusername, adduser))

		container = uidata.MediumContainer('Administration')
		container.addObjects((groupscontainer,))
		self.uiserver.addObject(container)

