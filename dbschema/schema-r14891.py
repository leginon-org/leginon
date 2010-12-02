#!/usr/bin/env python

import sys
from sinedon import dbupgrade, dbconfig
from leginon import projectdata, leginondata

# This will update leginon databases that were installed prior to r14897.
# This script is going to fix the timestamp problem on LaunchedApplicationData table.
# Originally default timestamp set to null which cause leginon session not remember
# last launched application since a query for recent time fails.
# see issue number 942 in redmine.

if __name__ == "__main__":
    leginondb = dbupgrade.DBUpgradeTools('leginondata', drop=False)
    
    alterSQL = (" Alter Table LaunchedApplicationData " + 
                " Modify `DEF_timestamp` timestamp not null " + 
                " default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP")
    
    result = leginondb.executeCustomSQL(alterSQL)
    
    if result:
       print "Database Updated....."
    else:
        print result
        
    