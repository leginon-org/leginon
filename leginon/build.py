#!/usr/bin/env python

import tarfile
import zipfile
import sys

try:
	sys.argv[1]
except IndexError:
	print 'No file name specified.'
	sys.exit(1)

buildfiles = []
for directory in sys.argv[2:]:
	directory += '/'
	print directory
	try:
		files = open(directory + 'buildfiles.txt')
	except:
		pass
	buildfiles += map(lambda x: directory + x[:-1], files.readlines())

if not buildfiles:
	print 'Building in local directory'
	try:
		buildfiles = open('buildfiles.txt')
		buildfiles = map(lambda x: x[:-1], buildfiles.readlines())
	except:
		print 'Cannot open buildfiles.txt'
		sys.exit(1)

print 'Building %s.tar.gz...' % sys.argv[1],
try:
	tar = tarfile.open(sys.argv[1] + '.tar.gz', 'w:gz')
except:
	print 'Cannot create tar file %s' % sys.argv[1]
else:
	for buildfile in buildfiles:
		try:
			tar.add(buildfile, sys.argv[1] + '/' + buildfile)
		except:
			print 'Cannot add file %s' % buildfile
	tar.close()
	print 'completed.'

print 'Building %s.zip...' % sys.argv[1],
try:
	zip = zipfile.ZipFile(sys.argv[1] + '.zip', 'w', zipfile.ZIP_DEFLATED)
except:
	print 'Cannot create zip file %s' % sys.argv[1]
else:
	for buildfile in buildfiles:
		try:
			zip.write(buildfile, sys.argv[1] + '/' + buildfile)
		except:
			print 'Cannot add file %s' % buildfile
	zip.close()
	print 'completed.'

