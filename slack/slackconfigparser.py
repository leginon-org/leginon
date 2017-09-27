import os
import ConfigParser
import pyami.fileutil

def getSlackConfig():
	slackconfigparser = ConfigParser.SafeConfigParser()
	confdirs = pyami.fileutil.get_config_dirs()
	conf_files = [os.path.join(confdir, 'slack.cfg') for confdir in confdirs]
	pyami.fileutil.check_exist_one_file(conf_files)
	configfiles = slackconfigparser.read(conf_files)
	print("configfiles:",configfiles)

	return configfiles

def getSlackData():

	slackdict = {}
	slackconfig = ConfigParser.ConfigParser()
	slackconfig.read(getSlackConfig())
	for option in slackconfig.options('config'):
		slackdict[option] = slackconfig.get('config',option)
	#slackdict['slack_token'] = slackconfig.get('config','slack_token')
	#slackdict['virtualenv_path'] = slackconfig.get('config','virtualenv_path')
	return slackdict
