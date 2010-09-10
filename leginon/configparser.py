#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import os
import ConfigParser
import inspect

HOME = os.path.expanduser('~')
CURRENT = os.getcwd()
this_file = inspect.currentframe().f_code.co_filename
MODULE = os.path.dirname(this_file)

configparser = ConfigParser.SafeConfigParser()
# look in the same directory as this module
defaultfilename = os.path.join(MODULE, 'config', 'default.cfg')
try:
	configparser.readfp(open(defaultfilename), defaultfilename)
except IOError:
	raise LeginonConfigError('cannot find configuration file default.cfg')
## process configs in this order (later ones overwrite earlier ones)
config_locations = [
	'leginon.cfg',
	os.path.join(MODULE, 'config', 'leginon.cfg'),
	os.path.join(HOME, 'leginon.cfg'),
]
configfiles = configparser.read(config_locations)
