#!/usr/bin/python -O
import sys
import re

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print "Usage: ./genScriptSumm.py function.py"
		sys.exit(1)
	file = sys.argv[1];
	f = open(file, "r")
	function = False
	comment = False
	for line in f:
		commentLine = re.match("^\t*[\"']{3}",line)
		if re.match("^def _?[a-z]",line):
			function = True
			print line.strip()
		elif(comment and commentLine):
			#print "comment off"
			comment = False
			function = False
			#print line.strip()
		elif(function and commentLine):
			#print "comment on"
			comment = True 
			#print line.strip()
		elif(comment):
			print "\t## ",line.strip()
