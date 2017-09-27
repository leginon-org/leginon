#!/usr/env/bin python

import os
import slackconfigparser
import subprocess
import sys

from optparse import OptionParser
from slackclient import SlackClient



class slack_interface:
	def __init__(self):

		slackconfig = slackconfigparser.getSlackData()
		
		self.slack_token = slackconfig['slack_token']
		self.virtualenv_path = slackconfig['virtualenv_path']+"activate.csh"


		#self.slack_token = os.environ["SLACK_TOKEN"]
		#self.virtualenv_path = os.environ["SLACK_ENV"]+"activate.csh"

		self.client = SlackClient(self.slack_token)


	def send_message(self,slackchannel,message):
		#print("Token: ",self.slack_token)
		#print("Channel: ",slackchannel)
		return self.client.api_call(
				"chat.postMessage",
				channel=slackchannel,
				text=message)


if __name__ == "__main__":
	client = slack_interface()
	#print(client.slack_token)
	#print(client.virtualenv_path)
	#print(client.client)
	#print(client.client.api_call("api.test"))

	parser = OptionParser(usage="usage: slack_interface.py [options]", version="0.1")
	parser.add_option("-c","--channel",action="store",type="string",dest="channel")
	parser.add_option("-m","--message",action="store",type="string",dest="message")
	(options, args) = parser.parse_args()

	if options.channel and options.message:
		if options.channel[0] == "#":
			slackchannel = options.channel
		else:
			slackchannel = "#"+options.channel

		message = options.message


		#print(options)
		#if len(sys.argv[1:]) == 0:
		#	parser.print_help()
		#else:
		#        a = client.send_message(slackchannel,message)
		#	print(a)
		a = client.send_message(slackchannel,message)
		print(a)


	else:
		#len(sys.argv[1:]) == 0:
		parser.print_help()


