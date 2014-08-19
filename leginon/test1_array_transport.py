#!/usr/bin/env python
import databinder
import time
import event
import socket
import datatransport
import numpy

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
   del myloc['local transport']
   shape = (4096,4096)
   e = event.ArrayPassingEvent(location=myloc, destination=managerhost,array=numpy.ones(shape))
   t0 = time.time()
   client.send(e)
   t1 = time.time()
   print 'Event Sent Time (sec)', t1 - t0

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
