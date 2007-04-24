#Part of the new appion

import data
import dbdatakeeper

db     = dbdatakeeper.DBDataKeeper()
apdb   = dbdatakeeper.DBDataKeeper(db='dbappiondata')
projdb = dbdatakeeper.DBDataKeeper(db='project')
