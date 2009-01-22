#!/usr/bin/env python
'''
This simulates a robot server that checks a database for signals/attributes.
'''

import robot2
import time

def getAttributesFromDB():
	'''
	Get the latest attributes from the database.
	'''
	myquery = robot2.RobotAttributes()
	robotattrs = myquery.query(results=1)
	if robotattrs:
		# Only get the latest one, but we should think about getting
		# all of them since the last time we checked
		robotattrs = robotattrs[0]
	else:
		# none in the database, return a default empty object
		robotattrs = robot2.RobotAttributes()
	return robotattrs

def setAttributeToDB(name, value):
	## get the latest attrs from DB
	attrs = getAttributesFromDB()
	## make a copy
	attrs = robot2.RobotAttributes(initializer=attrs)
	## update the new attr
	attrs[name] = value
	## store new object back to DB
	attrs.insert(force=True)


class RobotServer(object):
	def __init__(self):
		self.attrs_from_db = getAttributesFromDB()

	def mainloop(self):
		while True:
			### check for changes from DB
			newattrs = getAttributesFromDB()
			oldattrs = self.attrs_from_db
			for key,value in newattrs.items():
				if newattrs[key] != oldattrs[key]:
					## something changed, look for method to handle it
					method_name = 'handle_' + key
					try:
						method = getattr(self, method_name)
						# call handler method, give it the new value
						method(value)
					except:
						## no handler method, do nothing
						pass
			self.attrs_from_db = newattrs
			# check for changes in robot status
			changed = self.checkRobot()
			for name,value in changed:
				setAttributeToDB(name, value)
			time.sleep(1)

	def handle_Signal11(self, value):
		'Handles a change in the value of Signal11'
		print 'I got Signal11 = ', value

	def checkRobot(self):
		return []
		
if __name__ == '__main__':
	rs = RobotServer()
	rs.mainloop()
