#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import os
import ConfigParser
import pyami.fileutil

configparser = ConfigParser.SafeConfigParser()
confdirs = pyami.fileutil.get_config_dirs()
conf_files = [os.path.join(confdir, 'leginon.cfg') for confdir in confdirs]
configfiles = configparser.read(conf_files)
