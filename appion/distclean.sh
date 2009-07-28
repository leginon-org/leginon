#!/bin/sh

echo "WARNING: DELETING SUBVERSION FILES"
sleep 10
rm -fr `find . -name .svn -type d`
rm -fv `find . -size +1M`
