#!/usr/bin/env python
import time
import socket
import numpy
from leginon import databinder
from leginon import event
from leginon import datatransport

'''
This is a datatransport test for passing numpy array across the network.
test1_array_transport.py is opens a server ready to serve printData to
the client that will be opened by test2_array_transport.py and requests
printData as ArrayPassingEvent.
'''

# constants that defines the array. modify these to pass different size
# and type of array
ARRAY_SHAPE = (4096,4096)
ARRAY_DTYPE = numpy.uint32


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
   # create the ArrayPassingEvent with the array
   shape = ARRAY_SHAPE
   array_to_pass = numpy.ones(ARRAY_SHAPE,ARRAY_DTYPE)
   e = event.ArrayPassingEvent(location=myloc, destination=managerhost,array=array_to_pass)
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
