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
	appiondb = dbupgrade.DBUpgradeTools('appiondata', drop=True)
	projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)
	leginondb = dbupgrade.DBUpgradeTools('leginondata', drop=False)

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
	
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+" SET "+leginondb.dbname+".UserData.`full name` = concat("+leginondb.dbname+".UserData.firstname, ' ', "+leginondb.dbname+".UserData.lastname) "
				+" WHERE "+leginondb.dbname+".UserData.`full name` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		#===================	
		# 6 Set the first and last name in dbemdata.UserData.
		#
		#===================	
	
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+" SET "+leginondb.dbname+".UserData.`firstname` = left("+leginondb.dbname+".UserData.`full name`, instr("+leginondb.dbname+".UserData.`full name`,' ')-1) "
				+" WHERE 1; "
				#+" WHERE "+leginondb.dbname+".UserData.`lastname` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+" SET "+leginondb.dbname+".UserData.`lastname` = "
				+" right("+leginondb.dbname+".UserData.`full name`, "
				+" length("+leginondb.dbname+".UserData.`full name`)-instr("+leginondb.dbname+".UserData.`full name`,' ')) "
				+" WHERE 1; "
				#+" WHERE "+leginondb.dbname+".UserData.`lastname` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		
		#===================	
		# 7 Set the username in dbemdata.UserData to the name.
		#===================	
	
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+" SET "+leginondb.dbname+".UserData.`username` = "+leginondb.dbname+".UserData.`name` "
				+" WHERE "+leginondb.dbname+".UserData.`username` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
			
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+" SET "+leginondb.dbname+".UserData.password = MD5("+leginondb.dbname+".UserData.username) "
				+" WHERE "+leginondb.dbname+".UserData.password IS NULL; "
				)

		leginondb.executeCustomSQL(updateq)
			
		updateq = (" UPDATE "+leginondb.dbname+".UserData "
				+' SET '+leginondb.dbname+'.UserData.firstname = "" ' 
				+" WHERE "+leginondb.dbname+".UserData.firstname IS NULL; "
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
			updateq = (" UPDATE "+leginondb.dbname+".GroupData "
					+" SET "+leginondb.dbname+".GroupData.`REF|projectdata|privileges|privilege`= %d"
					% (adminprivid,)
					+" WHERE "+leginondb.dbname+".GroupData.`DEF_id`= %d" % (admingroupid,)
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
			updateq = (" UPDATE "+leginondb.dbname+".GroupData "
					+" SET "+leginondb.dbname+".GroupData.`REF|projectdata|privileges|privilege`= %d"
					% (userprivid,)
					+" WHERE "+leginondb.dbname+".GroupData.`REF|projectdata|privileges|privilege` IS NULL "
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
				updateq = (" UPDATE "+leginondb.dbname+".UserData "
					+" SET "+leginondb.dbname+".UserData.`REF|GroupData|group`= %d" %(usergroupid,)
					+" WHERE "+leginondb.dbname+".UserData.`REF|GroupData|group` IS NULL "
					)
	
				leginondb.executeCustomSQL(updateq)
		else:
			print "privilege level for general users not set"

		# update shareexperiments
	if projectdb.tableExists('shareexperiments') and projectdb.getNumberOfRows('shareexperiments') and projectdb.columnExists('shareexperiments','experimentId'):
		updateq = (" UPDATE "+projectdb.dbname+".shareexperiments "
				+" SET "+projectdb.dbname+".shareexperiments.`REF|leginondata|SessionData|experiment` = "+projectdb.dbname+".shareexperiments.experimentId "
				+" WHERE "+projectdb.dbname+".shareexperiments.`REF|leginondata|SessionData|experiment` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		# add usernames where they are missing
	
		updateq = (" UPDATE "+projectdb.dbname+".shareexperiments, "+projectdb.dbname+".users "
				+" SET "+projectdb.dbname+".shareexperiments.username = "+projectdb.dbname+".users.username " 
				+" WHERE "+projectdb.dbname+".users.userId = "+projectdb.dbname+".shareexperiments.userId "
				+" AND "+projectdb.dbname+".shareexperiments.username IS NULL "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		# update users who have a matching username in dbemdata
	
		updateq = (" UPDATE "+projectdb.dbname+".shareexperiments, "+leginondb.dbname+".UserData " 
				+" SET "+projectdb.dbname+".shareexperiments.`REF|leginondata|UserData|user` = "+leginondb.dbname+".UserData.DEF_id " 
				+" WHERE "+leginondb.dbname+".UserData.username = "+projectdb.dbname+".shareexperiments.username "
				+" AND "+projectdb.dbname+".shareexperiments.`REF|leginondata|UserData|user` IS NULL "
				)
	 	
		leginondb.executeCustomSQL(updateq)

