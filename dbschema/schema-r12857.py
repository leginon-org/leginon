#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig

# This will update databases that were installed prior to r12857.
# The tables that will be affected are in the dbemdata database and the project database.
# Migrate the user data from project to dbemdata because dbemdata is already in Sinedon format.
# The tables affected are dbemdata[GroupData, UserData] 
# and project[users,login,pis,userdetails,projectowner]

if __name__ == "__main__":
	appiondb = dbupgrade.DBUpgradeTools('appiondata', 'aptest', drop=True)
	projectdb = dbupgrade.DBUpgradeTools('projectdata', 'projtest', drop=True)
	leginondb = dbupgrade.DBUpgradeTools('leginondata', 'dbemtest', drop=False)

	#===================
	# leginon table
	# update from Anchi which occured in revison 12330
	#===================

	if leginondb.columnExists('PresetData', 'exposure time'):
		updateq = ("ALTER TABLE `PresetData` "
			+" CHANGE `exposure time` `exposure time` DOUBLE NULL DEFAULT NULL "
		)
		
		leginondb.executeCustomSQL(updateq)

	#===================
	# Check to see if this script has already been run. 
	# If the username column exists in the UserData table, 
	# we do not need to make any further updates 
	#===================
	if leginondb.tableExists('UserData') and leginondb.tableExists('GroupData') \
	   and projectdb.tableExists('users') and projectdb.tableExists('login') \
	   and projectdb.tableExists('pis') and projectdb.tableExists('userdetails') \
	   and projectdb.tableExists('projectowner') and not leginondb.columnExists('UserData', 'username'):
	
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
		leginondb.addColumn('UserData', 'fullname', leginondb.str)
		leginondb.addColumn('UserData', 'firstname', leginondb.str)
		leginondb.addColumn('UserData', 'lastname', leginondb.str)
		leginondb.addColumn('UserData', 'password', leginondb.str)
		leginondb.addColumn('UserData', 'email', leginondb.str)

		#===================
		#
		# 2 Copy data to the UserData table
		#
		#===================
	
		
		updateq = ("UPDATE UserData, projectdb.users, projectdb.login "
				+" SET UserData.username=projectdb.users.username, "
				+" UserData.firstname=projectdb.users.firstname, "
				+" UserData.lastname=projectdb.users.lastname, "
				+" UserData.email=projectdb.users.email "
				+" WHERE UserData.`full name` like concat(projectdb.users.firstname, ' ',project.users.lastname)" 
				+" and projectdb.login.userId = projectdb.users.userId "
				)
		leginondb.executeCustomSQL(updateq)
			
		#===================	
		#
		# 3 Modify userdetails table
		#
		#===================
		
		projectdb.dropColumn('userdetails', 'email')
		
		updateq = ("INSERT INTO projectdb.userdetails "
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
				+" SELECT leginondb.UserData.DEF_id, projectdb.users.title, projectdb.users.institution, " 
				+" projectdb.users.dept, projectdb.users.address, projectdb.users.city, "
				+" projectdb.users.statecountry, projectdb.users.zip, projectdb.users.phone, "
				+" projectdb.users.fax, projectdb.users.url "
				+" FROM leginondb.UserData, projectdb.users "
				+" WHERE leginondb.UserData.username = projectdb.users.username "
				)
		
		leginondb.executeCustomSQL(updateq)
		
		
		
		#===================	
		#
		# 4	Insert rows into projectowners.
		#
		# All project owners now have usernames in dbemdata.UserData and all projects have an active owner in project.pis.
		#
		#===================	
	
		updateq = (" INSERT INTO leginondb.projectowners (`REF|projects|project`, `REF|leginondata|UserData|user`) "
				+" SELECT leginondb.pis.projectId, leginondb.UserData.DEF_id "
				+" FROM leginondb.UserData, projectdb.pis "
				+" WHERE leginondb.UserData.username = projectdb.pis.username "
				)
	
		leginondb.executeCustomSQL(updateq)
		
		#===================	
		#
		# 5 Set groups and privileges
		# Set all null groups to 4 (users)
		#
		#===================	
	
		updateq = (" UPDATE leginondb.UserData "
				+" SET leginondb.UserData.`REF|GroupData|group`= 4 "
				+" WHERE leginondb.UserData.`REF|GroupData|group` IS NULL "
				)
	
		leginondb.executeCustomSQL(updateq)
	
		#===================	
		#
		# set all group privileges that are null to 3
		#
		#===================	
	
		updateq = (" UPDATE leginondb.GroupData "
				+" SET leginondb.GroupData.`REF|projectdata|privileges|privilege`=3 "
				+" WHERE leginondb.GroupData.`REF|projectdata|privileges|privilege` IS NULL "
				)
		
		leginondb.executeCustomSQL(updateq)
	
		#===================	
		# 6 Set the full name in dbemdata.UserData.
		#
		#===================	
	
		updateq = (" UPDATE leginondb.UserData "
				+" SET leginondb.UserData.`full name` = concat(leginondb.UserData.firstname, ' ', leginondb.UserData.lastname) "
				+" WHERE leginondb.UserData.`full name` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
		
		
		#===================	
		# 7 Set the username in dbemdata.UserData to the name.
		#===================	
	
		updateq = (" UPDATE leginondb.UserData "
				+" SET leginondb.UserData.`username` = leginondb.UserData.`name` "
				+" WHERE leginondb.UserData.`username` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		updateq = (" UPDATE leginondb.UserData "
				+" SET leginondb.UserData.password = leginondb.UserData.username "
				+" WHERE leginondb.UserData.password IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		updateq = (" UPDATE leginondb.UserData "
				+" SET leginondb.UserData.firstname = "" " 
				+" WHERE leginondb.UserData.firstname IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		# update shareexperiments
	
		updateq = (" UPDATE projectdb.shareexperiments "
				+" SET projectdb.shareexperiments.`REF|leginondata|SessionData|experiment` = projectdb.shareexperiments.experimentId "
				+" WHERE projectdb.shareexperiments.`REF|leginondata|SessionData|experiment` IS NULL; "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		# add usernames where they are missing
	
		updateq = (" UPDATE projectdb.shareexperiments, projectdb.users "
				+" SET projectdb.shareexperiments.username = projectdb.users.username " 
				+" WHERE projectdb.users.userId = projectdb.shareexperiments.userId "
				+" AND projectdb.shareexperiments.username IS NULL "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
		# update users who have a matching username in dbemdata
	
		updateq = (" UPDATE projectdb.shareexperiments, leginondb.UserData " 
				+" SET projectdb.shareexperiments.`REF|leginondata|UserData|user` = leginondb.UserData.DEF_id " 
				+" WHERE leginondb.UserData.username = projectdb.shareexperiments.username "
				+" AND projectdb.shareexperiments.`REF|leginondata|UserData|user` IS NULL "
				)
	 	
		leginondb.executeCustomSQL(updateq)
	
