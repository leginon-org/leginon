import node
import data
import uidata
import emregistry

class Administration(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.groupdatadict = {}
		self.updateGroupDataDict()
		self.start()

	def updateGroupDataDict(self):
		groupdata = self.research(datainstance=data.GroupData())
		print groupdata
		for i in groupdata:
			if 'name' in i and i['name'] is not None:
				self.groupdatadict[i['name']] = i
		self.selectgroup.set(self.groupdatadict.keys(), 0)

	def addGroup(self):
		name = self.addgroupname.get()
		description = self.addgroupdescription.get()
		initializer = {'name': name, 'description': description}
		groupdata = data.GroupData(initializer=initializer)
		self.publish(groupdata, database=True)
		# timing
		self.updateGroupDataDict()

	def addUser(self):
		name = self.addusername.get()
		fullname = self.adduserfullname.get()
		groupname = self.selectgroup.getSelectedValue()
		if groupname is not None and groupname in self.groupdatadict:
			groupdata = self.groupdatadict[groupname]
			initializer = {'name': name, 'full name': fullname, 'group': groupdata}
			userdata = data.UserData(initializer=initializer)
			self.publish(userdata, database=True)

	def addInstrument(self):
		name = self.addinstrumentname.get()
		description = self.addinstrumentdescription.get()
		scope = self.addinstrumentscope.getSelectedValue()
		if scope == 'None':
			scope = None
		camera = self.addinstrumentcamera.getSelectedValue()
		if camera == 'None':
			camera = None
		camsize = self.camsize.get()
		hostname = self.addinstrumenthostname.get()
		initializer = {'name': name,
										'description': description,
										'scope': scope,
										'camera': camera, 'camera size': camsize,
										'hostname': hostname}
		instrumentdata = data.InstrumentData(initializer=initializer)
		self.publish(instrumentdata, database=True)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.addgroupname = uidata.String('Name', '', 'rw')
		self.addgroupdescription = uidata.String('Description', '', 'rw')
		addgroup = uidata.Method('Add', self.addGroup)
		groupcontainer = uidata.Container('Groups')
		groupcontainer.addObjects((self.addgroupname, self.addgroupdescription,
																addgroup))

		self.addusername = uidata.String('Name', '', 'rw')
		self.adduserfullname = uidata.String('Full Name', '', 'rw')
		self.selectgroup = uidata.SingleSelectFromList('Group', [], 0)
		adduser = uidata.Method('Add', self.addUser)
		usercontainer = uidata.Container('Users')
		usercontainer.addObjects((self.addusername, self.adduserfullname,
																self.selectgroup, adduser))

		self.addinstrumentname = uidata.String('Name', '', 'rw')
		self.addinstrumentdescription = uidata.String('Description', '', 'rw')
		self.addinstrumentscope = uidata.SingleSelectFromList('Microscope',
																			['None'] + emregistry.getScopeNames(), 0)
		self.addinstrumentcamera = uidata.SingleSelectFromList('Camera',
																			['None'] + emregistry.getCameraNames(), 0)
		self.camsize = uidata.Integer('Camera Size', 2048, 'rw')
		self.addinstrumenthostname = uidata.String('Hostname', '', 'rw')
		addinstrument = uidata.Method('Add', self.addInstrument)
		instrumentcontainer = uidata.Container('Instruments')
		instrumentcontainer.addObjects((self.addinstrumentname,
																			self.addinstrumentdescription,
																			self.addinstrumentscope,
																			self.addinstrumentcamera, self.camsize,
																			self.addinstrumenthostname,
																			addinstrument))

		container = uidata.LargeContainer('Administration')
		container.addObjects((groupcontainer, usercontainer, instrumentcontainer))
		self.uiserver.addObject(container)

