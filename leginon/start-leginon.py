#!/usr/bin/env python
#
# Normal users should start Leginon with this script.
#

from leginon import legoptparse
## this starts Leginon user interface
from leginon import start

if __name__ == "__main__":
	start.start(legoptparse.options)
