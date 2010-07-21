import os.path
import inspect

def getPath(filename):
	this_file = inspect.currentframe().f_code.co_filename
	return os.path.join(os.path.dirname(this_file), filename)

