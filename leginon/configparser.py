#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import os
import ConfigParser
import pyami.fileutil

configparser = ConfigParser.SafeConfigParser()
confdirs = pyami.fileutil.get_config_dirs()
conf_files = [os.path.join(confdir, 'leginon.cfg') for confdir in confdirs]
configfiles = configparser.read(conf_files)
