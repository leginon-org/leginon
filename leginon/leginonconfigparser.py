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

leginonconfigparser = ConfigParser.SafeConfigParser()
confdirs = pyami.fileutil.get_config_dirs()
conf_files = [os.path.join(confdir, 'leginon.cfg') for confdir in confdirs]
# Combine sections of the same name from all existing files in conf_files
conf_files = pyami.fileutil.check_exist_one_file(conf_files, combine=True)
configfiles = leginonconfigparser.read(conf_files)
