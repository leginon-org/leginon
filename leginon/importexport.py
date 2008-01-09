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
from xml.parsers.expat import ExpatError
import xml.dom.minidom as dom
from sinedon import sqldb
import re

class ApplicationImportError(Exception):
	pass

class XMLApplicationExport:
	"""XMLApplicationExport: An object class which exports an application as
	a xml file"""

	def __init__(self,db):
		self.db = db
		self.setCRLF('\n')

	def setCRLF(self, newcrlf):
		self.crlf = str(newcrlf)

	def getCRLF(self):
		return self.crlf

	def getXMLheader(self, name, version, date):
		header = '<!--'+self.crlf \
			+ '-' + self.crlf \
			+ '- Application XML-Dump' + self.crlf \
			+ '- http://ami.scripps.edu/ ' + self.crlf \
			+ '-' + self.crlf \
			+ '- Application :' + str(name) + self.crlf \
			+ '- Version     :' + str(version) + self.crlf \
			+ '- Date : ' + str(date) + self.crlf \
			+ '-' + self.crlf \
			+ '-->' + self.crlf + self.crlf 
		return header

	def getXMLdump(self, ref_tables, applicationId):
		""" build the final XML structure of an application:

		<applicationdump>
		 <definition>
		 [xml table definition]
		 </definition>
		 <data>
		 [xml data]
		 </data>
		<applicationdump>
		"""
		dump = '<applicationdump>%s' % (self.crlf,)
		dump += ' <definition>%s' % (self.crlf,)
		for table in ref_tables:
			dump += self.getSQLTableDefinitionXML(table)
		dump += ' </definition>%s' % (self.crlf,)
		dump += ' <data>%s' % (self.crlf,)
		for table in ref_tables:
			dump += self.getXMLData(table, applicationId)
		dump += ' </data>%s' % (self.crlf,)
		dump += '</applicationdump>%s' % (self.crlf,)
		return dump
		
	def getSQLTableDefinitionXML(self,table):
		"""
	Convert any SQL Table definition into XML. For example:

	+---------------+---------------+------+-----+---------+----------------+
	| Field         | Type          | Null | Key | Default | Extra          |
	+---------------+---------------+------+-----+---------+----------------+
	| DEF_id        | int(16)       |      | PRI | NULL    | auto_increment |
	| DEF_timestamp | timestamp(14) | YES  | MUL | NULL    |                |
	| name          | text          |      |     |         |                |
	| version       | int(11)       |      |     | 0       |                |
	+---------------+---------------+------+-----+---------+----------------+

	=>

		<sqltable name="ApplicationData" >
		<field name="DEF_id" type="int(16)" null="NOT NULL" extra="auto_increment" />
		<field name="DEF_timestamp" type="timestamp(14)" />
		<field name="name" type="text" null="NOT NULL" />
		<field name="version" type="int(11)" default="DEFAULT '0'" null="NOT NULL" />
		<key>PRIMARY KEY (`DEF_id`)</key>
		<key>KEY `DEF_timestamp` (`DEF_timestamp`)</key>
		</sqltable>
	"""
		schema_create = '  <sqltable name="%s" >%s' % (table,self.crlf)

		rows = self.db.selectall("SHOW FIELDS FROM `%s`" % (table,))
		for row in rows:
			schema_create += '    <field %s' % (self.crlf,) 
			schema_create += '      name="%s" %s' % (row['Field'], self.crlf)
			schema_create += '      type="%s" %s' % (row['Type'], self.crlf)
			if row['Default']:
				schema_create += '      default="DEFAULT \'%s\'"%s' % (row['Default'], self.crlf)
			if not row['Null']:
				schema_create += '      null="NOT NULL"%s' % (self.crlf,)
			if row['Extra']:
				schema_create += '      extra="%s"%s' % (row['Extra'], self.crlf)
			schema_create += "    />%s" % (self.crlf,)
		
		keys = self.db.selectall("SHOW KEYS FROM `%s`" % (table,)) 

		keys_dict={}
		for key in keys:
			kname = key['Key_name']
			if kname!='PRIMARY':
				kname = sqldb.addbackquotes(kname)
			if key['Non_unique']==0 and kname!='PRIMARY':
				kname = "UNIQUE|%s" % (kname,)
			if not keys_dict.has_key(kname):
				keys_dict[kname]=[]
			keys_dict[kname].append(sqldb.addbackquotes(key['Column_name']))

		for key,value in keys_dict.items():
			schema_create += '    <key>'
			value_str = ', '.join(value)
			if key=='PRIMARY':
				schema_create += 'PRIMARY KEY (%s)' % (value_str,) 
			elif re.findall('^UNIQUE\|',key):
				k = re.sub('^UNIQUE\|', '', key)
				schema_create += 'UNIQUE %s (%s)' % (k, value_str) 
			else:
				schema_create += 'KEY %s (%s)' % (key, value_str) 
			schema_create += '</key>%s' % (self.crlf,) 
		
		schema_create += '  </sqltable>%s' % (self.crlf,)
		return schema_create

	def getXMLData(self, table, applicationId):
		"""
	Convert each row (field/column name) into XML:
	For example:
		+--------+----------------+---------+---------+
		| DEF_id | DEF_timestamp  | name    | version |
		+--------+----------------+---------+---------+
		|      1 | 20040121162912 | 03dec15 |       0 |
		+--------+----------------+---------+---------+
		
		This sql result will be in XML:
	
		<!--  ApplicationData -->
	    <sqltable name="ApplicationData" >
		<field name="DEF_id" >79</field>
		<field name="DEF_timestamp" >20031215125843</field>
		<field name="name" >03dec15</field>
		<field name="version" >0</field>
	    </sqltable>
		"""
		data = "<!-- %s -->%s" % (table,self.crlf) 
		if table == 'ApplicationData':
			key = 'DEF_id'
		else:
			key = 'REF|ApplicationData|application'

		q = 'SELECT * FROM `%s` WHERE `%s`=%s ' % (table, key, applicationId)
		results = self.db.selectall(q)
		for result in results:
			data += '    <sqltable name="%s">%s' % (table,self.crlf)
			for k,v in result.items():
				if k=='DEF_timestamp':
					v = v.strftime('%Y%m%d%H%M%S')
				data += '        <field name="%s" >%s</field>%s' % (k,v,self.crlf)
			data += '    </sqltable>%s' % (self.crlf,)
		return data
		



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
		try:
			xmlapp = dom.parse(filename)
		except ExpatError:
			raise ValueError('unable to parse XML file "%s"' % filename)
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
				elif n.firstChild is not None:
					fvalue = "'%s'" % (sqldb.escape(n.firstChild.data),)
				else:
					fvalue = "''"

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
		self.warning = ""
		self.information = ""

	def setDBparam(self, **kwargs):
		self.db = sqldb.sqlDB(**kwargs)

	def getMessageLog(self):
		return {	'warning': self.warning,
				'information': self.information
			}

	def importApplication(self, filename):
		try:
			xmlapp = XMLApplicationImport(filename)
		except IOError,e:
			raise ApplicationImportError(e)
			return
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
		check = False

		# Insert New Application data
		if check:
			raise ApplicationImportError("Application %s (version %d) exists" % (check['name'], check['version']))
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
			self.information =  "Application %s-%s inserted sucessfully" % (check['name'], check['version'])

	def exportApplication(self, name=None, applicationId=None):
		""" Export an application by name or by Id. If an application name is not None,
		the latest version of this application will be exported"""
		
		if applicationId is not None:
			q = "SELECT `DEF_id`, date_format(DEF_timestamp,'%m/%d/%Y') as date, " \
			+ "`name`, `version` from ApplicationData " \
			+ "where `DEF_Id` = " + str(applicationId)
		elif name is not None:
			q = "SELECT `DEF_id`, date_format(DEF_timestamp,'%m/%d/%Y') as date, " \
			+ "`name`, `version` from ApplicationData " \
			+ "where `name` = '" + str(name) +"'" \
			+ " ORDER BY `DEF_timestamp` DESC LIMIT 1"
		else:
			return
		try: 
			result = self.db.selectone(q)
			if not result:
				return
		except sqldb.MySQLdb.ProgrammingError, e:
			return e

		applicationId = result['DEF_id']
		name = result['name']
		version = result['version']
		date = result['date']

		ref_tables=['ApplicationData',]
		tables = self.db.selectall("SHOW TABLES")
		for table in tables:
			tablename=table.values()[0]
			### do not export table LaunchedApplicationData ###
			if tablename=='LaunchedApplicationData':
				continue
			q = "SHOW FIELDS FROM `%s`" % (tablename,)
			rows = self.db.selectall(q)
			for row in rows:
				if re.findall('^REF\|ApplicationData', row['Field']):
					try:
						ref_tables.index(tablename)
					except:
						ref_tables.append(tablename)
		xmlexp = XMLApplicationExport(self.db)
		dump = xmlexp.getXMLheader(name,version,date)
		dump += xmlexp.getXMLdump(ref_tables,applicationId)
		
		return dump

########################################
## Testing
########################################

if __name__ == "__main__":
	appname = "MSI1_062"
#	appfile= "/home/dfellman/MSI1_062_1.xml"
	app = ImportExport()
#	app.setDBparam(host="stratocaster")
#	app.importApplication(appfile)
#	print app.getMessageLog()
	dump = app.exportApplication(appname)
	print dump
