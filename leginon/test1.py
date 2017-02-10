#!/usr/bin/env python
import databinder
import time
import event
import socket
import datatransport

class Logger(object):
   def info(self, stuff):
      print 'INFO', stuff
   def exception(self, stuff):
      print 'EXCEPTION', stuff
   def warning(self, stuff):
      print 'WARNING', stuff

def printData(d):
   manlocation = d['location']
   managerhost = manlocation['TCP transport']['hostname']
   managerport = manlocation['TCP transport']['port']
   print 'MANAGER:  %s:%s' % (managerhost, managerport)
   print 'connecting to manager...'
   client = datatransport.Client(manlocation, Logger())
   myloc = db.location()
   print 'MYLOC', myloc
   del myloc['local transport']
   e = event.NodeAvailableEvent(location=myloc, destination=managerhost)
   client.send(e)

myhostname = socket.gethostname().lower()

for myport in range(49152,65536):
   try:
      db = databinder.DataBinder(myhostname, Logger(), tcpport=myport)
      break
   except:
      continue

db.addBinding(myhostname, event.SetManagerEvent, printData)

print 'ACCEPTING CONNECTIONS AT:  %s:%s' % (myhostname, myport)

raw_input('hit enter to kill')
db.exit()
