import os
import socket
from . import slack_interface

sc = slack_interface.SlackInterface()
dc = sc.getDefaultChannel()
print((sc.sendMessage(dc,"You have successfully configured Slack for Leginon!",checkchannel=True)))

