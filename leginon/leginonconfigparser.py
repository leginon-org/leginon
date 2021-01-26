#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import os
# Python3 has configparser but not ConfigParser module
# Python2 has ConfigParser but not configparser module
import configparser
import pyami.fileutil

leginonconfigparser = configparser.ConfigParser()
confdirs = pyami.fileutil.get_config_dirs()
conf_files = [os.path.join(confdir, 'leginon.cfg') for confdir in confdirs]
# Use only the last existing file in conf_files
conf_files = pyami.fileutil.check_exist_one_file(conf_files)
configfiles = leginonconfigparser.read(conf_files)
