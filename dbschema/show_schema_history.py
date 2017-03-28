#!/usr/bin/env python

import pprint
from leginon import projectdata

if __name__ == "__main__":
		schemaquery = projectdata.schemaupdates()
		schemadata = schemaquery.query()
		for data in schemadata:
			print ""
			### TODO make this nicer in future
			pprint.pprint(data)

