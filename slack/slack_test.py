import os
import socket
import slack_interface

sc = slack_interface.slack_interface()
print(sc.send_message('testchannel',"You have successfully configured Slack for Leginon!",checkchannel=True))

