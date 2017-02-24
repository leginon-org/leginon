#!/usr/bin/env python
import sys
import time
import socket
from leginon import databinder
from leginon import event
from leginon import datatransport

'''
This is a datatransport test for passing numpy array across the network.
test1_array_transport.py is opens a server ready to serve printData to
the client that will be opened by test2_array_transport.py and requests
printData as ArrayPassingEvent.
'''
if len(sys.argv) != 3:
   print 'usage:   test2_array_transport.py <remote_host> <remote_port>'
   sys.exit(1)

yourhostname = sys.argv[1]
yourport = int(sys.argv[2])

def printData(d):
   remotehost = d['location']['TCP transport']['hostname']
   remoteport = d['location']['TCP transport']['port']
   print 'got array',d['array'].shape

class Logger(object):
   def info(self, stuff):
      print 'INFO', stuff
   def exception(self, stuff):
      print 'EXCEPTION', stuff
   def warning(self, stuff):
      print 'WARNING', stuff

myhostname = socket.gethostname().lower()

for myport in range(49152,65536):
   try:
      db = databinder.DataBinder(myhostname, Logger(), tcpport=myport)
      break
   except:
      continue
print 'ACCEPTING CONNECTIONS AT:  %s:%s' % (myhostname, myport)

db.addBinding(myhostname, event.ArrayPassingEvent, printData)

mylocation = {'TCP transport': {'hostname': myhostname, 'port': myport}}
yourlocation = {'TCP transport': {'hostname': yourhostname, 'port': yourport}}

e = event.SetManagerEvent(destination=yourhostname, location=mylocation)
print 'CONNECTING TO:  %s:%s' % (yourhostname, yourport)
client = datatransport.Client(yourlocation, Logger())

## this will connect to the server opened by test1_array_transport.py
for i in range(3):
	client.send(e)
	# a two second pause is typical for the socket to reset and
	# ready to be used again.  Failed at 1 second.
	time.sleep(2)
raw_input('hit enter to kill')
db.exit()
