#!/usr/bin/env python
import sys
if len(sys.argv) < 2:
	"check module import and show where it is imported from"
	"Usage: check_import.py <python module name>"
module_name = sys.argv[1]
print 'Here are the pathes the program looks for in module import'
print '------------'
print sys.path
print '------------'
print ''
print 'Attempt to import %s' % module_name
#import importlib
#i = importlib.import_module(module_name)
i = __import__(module_name)
print 'Successful import should give you the path it is imported from below'
print '------------'
print i
