#!/bin/sh
# find all *.pyc and *.pyo files and then delete them
find . -name *.py[co] -delete
