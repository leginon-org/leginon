#!/usr/bin/env python
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
"""
importexport: this Module allows to Import/Export Leginon II applications
"""
import xml.dom.minidom as dom
import sqldb
import re

class XMLApplicationImport:
	"""XMLApplicationImport: An object class which import an application.xml file
	and convert into SQL queries"""

	def __init__(self, filename):
		self.importXML(filename)

	def getSQLApplicationQuery(self):
		return self.applicationquery

	def getSQLDataQueries(self):
		return self.insertqueries

	def getSQLDefinitionQueries(self):
		return self.tablequeries

	def getFieldValues(self):
		return self.fieldvalues

	def importXML(self, filename):
		self.fieldvalues={}
		self.insertqueries=[]
		self.tablequeries=[]
		xmlapp = dom.parse(filename)
		definition = xmlapp.getElementsByTagName('definition')[0]
		sdefinition = definition.getElementsByTagName('sqltable')
		for d in sdefinition:
			self.xmldefinition2sql(d)
			self.tablequeries.append(self.cursqldef)

		data = xmlapp.getElementsByTagName('data')[0]
		sdata = data.getElementsByTagName('sqltable')
		for d in sdata:
			self.xmldata2sql(d)
			if self.curtable == 'ApplicationData':
				self.applicationquery = self.curinsert
			else:
				self.insertqueries.append(self.curinsert)
				
			self.fieldvalues[self.curtable]=self.curfieldvalues

	def xmldata2sql(self, node):
		tablename = node.attributes['name'].value

		conditions = {
				'DEF_timestamp': 'NOW()',
				'REF|ApplicationData|application': '%s'
			}
		fieldvalues={}
		values=[]
		fields=[]
		sqlinserts = []
		for n in node.childNodes:
			if n.nodeName == 'field':
				d = n.attributes
				fname = self.getAttribute(d, 'name')
				if conditions.has_key(fname):
					fvalue = conditions[fname]
				else:
					fvalue = "'%s'" % (sqldb.escape(n.firstChild.data),)
				fieldvalues[fname]=fvalue

				if fname <> 'DEF_id':
					fields.append(sqldb.addbackquotes(fname))
					values.append(fvalue)

		sqlinsert = "INSERT into `%s` (%s) VALUES (%s)" % (tablename, ', '.join(fields), ', '.join(values))
		self.curtable = tablename
		self.curinsert = sqlinsert
		self.curfieldvalues = fieldvalues

	def xmldefinition2sql(self, node):

		tablename = node.attributes['name'].value
		sqlfields=[]
		for n in node.childNodes:
			if n.nodeName == 'field':
				d = n.attributes
				fname = self.getAttribute(d, 'name')
				ftype = self.getAttribute(d,'type')
				fnull = self.getAttribute(d, 'null')
				fextra = self.getAttribute(d, 'extra')

				sqlfield  = "`%s` %s %s %s" % (fname, ftype, fnull, fextra)
				sqlfields.append(sqlfield)

			if n.nodeName == 'key':
				sqlfields.append(n.firstChild.data)

		sqldef = "CREATE TABLE IF NOT EXISTS `%s` ( %s )" % (tablename, ', '.join(sqlfields))
		self.cursqldef = sqldef

	def getAttribute(self, attributes, key):
		if attributes.has_key(key):
			return attributes[key].value
		else:
			return ""

class ImportExport:
	"""ImportExport: An object class to import/export Leginon II applications from
	database to another via a XML file
	"""

	def __init__(self):
		self.db = sqldb.sqlDB()

	def setDBparam(self, **kwargs):
		"""
		'host':leginonconfig.DB_HOST,
		'user':leginonconfig.DB_USER,
		'db':leginonconfig.DB_NAME,
		'passwd':leginonconfig.DB_PASS
		"""
		self.db = sqldb.sqlDB(**kwargs)
		

	def importApplication(self, filename):
		xmlapp = XMLApplicationImport(filename)
		# Create SQL tables
		sqldef = xmlapp.getSQLDefinitionQueries()
		for q in sqldef:
			self.db.execute(q)

		# Check if application exists
		application = xmlapp.getFieldValues()['ApplicationData']
		sqlwhere=[]
		for k,v in application.items():
			if not re.findall('^DEF_',k):
				sqlwhere.append('%s=%s' % (sqldb.addbackquotes(k),v))
		where = ' 1 '
		if len(sqlwhere):
			where = ' AND '.join(sqlwhere)
			
		checkquery = "Select `DEF_id`, name, version from ApplicationData where %s" % (where,)
		check = self.db.selectone(checkquery)

		# Insert New Application data
		if check:
			print "Application %s-%s exists" % (check['name'], check['version'])
		else:
			q = xmlapp.getSQLApplicationQuery()
			applicationId = self.db.insert(q)
			queries = xmlapp.getSQLDataQueries()
			for q in queries:
				try:
					q = q % (applicationId,)
				except:
					pass
				self.db.insert(q)

			checkquery = "Select `DEF_id`, name, version from ApplicationData where %s" % (where,)
			check = self.db.selectone(checkquery)
			print "Application %s-%s inserted sucessfully" % (check['name'], check['version'])

	def exportApplication(self, name, version):
		pass

########################################
## Testing
########################################

if __name__ == "__main__":
	app = ImportExport()
	app.setDBparam(host="stratocaster")
	app.importApplication('/home/dfellman/03dec15_0.xml')

