#!/usr/bin/env python

# borrowed the basic structure of this file from EM.py

import node
import datahandler
import scopedict
import data
import event
import sys
import MySQLdb
import presettable
import threading
import cPickle

class DataHandler(datahandler.DataBinder):
	def __init__(self, id, lock, table, DBnode):
		datahandler.DataBinder.__init__(self, id)
		self.lock = lock
		self.table = table
		self.DBnode = DBnode

	def query(self, id):
		# convert id to string for mysql
		idstr = cPickle.dumps(id)

		self.lock.acquire()

		## query DB for this id
		row = self.table[idstr]
		del row['leginonid']
		result = data.DBData(id, row)

		self.lock.release()
		return result

	def insert(self, idata):
		if isinstance(idata, event.Event):
			datahandler.DataBinder.insert(self, idata)
		elif isinstance(idata, data.DBData):
			self.lock.acquire()
			rowdict = idata.content
			## insert this rowdict into the sqltable
			newid = idata.id
			newidstr = cPickle.dumps(newid)
			self.table[newidstr] = rowdict
			self.lock.release()

	# borrowed from NodeDataHandler
	def setBinding(self, eventclass, func):
		if issubclass(eventclass, event.Event):
			datahandler.DataBinder.setBinding(self, eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')

class DBTable(node.Node):
	def __init__(self, id, nodelocations, dbhost, dbuser, dbpasswd, dbname, tablename, presetspec):
	#def __init__(self, id, nodelocations, dbconnectdict, tablename):
		#self.db = MySQLdb.connect(**dbconnectdict)
		self.db = MySQLdb.connect(host=dbhost,user=dbuser,passwd=dbpasswd,db=dbname)
		self.tablename = tablename
		self.table = presettable.Presets(self.db, self.tablename, presetspec)
		# internal
		self.lock = threading.Lock()
		# external
		self.nodelock = threading.Lock()
		self.locknodeid = None

		node.Node.__init__(self, id, nodelocations, DataHandler, (self.lock, self.table, self))

		self.addEventInput(event.LockEvent, self.lock)
		self.addEventInput(event.UnlockEvent, self.unlock)

		self.start()

	def main(self):
		self.addEventOutput(event.ListPublishEvent)
		ids = []
		if self.db:
			## get field names from this table
			#ids.append(...)
			pass
		e = event.ListPublishEvent(self.ID(), ids)
		self.outputEvent(e)

	def lock(self, ievent):
		if ievent.id[-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent.id[-1]
		self.confirmEvent(ievent)

	def unlock(self, ievent):
		if ievent.id[-1] == self.locknodeid:
			self.locknodeid = None
			self.nodelock.release()

if __name__ == '__main__':
	import signal

	myid = ('dbtable',)
	foo = DBTable(myid, None, 'localhost', 'pulokas', 'jimbo5', 'jimtest', 'mypresets2', ())
	signal.pause()
