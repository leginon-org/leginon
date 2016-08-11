#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

DIR=$( dirname ${0} )

DATE=$( date '+%Y%m%d%H%M' )

ID=${DATE}

echo "#define BUILD_ID \"${ID}\""

echo "#define COMPILE_DATE \"${DATE}\""
