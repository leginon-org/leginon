import os
from pyami import gitlib
from leginon import version
from leginon import projectdata
import xml.dom.minidom as dom

class UpdateLib:
	def __init__(self, project_dbupgrade):
		msg = True
		self.project_dbupgrade = project_dbupgrade
		self.branch_name = gitlib.getCurrentBranch()
		if msg is True:
			print "Branch name '%s'"%(self.branch_name)
		self.commit_count = self.getCommitCount(msg=msg)
		self.db_revision = self.getDatabaseRevision(msg=msg)
		self.db_branch = self.getDatabaseBranch(msg=msg)

	def checkSchemaInDatabase(self):
		squery = projectdata.schemaupdates()
		sdata = squery.query(results=1)
		if sdata and len(sdata) > 0:
			idlist = []
			for s in sdata:
				idlist.append(s['schemaid'])
			print idlist
			return True
		# perform upgrade
		self.subversionSchemaUpgrade()

	def subversionSchemaUpgrade(self):
		print "update schema table in database from legacy version"
		last_revision = self.getDatabaseRevision(msg=False)
		db_branch = self.getDatabaseBranch(msg=False)
		if db_branch != self.branch_name:
			print "new branch: reset revision"
			last_revision = self.getBranchResetRevision(self.branch_name)
		if last_revision == 0:
			print "first ever update: reset revision"
			last_revision = self.getBranchResetRevision(self.branch_name)
		tag_number_list = self.getAvailableTagsForBranch()
		for tag_number in tag_number_list:
			if tag_number < last_revision:
				print "putting schema update %d into database"%(tag_number)
				self.legacyAddUpdateToSchemaTable(tag_number)

	def legacyAddUpdateToSchemaTable(self, schema_number):
		updateq = projectdata.schemaupdates()
		updateq['schemaid'] = schema_number
		schema_tag = "schema%d"%(schema_number)
		updateq['schematag'] = schema_tag
		updateq['schemacommitid'] = gitlib.getCommitIDfromTag(schema_tag)
		updateq['branch'] = gitlib.getCurrentBranch()
		updateq['commitcount'] = gitlib.getCurrentCommitCount()
		updateq['gitversion'] = gitlib.getVersion()
		updateq['recentcommitid'] = gitlib.getMostRecentCommitID()
		updateq.insert(force=True)

	def getAvailableTagsForBranch(self):
		tag_list = gitlib.getAvailableTagsForBranch()
		tag_number_list = []
		for tag in tag_list:
			if tag.startswith("schema"):
				tagnum = int(tag[6:])
				tag_number_list.append(tagnum)
		return tag_number_list

	def getUpdateRevisionSequence(self, branch_name):
		'''
		Update revision sequence according to branch input.
		Please update the revision sequence in this function when
		new schema update script is added.
		'''
		has_appiondbs = self.checkProcessingDB()
		### this seems so clunky, can we do this better
		if branch_name == 'trunk':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607,17035,17111,17224,17561,17562,17617,17812,17813,17916,18000,18034,19470]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446,17035,17311,17982]
		elif branch_name == 'myami-3.3':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607,17035,17111,17224,17561,17562,17617,17812,17813,17916,18000,18034,19470]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446,17035,17311,17982]
		elif branch_name == 'myami-3.2':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607,17035,17111,17224,17561,17562,17617,17812,17813,17916,18000,18034,19470]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446,17035,17311,17982]
		elif branch_name == 'myami-3.1':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607,17035,17111,17224,17561,17562,17617,17812,17813,17916,18000,18034]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446,17035,17311,17982]
		elif branch_name == 'myami-3.0':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607,17035,17111,17224,17561,17562,17617,17812,17813,17916,18000,18034]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446,17035,17311,17982]
		elif branch_name == 'myami-2.2':
			schema_revisions = [12857,13713,14077,14891,15069,15497,15526,15653,16182,16607]
			appion_only_revisions = [15248,15251,15293,15961,16412,16446]
		elif branch_name == 'myami-2.1':
			schema_revisions = [12857,13713,14077,14891]
			appion_only_revisions = [15293]
		elif branch_name == 'myami-2.0':
			schema_revisions = [12857,13713,14077,14380]
			appion_only_revisions = [15293]
		else:
			raise ValueError("Unknown branch name %s"%(branch_name))
		if has_appiondbs:
			schema_revisions.extend(appion_only_revisions)
			schema_revisions.sort()
		return schema_revisions

	def getBranchResetRevision(self,branch_name):
		'''
		branch_reset_revision refers to the schemaupdate revision
		after which it may have new update if updating to newer branches.
		ResetRevision is necessary because new development in newer branch
		may have a necessary schema update prior to the most recent version
		of the older branch.  Please add the revision number for new branch
		'''
		branch_reset_revision = self.db_revision
		if not self.getDatabaseReset():
			if branch_name == 'trunk':
				branch_reset_revision = 18034
			elif branch_name == 'myami-3.3':
				branch_reset_revision = 18034
			elif branch_name == 'myami-3.2':
				branch_reset_revision = 18034
			elif branch_name == 'myami-3.1':
				branch_reset_revision = 18034
			elif branch_name == 'myami-3.0':
				branch_reset_revision = 17973
			elif branch_name == 'myami-2.2':
				branch_reset_revision = 16607
			elif branch_name == 'myami-2.1':
				if self.db_revision >= 15293:
					branch_reset_revision = 14891
			elif branch_name == 'myami-2.0':
				# schema-r14380 in myami-2.0 and schema-r14891 in later are equivalent
				branch_reset_revision = 14891
			else:
				raise ValueError("Unknown branch name")
		return branch_reset_revision

	def getPackageVersion(self):
		'''
		This function outputs the string to put in database as
		the version of myami package.  It uses gitlib Branch gives branch
		'''
		branch = gitlib.getCurrentBranch()
		if branch == 'trunk':
			version_log = branch
		elif 'myami-' in branch:
			version_log = branch.split('-')[-1]
		else:
			raise ValueError("Unknown git branch name")
		return version_log

	def checkProcessingDB(self):
		appiondbs = projectdata.processingdb().query()
		if appiondbs:
			return True
		return False

	def getBranchUpdateSequence(self):
		'''
		This function obtains update revision sequence according
		to db and checkout branch and revision changes.
		'''
		checkout_update_sequence = self.getUpdateRevisionSequence(self.branch_name)
		db_update_sequence = self.getUpdateRevisionSequence(self.db_branch)
		if self.branch_name == self.db_branch:
			return checkout_update_sequence
		else:
			for revision in db_update_sequence:
				if revision <= self.db_revision and revision in checkout_update_sequence:
					del checkout_update_sequence[checkout_update_sequence.index(revision)]
			return checkout_update_sequence

	def getCommitCount(self, module_path='.', msg=False):
		try:
			# Only svn checkout have integer revision number
			commit_count = int(gitlib.getCurrentCommitCount())
			if msg is True:
				print '\033[36mCommit count is %s\033[0m' % commit_count
			return commit_count
		except:
			release_revision = self.getReleaseRevisionFromXML(module_path)
			if release_revision:
				if msg is True:
					print '\033[36mRelease revision is %s\033[0m' % release_revision
				return release_revision
			else:
				# For unknown releases, assume head revision
				return 1000000000

	def getDatabaseBranch(self, msg=False):
		### get revision from database
		selectq = " SELECT value FROM `install` WHERE `key`='version'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		versiontext = values[0][0]
		versionlist = versiontext.split('.')
		if len(versionlist) > 1:
			branch_name = 'myami-'+'.'.join(versionlist[:2])
		else:
			# trunk
			branch_name = versionlist[0]
		return branch_name

	def getDatabaseRevision(self, msg=False):
		##check if git update has ever been done
		schemaquery = projectdata.schemaupdates()
		schemadatas = schemaquery.query()
		if len(schemadatas) == 0:
			#git update has never been applied
			print "getDatabaseRevisionOLD()"
			return self.getDatabaseRevisionOLD()
		maxSchemaNumber = -1
		for data in schemadatas:
			schemaid = data['schemaid']
			maxSchemaNumber = max(maxSchemaNumber, schemaid)
		if msg:
			print '\033[36mDatabase recorded revision is %s\033[0m' % maxSchemaNumber
		return maxSchemaNumber

	def getDatabaseRevisionOLD(self, msg=False):
		### get revision from database
		selectq = " SELECT value FROM `install` WHERE `key`='revision'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		if values:
			revision = int(values[0][0])
		else:
			selectq = " SELECT value FROM `install` WHERE `key`='version'"
			versionvalues = self.project_dbupgrade.returnCustomSQL(selectq)
			if versionvalues:
				dbversion = versionvalues[0][0]
				if dbversion == '1.7':
					# pre myami-2.0 database need more updates
					revision = 12000
				else:
					# early myami-2.0 database has no revision record
					revision = 14077
			else:
				raise ValueError("Unknown version log in database, cannot proceed")
		return revision

	def allowVersionLog(self,checkout_revision):
		'''
			Package version log is allowed only if the checkout_revision
			ahead of the current revision_in_database less than one
			required update ahead
		'''
		revision_in_database = self.getDatabaseRevisionByBranch()
		if checkout_revision <= revision_in_database:
			print '\033[35mDatabase revision log up to date, Nothing to do\033[0m'
			return False
		schema_revisions = self.getBranchUpdateSequence()
		schema_revisions.sort()
		schema_revisions.reverse()
		minimal_revision_in_database = revision_in_database
		for revision in schema_revisions:
			if revision < checkout_revision:
				minimal_revision_in_database = revision
				break
		if minimal_revision_in_database <= revision_in_database:
			return True
		else:
			print '\033[35mYou must successfully run schema-r%d.py first\033[0m' % (minimal_revision_in_database)
			return False

	def getDatabaseRevisionByBranch(self,msg=False):
		branch_reset_revision = self.getBranchResetRevision(self.db_branch)
		if self.db_branch == self.branch_name:
			return self.db_revision
		else:
			return min(self.db_revision,branch_reset_revision)

	def needUpdate(self, schema_number, force=False):
		if force:
			return True

		##check if update has ever been done
		schemaquery = projectdata.schemaupdates()
		schemaquery['schemaid'] = schema_number
		schemadata = schemaquery.query()
		if len(schemadata) == 0:
			#this update has never been applied
			return True

		##check if update has ever been done to this branch
		schemaquery = projectdata.schemaupdates()
		schemaquery['schemaid'] = schema_number
		schemaquery['branch'] = self.branch_name
		schemadata = schemaquery.query()
		if len(schemadata) > 0:
			#this update has already been applied
			return False

		## hack for python 2.6, yuck
		module_name = "schema-r%s"%(str(schema_number))
		my_module = getattr(__import__("updates", fromlist=[module_name]), module_name)
		try:
			my_class = my_module.SchemaUpdate()
		except AttributeError:
			# this module needs updating
			return False
		if my_class.reRunOnBranchUpgrade is False:
			print "reRunOnBranchUpgrade"
			return False

		#update has been done, but not on this branch
		raise NotImplementedError

		return False

	def getReleaseRevisionFromXML(self,module_path='.'):
		if not module_path:
			module_path = version.getInstalledLocation()
		module_path = os.path.abspath(module_path)
		pieces = module_path.split('/')
		xmlpathpieces = pieces[:-1]
		xmlpathpieces.extend(['myamiweb','xml','projectDefaultValues.xml'])
		xmlfilepath = '/'.join(xmlpathpieces)
		print '\033[35mGetting release revision from %s\033[0m' % xmlfilepath
		curkey = None
		installdata = {}
		try:
			xmlapp = dom.parse(xmlfilepath)
		except:
			raise ValueError('unable to parse XML file "%s"' % xmlfilepath)
		defaulttables = xmlapp.getElementsByTagName('defaulttables')[0]
		### data is not used
		#data = defaulttables.getElementsByTagName('data')[0]
		sqltables = defaulttables.getElementsByTagName('sqltable')
		for node in sqltables:
			if node.attributes['name'].value == 'install':
				for n in node.childNodes:
					if n.nodeName == 'field':
						if n.attributes['name'].value == 'key':
							curkey = n.firstChild.data
						if n.attributes['name'].value == 'value':
							installdata[curkey] = n.firstChild.data
		if 'revision' in installdata:
			return int(installdata['revision'])

	def updateDatabaseRevision(self,current_revision):
		### set version of database
		selectq = " SELECT * FROM `install` WHERE `key`='revision'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		if values:
			self.project_dbupgrade.updateColumn("install", "value", "'%d'" % (current_revision),
				"install.key = 'revision'",timestamp=False)
		else:
			insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('revision', %d)"% (current_revision)
			self.project_dbupgrade.executeCustomSQL(insertq)

	def updateDatabaseVersion(self,current_version):
		### set version of database
		selectq = " SELECT * FROM `install` WHERE `key`='version'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		if values:
			self.project_dbupgrade.updateColumn("install", "value", "'%s'" % (current_version),
				"install.key = 'version'",timestamp=False)

	def getDatabaseReset(self):
		selectq = " SELECT * FROM `install` WHERE `key`='resetfrom'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		if values:
			print int(values[0][1])
			return int(values[0][1])
		else:
			return False

	def deleteDatabaseReset(self):
		if self.getDatabaseReset():
			self.project_dbupgrade.updateColumn("install", "value", "'0'",
					"install.key = 'resetfrom'",timestamp=False)

	def updateDatabaseReset(self,reset_from_revision):
		### set version of database
		selectq = " SELECT * FROM `install` WHERE `key`='resetfrom'"
		values = self.project_dbupgrade.returnCustomSQL(selectq)
		if values:
			if int(values[0][1]) == 0:
				self.project_dbupgrade.updateColumn("install", "value", "'%d'" % (reset_from_revision),
					"install.key = 'resetfrom'",timestamp=False)
		else:
			insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('resetfrom', %d)"% (reset_from_revision)
			self.project_dbupgrade.executeCustomSQL(insertq)
