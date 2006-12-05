#!/usr/bin/env python
#
# Normal users should start Leginon with this script.
#


import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-v', '--version', action='store_true', dest='version',
                  help="get version information")
(options, args) = parser.parse_args()

if options.version:
	import version
	print 'Leginon version: %s' % (version.getVersion(),)
	print '   Installed in: %s' % (version.getInstalledLocation(),)
	sys.exit()

## this starts Leginon user interface
import start
start.start()
