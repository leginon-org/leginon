#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata

# This will update databases that were installed prior to r12857.
# The tables that will be affected are in the dbemdata database and the project database.
# Migrate the user data from project to dbemdata because dbemdata is already in Sinedon format.
# The tables affected are dbemdata[GroupData, UserData] 
# and project[users,login,pis,userdetails,projectowner]

if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)
	leginondb = dbupgrade.DBUpgradeTools('leginondata', drop=False)

	print "\nWould you like to back up the database to local file before upgrading?"
	answer = raw_input('Yes/No (default=Yes): ')
	if not answer.lower().startswith('n'):
		leginondb.backupDatabase("leginondb.sql", data=True)
		projectdb.backupDatabase("projectdb.sql", data=True)


	#===================
	# leginon table
	# update from Anchi which occured in revison 12330
	#===================

	if leginondb.columnExists('AcquisitionImageTargetData', 'delta row'):
		leginondb.changeColumnDefinition('AcquisitionImageTargetData', 'delta row', leginondb.float)
		leginondb.changeColumnDefinition('AcquisitionImageTargetData', 'delta column', leginondb.float)

	#===================
	# Check to see if this script has already been run. 
	# If the username column exists in the UserData table, 
	# we do not need to make any further updates 
	#===================
	if leginondb.tableExists('UserData'):
		if not leginondb.columnExists('UserData','username'):

			#===================
			# 1 Add new columns to UserData
			#
			# Add:
			#
			#    * username
			#    * fullname
			#    * firstname
			#    * lastname
			#    * password
			#    * email
			#
			# Leave the existing columns as is. 
			# Use of "name" and "full name" (with a space) will be phased out.
			#===================
			leginondb.addColumn('UserData', 'username', leginondb.str)
			leginondb.addColumn('UserData', 'firstname', leginondb.str)
			leginondb.addColumn('UserData', 'lastname', leginondb.str)
			leginondb.addColumn('UserData', 'password', leginondb.str)
			leginondb.addColumn('UserData', 'email', leginondb.str)

		if projectdb.tableExists('users') and projectdb.tableExists('login') \
	   and projectdb.tableExists('userdetails'):
			#===================
			#
			# 2 Copy data to the UserData table
			#
			#===================
			updateq = ("UPDATE UserData, "+projectdb.dbname+".users, "+projectdb.dbname+".login "
					+" SET UserData.username="+projectdb.dbname+".users.username, "
					+" UserData.firstname="+projectdb.dbname+".users.firstname, "
					+" UserData.lastname="+projectdb.dbname+".users.lastname, "
					+" UserData.email="+projectdb.dbname+".users.email "
					+" WHERE UserData.`full name` like concat("+projectdb.dbname+".users.firstname, ' ',project.users.lastname)" 
					+" and "+projectdb.dbname+".login.userId = "+projectdb.dbname+".users.userId "
					)
			leginondb.executeCustomSQL(updateq)
			
			#===================	
			#
			# 3 Modify userdetails table
			#
			#===================
		
			projectdb.dropColumn('userdetails', 'email')
		
			updateq = ("INSERT INTO "+projectdb.dbname+".userdetails "
					+" (`REF|leginondata|UserData|user`, "
					+" title, "
					+" institution, "
					+" dept, "
					+" address, "
					+" city, "
					+" statecountry, "
					+" zip, "
					+" phone, "
					+" fax, "
					+" url) "
					+" SELECT "+leginondb.dbname+".UserData.DEF_id, "+projectdb.dbname+".users.title, "+projectdb.dbname+".users.institution, " 
					+" "+projectdb.dbname+".users.dept, "+projectdb.dbname+".users.address, "+projectdb.dbname+".users.city, "
					+" "+projectdb.dbname+".users.statecountry, "+projectdb.dbname+".users.zip, "+projectdb.dbname+".users.phone, "
					+" "+projectdb.dbname+".users.fax, "+projectdb.dbname+".users.url "
					+" FROM "+leginondb.dbname+".UserData, "+projectdb.dbname+".users "
					+" WHERE "+leginondb.dbname+".UserData.username = "+projectdb.dbname+".users.username "
					)
		
			leginondb.executeCustomSQL(updateq)
		
		
		if projectdb.tableExists('projectowner') and not projectdb.getNumberOfRows('projectowner') and projectdb.tableExists('pis') and projectdb.getNumberOfRows('pis'):
		
			#===================	
			#
			# 4	Insert rows into projectowners.
			#
			# All project owners now have usernames in dbemdata.UserData and all projects have an active owner in project.pis.
			#
			#===================	
	
			updateq = (" INSERT INTO "+projectdb.dbname+".projectowners (`REF|projects|project`, `REF|leginondata|UserData|user`) "
					+" SELECT "+projectdb.dbname+".pis.projectId, "+leginondb.dbname+".UserData.DEF_id "
					+" FROM "+leginondb.dbname+".UserData, "+projectdb.dbname+".pis "
					+" WHERE "+leginondb.dbname+".UserData.username = "+projectdb.dbname+".pis.username "
					)
	
			leginondb.executeCustomSQL(updateq)
		
	
		#===================	
		# 6 Set the full name in dbemdata.UserData.
		#
		#===================	
	
		updateq = (" UPDATE UserData "
				+" SET UserData.`full name` = concat(UserData.firstname, ' ', UserData.lastname) "
				+" WHERE UserData.`full name` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		#===================	
		# 6 Set the first and last name in dbemdata.UserData.
		#
		#===================	
	
		updateq = (" UPDATE UserData "
				+" SET UserData.`firstname` = left(UserData.`full name`, instr(UserData.`full name`,' ')-1) "
				+" WHERE UserData.`lastname` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		updateq = (" UPDATE UserData "
				+" SET UserData.`lastname` = "
				+" right(UserData.`full name`, "
				+" length(UserData.`full name`)-instr(UserData.`full name`,' ')) "
				+" WHERE UserData.`lastname` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		
		#===================	
		# 7 Set the username in dbemdata.UserData to the name.
		#===================	
	
		updateq = (" UPDATE UserData "
				+" SET UserData.`username` = UserData.`name` "
				+" WHERE UserData.`username` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
			
		updateq = (" UPDATE UserData "
				+" SET UserData.password = MD5(UserData.username) "
				+" WHERE UserData.password IS NULL; "
				)

		leginondb.executeCustomSQL(updateq)
			
		updateq = (" UPDATE UserData "
				+' SET UserData.firstname = "" ' 
				+" WHERE UserData.firstname IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)

		#===================	
		#
		# set administrators group privileges to highest privilege for groups
		#
		#===================	
		q = projectdata.privileges(groups=4)
		adminpriv = q.query(results=1)
		adminprivid = adminpriv[0].dbid
		q = leginondata.UserData(username='administrator')
		adminuser = q.query(results=1)
		admingroupid = adminuser[0]['group'].dbid
		if adminprivid and admingroupid:	
			updateq = (" UPDATE GroupData "
					+" SET GroupData.`REF|projectdata|privileges|privilege`= %d"
					% (adminprivid,)
					+" WHERE GroupData.`DEF_id`= %d" % (admingroupid,)
					)
		
			leginondb.executeCustomSQL(updateq)
		else:
			print "Can not set administrator group privilege"
		#===================	
		#
		# set all group privileges that are null to data user privilege
		#
		#===================	
		q = projectdata.privileges(data=2)
		userpriv = q.query(results=1)
		if userpriv:
			userprivid = userpriv[0].dbid
			updateq = (" UPDATE GroupData "
					+" SET GroupData.`REF|projectdata|privileges|privilege`= %d"
					% (userprivid,)
					+" WHERE GroupData.`REF|projectdata|privileges|privilege` IS NULL "
					)
		
			leginondb.executeCustomSQL(updateq)
	
			#===================	
			#
			# Set all null groups to (users)
			#
			#===================	
			userprivdata = userpriv[0]
			q = leginondata.GroupData(privilege=userprivdata)
			usergroup = q.query(results=1)
			if usergroup:
				usergroupid = usergroup[0].dbid
			else:
				q = leginondata.GroupData()
				anygroup = q.query(results=1)
				if anygroup:
					usergroupid = anygroup[0].dbid
				updateq = (" UPDATE UserData "
					+" SET UserData.`REF|GroupData|group`= %d" %(usergroupid,)
					+" WHERE UserData.`REF|GroupData|group` IS NULL "
					)
	
				leginondb.executeCustomSQL(updateq)
		else:
			print "privilege level for general users not set"

		# update shareexperiments
	if projectdb.tableExists('shareexperiments') and projectdb.getNumberOfRows('shareexperiments') and projectdb.columnExists('shareexperiments','experimentId'):
		updateq = (" UPDATE shareexperiments "
				+" SET shareexperiments.`REF|leginondata|SessionData|experiment` = shareexperiments.experimentId "
				+" WHERE shareexperiments.`REF|leginondata|SessionData|experiment` IS NULL; "
				)
	 	
		projectdb.executeCustomSQL(updateq)
	
		# add usernames where they are missing
	
		updateq = (" UPDATE shareexperiments, users "
				+" SET shareexperiments.username = users.username " 
				+" WHERE users.userId = shareexperiments.userId "
				+" AND shareexperiments.username IS NULL "
				)
	 	
		projectdb.executeCustomSQL(updateq)
	
		# update users who have a matching username in dbemdata
	
		updateq = (" UPDATE "+projectdb.dbname+".shareexperiments, "+leginondb.dbname+".UserData " 
				+" SET "+projectdb.dbname+".shareexperiments.`REF|leginondata|UserData|user` = "+leginondb.dbname+".UserData.DEF_id " 
				+" WHERE "+leginondb.dbname+".UserData.username = "+projectdb.dbname+".shareexperiments.username "
				+" AND "+projectdb.dbname+".shareexperiments.`REF|leginondata|UserData|user` IS NULL "
				)
	 	
		projectdb.executeCustomSQL(updateq)

	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='version'"
	values = projectdb.returnCustomSQL(selectq)
	if values:
		projectdb.updateColumn("install", "value", "'1.8'", 
			"install.key = 'version'",timestamp=False)
	else:
		insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('version', '1.8')"
		projectdb.executeCustomSQL(insertq)

