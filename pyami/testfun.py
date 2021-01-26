#!/usr/bin/python

def printResult(module_str,is_success, extra=None):
	if is_success:
		output = '%s [OK]' % (module_str,)
	else:
		output = '%s [NOT OK]' % (module_str,)
	if extra:
		output +='\n\t%s' % (extra,)
	print(output)
	return output
