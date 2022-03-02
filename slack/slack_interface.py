#!/usr/env/bin python

import os
from . import slackconfigparser
import subprocess
import sys

from optparse import OptionParser
from slackclient import SlackClient

#Using slackclient 1.0.0 for now until we upgrade to python2.7 (at least). The latest version, 1.0.9, does not work.

# class to manage leginon and appion interactions with slack.
class SlackInterface(SlackClient):
	def __init__(self):

		slackconfig = slackconfigparser.getSlackData()
		
		self.slack_token = slackconfig['slack_token']
		if 'virtualenv_path' in list(slackconfig.keys()) and slackconfig['virtualenv_path']:
			self.virtualenv_path = slackconfig['virtualenv_path']+"activate.csh"
			print(("Virtualenv path: ",self.virtualenv_path))
		#self.slack_token = os.environ["SLACK_TOKEN"]
		#self.virtualenv_path = os.environ["SLACK_ENV"]+"activate.csh"

		self.client = SlackClient(self.slack_token)
		self.default_channel = 'general'
		if 'default_channel' in list(slackconfig.keys()):
			self.setDefaultChannel(slackconfig['default_channel'])


	def getDefaultChannel(self):
		return self.default_channel

	def setDefaultChannel(self,name):
		if name not in self.getChannelNames():
			raise ValueError('Channel %s does not exist' % name)
		self.default_channel = name

	# send a message to a certain channel. Optional checkchannel flag will check if the channel exists, and create it if not.
	# if checkchannel is false and a channel does not exist, slack will return an error.
	def sendMessage(self,slackchannel,message,checkchannel=True):

		#print("Token: ",self.slack_token)
		#print("Channel: ",slackchannel)

		if checkchannel is True:
			if slackchannel in self.getChannelNames():
				return self.client.api_call(
						"chat.postMessage",
						channel=slackchannel,
						text=message)
			else:
				self.client.api_call('channels.create',name=slackchannel,validate=True)
				print(( 'Channel '+slackchannel+' does not exist; creating channel.'))

		return self.client.api_call(
				"chat.postMessage",
				channel=slackchannel,
				text=message)	

	# get the normalized names of all the channels in the slack workspace.
	def getChannelNames(self):
		channels = self.client.api_call('conversations.list')
		names = []
		for channel in channels['channels']:
			        names.append(channel['name_normalized'])
		return names

if __name__ == "__main__":
	client = SlackInterface()

	parser = OptionParser(usage="usage: slack_interface.py [options]", version="0.1")
	parser.add_option("-c","--channel",action="store",type="string",dest="channel")
	parser.add_option("-m","--message",action="store",type="string",dest="message")
	parser.add_option("--checkchannel",action="store_true",default=False,dest="checkchannel")
	(options, args) = parser.parse_args()

	if options.channel and options.message:
		slackchannel = options.channel
		message = options.message

		sc = client.sendMessage(slackchannel,message,checkchannel=options.checkchannel)
		print(sc)


	else:
		parser.print_help()


