#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import dbdatakeeper

dk = dbdatakeeper.DBDataKeeper(('asdf',3), None)

md = data.MyData()
mod = data.MyOtherData()
mod['stuff'] = 6
mod['encore'] = 'asdf'

md['other'] = mod

dk.insert(md)
