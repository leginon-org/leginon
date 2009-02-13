#!/usr/bin/env python
import databinder
import socket
import event
import datatransport
import sys
import time

if len(sys.argv) != 3:
   print 'usage:   test2.py <remote_host> <remote_port>'
   sys.exit(1)

tecnaihost = sys.argv[1]
tecnaiport = int(sys.argv[2])

def printData(d):
   remotehost = d['location']['TCP transport']['hostname']
   remoteport = d['location']['TCP transport']['port']
   print 'REMOTE CLIENT RESPONDED:  %s:%s' % (remotehost, remoteport)

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

db.addBinding(myhostname, event.NodeAvailableEvent, printData)

mylocation = {'TCP transport': {'hostname': myhostname, 'port': myport}}
yourlocation = {'TCP transport': {'hostname': tecnaihost, 'port': tecnaiport}}

e = event.SetManagerEvent(destination=tecnaihost, location=mylocation)
print 'CONNECTING TO:  %s:%s' % (tecnaihost, tecnaiport)
client = datatransport.Client(yourlocation, Logger())

## this will connect to the tecnai
client.send(e)

raw_input('hit enter to kill')
db.exit()
