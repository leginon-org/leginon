#!/usr/bin/env python
print(" Usage: Run this as python2.7 script with 2to3 installed")
option=''
pattern = raw_input('Directory to check (i.e., redux/pipes/)  ')
pattern +='*.py'
import glob

files = glob.glob(pattern)
if files:
	print('creating 2to3 test shell from %s' % (pattern,))
	answer = raw_input('Ready to write ? (Y/y/N/n)')
	if answer.lower() == 'y':
		option = '-w '
else:
	print('Error: No files found')
out = open('2to3test.sh','w')
for f in files:
	out.write('2to3 %s%s\n' % (option,f))
out.close()
print('Done. Please run "source 2to3test.sh"')
