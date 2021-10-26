#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
import event
import threading
import node
import project
import gui.wx.GridEntry

class GridEntry(node.Node):
	eventinputs = node.Node.eventinputs + [event.TargetListDoneEvent,
																					event.MosaicDoneEvent]
	eventoutputs = node.Node.eventoutputs + [event.MakeTargetListEvent
										]
	panelclass = gui.wx.GridEntry.Panel
	settingsclass = leginondata.GridEntrySettingsData
	defaultsettings = {
		'grid name': None,
		'stage z': 0.0,
	}

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.projectid = self.getProjectId(session)
		self.addEventInput(event.MosaicDoneEvent, self.handleGridDataCollectionDone)
		self.addEventInput(event.TargetListDoneEvent,
												self.handleGridDataCollectionDone)
		self.start()

	def publishNewEMGrid(self,newgrid):
		try:
			self.checkGridName(newgrid)
		except ValueError, e:
			raise
		emgridq = leginondata.EMGridData()
		emgridq['name'] = newgrid
		emgridq['project'] = self.projectid
		try:
			self.publish(emgridq, database=True)
		except node.PublishError:
			raise
		self.settings['grid name'] = newgrid
		self.logger.info('new grid inserted into the database')

	def getProjectId(self,sessiondata):
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.warning('Failed to associate the grid to a project: %s' % e)
			return None
		return projectdata.getProjectId(sessiondata)

	def getGridNames(self):
		gridnames = []
		if self.projectid is not None:
			emgridq = leginondata.EMGridData(project = self.projectid)
		else:
			emgridq = leginondata.EMGridData()
		results = emgridq.query()
		if results:
			for result in results:
				newname = result['name']
				if newname not in gridnames:
					gridnames.append(newname)
				else:
					self.logger.warning('Duplicated grid name "%s" not included' % newname)
		return gridnames
					
	def getEMGrid(self, gridname):
		if self.projectid is not None:
			emgridq = leginondata.EMGridData(project = self.projectid, name = gridname)
		else:
			emgridq = leginondata.EMGridData(name = gridname)
		results = emgridq.query(results=1)
		if results:
			return results[0]
		else:
			return None

	def makeGridData(self, gridname):
		emgriddata = self.getEMGrid(gridname)
		if emgriddata is None:
			return None
		emgridid = emgriddata.dbid
		initializer = {'emgrid': emgriddata}
		querydata = leginondata.GridData(initializer=initializer)
		griddatalist = self.research(querydata)
		insertion = 0
		for griddata in griddatalist:
			if griddata['insertion'] > insertion:
				insertion = griddata['insertion']
		initializer = {'grid ID': None, 'insertion': insertion+1,'emgrid':emgriddata}
		griddata = leginondata.GridData(initializer=initializer)
		self.publish(griddata, database=True)
		return griddata

	def checkGridName(self, label):
		if label is not None and label != '' and not label.isalnum():
			if not ''.join(''.join(label.split('_')).split('-')).isalnum():
				raise ValueError('Only alpha numeric and "-" and "_" are allowed as grid name')
		return

	def submitGrid(self):
		gridname = self.settings['grid name']
		try:
			self.checkGridName(gridname)
		except ValueError, e:
			self.logger.error(e)
			self.logger.error('Data collection event not sent')
			return

		stagez = self.settings['stage z']
		if stagez is None:
			stagez = 0.0
		evt = event.MakeTargetListEvent()
		evt['grid'] = self.makeGridData(gridname)
		evt['stagez'] = stagez
		if evt['grid'] is None:
			self.logger.error('Data collection event not sent')
		else:
			self.outputEvent(evt)
			self.logger.info('Data collection initiated')
		return evt['grid']

	def onBadEMGridName(self,e):
		self.logger.error('New grid entry failed: %s' % e)

	def handleGridDataCollectionDone(self, ievent):
		self.panel.onGridDone()
