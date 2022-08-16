import os
import configparser
import pyami.fileutil

# Help functions to get Slack configuration data.

# Locate slack.cfg, which should be placed in any of the same locations as leginon.cfg (e.g. /etc/myami/, /home/username/)

def getSlackConfig(printfiles=False):
	slackconfigparser = configparser.ConfigParser()
	confdirs = pyami.fileutil.get_config_dirs()
	conf_files = [os.path.join(confdir, 'slack.cfg') for confdir in confdirs]
	pyami.fileutil.check_exist_one_file(conf_files)
	# Combine sections of the same name from all existing files in conf_files
	configfiles = slackconfigparser.read(conf_files)
	if printfiles:
		print("***************************")
		print("Config files are:")
		
		for config in configfiles:
			print(config)

		print("***************************")

	return configfiles

def getSlackData():

	slackdict = {}
	slackconfig = configparser.ConfigParser()
	slackconfig.read(getSlackConfig())
	for option in slackconfig.options('config'):
		slackdict[option] = slackconfig.get('config',option)
	return slackdict


if __name__ == '__main__':
	getSlackConfig(printfiles=True)
