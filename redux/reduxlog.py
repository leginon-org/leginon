
import sys
import logging
import logging.handlers
import redux.reduxconfig

LOG_FILE = redux.reduxconfig.config['log file']
LOG_LEVEL = logging.DEBUG
LOG_DURATION = 1   # applied to unit below
LOG_DURATION_UNIT = 'D'  # S, M, H, D, W
LOG_KEEP = 10  # how many logs to keep in backup rotation

logger = None

def setup():
	global logger
	if logger is not None:
		return
	logger = logging.getLogger('redux')
	logger.setLevel(LOG_LEVEL)

	handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when=LOG_DURATION_UNIT, interval=LOG_DURATION, backupCount=LOG_KEEP)

	logger.addHandler(handler)

	## pipe stderr and stdout through the logger
	class Stdout(object):
		def write(self, s):
			if s.endswith('\n'):
				s = s[:-1]
			logger.info(s)
	class Stderr(object):
		def write(self, s):
			if s.endswith('\n'):
				s = s[:-1]
			logger.error(s)
	sys.stdout = Stdout()
	sys.stderr = Stderr()

