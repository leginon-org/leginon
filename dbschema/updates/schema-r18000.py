#!/usr/bin/env python
import schemabase
from leginon import leginondata

class SchemaUpdate18000(schemabase.SchemaUpdate):
	'''
	This schema hides applications from leginon if its TransformManager is not bound to its Navigator.  It is associated with r17932 but not made until after r17982 schema change.
	'''

	def getTransformManagerNavigatorNodes(self,appdata):
		transform_q = leginondata.NodeSpecData(application=appdata)
		transform_q['class string'] = 'TransformManager'
		t_results = transform_q.query()

		navigator_q = leginondata.NodeSpecData(application=appdata)
		navigator_q['class string'] = 'Navigator'
		n_results = navigator_q.query()
		return t_results, n_results

	def hasTransformManagerNavigatorBindings(self,appdata,t_nodedata,n_nodedata):
		binding_q = leginondata.BindingSpecData(application=appdata)
		binding_q['from node alias'] = t_nodedata['alias']
		binding_q['to node alias'] = n_nodedata['alias']
		binding_q['event class string'] = 'MoveToTargetEvent'
		binding_results = binding_q.query()
		if binding_results:
			return True
		else:
			return False

	def upgradeLeginonDB(self):
		if not self.leginon_dbupgrade.tableExists('ApplicationData'):
			return
		
		if not self.leginon_dbupgrade.columnExists('ApplicationData', 'hide'):
			self.leginon_dbupgrade.addColumn('ApplicationData', 'hide', self.leginon_dbupgrade.bool)

		apps = leginondata.ApplicationData().query()

		for appdata in apps:
			t_results, n_results = self.getTransformManagerNavigatorNodes(appdata)
			# Only on applications with the two nodes
			if t_results and n_results:
				hasbindings = self.hasTransformManagerNavigatorBindings(appdata,t_results[0],n_results[0])
				if not hasbindings:
					print appdata['name'], appdata['version'], appdata['hide']
					q = "UPDATE `ApplicationData` SET `hide` = '1' WHERE `DEF_id` =%d" % appdata.dbid
					self.leginon_dbupgrade.executeCustomSQL(q)


if __name__ == "__main__":
	update = SchemaUpdate18000()
	# update only leginon database
	update.setRequiredUpgrade('leginon')
	update.run()
