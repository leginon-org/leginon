#!/usr/env/bin python

import os
from slack_leginon import slackconfigparser
import subprocess
import sys

from optparse import OptionParser
from slack import WebClient as SlackClient

#Using slackclient 2.9.4

# class to manage leginon and appion interactions with slack.
class SlackInterface(SlackClient):
	def __init__(self):

		slackconfig = slackconfigparser.getSlackData()
		self.check_channel = slackconfig['check_channel'] if 'check_channel' in slackconfig.keys() and (slackconfig['check_channel']).lower() == 'true' else False
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
		if self.check_channel and name not in self.getChannelNames():
			raise ValueError('Channel %s does not exist' % name)
		self.default_channel = name

	# send a message to a certain channel. check_channel flag in slack.cfg will check if the channel exists, and create it if not.
	# if check_channel is false and a channel does not exist, slack will return an error.
	def sendMessage(self,slackchannel,message):

		#print("Token: ",self.slack_token)
		#print("Channel: ",slackchannel)

		if self.check_channel is True:
			if slackchannel in self.getChannelNames():
				return self.client.chat_postMessage(
						channel=slackchannel,
						text=message)
			else:
				print(( 'Channel '+slackchannel+' does not exist; Please create channel in Slack.'))

		return self.client.chat_postMessage(
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
	(options, args) = parser.parse_args()

	if options.channel and options.message:
		slackchannel = options.channel
		message = options.message

		sc = client.sendMessage(slackchannel,message)
		print(sc)


	else:
		parser.print_help()


